"""
scratch/sprint15b/feature_importance.py

Task 2: Feature Contribution Audit.
Computes multi-level permutation importance for features, sensors, and groups on a representative test subset.
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

# Feature column specs
with open("artifacts/feature_columns_v3.json") as f:
    v3_cols = json.load(f)
GOES_COLS = v3_cols["goes"]
SOLEXS_COLS = v3_cols["solexs"]
HEL1OS_COLS = v3_cols["hel1os"]
ALL_COLS = GOES_COLS + SOLEXS_COLS + HEL1OS_COLS

# Feature groups mapping
GROUPS = {
    "Flux": ["short_flux", "long_flux", "log_long_flux"],
    "Counts": [c for c in SOLEXS_COLS if "counts" in c] + [c for c in HEL1OS_COLS if "counts" in c],
    "Rates": [c for c in SOLEXS_COLS if "rate" in c] + [c for c in HEL1OS_COLS if "rate" in c],
    "Temporal": ["minutes_since_last_flare"],
    "Derived": ["mean_15m", "variance_15m", "mean_60m", "variance_60m", "peak_30m", "peak_60m", "flux_gradient_5m", "flux_gradient_15m", "flux_acceleration_5m", "flux_acceleration_15m"]
}

def compute_tss(y_true, y_pred):
    tp = np.sum((y_true == 1) & (y_pred == 1))
    fp = np.sum((y_true == 0) & (y_pred == 1))
    fn = np.sum((y_true == 1) & (y_pred == 0))
    tn = np.sum((y_true == 0) & (y_pred == 0))
    pod = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    pofd = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    return pod - pofd

def run_evaluation_on_shuffled_dataset(model, dataset, subset_indices, device, best_th, evaluator, shuffle_spec):
    # Backup original arrays
    orig_goes = dataset.features_goes.copy()
    orig_solexs = dataset.features_solexs.copy()
    orig_hel1os = dataset.features_hel1os.copy()
    
    # Apply shuffles on the full time series arrays
    np.random.seed(42)
    if "goes" in shuffle_spec:
        for col_idx in shuffle_spec["goes"]:
            np.random.shuffle(dataset.features_goes[:, col_idx])
    if "solexs" in shuffle_spec:
        for col_idx in shuffle_spec["solexs"]:
            np.random.shuffle(dataset.features_solexs[:, col_idx])
    if "hel1os" in shuffle_spec:
        for col_idx in shuffle_spec["hel1os"]:
            np.random.shuffle(dataset.features_hel1os[:, col_idx])
            
    # Run evaluation on subset only
    subset_ds = Subset(dataset, subset_indices)
    loader = DataLoader(subset_ds, batch_size=256, shuffle=False, num_workers=0, pin_memory=False)
    probs, targets, _, _ = evaluate_simple(model, loader, device)
    logits = np.log(probs / (1.0 - probs + 1e-9))
    cal_probs = evaluator.calibrate_probabilities(logits, method="isotonic")
    preds = (cal_probs >= best_th).astype(int)
    
    # Restore original arrays
    dataset.features_goes = orig_goes
    dataset.features_solexs = orig_solexs
    dataset.features_hel1os = orig_hel1os
    
    return compute_tss(targets, preds)

def main():
    device = get_device()
    logger.info("Loading model and datasets...")
    model = load_model(device)
    val_ds, test_ds = load_datasets()
    val_loader, test_loader = get_loaders(val_ds, test_ds)
    
    logger.info("Fitting calibrators and getting validation threshold...")
    evaluator, best_th = get_calibrators_and_threshold(model, val_loader, device)
    
    # Select 20,000 representative test samples for permutation evaluation speed
    np.random.seed(42)
    subset_size = 20000
    subset_indices = np.random.choice(len(test_ds), subset_size, replace=False)
    
    logger.info("Computing baseline subset TSS...")
    subset_ds = Subset(test_ds, subset_indices)
    subset_loader = DataLoader(subset_ds, batch_size=256, shuffle=False, num_workers=0, pin_memory=False)
    test_probs, test_targets, _, _ = evaluate_simple(model, subset_loader, device)
    test_logits = np.log(test_probs / (1.0 - test_probs + 1e-9))
    cal_probs = evaluator.calibrate_probabilities(test_logits, method="isotonic")
    baseline_preds = (cal_probs >= best_th).astype(int)
    baseline_tss = compute_tss(test_targets, baseline_preds)
    logger.info(f"Baseline Subset TSS: {baseline_tss:.6f}")
    
    importance_records = []
    
    # -------------------------------------------------------------
    # LEVEL 1: Feature-level permutation
    # -------------------------------------------------------------
    logger.info("Running Level 1: Feature-level permutation importance...")
    for idx, feature_name in enumerate(ALL_COLS):
        if feature_name in GOES_COLS:
            branch = "goes"
            col_idx = GOES_COLS.index(feature_name)
        elif feature_name in SOLEXS_COLS:
            branch = "solexs"
            col_idx = SOLEXS_COLS.index(feature_name)
        else:
            branch = "hel1os"
            col_idx = HEL1OS_COLS.index(feature_name)
            
        spec = {branch: [col_idx]}
        perm_tss = run_evaluation_on_shuffled_dataset(model, test_ds, subset_indices, device, best_th, evaluator, spec)
        importance = baseline_tss - perm_tss
        importance_records.append({
            "Level": "Feature",
            "Name": feature_name,
            "Baseline_TSS": baseline_tss,
            "Permuted_TSS": perm_tss,
            "Importance_TSS": importance
        })
        logger.info(f"  Feature {feature_name}: TSS drop = {importance:.6f}")
        
    # -------------------------------------------------------------
    # LEVEL 2: Sensor-level permutation
    # -------------------------------------------------------------
    logger.info("Running Level 2: Sensor-level permutation importance...")
    sensors = {
        "GOES": {"goes": list(range(len(GOES_COLS)))},
        "SoLEXS": {"solexs": list(range(len(SOLEXS_COLS)))},
        "HEL1OS": {"hel1os": list(range(len(HEL1OS_COLS)))}
    }
    for sensor_name, spec in sensors.items():
        perm_tss = run_evaluation_on_shuffled_dataset(model, test_ds, subset_indices, device, best_th, evaluator, spec)
        importance = baseline_tss - perm_tss
        importance_records.append({
            "Level": "Sensor",
            "Name": sensor_name,
            "Baseline_TSS": baseline_tss,
            "Permuted_TSS": perm_tss,
            "Importance_TSS": importance
        })
        logger.info(f"  Sensor {sensor_name}: TSS drop = {importance:.6f}")
        
    # -------------------------------------------------------------
    # LEVEL 3: Group-level permutation
    # -------------------------------------------------------------
    logger.info("Running Level 3: Group-level permutation importance...")
    for group_name, features in GROUPS.items():
        spec = {}
        for feature_name in features:
            if feature_name in GOES_COLS:
                spec.setdefault("goes", []).append(GOES_COLS.index(feature_name))
            elif feature_name in SOLEXS_COLS:
                spec.setdefault("solexs", []).append(SOLEXS_COLS.index(feature_name))
            elif feature_name in HEL1OS_COLS:
                spec.setdefault("hel1os", []).append(HEL1OS_COLS.index(feature_name))
                
        perm_tss = run_evaluation_on_shuffled_dataset(model, test_ds, subset_indices, device, best_th, evaluator, spec)
        importance = baseline_tss - perm_tss
        importance_records.append({
            "Level": "Group",
            "Name": group_name,
            "Baseline_TSS": baseline_tss,
            "Permuted_TSS": perm_tss,
            "Importance_TSS": importance
        })
        logger.info(f"  Group {group_name}: TSS drop = {importance:.6f}")
        
    # Compile and save
    df_importance = pd.DataFrame(importance_records)
    df_importance = df_importance.sort_values(by="Importance_TSS", ascending=False)
    
    os.makedirs("artifacts/sprint15b", exist_ok=True)
    df_importance.to_csv("feature_importance.csv", index=False)
    df_importance.to_csv("artifacts/sprint15b/feature_importance.csv", index=False)
    
    logger.info("Task 2 completed successfully.")
    print("FEATURE_CONTRIBUTION_AUDIT: PASS")

if __name__ == "__main__":
    main()
