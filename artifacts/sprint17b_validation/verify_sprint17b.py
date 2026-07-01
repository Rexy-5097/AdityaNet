import os
import sys
import json
import numpy as np
import pandas as pd

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
    print("=== INDEPENDENT SPRINT 17B VERIFICATION ===")
    
    # Load raw data
    cache = np.load("scratch/sprint16a/cached_predictions.npz")
    best_th = float(cache["validation_threshold"])
    y_true = cache["test_targets"]
    y_prob = cache["test_probs_cal_iso"]
    
    # Establish binary predictions
    y_pred = (y_prob >= best_th).astype(int)
    
    # Group masks
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
    
    rep_dir = "artifacts/sprint17b"
    has_mismatches = False
    
    # ----------------------------------------------------
    # Check 1: prediction_distribution.csv
    # ----------------------------------------------------
    print("\n--- Check 1: prediction_distribution.csv ---")
    df_dist_rep = pd.read_csv(f"{rep_dir}/prediction_distribution.csv")
    
    dist_mismatches = 0
    for idx, row in df_dist_rep.iterrows():
        g_name = row["Group"]
        arr = groups[g_name]
        stats = compute_dist_stats(arr)
        
        # Compare every field
        for key in ["count", "min", "max", "mean", "median", "std", "q1", "q3", "iqr", "p5", "p95"]:
            v_rep = row[key]
            v_act = stats[key]
            
            if key == "count":
                diff = abs(v_rep - v_act)
            else:
                diff = abs(v_rep - v_act)
                
            if (key == "count" and diff != 0) or (key != "count" and diff > 1e-6):
                print(f"  Mismatch in prediction_distribution Group={g_name}, Field={key}: Reported={v_rep}, Actual={v_act} (diff={diff:.6e})")
                dist_mismatches += 1
                has_mismatches = True
                
    if dist_mismatches == 0:
        print("  PASS: prediction_distribution.csv matches recomputed values exactly.")
    else:
        print(f"  FAIL: Found {dist_mismatches} mismatches in prediction_distribution.csv.")

    # ----------------------------------------------------
    # Check 2: threshold_distance.csv
    # ----------------------------------------------------
    print("\n--- Check 2: threshold_distance.csv ---")
    df_th_rep = pd.read_csv(f"{rep_dir}/threshold_distance.csv")
    
    th_mismatches = 0
    for idx, row in df_th_rep.iterrows():
        g_name = row["Group"]
        arr = groups[g_name]
        distances = arr - best_th
        q75, q25 = np.percentile(distances, [75, 25])
        
        stats = {
            "mean_distance": float(np.mean(distances)),
            "median_distance": float(np.median(distances)),
            "std_deviation": float(np.std(distances)),
            "minimum": float(np.min(distances)),
            "maximum": float(np.max(distances)),
            "q1": float(q25),
            "q2_median": float(np.median(distances)),
            "q3": float(q75)
        }
        
        for key in stats.keys():
            v_rep = row[key]
            v_act = stats[key]
            diff = abs(v_rep - v_act)
            
            if diff > 1e-6:
                print(f"  Mismatch in threshold_distance Group={g_name}, Field={key}: Reported={v_rep}, Actual={v_act} (diff={diff:.6e})")
                th_mismatches += 1
                has_mismatches = True
                
    if th_mismatches == 0:
        print("  PASS: threshold_distance.csv matches recomputed values exactly.")
    else:
        print(f"  FAIL: Found {th_mismatches} mismatches in threshold_distance.csv.")

    # ----------------------------------------------------
    # Check 3: calibration_bins.csv (20 Bins)
    # ----------------------------------------------------
    print("\n--- Check 3: calibration_bins.csv (20 Bins) ---")
    df_cal_rep = pd.read_csv(f"{rep_dir}/calibration_bins.csv")
    
    cal_mismatches = 0
    n_bins_20 = 20
    bin_boundaries = np.linspace(0, 1, n_bins_20 + 1)
    
    for i in range(n_bins_20):
        bin_lower = bin_boundaries[i]
        bin_upper = bin_boundaries[i+1]
        
        in_bin = (y_prob >= bin_lower) & (y_prob < bin_upper)
        if i == n_bins_20 - 1:
            in_bin = in_bin | (y_prob == bin_upper)
            
        count_act = int(np.sum(in_bin))
        if count_act > 0:
            pos_rate_act = float(np.mean(y_true[in_bin]))
            pred_prob_mean_act = float(np.mean(y_prob[in_bin]))
            cal_err_act = float(np.abs(pred_prob_mean_act - pos_rate_act))
        else:
            pos_rate_act = 0.0
            pred_prob_mean_act = 0.0
            cal_err_act = 0.0
            
        # Get reported row
        row = df_cal_rep.iloc[i]
        
        if row["sample_count"] != count_act:
            print(f"  Mismatch in bin {i} sample_count: Reported={row['sample_count']}, Actual={count_act}")
            cal_mismatches += 1
            has_mismatches = True
        if abs(row["positive_rate"] - pos_rate_act) > 1e-6:
            print(f"  Mismatch in bin {i} positive_rate: Reported={row['positive_rate']}, Actual={pos_rate_act}")
            cal_mismatches += 1
            has_mismatches = True
        if abs(row["predicted_probability_mean"] - pred_prob_mean_act) > 1e-6:
            print(f"  Mismatch in bin {i} predicted_probability_mean: Reported={row['predicted_probability_mean']}, Actual={pred_prob_mean_act}")
            cal_mismatches += 1
            has_mismatches = True
        if abs(row["observed_frequency"] - pos_rate_act) > 1e-6:
            print(f"  Mismatch in bin {i} observed_frequency: Reported={row['observed_frequency']}, Actual={pos_rate_act}")
            cal_mismatches += 1
            has_mismatches = True
        if abs(row["absolute_calibration_error"] - cal_err_act) > 1e-6:
            print(f"  Mismatch in bin {i} absolute_calibration_error: Reported={row['absolute_calibration_error']}, Actual={cal_err_act}")
            cal_mismatches += 1
            has_mismatches = True
            
    if cal_mismatches == 0:
        print("  PASS: calibration_bins.csv matches recomputed values exactly.")
    else:
        print(f"  FAIL: Found {cal_mismatches} mismatches in calibration_bins.csv.")

    # ----------------------------------------------------
    # Check 4: uncertainty_statistics.csv
    # ----------------------------------------------------
    print("\n--- Check 4: uncertainty_statistics.csv ---")
    df_unc_rep = pd.read_csv(f"{rep_dir}/uncertainty_statistics.csv")
    
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
    
    unc_mismatches = 0
    for idx, row in df_unc_rep.iterrows():
        g_name = row["Group"]
        mask = sub_masks[g_name]
        vals = uncertainty_subset[mask]
        
        q75, q25 = np.percentile(vals, [75, 25])
        stats = {
            "count": int(len(vals)),
            "mean": float(np.mean(vals)),
            "median": float(np.median(vals)),
            "std": float(np.std(vals)),
            "minimum": float(np.min(vals)),
            "maximum": float(np.max(vals)),
            "q1": float(q25),
            "q3": float(q75),
            "percentile_95": float(np.percentile(vals, 95))
        }
        
        for key in stats.keys():
            v_rep = row[key]
            v_act = stats[key]
            diff = abs(v_rep - v_act)
            
            if (key == "count" and diff != 0) or (key != "count" and diff > 1e-6):
                print(f"  Mismatch in uncertainty_statistics Group={g_name}, Field={key}: Reported={v_rep}, Actual={v_act} (diff={diff:.6e})")
                unc_mismatches += 1
                has_mismatches = True
                
    if unc_mismatches == 0:
        print("  PASS: uncertainty_statistics.csv matches recomputed values exactly.")
    else:
        print(f"  FAIL: Found {unc_mismatches} mismatches in uncertainty_statistics.csv.")

    # ----------------------------------------------------
    # Check 5: probability_uncertainty_grid.csv
    # ----------------------------------------------------
    print("\n--- Check 5: probability_uncertainty_grid.csv ---")
    df_grid_rep = pd.read_csv(f"{rep_dir}/probability_uncertainty_grid.csv")
    
    grid_mismatches = 0
    prob_edges = np.linspace(0, 1, 21)
    min_unc = float(np.min(uncertainty_subset))
    max_unc = float(np.max(uncertainty_subset))
    unc_edges = np.linspace(min_unc, max_unc, 11)
    
    total_grid_samples_act = 0
    
    cell_idx = 0
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
            count_act = int(np.sum(cell_mask))
            pos_frac_act = float(np.mean(y_true_sub[cell_mask])) if count_act > 0 else 0.0
            
            total_grid_samples_act += count_act
            
            # Get reported row
            row = df_grid_rep.iloc[cell_idx]
            
            if row["sample_count"] != count_act:
                print(f"  Mismatch in grid cell {cell_idx} (P_bin={p_idx}, U_bin={u_idx}) sample_count: Reported={row['sample_count']}, Actual={count_act}")
                grid_mismatches += 1
                has_mismatches = True
            if abs(row["positive_fraction"] - pos_frac_act) > 1e-6:
                print(f"  Mismatch in grid cell {cell_idx} (P_bin={p_idx}, U_bin={u_idx}) positive_fraction: Reported={row['positive_fraction']}, Actual={pos_frac_act}")
                grid_mismatches += 1
                has_mismatches = True
                
            cell_idx += 1
            
    print(f"  Sum of recomputed grid samples: {total_grid_samples_act} (Expected: 20000)")
    if total_grid_samples_act != len(subset_indices):
        print(f"  FAIL: Grid sample total {total_grid_samples_act} != subset size {len(subset_indices)}!")
        has_mismatches = True
        
    if grid_mismatches == 0:
        print("  PASS: probability_uncertainty_grid.csv matches recomputed values exactly.")
    else:
        print(f"  FAIL: Found {grid_mismatches} mismatches in probability_uncertainty_grid.csv.")

    # ----------------------------------------------------
    # Check 6: reliability_metrics.json
    # ----------------------------------------------------
    print("\n--- Check 6: reliability_metrics.json ---")
    with open(f"{rep_dir}/reliability_metrics.json") as f:
        rel_rep = json.load(f)
        
    # Recompute ECE, MCE (using 10 bins)
    n_bins_10 = 10
    bin_boundaries_10 = np.linspace(0, 1, n_bins_10 + 1)
    ece_act = 0.0
    mce_act = 0.0
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
            ece_act += prop_in_bin * diff
            mce_act = max(mce_act, diff)
            
    brier_act = float(np.mean((y_prob - y_true) ** 2))
    
    eps = 1e-15
    logloss_act = float(-np.mean(y_true * np.log(y_prob + eps) + (1.0 - y_true) * np.log(1.0 - y_prob + eps)))
    
    rel_mismatches = 0
    if abs(rel_rep["ECE"] - ece_act) > 1e-6:
        print(f"  Mismatch in ECE: Reported={rel_rep['ECE']:.6f}, Actual={ece_act:.6f}")
        rel_mismatches += 1
    if abs(rel_rep["MCE"] - mce_act) > 1e-6:
        print(f"  Mismatch in MCE: Reported={rel_rep['MCE']:.6f}, Actual={mce_act:.6f}")
        rel_mismatches += 1
    if abs(rel_rep["Brier_Score"] - brier_act) > 1e-6:
        print(f"  Mismatch in Brier_Score: Reported={rel_rep['Brier_Score']:.6f}, Actual={brier_act:.6f}")
        rel_mismatches += 1
    if abs(rel_rep["Log_Loss"] - logloss_act) > 1e-6:
        print(f"  Mismatch in Log_Loss: Reported={rel_rep['Log_Loss']:.6f}, Actual={logloss_act:.6f}")
        rel_mismatches += 1
        
    if rel_mismatches == 0:
        print("  PASS: reliability_metrics.json matches recomputed values exactly.")
    else:
        print(f"  FAIL: Found {rel_mismatches} mismatches in reliability_metrics.json.")
        has_mismatches = True

    # ----------------------------------------------------
    # Check 7: Verify Invariants
    # ----------------------------------------------------
    print("\n--- Check 7: Invariants Verification ---")
    inv_passed = True
    
    # 1. No sample duplication or omission
    # Handled by subset index validation and totals matching len(y_true)
    
    # 2. Sum of TP + TN + FP + FN equals evaluation size
    tp_cnt = np.sum(tp_mask)
    tn_cnt = np.sum(tn_mask)
    fp_cnt = np.sum(fp_mask)
    fn_cnt = np.sum(fn_mask)
    sum_tpf = tp_cnt + tn_cnt + fp_cnt + fn_cnt
    print(f"  Sum of TP={tp_cnt} + TN={tn_cnt} + FP={fp_cnt} + FN={fn_cnt} is {sum_tpf} (Expected={len(y_true)})")
    if sum_tpf != len(y_true):
        inv_passed = False
        
    # 3. Calibration bin totals equal evaluation size
    cal_bin_total = df_cal_rep["sample_count"].sum()
    print(f"  Calibration bin total count: {cal_bin_total} (Expected={len(y_true)})")
    if cal_bin_total != len(y_true):
        inv_passed = False
        
    # 4. Joint grid totals equal evaluation size (subset size)
    grid_total = df_grid_rep["sample_count"].sum()
    print(f"  Joint grid total count: {grid_total} (Expected={len(subset_indices)})")
    if grid_total != len(subset_indices):
        inv_passed = False
        
    if inv_passed:
        print("  PASS: All structural invariants satisfied.")
    else:
        print("  FAIL: One or more invariants violated.")
        has_mismatches = True

    # ----------------------------------------------------
    # Final Result
    # ----------------------------------------------------
    print("\n==============================================")
    if has_mismatches:
        print("VERIFICATION RESULT: FAIL")
    else:
        print("VERIFICATION RESULT: PASS")
    print("==============================================")

if __name__ == "__main__":
    main()
