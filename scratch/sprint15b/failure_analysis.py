"""
scratch/sprint15b/failure_analysis.py

Task 4: Failure Analysis with Clustering.
Identifies Top 100 False Positives and Top 100 False Negatives, clusters them using heuristics,
and saves the detailed results to failure_analysis.csv.
"""

import os
import sys
import json
import logging
import numpy as np
import pandas as pd
import torch
from torch.utils.data import DataLoader, Subset

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import get_device, load_model, load_datasets, get_loaders, evaluate_simple, get_calibrators_and_threshold

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Feature indices
LONG_FLUX_IDX = 1
SHORT_FLUX_IDX = 0
GRAD_15M_IDX = 10

def get_failure_cluster(target, pred, long_flux, grad_15m, mask_s, mask_h, idx, test_targets):
    """
    Categorizes the failure into one of 4 clusters: Data Gaps, Flux Spikes, Transition Period, Quiet Sun.
    """
    # 1. Data Gaps
    if mask_s == 0.0 or mask_h == 0.0:
        return "Data Gaps"
        
    # 2. Transition Period
    # Check if close to target transition (within 60 minutes)
    window = test_targets[max(0, idx - 60) : min(len(test_targets), idx + 61)]
    if len(np.unique(window)) > 1:
        return "Transition Period"
        
    # 3. Flux Spikes
    # If the gradient/acceleration is high
    if grad_15m > 0.05:
        return "Flux Spikes"
        
    # 4. Quiet Sun
    # Target is 0, prediction is 1, and flux is background level
    if target == 0 and pred == 1 and long_flux < 5e-6:
        return "Quiet Sun"
        
    return "Other / Indeterminate"

def main():
    device = get_device()
    logger.info("Loading model and datasets...")
    model = load_model(device)
    val_ds, test_ds = load_datasets()
    val_loader, test_loader = get_loaders(val_ds, test_ds)
    
    logger.info("Fitting calibrators and getting validation threshold...")
    evaluator, best_th = get_calibrators_and_threshold(model, val_loader, device)
    
    # Load timestamps from parquet
    logger.info("Loading timestamps...")
    df_test = pd.read_parquet("artifacts/sprint14c/s2_test.parquet", columns=["timestamp"])
    timestamps = df_test["timestamp"].values[360:]
    
    # Run simple evaluation to get baseline predictions
    logger.info("Evaluating test set...")
    test_probs, test_targets, mask_s, mask_h = evaluate_simple(model, test_loader, device)
    test_logits = np.log(test_probs / (1.0 - test_probs + 1e-9))
    cal_probs = evaluator.calibrate_probabilities(test_logits, method="isotonic")
    preds = (cal_probs >= best_th).astype(int)
    
    # Find all FP and FN indices
    fp_indices = np.where((test_targets == 0) & (preds == 1))[0]
    fn_indices = np.where((test_targets == 1) & (preds == 0))[0]
    
    logger.info(f"Test Set: {len(fp_indices)} FPs, {len(fn_indices)} FNs.")
    
    # Sort FPs descending by calibrated probability (highest confidence wrong prediction first)
    fp_sorted_indices = fp_indices[np.argsort(cal_probs[fp_indices])[::-1]]
    top_100_fps = fp_sorted_indices[:100]
    
    # Sort FNs ascending by calibrated probability (lowest probability wrong prediction first)
    fn_sorted_indices = fn_indices[np.argsort(cal_probs[fn_indices])]
    top_100_fns = fn_sorted_indices[:100]
    
    selected_indices = np.concatenate([top_100_fps, top_100_fns])
    
    # Compute MC Dropout uncertainty only on the selected 200 samples
    logger.info("Running MC Dropout (50 samples) on top 200 failure samples...")
    model.train() # Activate dropout
    uncertainties = {}
    
    # Batch the 200 samples for fast inference
    selected_ds = Subset(test_ds, selected_indices)
    selected_loader = DataLoader(selected_ds, batch_size=64, shuffle=False, num_workers=0, pin_memory=False)
    
    all_std_probs = []
    with torch.no_grad():
        for inputs, _ in selected_loader:
            x_g, x_s, x_h, m_s, m_h = [x.to(device) for x in inputs]
            batch_probs = []
            for _ in range(50):
                with torch.amp.autocast(device_type=device.type, enabled=True, dtype=torch.bfloat16):
                    logits = model(x_g, x_s, x_h, m_s, m_h)
                probs = torch.sigmoid(logits).squeeze(-1)
                batch_probs.append(probs)
                
            batch_probs = torch.stack(batch_probs, dim=0) # [50, B]
            std_p = batch_probs.std(dim=0).float().cpu().numpy()
            all_std_probs.extend(std_p)
            
    std_probs = np.array(all_std_probs)
    model.eval()
    
    # Map uncertainties back to global indices
    uncertainty_map = {idx: std_probs[i] for i, idx in enumerate(selected_indices)}
    
    # Build failure analysis records
    records = []
    for idx in selected_indices:
        inputs, target_val = test_ds[idx]
        x_g, x_s, x_h, m_s, m_h = inputs
        
        # Last step features
        goes_long_flux = float(x_g[-1, LONG_FLUX_IDX])
        goes_short_flux = float(x_g[-1, SHORT_FLUX_IDX])
        grad_15m = float(x_g[-1, GRAD_15M_IDX])
        
        availability_solexs = float(m_s)
        availability_hel1os = float(m_h)
        
        prob_raw = float(test_probs[idx])
        prob_cal = float(cal_probs[idx])
        pred_val = int(preds[idx])
        target_val = int(target_val)
        timestamp_str = str(timestamps[idx])
        unc_val = float(uncertainty_map[idx])
        
        cluster_name = get_failure_cluster(
            target_val, pred_val, goes_long_flux, grad_15m, 
            availability_solexs, availability_hel1os, idx, test_targets
        )
        
        records.append({
            "timestamp": timestamp_str,
            "raw_probability": prob_raw,
            "calibrated_probability": prob_cal,
            "target": target_val,
            "prediction": pred_val,
            "goes_long_flux": goes_long_flux,
            "goes_short_flux": goes_short_flux,
            "solexs_availability": availability_solexs,
            "hel1os_availability": availability_hel1os,
            "uncertainty": unc_val,
            "failure_cluster": cluster_name
        })
        
    df_failures = pd.DataFrame(records)
    
    # Write files
    os.makedirs("artifacts/sprint15b", exist_ok=True)
    df_failures.to_csv("failure_analysis.csv", index=False)
    df_failures.to_csv("artifacts/sprint15b/failure_analysis.csv", index=False)
    
    # Print cluster statistics for verification
    logger.info("Failure Cluster Statistics:")
    print(df_failures["failure_cluster"].value_counts())
    
    logger.info("Task 4 completed successfully.")
    print("FAILURE_ANALYSIS: PASS")

if __name__ == "__main__":
    main()
