"""
scratch/sprint16a/uncertainty_analysis.py

Task 7: Prediction Uncertainty.
Correlates MC Dropout uncertainty with correctness, FPs, and FNs, and performs
statistical analysis of uncertainty distributions.
"""

import os
import json
import logging
import numpy as np
from scipy.stats import pearsonr, spearmanr, mannwhitneyu

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def main():
    logger.info("Loading predictions cache...")
    cache = np.load("scratch/sprint16a/cached_predictions.npz")
    
    subset_indices = cache["subset_indices"]
    uncertainty = cache["subset_uncertainty"]
    
    y_true_full = cache["test_targets"]
    y_prob_full = cache["test_probs_cal_iso"]
    best_th = float(cache["validation_threshold"])
    
    y_true = y_true_full[subset_indices]
    y_prob = y_prob_full[subset_indices]
    y_pred = (y_prob >= best_th).astype(int)
    
    # Calculate correctness and error categories
    correctness = (y_pred == y_true).astype(float)
    fp = ((y_true == 0) & (y_pred == 1)).astype(float)
    fn = ((y_true == 1) & (y_pred == 0)).astype(float)
    absolute_error = np.abs(y_prob - y_true)
    
    # 1. Compute correlation coefficients
    correlations = {}
    metrics_to_correlate = {
        "correctness": correctness,
        "false_positives": fp,
        "false_negatives": fn,
        "absolute_error": absolute_error
    }
    
    for name, arr in metrics_to_correlate.items():
        p_coef, p_pval = pearsonr(uncertainty, arr)
        s_coef, s_pval = spearmanr(uncertainty, arr)
        
        correlations[name] = {
            "pearson": {"coefficient": float(p_coef), "p_value": float(p_pval)},
            "spearman": {"coefficient": float(s_coef), "p_value": float(s_pval)}
        }
        logger.info(f"Uncertainty vs {name} | Pearson: {p_coef:.4f} (p={p_pval:.2e}) | Spearman: {s_coef:.4f} (p={s_pval:.2e})")
        
    # 2. Analyze uncertainty distributions for groups
    tp_idx = (y_true == 1) & (y_pred == 1)
    tn_idx = (y_true == 0) & (y_pred == 0)
    fp_idx = (y_true == 0) & (y_pred == 1)
    fn_idx = (y_true == 1) & (y_pred == 0)
    
    groups = {
        "TP": uncertainty[tp_idx],
        "TN": uncertainty[tn_idx],
        "FP": uncertainty[fp_idx],
        "FN": uncertainty[fn_idx],
        "Correct": uncertainty[y_pred == y_true],
        "Incorrect": uncertainty[y_pred != y_true]
    }
    
    group_stats = {}
    for name, vals in groups.items():
        group_stats[name] = {
            "count": int(len(vals)),
            "mean": float(np.mean(vals)) if len(vals) > 0 else 0.0,
            "std": float(np.std(vals)) if len(vals) > 0 else 0.0,
            "median": float(np.median(vals)) if len(vals) > 0 else 0.0
        }
        logger.info(f"Group {name} Uncertainty | Mean: {group_stats[name]['mean']:.4f} | Std: {group_stats[name]['std']:.4f}")
        
    # 3. Statistical significance: Mann-Whitney U test between Correct vs Incorrect uncertainty
    mw_stat, mw_pval = mannwhitneyu(groups["Correct"], groups["Incorrect"], alternative="two-sided")
    logger.info(f"Mann-Whitney U test (Correct vs Incorrect uncertainty) | stat: {mw_stat:.4f} | p-value: {mw_pval:.2e}")
    
    output = {
        "correlations": correlations,
        "group_statistics": group_stats,
        "significance_tests": {
            "correct_vs_incorrect_uncertainty_mw": {
                "statistic": float(mw_stat),
                "p_value": float(mw_pval),
                "interpretation": "Incorrect predictions have significantly different uncertainty than correct ones" if mw_pval < 0.05 else "No significant difference in uncertainty"
            }
        },
        "status": "PASS"
    }
    
    os.makedirs("artifacts/sprint16a", exist_ok=True)
    with open("artifacts/sprint16a/uncertainty_analysis.json", "w") as f:
        json.dump(output, f, indent=2)
        
    logger.info("Task 7 completed successfully. Results saved.")

if __name__ == "__main__":
    main()
