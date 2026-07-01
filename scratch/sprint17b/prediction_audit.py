"""
scratch/sprint17b/prediction_audit.py

Sprint 17B: Prediction Distribution & Calibration Audit.
Performs a read-only statistical audit of V3 predictions and MC Dropout uncertainty.
Generates descriptive distributions, threshold distances, calibration curves, joint tables,
and overall reliability scores.
"""

import os
import json
import logging
import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def compute_dist_stats(arr):
    if len(arr) == 0:
        return {
            "count": 0, "min": 0.0, "max": 0.0, "mean": 0.0, "median": 0.0,
            "std": 0.0, "q1": 0.0, "q3": 0.0, "iqr": 0.0, "p5": 0.0, "p95": 0.0
        }
    q75, q25 = np.percentile(arr, [75, 25])
    return {
        "count": int(len(arr)),
        "min": float(np.min(arr)),
        "max": float(np.max(arr)),
        "mean": float(np.mean(arr)),
        "median": float(np.median(arr)),
        "std": float(np.std(arr)),
        "q1": float(q25),
        "q3": float(q75),
        "iqr": float(q75 - q25),
        "p5": float(np.percentile(arr, 5)),
        "p95": float(np.percentile(arr, 95))
    }

def main():
    logger.info("Loading predictions cache and parquet test set...")
    cache = np.load("scratch/sprint16a/cached_predictions.npz")
    
    best_th = float(cache["validation_threshold"])
    y_true = cache["test_targets"]
    y_prob = cache["test_probs_cal_iso"]
    
    # Establish binary predictions
    y_pred = (y_prob >= best_th).astype(int)
    
    # Groups selection indices
    tp_mask = (y_true == 1) & (y_pred == 1)
    tn_mask = (y_true == 0) & (y_pred == 0)
    fp_mask = (y_true == 0) & (y_pred == 1)
    fn_mask = (y_true == 1) & (y_pred == 0)
    
    groups = {
        "Overall": y_prob,
        "TP": y_prob[tp_mask],
        "TN": y_prob[tn_mask],
        "FP": y_prob[fp_mask],
        "FN": y_prob[fn_mask]
    }
    
    # ----------------------------------------------------
    # 1. Probability Distribution
    # ----------------------------------------------------
    logger.info("Computing probability distributions...")
    dist_records = []
    for name, arr in groups.items():
        stats = compute_dist_stats(arr)
        stats["Group"] = name
        dist_records.append(stats)
        
    df_dist = pd.DataFrame(dist_records)
    # Reorder columns
    cols = ["Group", "count", "min", "max", "mean", "median", "std", "q1", "q3", "iqr", "p5", "p95"]
    df_dist = df_dist[cols]
    
    # ----------------------------------------------------
    # 2. Threshold Distance Statistics
    # ----------------------------------------------------
    logger.info("Computing threshold distance statistics...")
    dist_stats_records = []
    # distance = prob - threshold
    for name in ["TP", "TN", "FP", "FN"]:
        arr = groups[name]
        if len(arr) > 0:
            distances = arr - best_th
            q75, q25 = np.percentile(distances, [75, 25])
            dist_stats_records.append({
                "Group": name,
                "mean_distance": float(np.mean(distances)),
                "median_distance": float(np.median(distances)),
                "std_deviation": float(np.std(distances)),
                "minimum": float(np.min(distances)),
                "maximum": float(np.max(distances)),
                "q1": float(q25),
                "q2_median": float(np.median(distances)),
                "q3": float(q75)
            })
        else:
            dist_stats_records.append({
                "Group": name, "mean_distance": 0.0, "median_distance": 0.0, "std_deviation": 0.0,
                "minimum": 0.0, "maximum": 0.0, "q1": 0.0, "q2_median": 0.0, "q3": 0.0
            })
    df_threshold_dist = pd.DataFrame(dist_stats_records)
    
    # ----------------------------------------------------
    # 3. Calibration Bin Statistics (20 Bins)
    # ----------------------------------------------------
    logger.info("Computing calibration bin statistics...")
    n_bins_20 = 20
    bin_boundaries = np.linspace(0, 1, n_bins_20 + 1)
    cal_records = []
    
    for i in range(n_bins_20):
        bin_lower = bin_boundaries[i]
        bin_upper = bin_boundaries[i+1]
        
        in_bin = (y_prob >= bin_lower) & (y_prob < bin_upper)
        if i == n_bins_20 - 1:
            in_bin = in_bin | (y_prob == bin_upper)
            
        count = int(np.sum(in_bin))
        if count > 0:
            pos_rate = float(np.mean(y_true[in_bin]))
            pred_prob_mean = float(np.mean(y_prob[in_bin]))
            cal_err = float(np.abs(pred_prob_mean - pos_rate))
        else:
            pos_rate = 0.0
            pred_prob_mean = 0.0
            cal_err = 0.0
            
        cal_records.append({
            "Bin": f"({bin_lower:.2f}, {bin_upper:.2f}]" if i > 0 else f"[{bin_lower:.2f}, {bin_upper:.2f}]",
            "sample_count": count,
            "positive_rate": pos_rate,
            "predicted_probability_mean": pred_prob_mean,
            "observed_frequency": pos_rate,
            "absolute_calibration_error": cal_err
        })
    df_cal_bins = pd.DataFrame(cal_records)
    
    # ----------------------------------------------------
    # 4. Uncertainty Statistics (using 20,000 subset)
    # ----------------------------------------------------
    logger.info("Computing uncertainty statistics...")
    subset_indices = cache["subset_indices"]
    uncertainty_subset = cache["subset_uncertainty"]
    
    y_true_sub = y_true[subset_indices]
    y_prob_sub = y_prob[subset_indices]
    y_pred_sub = (y_prob_sub >= best_th).astype(int)
    
    sub_masks = {
        "TP": (y_true_sub == 1) & (y_pred_sub == 1),
        "TN": (y_true_sub == 0) & (y_pred_sub == 0),
        "FP": (y_true_sub == 0) & (y_pred_sub == 1),
        "FN": (y_true_sub == 1) & (y_pred_sub == 0)
    }
    
    unc_records = []
    for name, mask in sub_masks.items():
        vals = uncertainty_subset[mask]
        if len(vals) > 0:
            q75, q25 = np.percentile(vals, [75, 25])
            unc_records.append({
                "Group": name,
                "count": int(len(vals)),
                "mean": float(np.mean(vals)),
                "median": float(np.median(vals)),
                "std": float(np.std(vals)),
                "minimum": float(np.min(vals)),
                "maximum": float(np.max(vals)),
                "q1": float(q25),
                "q3": float(q75),
                "percentile_95": float(np.percentile(vals, 95))
            })
        else:
            unc_records.append({
                "Group": name, "count": 0, "mean": 0.0, "median": 0.0, "std": 0.0,
                "minimum": 0.0, "maximum": 0.0, "q1": 0.0, "q3": 0.0, "percentile_95": 0.0
            })
    df_unc_stats = pd.DataFrame(unc_records)
    
    # ----------------------------------------------------
    # 5. Probability × Uncertainty Joint Table (using 20k subset)
    # ----------------------------------------------------
    logger.info("Computing joint probability-uncertainty table...")
    prob_edges = np.linspace(0, 1, 21)
    
    # Dynamic uncertainty edges
    min_unc = float(np.min(uncertainty_subset))
    max_unc = float(np.max(uncertainty_subset))
    unc_edges = np.linspace(min_unc, max_unc, 11)
    
    joint_records = []
    for p_idx in range(20):
        p_lower = prob_edges[p_idx]
        p_upper = prob_edges[p_idx+1]
        
        p_mask = (y_prob_sub >= p_lower) & (y_prob_sub < p_upper)
        if p_idx == 19:
            p_mask = p_mask | (y_prob_sub == p_upper)
            
        for u_idx in range(10):
            u_lower = unc_edges[u_idx]
            u_upper = unc_edges[u_idx+1]
            
            u_mask = (uncertainty_subset >= u_lower) & (uncertainty_subset < u_upper)
            if u_idx == 9:
                u_mask = u_mask | (uncertainty_subset == u_upper)
                
            cell_mask = p_mask & u_mask
            count = int(np.sum(cell_mask))
            pos_frac = float(np.mean(y_true_sub[cell_mask])) if count > 0 else 0.0
            
            joint_records.append({
                "Probability_Bin": f"({p_lower:.2f}, {p_upper:.2f}]" if p_idx > 0 else f"[{p_lower:.2f}, {p_upper:.2f}]",
                "Uncertainty_Bin": f"({u_lower:.6f}, {u_upper:.6f}]" if u_idx > 0 else f"[{u_lower:.6f}, {u_upper:.6f}]",
                "sample_count": count,
                "positive_fraction": pos_frac
            })
    df_joint_grid = pd.DataFrame(joint_records)
    
    # ----------------------------------------------------
    # 6. Reliability Metrics
    # ----------------------------------------------------
    logger.info("Recomputing reliability metrics...")
    # ECE and MCE (using 10 bins which is standard)
    n_bins_10 = 10
    bin_boundaries_10 = np.linspace(0, 1, n_bins_10 + 1)
    ece_val = 0.0
    mce_val = 0.0
    for i in range(n_bins_10):
        bin_lower = bin_boundaries_10[i]
        bin_upper = bin_boundaries_10[i+1]
        in_bin = (y_prob >= bin_lower) & (y_prob < bin_upper)
        if i == n_bins_10 - 1:
            in_bin = in_bin | (y_prob == bin_upper)
            
        prop_in_bin = np.mean(in_bin)
        if prop_in_bin > 0:
            accuracy_in_bin = np.mean(y_true[in_bin])
            avg_confidence_in_bin = np.mean(y_prob[in_bin])
            diff = np.abs(avg_confidence_in_bin - accuracy_in_bin)
            ece_val += prop_in_bin * diff
            mce_val = max(mce_val, diff)
            
    brier_score = float(np.mean((y_prob - y_true) ** 2))
    
    # Log loss
    eps = 1e-15
    log_loss_val = float(-np.mean(y_true * np.log(y_prob + eps) + (1.0 - y_true) * np.log(1.0 - y_prob + eps)))
    
    reliability = {
        "ECE": float(ece_val),
        "MCE": float(mce_val),
        "Brier_Score": brier_score,
        "Log_Loss": log_loss_val
    }
    
    # Save all output files
    out_dir = "artifacts/sprint17b"
    os.makedirs(out_dir, exist_ok=True)
    
    df_dist.to_csv(f"{out_dir}/prediction_distribution.csv", index=False)
    df_threshold_dist.to_csv(f"{out_dir}/threshold_distance.csv", index=False)
    df_cal_bins.to_csv(f"{out_dir}/calibration_bins.csv", index=False)
    df_unc_stats.to_csv(f"{out_dir}/uncertainty_statistics.csv", index=False)
    df_joint_grid.to_csv(f"{out_dir}/probability_uncertainty_grid.csv", index=False)
    
    with open(f"{out_dir}/reliability_metrics.json", "w") as f:
        json.dump(reliability, f, indent=2)
        
    logger.info("Sprint 17B audit statistics computed successfully.")

if __name__ == "__main__":
    main()
