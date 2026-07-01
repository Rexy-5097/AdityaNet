"""
scratch/sprint16a/temporal_robustness.py

Task 4: Temporal Robustness.
Splits the test set into monthly blocks, computes standard metrics, and performs
Kruskal-Wallis and Mann-Whitney U tests on sample-level Brier scores and bootstrapped TSS distributions.
"""

import os
import sys
import json
import logging
import numpy as np
import pandas as pd
from scipy.stats import kruskal, mannwhitneyu
from sklearn.metrics import roc_auc_score, average_precision_score

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bootstrap_analysis import compute_tss, compute_hss, compute_ece

def main():
    logger.info("Loading predictions cache...")
    cache = np.load("scratch/sprint16a/cached_predictions.npz")
    
    y_true = cache["test_targets"]
    y_prob = cache["test_probs_cal_iso"]
    ts = pd.to_datetime(cache["test_timestamps"])
    best_th = float(cache["validation_threshold"])
    
    # Create a DataFrame for grouping
    df = pd.DataFrame({
        "target": y_true,
        "prob": y_prob,
        "month": ts.to_period("M").astype(str),
        "brier_err": (y_prob - y_true) ** 2
    })
    
    months = sorted(df["month"].unique())
    logger.info(f"Identified monthly blocks: {months}")
    
    monthly_records = []
    sample_errors_by_month = {}
    bootstrap_tss_by_month = {}
    
    np.random.seed(42)
    
    for m in months:
        m_df = df[df["month"] == m]
        y_true_m = m_df["target"].values
        y_prob_m = m_df["prob"].values
        y_pred_m = (y_prob_m >= best_th).astype(int)
        
        # Sample errors (Brier scores)
        brier_errs = m_df["brier_err"].values
        sample_errors_by_month[m] = brier_errs
        
        # Calculate standard metrics
        tp = np.sum((y_true_m == 1) & (y_pred_m == 1))
        fp = np.sum((y_true_m == 0) & (y_pred_m == 1))
        fn = np.sum((y_true_m == 1) & (y_pred_m == 0))
        tn = np.sum((y_true_m == 0) & (y_pred_m == 0))
        
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        far = fp / (tp + fp) if (tp + fp) > 0 else 0.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        
        roc = float(roc_auc_score(y_true_m, y_prob_m)) if len(np.unique(y_true_m)) > 1 else 0.5
        pr = float(average_precision_score(y_true_m, y_prob_m)) if len(np.unique(y_true_m)) > 1 else 0.0
        tss = float(compute_tss(y_true_m, y_pred_m))
        hss = float(compute_hss(y_true_m, y_pred_m))
        brier = float(np.mean(brier_errs))
        ece = float(compute_ece(y_true_m, y_prob_m))
        
        # Bootstrap TSS for significance distribution comparison (1,000 iterations)
        N_m = len(y_true_m)
        boot_tss = []
        for _ in range(1000):
            boot_idx = np.random.choice(N_m, N_m, replace=True)
            y_t_b = y_true_m[boot_idx]
            y_p_b = y_prob_m[boot_idx]
            y_pred_b = (y_p_b >= best_th).astype(int)
            boot_tss.append(compute_tss(y_t_b, y_pred_b))
        bootstrap_tss_by_month[m] = np.array(boot_tss)
        
        monthly_records.append({
            "Month": m,
            "Sample_Count": N_m,
            "ROC-AUC": roc,
            "PR-AUC": pr,
            "TSS": tss,
            "HSS": hss,
            "Recall": recall,
            "Precision": precision,
            "FAR": far,
            "F1": f1,
            "Brier_Score": brier,
            "ECE": ece
        })
        logger.info(f"Month {m} | TSS: {tss:.4f} | Brier: {brier:.4f} | Count: {N_m}")
        
    df_metrics = pd.DataFrame(monthly_records)
    os.makedirs("artifacts/sprint16a", exist_ok=True)
    df_metrics.to_csv("artifacts/sprint16a/monthly_metrics.csv", index=False)
    
    # Statistical tests: Kruskal-Wallis across all months
    # 1. Sample-level errors
    kw_stat_err, kw_pval_err = kruskal(*[sample_errors_by_month[m] for m in months])
    # 2. Bootstrapped TSS
    kw_stat_tss, kw_pval_tss = kruskal(*[bootstrap_tss_by_month[m] for m in months])
    
    # Pairwise Mann-Whitney U test between consecutive months
    consecutive_mw_results = []
    for i in range(len(months) - 1):
        m1, m2 = months[i], months[i+1]
        
        # Errors comparison
        mw_stat_err, mw_pval_err = mannwhitneyu(sample_errors_by_month[m1], sample_errors_by_month[m2], alternative="two-sided")
        # TSS comparison
        mw_stat_tss, mw_pval_tss = mannwhitneyu(bootstrap_tss_by_month[m1], bootstrap_tss_by_month[m2], alternative="two-sided")
        
        consecutive_mw_results.append({
            "comparison": f"{m1} vs {m2}",
            "sample_error_mw_stat": float(mw_stat_err),
            "sample_error_p_value": float(mw_pval_err),
            "bootstrapped_tss_mw_stat": float(mw_stat_tss),
            "bootstrapped_tss_p_value": float(mw_pval_tss)
        })
        
    stats_out = {
        "kruskal_wallis_sample_errors": {
            "statistic": float(kw_stat_err),
            "p_value": float(kw_pval_err),
            "interpretation": "Significant differences in monthly sample errors" if kw_pval_err < 0.05 else "No significant differences in monthly sample errors"
        },
        "kruskal_wallis_bootstrapped_tss": {
            "statistic": float(kw_stat_tss),
            "p_value": float(kw_pval_tss),
            "interpretation": "Significant differences in monthly bootstrapped TSS distributions" if kw_pval_tss < 0.05 else "No significant monthly TSS differences"
        },
        "consecutive_months_pairwise_tests": consecutive_mw_results,
        "status": "PASS"
    }
    
    with open("artifacts/sprint16a/temporal_statistical_tests.json", "w") as f:
        json.dump(stats_out, f, indent=2)
        
    logger.info("Task 4 completed successfully. Results saved.")

if __name__ == "__main__":
    main()
