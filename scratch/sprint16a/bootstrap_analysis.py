"""
scratch/sprint16a/bootstrap_analysis.py

Task 1: Bootstrap Confidence Intervals.
Computes 10,000 bootstrap iterations to calculate mean, std, median, IQR,
and 95% confidence intervals for ROC-AUC, PR-AUC, TSS, HSS, Brier Score, and ECE.
"""

import os
import sys
import json
import logging
import numpy as np
from sklearn.metrics import roc_auc_score, average_precision_score

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def compute_tss(y_true, y_pred):
    tp = np.sum((y_true == 1) & (y_pred == 1))
    fp = np.sum((y_true == 0) & (y_pred == 1))
    fn = np.sum((y_true == 1) & (y_pred == 0))
    tn = np.sum((y_true == 0) & (y_pred == 0))
    pod = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    pofd = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    return pod - pofd

def compute_hss(y_true, y_pred):
    tp = np.sum((y_true == 1) & (y_pred == 1))
    fp = np.sum((y_true == 0) & (y_pred == 1))
    fn = np.sum((y_true == 1) & (y_pred == 0))
    tn = np.sum((y_true == 0) & (y_pred == 0))
    N = tp + fp + fn + tn
    expected_correct = ((tp + fn) * (tp + fp) + (tn + fn) * (tn + fp)) / N if N > 0 else 0.0
    actual_correct = tp + tn
    numerator = actual_correct - expected_correct
    denominator = N - expected_correct
    return numerator / denominator if denominator > 0 else 0.0

def compute_ece(y_true, y_prob, n_bins=10):
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    for i in range(n_bins):
        bin_lower = bin_boundaries[i]
        bin_upper = bin_boundaries[i+1]
        in_bin = (y_prob >= bin_lower) & (y_prob < bin_upper)
        prop_in_bin = np.mean(in_bin)
        if prop_in_bin > 0:
            accuracy_in_bin = np.mean(y_true[in_bin])
            avg_confidence_in_bin = np.mean(y_prob[in_bin])
            ece += prop_in_bin * np.abs(avg_confidence_in_bin - accuracy_in_bin)
    return ece

def main():
    logger.info("Loading predictions cache...")
    cache = np.load("scratch/sprint16a/cached_predictions.npz")
    
    # Validation threshold
    best_th = float(cache["validation_threshold"])
    
    # We will run bootstrapping on the 20,000 representative test subset for speed and stability
    subset_indices = cache["subset_indices"]
    
    test_targets_full = cache["test_targets"]
    test_probs_cal_iso_full = cache["test_probs_cal_iso"]
    
    y_true = test_targets_full[subset_indices]
    y_prob = test_probs_cal_iso_full[subset_indices]
    
    N = len(y_true)
    logger.info(f"Running 10,000 bootstrap iterations on {N} samples...")
    
    np.random.seed(42)
    
    roc_list = []
    pr_list = []
    tss_list = []
    hss_list = []
    brier_list = []
    ece_list = []
    
    # Run 10,000 iterations
    for it in range(10000):
        boot_idx = np.random.choice(N, N, replace=True)
        y_true_b = y_true[boot_idx]
        y_prob_b = y_prob[boot_idx]
        y_pred_b = (y_prob_b >= best_th).astype(int)
        
        # Compute metrics
        roc = float(roc_auc_score(y_true_b, y_prob_b))
        pr = float(average_precision_score(y_true_b, y_prob_b))
        tss = float(compute_tss(y_true_b, y_pred_b))
        hss = float(compute_hss(y_true_b, y_pred_b))
        brier = float(np.mean((y_prob_b - y_true_b) ** 2))
        ece = float(compute_ece(y_true_b, y_prob_b))
        
        roc_list.append(roc)
        pr_list.append(pr)
        tss_list.append(tss)
        hss_list.append(hss)
        brier_list.append(brier)
        ece_list.append(ece)
        
        if (it + 1) % 2000 == 0:
            logger.info(f"  Completed {it + 1} iterations...")
            
    # Calculate stats
    stats = {}
    metrics_map = {
        "ROC-AUC": roc_list,
        "PR-AUC": pr_list,
        "TSS": tss_list,
        "HSS": hss_list,
        "Brier_Score": brier_list,
        "ECE": ece_list
    }
    
    for metric_name, values in metrics_map.items():
        arr = np.array(values)
        mean_val = float(np.mean(arr))
        std_val = float(np.std(arr))
        median_val = float(np.median(arr))
        q75, q25 = np.percentile(arr, [75, 25])
        iqr_val = float(q75 - q25)
        ci_lower = float(np.percentile(arr, 2.5))
        ci_upper = float(np.percentile(arr, 97.5))
        
        stats[metric_name] = {
            "mean": mean_val,
            "std": std_val,
            "median": median_val,
            "iqr": iqr_val,
            "ci_95_lower": ci_lower,
            "ci_95_upper": ci_upper
        }
        logger.info(f"Metric {metric_name} | mean: {mean_val:.4f} | 95% CI: [{ci_lower:.4f}, {ci_upper:.4f}]")
        
    os.makedirs("artifacts/sprint16a", exist_ok=True)
    with open("artifacts/sprint16a/bootstrap_metrics.json", "w") as f:
        json.dump(stats, f, indent=2)
        
    logger.info("Task 1 completed successfully.")

if __name__ == "__main__":
    main()
