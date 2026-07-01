import os
import sys
import json
import hashlib
import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr, mannwhitneyu, kruskal, chi2
from sklearn.metrics import roc_auc_score, average_precision_score

# Helper for file hashing
def sha256(path):
    if not os.path.exists(path):
        return None
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

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

def compute_ece_with_last_bin_inclusive(y_true, y_prob, n_bins=10):
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    for i in range(n_bins):
        bin_lower = bin_boundaries[i]
        bin_upper = bin_boundaries[i+1]
        in_bin = (y_prob >= bin_lower) & (y_prob < bin_upper)
        if i == n_bins - 1:
            in_bin = in_bin | (y_prob == bin_upper)
        prop_in_bin = np.mean(in_bin)
        if prop_in_bin > 0:
            accuracy_in_bin = np.mean(y_true[in_bin])
            avg_confidence_in_bin = np.mean(y_prob[in_bin])
            ece += prop_in_bin * np.abs(avg_confidence_in_bin - accuracy_in_bin)
    return ece

def compute_overlap_coefficient(x, y, n_bins=100):
    if len(x) == 0 or len(y) == 0:
        return 0.0
    hist_x, _ = np.histogram(x, bins=n_bins, range=(0, 1), density=False)
    hist_y, _ = np.histogram(y, bins=n_bins, range=(0, 1), density=False)
    px = hist_x / np.sum(hist_x) if np.sum(hist_x) > 0 else hist_x
    py = hist_y / np.sum(hist_y) if np.sum(hist_y) > 0 else hist_y
    return float(np.sum(np.minimum(px, py)))

