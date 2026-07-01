"""
scratch/sprint16a/confidence_distribution.py

Task 6: Class-wise Confidence.
Groups calibrated probabilities by TP, TN, FP, FN, and computes mean, variance,
and empirical overlap coefficients.
"""

import os
import json
import logging
import numpy as np

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def compute_overlap_coefficient(x, y, n_bins=100):
    if len(x) == 0 or len(y) == 0:
        return 0.0
    hist_x, _ = np.histogram(x, bins=n_bins, range=(0, 1), density=False)
    hist_y, _ = np.histogram(y, bins=n_bins, range=(0, 1), density=False)
    
    # Convert to probability density (sum to 1)
    px = hist_x / np.sum(hist_x) if np.sum(hist_x) > 0 else hist_x
    py = hist_y / np.sum(hist_y) if np.sum(hist_y) > 0 else hist_y
    
    return float(np.sum(np.minimum(px, py)))

def main():
    logger.info("Loading predictions cache...")
    cache = np.load("scratch/sprint16a/cached_predictions.npz")
    
    y_true = cache["test_targets"]
    y_prob = cache["test_probs_cal_iso"]
    best_th = float(cache["validation_threshold"])
    
    y_pred = (y_prob >= best_th).astype(int)
    
    # 1. Group by TP, TN, FP, FN
    tp_idx = (y_true == 1) & (y_pred == 1)
    tn_idx = (y_true == 0) & (y_pred == 0)
    fp_idx = (y_true == 0) & (y_pred == 1)
    fn_idx = (y_true == 1) & (y_pred == 0)
    
    groups = {
        "TP": y_prob[tp_idx],
        "TN": y_prob[tn_idx],
        "FP": y_prob[fp_idx],
        "FN": y_prob[fn_idx]
    }
    
    stats = {}
    for name, vals in groups.items():
        stats[name] = {
            "count": int(len(vals)),
            "mean": float(np.mean(vals)) if len(vals) > 0 else 0.0,
            "variance": float(np.var(vals)) if len(vals) > 0 else 0.0,
            "std": float(np.std(vals)) if len(vals) > 0 else 0.0
        }
        logger.info(f"Group {name} | Count: {stats[name]['count']} | Mean: {stats[name]['mean']:.4f} | Std: {stats[name]['std']:.4f}")
        
    # 2. Compute overlap coefficients
    overlaps = {
        "TP_vs_FP": compute_overlap_coefficient(groups["TP"], groups["FP"]),
        "TN_vs_FN": compute_overlap_coefficient(groups["TN"], groups["FN"]),
        "TP_vs_FN": compute_overlap_coefficient(groups["TP"], groups["FN"]),
        "TN_vs_FP": compute_overlap_coefficient(groups["TN"], groups["FP"]),
        "Positives_vs_Negatives": compute_overlap_coefficient(y_prob[y_true == 1], y_prob[y_true == 0]),
        "Correct_vs_Incorrect": compute_overlap_coefficient(
            y_prob[tp_idx | tn_idx],
            y_prob[fp_idx | fn_idx]
        )
    }
    
    for pair, val in overlaps.items():
        logger.info(f"Overlap coefficient for {pair}: {val:.4f}")
        
    output = {
        "group_statistics": stats,
        "overlap_coefficients": overlaps,
        "status": "PASS"
    }
    
    os.makedirs("artifacts/sprint16a", exist_ok=True)
    with open("artifacts/sprint16a/confidence_statistics.json", "w") as f:
        json.dump(output, f, indent=2)
        
    logger.info("Task 6 completed successfully. Results saved.")

if __name__ == "__main__":
    main()
