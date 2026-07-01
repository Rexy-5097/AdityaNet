"""
scratch/sprint16a/sensor_availability.py

Task 5: Sensor Availability.
Compares the baseline configuration against three masked configurations (GOES only, GOES + SoLEXS, GOES + HEL1OS).
Computes paired bootstrap tests and McNemar's tests for each.
"""

import os
import sys
import json
import logging
import numpy as np
from scipy.stats import chi2
from sklearn.metrics import roc_auc_score, average_precision_score

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bootstrap_analysis import compute_tss, compute_hss

def compute_basic_metrics(y_true, y_prob, threshold):
    y_pred = (y_prob >= threshold).astype(int)
    tp = np.sum((y_true == 1) & (y_pred == 1))
    fp = np.sum((y_true == 0) & (y_pred == 1))
    fn = np.sum((y_true == 1) & (y_pred == 0))
    tn = np.sum((y_true == 0) & (y_pred == 0))
    
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    tss = compute_tss(y_true, y_pred)
    hss = compute_hss(y_true, y_pred)
    
    # Try to compute ROC-AUC and PR-AUC, handle edge cases
    if len(np.unique(y_true)) > 1:
        roc = float(roc_auc_score(y_true, y_prob))
        pr = float(average_precision_score(y_true, y_prob))
    else:
        roc = 0.5
        pr = 0.0
        
    return {
        "ROC-AUC": roc,
        "PR-AUC": pr,
        "TSS": float(tss),
        "Recall": float(recall),
        "Precision": float(precision)
    }

def run_mcnemar_test(y_true, y_prob_base, y_prob_config, threshold):
    preds_base = (y_prob_base >= threshold).astype(int)
    preds_config = (y_prob_config >= threshold).astype(int)
    
    correct_base = (preds_base == y_true)
    correct_config = (preds_config == y_true)
    
    # contingency table cell counts:
    # b: base correct, config incorrect
    # c: base incorrect, config correct
    b = np.sum(correct_base & ~correct_config)
    c = np.sum(~correct_base & correct_config)
    
    if b + c == 0:
        stat = 0.0
        p_val = 1.0
    else:
        # Continuity-corrected McNemar's test
        stat = float((np.abs(b - c) - 1.0) ** 2 / (b + c))
        p_val = float(chi2.sf(stat, df=1))
        
    return {
        "stat": stat,
        "p_value": p_val,
        "b_base_correct_config_incorrect": int(b),
        "c_base_incorrect_config_correct": int(c)
    }

def main():
    logger.info("Loading predictions cache...")
    cache = np.load("scratch/sprint16a/cached_predictions.npz")
    
    y_true = cache["test_targets"]
    best_th = float(cache["validation_threshold"])
    
    configs = {
        "Baseline": cache["test_probs_cal_iso"],
        "GOES_Only": cache["test_probs_cal_iso_goes_only"],
        "GOES_SoLEXS": cache["test_probs_cal_iso_goes_solexs"],
        "GOES_HEL1OS": cache["test_probs_cal_iso_goes_hel1os"]
    }
    
    # 1. Compute point estimates
    point_estimates = {}
    for name, probs in configs.items():
        point_estimates[name] = compute_basic_metrics(y_true, probs, best_th)
        logger.info(f"Configuration {name} point estimates computed.")
        
    # 2. Run McNemar's tests
    mcnemar_results = {}
    for name in ["GOES_Only", "GOES_SoLEXS", "GOES_HEL1OS"]:
        mcnemar_results[name] = run_mcnemar_test(y_true, configs["Baseline"], configs[name], best_th)
        logger.info(f"McNemar's test vs {name} computed.")
        
    # 3. Bootstrapping (paired bootstrap tests and individual CIs)
    # We will use 1,000 bootstrap iterations on the 20,000 representative subset
    subset_indices = cache["subset_indices"]
    y_true_sub = y_true[subset_indices]
    configs_sub = {name: probs[subset_indices] for name, probs in configs.items()}
    
    N_sub = len(y_true_sub)
    logger.info(f"Running 1,000 paired bootstrap iterations on {N_sub} representative samples...")
    
    np.random.seed(42)
    
    # Lists to store bootstrap metrics
    boot_metrics = {name: {m: [] for m in ["ROC-AUC", "PR-AUC", "TSS", "Recall", "Precision"]} for name in configs.keys()}
    boot_diffs = {name: {m: [] for m in ["ROC-AUC", "PR-AUC", "TSS"]} for name in ["GOES_Only", "GOES_SoLEXS", "GOES_HEL1OS"]}
    
    for it in range(1000):
        idx = np.random.choice(N_sub, N_sub, replace=True)
        y_true_b = y_true_sub[idx]
        
        # Precompute metrics for this bootstrap sample for all configs
        sample_metrics = {}
        for name, probs in configs_sub.items():
            sample_metrics[name] = compute_basic_metrics(y_true_b, probs[idx], best_th)
            for m in boot_metrics[name].keys():
                boot_metrics[name][m].append(sample_metrics[name][m])
                
        # Differences (Baseline - Config)
        for name in boot_diffs.keys():
            for m in boot_diffs[name].keys():
                diff = sample_metrics["Baseline"][m] - sample_metrics[name][m]
                boot_diffs[name][m].append(diff)
                
        if (it + 1) % 200 == 0:
            logger.info(f"  Completed {it + 1} iterations...")
            
    # Calculate confidence intervals and p-values
    report = {
        "point_estimates": point_estimates,
        "mcnemar_tests": mcnemar_results,
        "bootstrap_results": {},
        "status": "PASS"
    }
    
    for name, probs in configs.items():
        report["bootstrap_results"][name] = {}
        for m in boot_metrics[name].keys():
            vals = np.array(boot_metrics[name][m])
            mean_val = float(np.mean(vals))
            std_val = float(np.std(vals))
            ci_lower = float(np.percentile(vals, 2.5))
            ci_upper = float(np.percentile(vals, 97.5))
            
            report["bootstrap_results"][name][m] = {
                "mean": mean_val,
                "std": std_val,
                "ci_95_lower": ci_lower,
                "ci_95_upper": ci_upper
            }
            
    # Paired differences analysis
    report["paired_differences"] = {}
    for name in boot_diffs.keys():
        report["paired_differences"][name] = {}
        for m in boot_diffs[name].keys():
            diffs = np.array(boot_diffs[name][m])
            mean_diff = float(np.mean(diffs))
            std_diff = float(np.std(diffs))
            ci_lower = float(np.percentile(diffs, 2.5))
            ci_upper = float(np.percentile(diffs, 97.5))
            
            # Bootstrap p-value (fraction of differences <= 0, two-tailed)
            p_val = 2.0 * min(np.mean(diffs <= 0), np.mean(diffs >= 0))
            # Handle edge case where p_val could be > 1.0 (though min makes it <= 1.0)
            p_val = min(1.0, p_val)
            
            report["paired_differences"][name][m] = {
                "mean_difference": mean_diff,
                "std_difference": std_diff,
                "ci_95_lower": ci_lower,
                "ci_95_upper": ci_upper,
                "bootstrap_p_value": p_val
            }
            logger.info(f"Baseline - {name} | {m} Mean Diff: {mean_diff:.4f} | 95% CI: [{ci_lower:.4f}, {ci_upper:.4f}] | p-value: {p_val:.4f}")
            
    os.makedirs("artifacts/sprint16a", exist_ok=True)
    with open("artifacts/sprint16a/sensor_availability_report.json", "w") as f:
        json.dump(report, f, indent=2)
        
    logger.info("Task 5 completed successfully.")

if __name__ == "__main__":
    main()
