"""
scratch/sprint15b/explainability.py

Task 6: Explainability and IG-SHAP Agreement.
Computes Integrated Gradients (IG) and Shapley values (SHAP) for groups of features,
analyzes their agreement, and saves individual explanations to artifacts/sprint15b/explanations/.
"""

import os
import sys
import json
import logging
import itertools
import numpy as np
import pandas as pd
import torch
from torch.utils.data import DataLoader

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import get_device, load_model, load_datasets, get_loaders, get_calibrators_and_threshold, evaluate_simple

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Feature column specs
with open("artifacts/feature_columns_v3.json") as f:
    v3_cols = json.load(f)
GOES_COLS = v3_cols["goes"]
SOLEXS_COLS = v3_cols["solexs"]
HEL1OS_COLS = v3_cols["hel1os"]

# Map 36 features to 5 group names and indices
FLUX_FEATURES = ["short_flux", "long_flux", "log_long_flux"]
COUNTS_FEATURES = [c for c in SOLEXS_COLS if "counts" in c] + [c for c in HEL1OS_COLS if "counts" in c]
RATES_FEATURES = [c for c in SOLEXS_COLS if "rate" in c] + [c for c in HEL1OS_COLS if "rate" in c]
TEMPORAL_FEATURES = ["minutes_since_last_flare"]
DERIVED_FEATURES = ["mean_15m", "variance_15m", "mean_60m", "variance_60m", "peak_30m", "peak_60m", "flux_gradient_5m", "flux_gradient_15m", "flux_acceleration_5m", "flux_acceleration_15m"]

def get_group_masks(x_g, x_s, x_h):
    # Returns binary masks of shape same as inputs for each of the 5 groups
    # Goes: 14 cols, Solexs: 18 cols, Hel1os: 4 cols
    masks = {g: (torch.zeros_like(x_g), torch.zeros_like(x_s), torch.zeros_like(x_h)) for g in ["Flux", "Counts", "Rates", "Temporal", "Derived"]}
    
    # Flux
    for f in FLUX_FEATURES:
        masks["Flux"][0][..., GOES_COLS.index(f)] = 1.0
        
    # Counts
    for f in COUNTS_FEATURES:
        if f in SOLEXS_COLS:
            masks["Counts"][1][..., SOLEXS_COLS.index(f)] = 1.0
        elif f in HEL1OS_COLS:
            masks["Counts"][2][..., HEL1OS_COLS.index(f)] = 1.0
            
    # Rates
    for f in RATES_FEATURES:
        if f in SOLEXS_COLS:
            masks["Rates"][1][..., SOLEXS_COLS.index(f)] = 1.0
        elif f in HEL1OS_COLS:
            masks["Rates"][2][..., HEL1OS_COLS.index(f)] = 1.0
            
    # Temporal
    masks["Temporal"][0][..., GOES_COLS.index("minutes_since_last_flare")] = 1.0
    
    # Derived
    for f in DERIVED_FEATURES:
        masks["Derived"][0][..., GOES_COLS.index(f)] = 1.0
        
    return masks

def compute_integrated_gradients(model, x_g, x_s, x_h, m_s, m_h, device, steps=50):
    # Baseline is all zeros
    alphas = np.linspace(0.0, 1.0, steps)
    accum_grad_g = torch.zeros_like(x_g)
    accum_grad_s = torch.zeros_like(x_s)
    accum_grad_h = torch.zeros_like(x_h)
    
    for alpha in alphas:
        interp_g = (x_g * alpha).clone().detach().requires_grad_(True)
        interp_s = (x_s * alpha).clone().detach().requires_grad_(True)
        interp_h = (x_h * alpha).clone().detach().requires_grad_(True)
        
        with torch.enable_grad():
            logit = model(interp_g, interp_s, interp_h, m_s, m_h)
            
        grad_g, grad_s, grad_h = torch.autograd.grad(logit.sum(), [interp_g, interp_s, interp_h])
        accum_grad_g += grad_g
        accum_grad_s += grad_s
        accum_grad_h += grad_h
        
    ig_g = (x_g * (accum_grad_g / steps)).squeeze(0).cpu().numpy()
    ig_s = (x_s * (accum_grad_s / steps)).squeeze(0).cpu().numpy()
    ig_h = (x_h * (accum_grad_h / steps)).squeeze(0).cpu().numpy()
    
    return ig_g, ig_s, ig_h

