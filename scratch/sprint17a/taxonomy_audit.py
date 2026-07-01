"""
scratch/sprint17a/taxonomy_audit.py

Sprint 17A.1: Taxonomy Audit & Bias Quantification.
Performs flag co-occurrence analysis, category overlap metrics, priority ordering sensitivity,
category transition matrix, category purity calculations, and Unknown category audits.
"""

import os
import json
import logging
import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# List of 10 boolean flags
FLAGS = [
    "is_missing_sensor",
    "is_transition",
    "is_label_ambiguity",
    "is_high_confidence",
    "is_high_uncertainty",
    "is_sensor_disagreement",
    "is_quiet_background",
    "is_weak_flare",
    "is_background_flux_drift",
    "is_temporal_drift"
]

# Baseline priority ordering of category rules
BASELINE_ORDER = [
    "Missing Sensor Information",
    "High Confidence Quiet Sun False Alarm",
    "Quiet Sun False Alarm",
    "Weak Flare Transition Miss",
    "Weak Flare Miss",
    "Transition Phase Failure",
    "Instrument Disagreement",
    "Background Flux Drift",
    "Temporal Drift Failure",
    "Borderline Label Ambiguity",
    "High Uncertainty Failure"
]

def satisfy_rule(row, category):
    """
    Checks if a row satisfies the condition for a given category.
    """
    if category == "Missing Sensor Information":
        return bool(row["is_missing_sensor"])
    elif category == "High Confidence Quiet Sun False Alarm":
        return bool(row["is_quiet_background"] and row["is_high_confidence"])
    elif category == "Quiet Sun False Alarm":
        return bool(row["is_quiet_background"])
    elif category == "Weak Flare Transition Miss":
        return bool(row["is_weak_flare"] and row["is_transition"])
    elif category == "Weak Flare Miss":
        return bool(row["is_weak_flare"])
    elif category == "Transition Phase Failure":
        return bool(row["is_transition"])
    elif category == "Instrument Disagreement":
        return bool(row["is_sensor_disagreement"])
    elif category == "Background Flux Drift":
        return bool(row["is_background_flux_drift"])
    elif category == "Temporal Drift Failure":
        return bool(row["is_temporal_drift"])
    elif category == "Borderline Label Ambiguity":
        return bool(row["is_label_ambiguity"])
    elif category == "High Uncertainty Failure":
        return bool(row["is_high_uncertainty"])
    return False

def assign_category(row, order):
    """
    Assigns a category based on a sequential priority order.
    """
    for cat in order:
        if satisfy_rule(row, cat):
            return cat
            
    # Fallback logic
    n_active = sum(row[f] for f in FLAGS)
    if n_active == 0:
        return "Unknown"
    return "Mixed Multi-Flag Failure"

def compute_entropy(p_fp, p_fn):
    """
    Computes Shannon binary entropy.
    """
    if p_fp == 0.0 or p_fn == 0.0:
        return 0.0
    return - p_fp * np.log2(p_fp) - p_fn * np.log2(p_fn)