def main():
    print("=== STARTING INDEPENDENT SPRINT 16A VALIDATION ===")
    
    # 1. Load test predictions and targets from the predictions cache
    cache_path = "scratch/sprint16a/cached_predictions.npz"
    if not os.path.exists(cache_path):
        print(f"ERROR: predictions cache not found at {cache_path}!")
        sys.exit(1)
    
    cache = np.load(cache_path)
    
    # Extract cache arrays
    validation_threshold = float(cache["validation_threshold"])
    test_targets = cache["test_targets"]
    test_probs_cal_iso = cache["test_probs_cal_iso"]
    test_timestamps = cache["test_timestamps"]
    subset_indices = cache["subset_indices"]
    subset_uncertainty = cache["subset_uncertainty"]
    
    print(f"Validation threshold from cache: {validation_threshold:.10f}")
    print(f"Total test set size: {len(test_targets)}")
    print(f"Subset size: {len(subset_indices)}")
    
    # Check 1: Verify bootstrap_metrics.json
    print("\n--- Check 1: bootstrap_metrics.json ---")
    bootstrap_path = "artifacts/sprint16a/bootstrap_metrics.json"
    if not os.path.exists(bootstrap_path):
        print("FAIL: bootstrap_metrics.json does not exist!")
    else:
        with open(bootstrap_path) as f:
            boot_data = json.load(f)
        
        # Verify 95% interval contains reported mean and standard deviation > 0
        c1_all_passed = True
        for metric, stats in boot_data.items():
            mean = stats["mean"]
            std = stats["std"]
            ci_lower = stats["ci_95_lower"]
            ci_upper = stats["ci_95_upper"]
            
            # Check CI contains mean
            in_ci = (ci_lower <= mean <= ci_upper)
            # Check std > 0
            std_ok = (std > 0)
            
            print(f"  {metric}: Mean={mean:.6f}, Std={std:.6f}, CI=[{ci_lower:.6f}, {ci_upper:.6f}] | In CI: {in_ci}, Std > 0: {std_ok}")
            if not (in_ci and std_ok):
                c1_all_passed = False
                
        # Recompute bootstrap metrics (with seed 42) to verify 10,000 bootstrap iterations
        print("  Recomputing bootstrap metrics (10,000 iterations)...")
        np.random.seed(42)
        y_true_sub = test_targets[subset_indices]
        y_prob_sub = test_probs_cal_iso[subset_indices]
        N_sub = len(y_true_sub)
        
        recalc_tss_list = []
        for _ in range(10000):
            boot_idx = np.random.choice(N_sub, N_sub, replace=True)
            y_true_b = y_true_sub[boot_idx]
            y_prob_b = y_prob_sub[boot_idx]
            y_pred_b = (y_prob_b >= validation_threshold).astype(int)
            recalc_tss_list.append(compute_tss(y_true_b, y_pred_b))
            
        recalc_mean_tss = np.mean(recalc_tss_list)
        recalc_std_tss = np.std(recalc_tss_list)
        recalc_ci_lower = np.percentile(recalc_tss_list, 2.5)
        recalc_ci_upper = np.percentile(recalc_tss_list, 97.5)
        
        reported_tss_stats = boot_data["TSS"]
        diff_mean = abs(recalc_mean_tss - reported_tss_stats["mean"])
        diff_std = abs(recalc_std_tss - reported_tss_stats["std"])
        diff_lower = abs(recalc_ci_lower - reported_tss_stats["ci_95_lower"])
        diff_upper = abs(recalc_ci_upper - reported_tss_stats["ci_95_upper"])
        
        print(f"  TSS recomputed: Mean={recalc_mean_tss:.6f}, Std={recalc_std_tss:.6f}, CI=[{recalc_ci_lower:.6f}, {recalc_ci_upper:.6f}]")
        print(f"  TSS differences: Mean={diff_mean:.6e}, Std={diff_std:.6e}, CI_Lower={diff_lower:.6e}, CI_Upper={diff_upper:.6e}")
        
        if diff_mean > 1e-5 or diff_std > 1e-5 or diff_lower > 1e-5 or diff_upper > 1e-5:
            print("  FAIL: Recomputed bootstrap metrics do not match reported bootstrap metrics!")
            c1_all_passed = False
        else:
            print("  PASS: Recomputed bootstrap metrics match reported bootstrap metrics exactly (confirming 10k iterations and seed).")
            
        if c1_all_passed:
            print("  Check 1: PASS")
        else:
            print("  Check 1: FAIL")

    # Check 2: Verify threshold_sweep.csv
    print("\n--- Check 2: threshold_sweep.csv ---")
    sweep_path = "artifacts/sprint16a/threshold_sweep.csv"
    if not os.path.exists(sweep_path):
        print("FAIL: threshold_sweep.csv does not exist!")
    else:
        df_sweep = pd.read_csv(sweep_path)
        
        # Ensure locked threshold exists (0.3168686869)
        locked_th = 0.3168686869
        has_locked = np.any(np.isclose(df_sweep["Threshold"].values, locked_th))
        print(f"  Locked threshold ({locked_th:.10f}) exists in sweep: {has_locked}")
        
        # Verify TSS values are consistent with test targets & probs
        c2_all_passed = has_locked
        for _, row in df_sweep.iterrows():
            th = row["Threshold"]
            rep_tss = row["TSS"]
            rep_recall = row["Recall"]
            rep_precision = row["Precision"]
            
            # Compute actual metrics at this threshold
            y_pred = (test_probs_cal_iso >= th).astype(int)
            act_tss = compute_tss(test_targets, y_pred)
            
            tp = np.sum((test_targets == 1) & (y_pred == 1))
            fp = np.sum((test_targets == 0) & (y_pred == 1))
            fn = np.sum((test_targets == 1) & (y_pred == 0))
            act_recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            act_precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            
            diff_tss = abs(rep_tss - act_tss)
            diff_rec = abs(rep_recall - act_recall)
            diff_prec = abs(rep_precision - act_precision)
            
            print(f"  Th={th:.6f} | TSS: Reported={rep_tss:.6f}, Actual={act_tss:.6f} (diff={diff_tss:.6e}) | Recall diff={diff_rec:.6e} | Precision diff={diff_prec:.6e}")
            if diff_tss > 1e-6 or diff_rec > 1e-6 or diff_prec > 1e-6:
                c2_all_passed = False
                
        # Check maximizing thresholds
        max_th_path = "artifacts/sprint16a/maximizing_thresholds.json"
        if os.path.exists(max_th_path):
            with open(max_th_path) as f:
                max_data = json.load(f)
            print("  Maximizing thresholds reported:", max_data)
            
            # Sweep fine grid to find the best thresholds
            fine_grid = np.linspace(0.01, 0.99, 99)
            best_recall_th, max_recall = 0.0, -1.0
            best_precision_th, max_precision = 0.0, -1.0
            best_f1_th, max_f1 = 0.0, -1.0
            
            for th in fine_grid:
                y_pred = (test_probs_cal_iso >= th).astype(int)
                tp = np.sum((test_targets == 1) & (y_pred == 1))
                fp = np.sum((test_targets == 0) & (y_pred == 1))
                fn = np.sum((test_targets == 1) & (y_pred == 0))
                rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
                prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
                f1 = 2 * (prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0
                
                # Check matching behavior of threshold_stability.py:
                # threshold_stability.py uses '>' for finding maximums. Let's do the same.
                if rec > max_recall:
                    max_recall = rec
                    best_recall_th = th
                if prec > max_precision:
                    max_precision = prec
                    best_precision_th = th
                if f1 > max_f1:
                    max_f1 = f1
                    best_f1_th = th
                    
            print(f"  Recomputed maximizing: Recall Th={best_recall_th:.4f} (val={max_recall:.6f}), Precision Th={best_precision_th:.4f} (val={max_precision:.6f}), F1 Th={best_f1_th:.4f} (val={max_f1:.6f})")
            
            # Compare
            diff_recall_th = abs(max_data["maximizing_recall"]["threshold"] - best_recall_th)
            diff_prec_th = abs(max_data["maximizing_precision"]["threshold"] - best_precision_th)
            diff_f1_th = abs(max_data["maximizing_f1"]["threshold"] - best_f1_th)
            
            if diff_recall_th > 1e-5 or diff_prec_th > 1e-5 or diff_f1_th > 1e-5:
                print("  FAIL: Recomputed maximizing thresholds mismatch reported ones!")
                c2_all_passed = False
            else:
                print("  PASS: Maximizing thresholds match recomputed ones.")
        else:
            print("  FAIL: maximizing_thresholds.json does not exist!")
            c2_all_passed = False
            
        if c2_all_passed:
            print("  Check 2: PASS")
        else:
            print("  Check 2: FAIL")

    # Check 3: Verify calibration_bins.csv
    print("\n--- Check 3: calibration_bins.csv ---")
    bins_path = "artifacts/sprint16a/calibration_bins.csv"
    if not os.path.exists(bins_path):
        print("FAIL: calibration_bins.csv does not exist!")
    else:
        df_bins = pd.read_csv(bins_path)
        
        # Check exactly 10 bins
        num_bins = len(df_bins)
        print(f"  Number of bins: {num_bins} (Expected: 10)")
        c3_passed = (num_bins == 10)
        
        # Check counts sum to test set size
        sum_counts = df_bins["Sample_Count"].sum()
        print(f"  Sum of counts: {sum_counts} (Expected: {len(test_targets)})")
        if sum_counts != len(test_targets):
            c3_passed = False
            
        # Check Expected_Probability and Observed_Frequency are monotonic (when count > 0)
        valid_df = df_bins[df_bins["Sample_Count"] > 0]
        expected_probs = valid_df["Expected_Probability"].values
        observed_freqs = valid_df["Observed_Frequency"].values
        
        exp_monotonic = np.all(np.diff(expected_probs) >= 0)
        obs_monotonic = np.all(np.diff(observed_freqs) >= 0)
        print(f"  Expected probabilities monotonic: {exp_monotonic}")
        print(f"  Observed frequencies monotonic: {obs_monotonic}")
        if not (exp_monotonic and obs_monotonic):
            c3_passed = False
            
        # Check ECE contributions are valid
        total_ece_recalc = 0.0
        n_total = len(test_targets)
        for idx, row in df_bins.iterrows():
            count = row["Sample_Count"]
            exp_prob = row["Expected_Probability"]
            obs_freq = row["Observed_Frequency"]
            rep_ece_contrib = row["ECE_Contribution"]
            
            # ECE contribution formula: (count / n_total) * abs(exp_prob - obs_freq)
            act_ece_contrib = (count / n_total) * abs(exp_prob - obs_freq)
            diff_ece = abs(rep_ece_contrib - act_ece_contrib)
            total_ece_recalc += act_ece_contrib
            
            if count > 0 and diff_ece > 1e-7:
                print(f"    Bin {idx} ECE mismatch: Reported={rep_ece_contrib:.6e}, Actual={act_ece_contrib:.6e}")
                c3_passed = False
                
        print(f"  Sum of ECE contributions: {total_ece_recalc:.6f}")
        # Verify reliability_statistics.json
        rel_stats_path = "artifacts/sprint16a/reliability_statistics.json"
        if os.path.exists(rel_stats_path):
            with open(rel_stats_path) as f:
                rel_data = json.load(f)
            rep_overall_ece = rel_data["overall_ece"]
            print(f"  Reported overall ECE: {rep_overall_ece:.6f}")
            if abs(rep_overall_ece - total_ece_recalc) > 1e-6:
                print("  FAIL: Overall ECE mismatch!")
                c3_passed = False
        else:
            print("  FAIL: reliability_statistics.json does not exist!")
            c3_passed = False
            
        if c3_passed:
            print("  Check 3: PASS")
        else:
            print("  Check 3: FAIL")

    # Check 4: Verify monthly_metrics.csv
    print("\n--- Check 4: monthly_metrics.csv ---")
    monthly_path = "artifacts/sprint16a/monthly_metrics.csv"
    if not os.path.exists(monthly_path):
        print("FAIL: monthly_metrics.csv does not exist!")
    else:
        df_monthly = pd.read_csv(monthly_path)
        
        # Check every test month is present
        reported_months = sorted(df_monthly["Month"].values)
        print("  Reported months:", reported_months)
        
        # Get actual months from timestamps
        df_ts = pd.DataFrame({"month": pd.to_datetime(test_timestamps).to_period("M").astype(str)})
        actual_months = sorted(df_ts["month"].unique())
        print("  Actual months in dataset:", actual_months)
        
        c4_passed = (reported_months == actual_months)
        
        # Check monthly counts sum to test set size
        sum_m_counts = df_monthly["Sample_Count"].sum()
        print(f"  Sum of monthly counts: {sum_m_counts} (Expected: {len(test_targets)})")
        if sum_m_counts != len(test_targets):
            c4_passed = False
            
        # Verify monthly metrics calculations
        for _, row in df_monthly.iterrows():
            month = row["Month"]
            count = row["Sample_Count"]
            rep_tss = row["TSS"]
            rep_brier = row["Brier_Score"]
            
            # Select month data
            m_idx = (df_ts["month"] == month).values
            y_t_m = test_targets[m_idx]
            y_p_m = test_probs_cal_iso[m_idx]
            
            y_pred_m = (y_p_m >= validation_threshold).astype(int)
            act_tss = compute_tss(y_t_m, y_pred_m)
            act_brier = np.mean((y_p_m - y_t_m) ** 2)
            
            diff_tss = abs(rep_tss - act_tss)
            diff_brier = abs(rep_brier - act_brier)
            
            print(f"  {month} | Count={count} (Actual={len(y_t_m)}) | TSS Diff={diff_tss:.6e} | Brier Diff={diff_brier:.6e}")
            if diff_tss > 1e-6 or diff_brier > 1e-6 or count != len(y_t_m):
                c4_passed = False
                
        # Check significance tests
        test_stats_path = "artifacts/sprint16a/temporal_statistical_tests.json"
        if os.path.exists(test_stats_path):
            with open(test_stats_path) as f:
                temp_data = json.load(f)
            print("  Temporal significance stats loaded.")
            
            # Recompute Kruskal-Wallis on sample errors
            sample_errors = []
            for m in actual_months:
                m_idx = (df_ts["month"] == m).values
                y_t_m = test_targets[m_idx]
                y_p_m = test_probs_cal_iso[m_idx]
                sample_errors.append((y_p_m - y_t_m) ** 2)
                
            kw_stat, kw_pval = kruskal(*sample_errors)
            rep_kw = temp_data["kruskal_wallis_sample_errors"]
            print(f"  Kruskal-Wallis Sample Errors | Recomputed: Stat={kw_stat:.4f}, p={kw_pval:.6e} | Reported: Stat={rep_kw['statistic']:.4f}, p={rep_kw['p_value']:.6e}")
            
            if abs(kw_stat - rep_kw["statistic"]) > 1e-4 or abs(kw_pval - rep_kw["p_value"]) > 1e-6:
                print("  FAIL: Kruskal-Wallis sample error stats mismatch!")
                c4_passed = False
        else:
            print("  FAIL: temporal_statistical_tests.json does not exist!")
            c4_passed = False
            
        if c4_passed:
            print("  Check 4: PASS")
        else:
            print("  Check 4: FAIL")

    # Check 5: Verify sensor_availability_report.json
    print("\n--- Check 5: sensor_availability_report.json ---")
    sensor_path = "artifacts/sprint16a/sensor_availability_report.json"
    if not os.path.exists(sensor_path):
        print("FAIL: sensor_availability_report.json does not exist!")
    else:
        with open(sensor_path) as f:
            sensor_data = json.load(f)
        
        # Verify point estimates are computed independently
        point_est = sensor_data["point_estimates"]
        c5_passed = True
        
        # Configurations
        configs = ["Baseline", "GOES_Only", "GOES_SoLEXS", "GOES_HEL1OS"]
        for config in configs:
            if config not in point_est:
                print(f"  FAIL: Configuration {config} not found in point estimates!")
                c5_passed = False
                continue
                
            # Verify TSS value for config
            rep_tss = point_est[config]["TSS"]
            
            # Recompute point estimate
            if config == "Baseline":
                probs = test_probs_cal_iso
            elif config == "GOES_Only":
                probs = cache["test_probs_cal_iso_goes_only"]
            elif config == "GOES_SoLEXS":
                probs = cache["test_probs_cal_iso_goes_solexs"]
            elif config == "GOES_HEL1OS":
                probs = cache["test_probs_cal_iso_goes_hel1os"]
                
            y_pred = (probs >= validation_threshold).astype(int)
            act_tss = compute_tss(test_targets, y_pred)
            diff_tss = abs(rep_tss - act_tss)
            print(f"  {config} Point TSS: Reported={rep_tss:.6f}, Recomputed={act_tss:.6f} (diff={diff_tss:.6e})")
            if diff_tss > 1e-6:
                c5_passed = False
                
        # Recompute McNemar's test for GOES_Only vs Baseline
        mcnemar_rep = sensor_data["mcnemar_tests"]["GOES_Only"]
        
        preds_base = (test_probs_cal_iso >= validation_threshold).astype(int)
        preds_config = (cache["test_probs_cal_iso_goes_only"] >= validation_threshold).astype(int)
        
        correct_base = (preds_base == test_targets)
        correct_config = (preds_config == test_targets)
        
        b_act = np.sum(correct_base & ~correct_config)
        c_act = np.sum(~correct_base & correct_config)
        stat_act = (abs(b_act - c_act) - 1.0) ** 2 / (b_act + c_act)
        pval_act = chi2.sf(stat_act, df=1)
        
        print(f"  McNemar GOES_Only vs Baseline:")
        print(f"    b (base correct, goes_only incorrect): Reported={mcnemar_rep['b_base_correct_config_incorrect']}, Actual={b_act}")
        print(f"    c (base incorrect, goes_only correct): Reported={mcnemar_rep['c_base_incorrect_config_correct']}, Actual={c_act}")
        print(f"    statistic: Reported={mcnemar_rep['stat']:.4f}, Actual={stat_act:.4f}")
        print(f"    p-value: Reported={mcnemar_rep['p_value']:.6e}, Actual={pval_act:.6e}")
        
        if b_act != mcnemar_rep['b_base_correct_config_incorrect'] or c_act != mcnemar_rep['c_base_incorrect_config_correct'] or abs(stat_act - mcnemar_rep['stat']) > 1e-4:
            print("  FAIL: McNemar test recomputation mismatch!")
            c5_passed = False
        else:
            print("  PASS: McNemar test recomputation matches.")
            
        if c5_passed:
            print("  Check 5: PASS")
        else:
            print("  Check 5: FAIL")

    # Check 6: Verify confidence_statistics.json
    print("\n--- Check 6: confidence_statistics.json ---")
    conf_path = "artifacts/sprint16a/confidence_statistics.json"
    if not os.path.exists(conf_path):
        print("FAIL: confidence_statistics.json does not exist!")
    else:
        with open(conf_path) as f:
            conf_data = json.load(f)
            
        # Recompute confusion matrix counts
        y_pred = (test_probs_cal_iso >= validation_threshold).astype(int)
        tp_idx = (test_targets == 1) & (y_pred == 1)
        tn_idx = (test_targets == 0) & (y_pred == 0)
        fp_idx = (test_targets == 0) & (y_pred == 1)
        fn_idx = (test_targets == 1) & (y_pred == 0)
        
        act_tp_count = np.sum(tp_idx)
        act_tn_count = np.sum(tn_idx)
        act_fp_count = np.sum(fp_idx)
        act_fn_count = np.sum(fn_idx)
        
        group_stats = conf_data["group_statistics"]
        print(f"  TP Count: Reported={group_stats['TP']['count']}, Recomputed={act_tp_count}")
        print(f"  TN Count: Reported={group_stats['TN']['count']}, Recomputed={act_tn_count}")
        print(f"  FP Count: Reported={group_stats['FP']['count']}, Recomputed={act_fp_count}")
        print(f"  FN Count: Reported={group_stats['FN']['count']}, Recomputed={act_fn_count}")
        
        c6_passed = (act_tp_count == group_stats['TP']['count'] and 
                     act_tn_count == group_stats['TN']['count'] and 
                     act_fp_count == group_stats['FP']['count'] and 
                     act_fn_count == group_stats['FN']['count'])
                     
        # Check means and std devs
        tp_mean = np.mean(test_probs_cal_iso[tp_idx])
        tp_std = np.std(test_probs_cal_iso[tp_idx])
        tn_mean = np.mean(test_probs_cal_iso[tn_idx])
        tn_std = np.std(test_probs_cal_iso[tn_idx])
        
        print(f"  TP Mean: Reported={group_stats['TP']['mean']:.6f}, Recomputed={tp_mean:.6f} | Std: Reported={group_stats['TP']['std']:.6f}, Recomputed={tp_std:.6f}")
        print(f"  TN Mean: Reported={group_stats['TN']['mean']:.6f}, Recomputed={tn_mean:.6f} | Std: Reported={group_stats['TN']['std']:.6f}, Recomputed={tn_std:.6f}")
        
        if abs(group_stats['TP']['mean'] - tp_mean) > 1e-6 or abs(group_stats['TP']['std'] - tp_std) > 1e-6:
            c6_passed = False
        if abs(group_stats['TN']['mean'] - tn_mean) > 1e-6 or abs(group_stats['TN']['std'] - tn_std) > 1e-6:
            c6_passed = False
            
        # Verify overlap statistics
        overlaps_rep = conf_data["overlap_coefficients"]
        overlap_tp_fp = compute_overlap_coefficient(test_probs_cal_iso[tp_idx], test_probs_cal_iso[fp_idx])
        overlap_tn_fn = compute_overlap_coefficient(test_probs_cal_iso[tn_idx], test_probs_cal_iso[fn_idx])
        
        print(f"  TP vs FP Overlap: Reported={overlaps_rep['TP_vs_FP']:.6f}, Recomputed={overlap_tp_fp:.6f}")
        print(f"  TN vs FN Overlap: Reported={overlaps_rep['TN_vs_FN']:.6f}, Recomputed={overlap_tn_fn:.6f}")
        
        if abs(overlaps_rep['TP_vs_FP'] - overlap_tp_fp) > 1e-6 or abs(overlaps_rep['TN_vs_FN'] - overlap_tn_fn) > 1e-6:
            print("  FAIL: Overlap coefficient mismatch!")
            c6_passed = False
            
        if c6_passed:
            print("  Check 6: PASS")
        else:
            print("  Check 6: FAIL")

    # Check 7: Verify uncertainty_analysis.json
    print("\n--- Check 7: uncertainty_analysis.json ---")
    unc_path = "artifacts/sprint16a/uncertainty_analysis.json"
    if not os.path.exists(unc_path):
        print("FAIL: uncertainty_analysis.json does not exist!")
    else:
        with open(unc_path) as f:
            unc_data = json.load(f)
            
        # Recompute correctness and groups for the subset
        y_true_sub = test_targets[subset_indices]
        y_prob_sub = test_probs_cal_iso[subset_indices]
        y_pred_sub = (y_prob_sub >= validation_threshold).astype(int)
        
        correct_sub_idx = (y_pred_sub == y_true_sub)
        incorrect_sub_idx = (y_pred_sub != y_true_sub)
        
        mean_unc_correct = np.mean(subset_uncertainty[correct_sub_idx])
        mean_unc_incorrect = np.mean(subset_uncertainty[incorrect_sub_idx])
        
        group_stats = unc_data["group_statistics"]
        print(f"  Uncertainty Correct predictions: Reported={group_stats['Correct']['mean']:.6f}, Recomputed={mean_unc_correct:.6f}")
        print(f"  Uncertainty Incorrect predictions: Reported={group_stats['Incorrect']['mean']:.6f}, Recomputed={mean_unc_incorrect:.6f}")
        
        # Check if uncertainty increases on wrong predictions:
        unc_increases = (mean_unc_incorrect > mean_unc_correct)
        print(f"  Uncertainty increases on wrong predictions: {unc_increases} (Correct: {mean_unc_correct:.6f}, Incorrect: {mean_unc_incorrect:.6f})")
        
        c7_passed = (abs(group_stats['Correct']['mean'] - mean_unc_correct) < 1e-6 and 
                     abs(group_stats['Incorrect']['mean'] - mean_unc_incorrect) < 1e-6)
                     
        # Recompute Pearson & Spearman correlations
        p_coef, _ = pearsonr(subset_uncertainty, correct_sub_idx.astype(float))
        s_coef, _ = spearmanr(subset_uncertainty, correct_sub_idx.astype(float))
        
        rep_corr = unc_data["correlations"]["correctness"]
        print(f"  Pearson correlation (correctness): Reported={rep_corr['pearson']['coefficient']:.6f}, Recomputed={p_coef:.6f}")
        print(f"  Spearman correlation (correctness): Reported={rep_corr['spearman']['coefficient']:.6f}, Recomputed={s_coef:.6f}")
        
        if abs(rep_corr['pearson']['coefficient'] - p_coef) > 1e-6 or abs(rep_corr['spearman']['coefficient'] - s_coef) > 1e-6:
            print("  FAIL: Correlation coefficient recomputation mismatch!")
            c7_passed = False
            
        if c7_passed:
            print("  Check 7: PASS")
        else:
            print("  Check 7: FAIL")

    # Check 8: Verify statistical_validation_report.md numbers match artifacts
    print("\n--- Check 8: statistical_validation_report.md ---")
    report_md_path = "artifacts/sprint16a/statistical_validation_report.md"
    if not os.path.exists(report_md_path):
        print("FAIL: statistical_validation_report.md does not exist!")
    else:
        with open(report_md_path) as f:
            report_content = f.read()
            
        # Parse reported numbers in report and check them against JSON/CSV
        # We will do a manual checklist but also verify some keys
        # E.g. ROC-AUC mean 0.7409, TSS mean 0.4002, overall calibrated ECE 0.043238
        checks_report = [
            ("0.7409", "0.7409" in report_content, "ROC-AUC mean is present"),
            ("0.4002", "0.4002" in report_content, "TSS mean is present"),
            ("0.4462", "0.4462" in report_content, "PR-AUC mean is present"),
            ("0.3443", "0.3443" in report_content, "HSS mean is present"),
            ("0.0876", "0.0876" in report_content, "Brier mean is present"),
            ("0.0439", "0.0439" in report_content, "ECE mean is present"),
            ("0.316869 (Locked)", "0.316869" in report_content, "Locked threshold is present"),
            ("15,772", "15,772" in report_content or "15772" in report_content, "TP count is present"),
            ("201,695", "201,695" in report_content or "201695" in report_content, "TN count is present"),
            ("28,289", "28,289" in report_content or "28289" in report_content, "FP count is present"),
            ("15,339", "15,339" in report_content or "15339" in report_content, "FN count is present"),
            ("0.5848", "0.5848" in report_content, "TP vs FP overlap is present"),
            ("0.8783", "0.8783" in report_content, "TN vs FN overlap is present"),
            ("0.0033", "0.0033" in report_content, "Uncertainty correct predictions mean is present"),
            ("0.0028", "0.0028" in report_content, "Uncertainty incorrect predictions mean is present"),
            ("Kruskal-Wallis", "Kruskal-Wallis" in report_content, "Kruskal-Wallis test is mentioned"),
            ("McNemar", "McNemar" in report_content, "McNemar test is mentioned")
        ]
        
        c8_passed = True
        for name, present, desc in checks_report:
            print(f"  Report contains '{name}' ({desc}): {present}")
            if not present:
                c8_passed = False
                
        if c8_passed:
            print("  Check 8: PASS")
        else:
            print("  Check 8: FAIL")

    # Check 9: Repository Integrity
    print("\n--- Check 9: Repository Integrity ---")
    manifest_path = "artifacts/sprint15a/benchmark_manifest.json"
    if not os.path.exists(manifest_path):
        print("FAIL: benchmark_manifest.json does not exist!")
        c9_passed = False
    else:
        with open(manifest_path) as f:
            manifest = json.load(f)
            
        hashes_to_check = {
            "train_parquet": "artifacts/sprint14c/s2_train.parquet",
            "val_parquet": "artifacts/sprint14c/s2_val.parquet",
            "test_parquet": "artifacts/sprint14c/s2_test.parquet",
            "feature_columns_v3_json": "artifacts/feature_columns_v3.json",
            "model_seed_42_stage2_best_pt": "artifacts/sprint14c/checkpoints/model_seed_42_stage2_best.pt",
            "model_seed_42_stage1_best_pt": "artifacts/sprint14c/checkpoints/model_seed_42_stage1_best.pt",
            "model_v3_py": "app/services/ml/model_v3.py"
        }
        
        c9_passed = True
        for key, path in hashes_to_check.items():
            computed = sha256(path)
            # Find expected hash in manifest
            expected = manifest["dataset_hashes" if "parquet" in key else ("feature_manifest" if "json" in key else ("checkpoint_hash" if "pt" in key else "model_hash"))][key]
            
            if computed != expected:
                print(f"  FAIL: Hash mismatch for {key} ({path}). Expected: {expected}, Got: {computed}")
                c9_passed = False
            else:
                print(f"  PASS: {key} ({path}) matches.")
                
        if c9_passed:
            print("  Check 9: PASS")
        else:
            print("  Check 9: FAIL")

if __name__ == "__main__":
    main()