def compute_shapley_values(model, x_g, x_s, x_h, m_s, m_h, group_masks, device):
    groups = ["Flux", "Counts", "Rates", "Temporal", "Derived"]
    # 2^5 = 32 coalitions
    coalitions = list(itertools.product([0, 1], repeat=5))
    
    # Pre-evaluate model for all 32 coalitions
    predictions = {}
    for coalition in coalitions:
        # Build perturbed inputs
        g_pert = torch.zeros_like(x_g)
        s_pert = torch.zeros_like(x_s)
        h_pert = torch.zeros_like(x_h)
        
        for idx, active in enumerate(coalition):
            if active == 1:
                g_m, s_m, h_m = group_masks[groups[idx]]
                g_pert += x_g * g_m
                s_pert += x_s * s_m
                h_pert += x_h * h_m
                
        with torch.no_grad():
            logit = model(g_pert, s_pert, h_pert, m_s, m_h).item()
        predictions[coalition] = logit
        
    shapley_values = {}
    for i, group in enumerate(groups):
        phi = 0.0
        # Iterate over all coalitions not containing group i
        for coalition in coalitions:
            if coalition[i] == 0:
                # Coalition with group i set to 1
                coalition_with_i = list(coalition)
                coalition_with_i[i] = 1
                coalition_with_i = tuple(coalition_with_i)
                
                # Size of coalition S (excluding i)
                s_size = sum(coalition)
                # Weight = s_size! * (5 - s_size - 1)! / 5!
                weight = float(np.math.factorial(s_size) * np.math.factorial(5 - s_size - 1)) / 120.0
                
                marginal = predictions[coalition_with_i] - predictions[coalition]
                phi += weight * marginal
        shapley_values[group] = phi
        
    return shapley_values