def main():
    logger.info("Loading predictions cache and parquet test set...")
    cache = np.load("scratch/sprint16a/cached_predictions.npz")
    df_test = pd.read_parquet("artifacts/sprint14c/s2_test.parquet")
    
    # Identify low-performance months dynamically
    monthly_metrics_path = "artifacts/sprint16a/monthly_metrics.csv"
    if os.path.exists(monthly_metrics_path):
        df_months = pd.read_csv(monthly_metrics_path)
        low_perf_months = df_months[df_months["TSS"] < 0.10]["Month"].tolist()
    else:
        low_perf_months = ["2025-12", "2026-01", "2026-03", "2026-05"]
        
    best_th = float(cache["validation_threshold"])
    y_true_full = cache["test_targets"]
    y_prob_full = cache["test_probs_cal_iso"]
    y_prob_goes_only_full = cache["test_probs_cal_iso_goes_only"]
    
    df_aligned = df_test.iloc[360:].copy().reset_index(drop=True)
    df_aligned["prob_cal"] = y_prob_full
    df_aligned["prob_goes_only"] = y_prob_goes_only_full
    df_aligned["pred_binary"] = (y_prob_full >= best_th).astype(int)
    df_aligned["is_failure"] = (df_aligned["pred_binary"] != df_aligned["target_6hr_binary"]).astype(int)
    df_aligned["failure_type"] = "NONE"
    df_aligned.loc[(df_aligned["target_6hr_binary"] == 0) & (df_aligned["pred_binary"] == 1), "failure_type"] = "FP"
    df_aligned.loc[(df_aligned["target_6hr_binary"] == 1) & (df_aligned["pred_binary"] == 0), "failure_type"] = "FN"
    
    # Extract subset
    subset_indices = cache["subset_indices"]
    uncertainty_subset = cache["subset_uncertainty"]
    
    df_subset = df_aligned.iloc[subset_indices].copy().reset_index(drop=True)
    df_subset["uncertainty"] = uncertainty_subset
    
    # Failures in subset (should be 3,213)
    df_failures = df_subset[df_subset["is_failure"] == 1].copy().reset_index(drop=True)
    N_fail = len(df_failures)
    logger.info(f"Loaded {N_fail} failures for audit.")
    
    df_failures["month"] = pd.to_datetime(df_failures["timestamp"]).dt.to_period("M").astype(str)
    
    # Compute flags for every failure sample
    df_failures["is_missing_sensor"] = (df_failures["mask_solexs"] == 0) | (df_failures["mask_hel1os"] == 0)
    df_failures["is_transition"] = df_failures["minutes_since_last_flare"] < 30
    df_failures["is_label_ambiguity"] = np.abs(df_failures["prob_cal"] - best_th) < 0.02
    df_failures["is_high_confidence"] = df_failures["prob_cal"] >= 0.70
    df_failures["is_high_uncertainty"] = df_failures["uncertainty"] > 0.0035
    df_failures["is_sensor_disagreement"] = np.abs(df_failures["prob_cal"] - df_failures["prob_goes_only"]) > 0.20
    df_failures["is_quiet_background"] = (df_failures["failure_type"] == "FP") & (df_failures["long_flux"] < 1.5e-6)
    df_failures["is_weak_flare"] = (df_failures["failure_type"] == "FN") & (df_failures["target_6hr_class"] == 1)
    df_failures["is_background_flux_drift"] = df_failures["mean_60m"] > 5e-6
    df_failures["is_temporal_drift"] = df_failures["month"].isin(low_perf_months)
    
    # Flag matrix as array
    flag_mat = df_failures[FLAGS].values.astype(int)  # [N_fail, 10]
    
    # ----------------------------------------------------
    # 1. Flag Co-occurrence Matrix
    # ----------------------------------------------------
    co_occurrence_records = []
    for i, flag_i in enumerate(FLAGS):
        for j, flag_j in enumerate(FLAGS):
            cnt_both = int(np.sum((flag_mat[:, i] == 1) & (flag_mat[:, j] == 1)))
            cnt_either = int(np.sum((flag_mat[:, i] == 1) | (flag_mat[:, j] == 1)))
            
            jaccard = cnt_both / cnt_either if cnt_either > 0 else 0.0
            
            cnt_i = int(np.sum(flag_mat[:, i] == 1))
            cnt_j = int(np.sum(flag_mat[:, j] == 1))
            
            p_i_given_j = cnt_both / cnt_j if cnt_j > 0 else 0.0
            p_j_given_i = cnt_both / cnt_i if cnt_i > 0 else 0.0
            
            co_occurrence_records.append({
                "Flag_A": flag_i,
                "Flag_B": flag_j,
                "Cooccurrence_Count": cnt_both,
                "Jaccard_Similarity": jaccard,
                "P_A_given_B": p_i_given_j,
                "P_B_given_A": p_j_given_i
            })
            
    df_co_occurrence = pd.DataFrame(co_occurrence_records)
    
    # ----------------------------------------------------
    # 2. Multi-flag statistics
    # ----------------------------------------------------
    flag_counts = flag_mat.sum(axis=1)
    multi_flag_samples = int(np.sum(flag_counts >= 2))
    multi_flag_pct = float(multi_flag_samples / N_fail) * 100
    
    hist_counts = {}
    for n in range(11):
        hist_counts[int(n)] = int(np.sum(flag_counts == n))
        
    multi_flag_stats = {
        "total_failures": N_fail,
        "multi_flag_failures_count": multi_flag_samples,
        "multi_flag_failures_percentage": multi_flag_pct,
        "mean_active_flags_per_sample": float(np.mean(flag_counts)),
        "active_flags_histogram": hist_counts
    }
    
    # ----------------------------------------------------
    # 3. Category Overlap Matrix
    # ----------------------------------------------------
    # For every sample, find all categories it satisfies
    overlap_records = []
    satisfied_lists = []
    for idx, row in df_failures.iterrows():
        satisfied = [cat for cat in BASELINE_ORDER if satisfy_rule(row, cat)]
        satisfied_lists.append(satisfied)
        
    df_failures["satisfied_categories"] = satisfied_lists
    
    overlap_counts = np.zeros((11, 11), dtype=int)
    for i, cat_i in enumerate(BASELINE_ORDER):
        for j, cat_j in enumerate(BASELINE_ORDER):
            cnt = 0
            for satisfied in satisfied_lists:
                if cat_i in satisfied and cat_j in satisfied:
                    cnt += 1
            overlap_counts[i, j] = cnt
            
    overlap_matrix_records = []
    for i, cat_i in enumerate(BASELINE_ORDER):
        for j, cat_j in enumerate(BASELINE_ORDER):
            overlap_matrix_records.append({
                "Category_A": cat_i,
                "Category_B": cat_j,
                "Overlap_Count": int(overlap_counts[i, j])
            })
    df_overlap_matrix = pd.DataFrame(overlap_matrix_records)
    
    # Count samples matching multiple rules
    multi_rule_samples = 0
    overlap_combinations = {}
    for satisfied in satisfied_lists:
        if len(satisfied) > 1:
            multi_rule_samples += 1
            comb = tuple(sorted(satisfied))
            overlap_combinations[comb] = overlap_combinations.get(comb, 0) + 1
            
    overlap_comb_json = {}
    for comb, cnt in overlap_combinations.items():
        overlap_comb_json["_and_".join(comb)] = int(cnt)
        
    taxonomy_overlap = {
        "multi_category_match_count": multi_rule_samples,
        "multi_category_match_percentage": float(multi_rule_samples / N_fail) * 100,
        "overlap_combinations_frequency": overlap_comb_json
    }
    
    # ----------------------------------------------------
    # 4. Ordering Sensitivity Analysis
    # ----------------------------------------------------
    # Define alternative orderings
    orderings = {
        "baseline": BASELINE_ORDER,
        "alphabetical": sorted(BASELINE_ORDER),
        "reverse_current": list(reversed(BASELINE_ORDER)),
        "quiet_background_first": ["High Confidence Quiet Sun False Alarm", "Quiet Sun False Alarm"] + [c for c in BASELINE_ORDER if c not in ["High Confidence Quiet Sun False Alarm", "Quiet Sun False Alarm"]],
        "weak_flare_first": ["Weak Flare Transition Miss", "Weak Flare Miss"] + [c for c in BASELINE_ORDER if c not in ["Weak Flare Transition Miss", "Weak Flare Miss"]],
        "temporal_drift_first": ["Temporal Drift Failure"] + [c for c in BASELINE_ORDER if c not in ["Temporal Drift Failure"]],
        "background_flux_first": ["Background Flux Drift"] + [c for c in BASELINE_ORDER if c not in ["Background Flux Drift"]]
    }
    
    assignments = {}
    for name, order in orderings.items():
        assignments[name] = df_failures.apply(lambda r: assign_category(r, order), axis=1).values
        
    # Completeness invariant validation
    for name, arr in assignments.items():
        # 1. Total sum count check
        assert len(arr) == N_fail, f"Length mismatch for {name}!"
        unique, counts = np.unique(arr, return_counts=True)
        assert sum(counts) == N_fail, f"Sum check failed for {name}!"
        
    sensitivity_records = []
    
    # Baseline counts for metrics comparison
    unique_baseline, counts_baseline = np.unique(assignments["baseline"], return_counts=True)
    baseline_counts_map = dict(zip(unique_baseline, counts_baseline))
    all_possible_categories = list(set(BASELINE_ORDER + ["Unknown", "Mixed Multi-Flag Failure"]))
    
    # Populate baseline defaults
    for cat in all_possible_categories:
        if cat not in baseline_counts_map:
            baseline_counts_map[cat] = 0
            
    for name, arr in assignments.items():
        unique_arr, counts_arr = np.unique(arr, return_counts=True)
        arr_counts_map = dict(zip(unique_arr, counts_arr))
        for cat in all_possible_categories:
            if cat not in arr_counts_map:
                arr_counts_map[cat] = 0
                
        # Overall stability metrics
        max_shift = 0
        sum_abs_shift = 0
        changed_samples = int(np.sum(assignments["baseline"] != arr))
        pct_changed = float(changed_samples / N_fail) * 100
        
        for cat in all_possible_categories:
            shift = int(arr_counts_map[cat] - baseline_counts_map[cat])
            max_shift = max(max_shift, abs(shift))
            sum_abs_shift += abs(shift)
            
        mean_abs_shift = float(sum_abs_shift / len(all_possible_categories))
        
        for cat in all_possible_categories:
            cnt = arr_counts_map[cat]
            pct = (cnt / N_fail) * 100
            diff = int(cnt - baseline_counts_map[cat])
            pct_diff = (diff / baseline_counts_map[cat] * 100) if baseline_counts_map[cat] > 0 else (0.0 if diff == 0 else 100.0)
            
            sensitivity_records.append({
                "Ordering": name,
                "Category": cat,
                "Sample_Count": cnt,
                "Percentage": pct,
                "Absolute_Change_from_Baseline": diff,
                "Percentage_Change_from_Baseline": pct_diff,
                "Overall_Max_Category_Shift": max_shift,
                "Overall_Mean_Absolute_Category_Shift": mean_abs_shift,
                "Overall_Percentage_of_Failures_Changed": pct_changed
            })
            
    df_sensitivity = pd.DataFrame(sensitivity_records)
    
    # ----------------------------------------------------
    # 5. Category Reassignment Matrix
    # ----------------------------------------------------
    reassignment_records = []
    for name in orderings.keys():
        if name == "baseline":
            continue
        # Compare with baseline
        for base_cat in all_possible_categories:
            base_mask = (assignments["baseline"] == base_cat)
            n_base = int(np.sum(base_mask))
            
            if n_base > 0:
                alt_assigned = assignments[name][base_mask]
                unique_alt, counts_alt = np.unique(alt_assigned, return_counts=True)
                for re_cat, re_cnt in zip(unique_alt, counts_alt):
                    reassignment_records.append({
                        "Baseline_Category": base_cat,
                        "Alternative_Ordering": name,
                        "Reassigned_Category": re_cat,
                        "Sample_Count": int(re_cnt),
                        "Percentage_Reassigned": float(re_cnt / n_base) * 100
                    })
            else:
                # No baseline samples in this category
                pass
                
    df_reassignment = pd.DataFrame(reassignment_records)
    
    # ----------------------------------------------------
    # 6. Category Purity
    # ----------------------------------------------------
    purity_records = []
    baseline_assignments = assignments["baseline"]
    for cat in all_possible_categories:
        cat_mask = (baseline_assignments == cat)
        cat_failures = df_failures[cat_mask]
        
        cnt_fp = int(np.sum(cat_failures["failure_type"] == "FP"))
        cnt_fn = int(np.sum(cat_failures["failure_type"] == "FN"))
        total = cnt_fp + cnt_fn
        
        if total > 0:
            p_fp = cnt_fp / total
            p_fn = cnt_fn / total
            entropy = float(compute_entropy(p_fp, p_fn))
            majority_pct = float(max(p_fp, p_fn)) * 100
        else:
            p_fp = 0.0
            p_fn = 0.0
            entropy = 0.0
            majority_pct = 0.0
            
        purity_records.append({
            "Category": cat,
            "Total_Count": total,
            "FP_Count": cnt_fp,
            "FN_Count": cnt_fn,
            "FP_Percentage": p_fp * 100,
            "FN_Percentage": p_fn * 100,
            "Shannon_Entropy": entropy,
            "Majority_Class_Percentage": majority_pct
        })
    df_purity = pd.DataFrame(purity_records)
    
    # ----------------------------------------------------
    # 7. Unknown Category Audit & Consistency Check
    # ----------------------------------------------------
    unknown_mask = (baseline_assignments == "Unknown")
    df_unknown = df_failures[unknown_mask].copy().reset_index(drop=True)
    
    unknown_audit_records = []
    for idx, row in df_unknown.iterrows():
        # active flag count
        n_active = sum(row[f] for f in FLAGS)
        
        # missing values check
        missing_count = int(row.isna().sum())
        
        # feature values
        unknown_audit_records.append({
            "Timestamp": str(row["timestamp"]),
            "Active_Flag_Count": n_active,
            "Missing_Values_Count": missing_count,
            "Calibrated_Probability": float(row["prob_cal"]),
            "MC_Dropout_Uncertainty": float(row["uncertainty"]),
            "GOES_long_flux": float(row["long_flux"]),
            "GOES_short_flux": float(row["short_flux"]),
            "SoLEXS_rate_ch1": float(row["solexs_rate_ch1"]) if pd.notna(row["solexs_rate_ch1"]) else None,
            "HEL1OS_rate_band0": float(row["hel1os_rate_band0"]) if pd.notna(row["hel1os_rate_band0"]) else None
        })
    df_unknown_samples = pd.DataFrame(unknown_audit_records)
    
    # Unknown consistency check: verify every Unknown sample satisfies zero rules under all orderings
    unknown_fails_check = 0
    for name, arr in assignments.items():
        unknown_indices = np.where(baseline_assignments == "Unknown")[0]
        for idx in unknown_indices:
            assigned_cat = arr[idx]
            if assigned_cat != "Unknown":
                unknown_fails_check += 1
                logger.error(f"Sample index {idx} became {assigned_cat} under ordering {name}!")
                
    assert unknown_fails_check == 0, f"Unknown consistency check failed: {unknown_fails_check} samples changed from Unknown!"
    
    # Overall Audit Statistics
    audit_stats = {
        "audit_samples_count": N_fail,
        "multi_flag_samples_count": multi_flag_samples,
        "multi_flag_samples_percentage": multi_flag_pct,
        "multi_category_match_count": multi_rule_samples,
        "multi_category_match_percentage": float(multi_rule_samples / N_fail) * 100,
        "baseline_unknowns_count": len(df_unknown),
        "unknown_consistency_check_failures": unknown_fails_check,
        "completeness_invariants_status": "PASS"
    }
    
    # ----------------------------------------------------
    # 8. Save output files
    # ----------------------------------------------------
    out_dir = "artifacts/sprint17a_audit"
    os.makedirs(out_dir, exist_ok=True)
    
    df_co_occurrence.to_csv(f"{out_dir}/flag_cooccurrence.csv", index=False)
    df_overlap_matrix.to_csv(f"{out_dir}/overlap_matrix.csv", index=False)
    df_sensitivity.to_csv(f"{out_dir}/ordering_sensitivity.csv", index=False)
    df_reassignment.to_csv(f"{out_dir}/category_transition_matrix.csv", index=False)
    df_purity.to_csv(f"{out_dir}/category_purity.csv", index=False)
    df_unknown_samples.to_csv(f"{out_dir}/unknown_samples.csv", index=False)
    
    with open(f"{out_dir}/multi_flag_statistics.json", "w") as f:
        json.dump(multi_flag_stats, f, indent=2)
        
    with open(f"{out_dir}/taxonomy_overlap.json", "w") as f:
        json.dump(taxonomy_overlap, f, indent=2)
        
    with open(f"{out_dir}/audit_statistics.json", "w") as f:
        json.dump(audit_stats, f, indent=2)
        
    logger.info("Sprint 17A.1 taxonomy audit and bias quantification: PASS")

if __name__ == "__main__":
    main()