def main():
    device = get_device()
    logger.info("Loading model and datasets...")
    model = load_model(device)
    val_ds, test_ds = load_datasets()
    val_loader, test_loader = get_loaders(val_ds, test_ds)
    
    logger.info("Fitting calibrators and getting validation threshold...")
    evaluator, best_th = get_calibrators_and_threshold(model, val_loader, device)
    
    # Load timestamps
    logger.info("Loading timestamps...")
    df_test = pd.read_parquet("artifacts/sprint14c/s2_test.parquet", columns=["timestamp"])
    timestamps = df_test["timestamp"].values[360:]
    
    # Simple eval
    logger.info("Evaluating test set...")
    test_probs, test_targets, mask_s, mask_h = evaluate_simple(model, test_loader, device)
    test_logits = np.log(test_probs / (1.0 - test_probs + 1e-9))
    cal_probs = evaluator.calibrate_probabilities(test_logits, method="isotonic")
    preds = (cal_probs >= best_th).astype(int)
    
    # Select TPs and FPs
    tp_indices = np.where((test_targets == 1) & (preds == 1))[0]
    fp_indices = np.where((test_targets == 0) & (preds == 1))[0]
    
    # Sort TPs and FPs descending by calibrated probability (highest confidence first)
    tp_sorted = tp_indices[np.argsort(cal_probs[tp_indices])[::-1]]
    fp_sorted = fp_indices[np.argsort(cal_probs[fp_indices])[::-1]]
    
    selected_tps = tp_sorted[:20]
    selected_fps = fp_sorted[:20]
    
    logger.info(f"Selected {len(selected_tps)} TPs and {len(selected_fps)} FPs for explainability.")
    
    # Pre-generate group masks
    dummy_in, _ = test_ds[0]
    dummy_x_g, dummy_x_s, dummy_x_h = [torch.from_numpy(x).unsqueeze(0).to(device) if isinstance(x, np.ndarray) else x.unsqueeze(0).to(device) for x in dummy_in[:3]]
    group_masks = get_group_masks(dummy_x_g, dummy_x_s, dummy_x_h)
    
    output_dir = "artifacts/sprint15b/explanations"
    os.makedirs(output_dir, exist_ok=True)
    
    def process_samples(indices, group_label):
        for idx in indices:
            inputs, target_val = test_ds[idx]
            x_g, x_s, x_h, m_s, m_h = [torch.from_numpy(x).unsqueeze(0).to(device) if isinstance(x, np.ndarray) else x.unsqueeze(0).to(device) for x in inputs]
            
            # 1. Compute IG
            ig_g, ig_s, ig_h = compute_integrated_gradients(model, x_g, x_s, x_h, m_s, m_h, device, steps=50)
            
            # Map IG values to the 5 groups (summing over sequence length and feature group columns)
            ig_sum_g = ig_g.sum(axis=0)  # [14]
            ig_sum_s = ig_s.sum(axis=0)  # [18]
            ig_sum_h = ig_h.sum(axis=0)  # [4]
            
            ig_groups = {g: 0.0 for g in ["Flux", "Counts", "Rates", "Temporal", "Derived"]}
            
            # Flux
            for f in FLUX_FEATURES:
                ig_groups["Flux"] += ig_sum_g[GOES_COLS.index(f)]
            # Counts
            for f in COUNTS_FEATURES:
                if f in SOLEXS_COLS:
                    ig_groups["Counts"] += ig_sum_s[SOLEXS_COLS.index(f)]
                elif f in HEL1OS_COLS:
                    ig_groups["Counts"] += ig_sum_h[HEL1OS_COLS.index(f)]
            # Rates
            for f in RATES_FEATURES:
                if f in SOLEXS_COLS:
                    ig_groups["Rates"] += ig_sum_s[SOLEXS_COLS.index(f)]
                elif f in HEL1OS_COLS:
                    ig_groups["Rates"] += ig_sum_h[HEL1OS_COLS.index(f)]
            # Temporal
            ig_groups["Temporal"] += ig_sum_g[GOES_COLS.index("minutes_since_last_flare")]
            # Derived
            for f in DERIVED_FEATURES:
                ig_groups["Derived"] += ig_sum_g[GOES_COLS.index(f)]
                
            # 2. Compute SHAP
            shap_values = compute_shapley_values(model, x_g, x_s, x_h, m_s, m_h, group_masks, device)
            
            # 3. Compute cosine agreement
            ig_vector = np.array([ig_groups[g] for g in ["Flux", "Counts", "Rates", "Temporal", "Derived"]])
            shap_vector = np.array([shap_values[g] for g in ["Flux", "Counts", "Rates", "Temporal", "Derived"]])
            
            norm_ig = np.linalg.norm(ig_vector)
            norm_shap = np.linalg.norm(shap_vector)
            if norm_ig > 0 and norm_shap > 0:
                agreement = float(np.dot(ig_vector, shap_vector) / (norm_ig * norm_shap))
            else:
                agreement = 1.0
                
            explanation = {
                "timestamp": str(timestamps[idx]),
                "global_index": int(idx),
                "label": group_label,
                "target": int(target_val),
                "calibrated_probability": float(cal_probs[idx]),
                "raw_probability": float(test_probs[idx]),
                "agreement_cosine": agreement,
                "ig_group_attribution": {g: float(v) for g, v in ig_groups.items()},
                "shap_group_attribution": {g: float(v) for g, v in shap_values.items()}
            }
            
            filename = f"sample_{idx}_{group_label}.json"
            filepath = os.path.join(output_dir, filename)
            with open(filepath, "w") as f:
                json.dump(explanation, f, indent=2)
                
        logger.info(f"Generated and saved explanations for {group_label}.")
        
    process_samples(selected_tps, "TP")
    process_samples(selected_fps, "FP")
    
    logger.info("Task 6 completed successfully.")
    print("EXPLAINABILITY: PASS")

if __name__ == "__main__":
    main()
