import os
import sys
import json
import numpy as np
import pandas as pd

# List of flags
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

def get_category_name(row):
    if row["is_missing_sensor"]:
        return "Missing Sensor Information"
    if row["is_quiet_background"] and row["is_high_confidence"]:
        return "High Confidence Quiet Sun False Alarm"
    if row["is_quiet_background"]:
        return "Quiet Sun False Alarm"
    if row["is_weak_flare"] and row["is_transition"]:
        return "Weak Flare Transition Miss"
    if row["is_weak_flare"]:
        return "Weak Flare Miss"
    if row["is_transition"]:
        return "Transition Phase Failure"
    if row["is_sensor_disagreement"]:
        return "Instrument Disagreement"
    if row["is_background_flux_drift"]:
        return "Background Flux Drift"
    if row["is_temporal_drift"]:
        return "Temporal Drift Failure"
    if row["is_label_ambiguity"]:
        return "Borderline Label Ambiguity"
    if row["is_high_uncertainty"]:
        return "High Uncertainty Failure"
    
    # Check if any flags are active
    active = [f for f in FLAGS if row[f]]
    if len(active) == 0:
        return "Unknown"
    return "Mixed Multi-Flag Failure"

def main():
    print("=== STARTING SPRINT 17A INDEPENDENT VALIDATION ===")
    
    # Load data
    cache = np.load("scratch/sprint16a/cached_predictions.npz")
    df_test = pd.read_parquet("artifacts/sprint14c/s2_test.parquet")
    
    # Read monthly metrics to determine low performance months
    monthly_metrics_path = "artifacts/sprint16a/monthly_metrics.csv"
    if os.path.exists(monthly_metrics_path):
        df_months = pd.read_csv(monthly_metrics_path)
        low_perf_months = df_months[df_months["TSS"] < 0.10]["Month"].tolist()
        print("Low performance months:", low_perf_months)
    else:
        low_perf_months = ["2025-12", "2026-01", "2026-03", "2026-05"]
        print("Low performance months (fallback):", low_perf_months)
        
    best_th = float(cache["validation_threshold"])
    y_true_full = cache["test_targets"]
    y_prob_full = cache["test_probs_cal_iso"]
    y_prob_goes_only_full = cache["test_probs_cal_iso_goes_only"]
    
    # Align parquet
    df_aligned = df_test.iloc[360:].copy().reset_index(drop=True)
    df_aligned["prob_cal"] = y_prob_full
    df_aligned["prob_goes_only"] = y_prob_goes_only_full
    df_aligned["pred_binary"] = (y_prob_full >= best_th).astype(int)
    df_aligned["is_failure"] = (df_aligned["pred_binary"] != df_aligned["target_6hr_binary"]).astype(int)
    df_aligned["failure_type"] = "NONE"
    df_aligned.loc[(df_aligned["target_6hr_binary"] == 0) & (df_aligned["pred_binary"] == 1), "failure_type"] = "FP"
    df_aligned.loc[(df_aligned["target_6hr_binary"] == 1) & (df_aligned["pred_binary"] == 0), "failure_type"] = "FN"
    
    subset_indices = cache["subset_indices"]
    uncertainty_subset = cache["subset_uncertainty"]
    
    df_subset = df_aligned.iloc[subset_indices].copy().reset_index(drop=True)
    df_subset["uncertainty"] = uncertainty_subset
    
    # Extract failure subset
    df_subset_failures = df_subset[df_subset["is_failure"] == 1].copy().reset_index(drop=True)
    print(f"Total failures in subset: {len(df_subset_failures)}")
    
    # Compute flags
    df_subset_failures["month"] = pd.to_datetime(df_subset_failures["timestamp"]).dt.to_period("M").astype(str)
    df_subset_failures["is_missing_sensor"] = (df_subset_failures["mask_solexs"] == 0) | (df_subset_failures["mask_hel1os"] == 0)
    df_subset_failures["is_transition"] = df_subset_failures["minutes_since_last_flare"] < 30
    df_subset_failures["is_label_ambiguity"] = np.abs(df_subset_failures["prob_cal"] - best_th) < 0.02
    df_subset_failures["is_high_confidence"] = df_subset_failures["prob_cal"] >= 0.70
    df_subset_failures["is_high_uncertainty"] = df_subset_failures["uncertainty"] > 0.0035
    df_subset_failures["is_sensor_disagreement"] = np.abs(df_subset_failures["prob_cal"] - df_subset_failures["prob_goes_only"]) > 0.20
    df_subset_failures["is_quiet_background"] = (df_subset_failures["failure_type"] == "FP") & (df_subset_failures["long_flux"] < 1.5e-6)
    df_subset_failures["is_weak_flare"] = (df_subset_failures["failure_type"] == "FN") & (df_subset_failures["target_6hr_class"] == 1)
    df_subset_failures["is_background_flux_drift"] = df_subset_failures["mean_60m"] > 5e-6
    df_subset_failures["is_temporal_drift"] = df_subset_failures["month"].isin(low_perf_months)
    
    # Map to category
    df_subset_failures["category"] = df_subset_failures.apply(get_category_name, axis=1)
    
    # Verify counts and percentages
    print("\n--- Taxonomy Category Breakdown ---")
    cat_counts = df_subset_failures["category"].value_counts()
    cat_pcts = df_subset_failures["category"].value_counts(normalize=True) * 100
    
    total_failures_sum = 0
    for cat in sorted(df_subset_failures["category"].unique()):
        cnt = cat_counts[cat]
        pct = cat_pcts[cat]
        total_failures_sum += cnt
        print(f"  {cat:<45} | Count: {cnt:<5} | Percentage: {pct:.2f}%")
        
    print(f"Sum of category counts: {total_failures_sum} (Expected: {len(df_subset_failures)})")
    
    # Check if every FP and FN appears exactly once
    print("\n--- Failure Membership Verification ---")
    # Total FP in subset failures
    fps_in_subset = df_subset_failures[df_subset_failures["failure_type"] == "FP"]
    fns_in_subset = df_subset_failures[df_subset_failures["failure_type"] == "FN"]
    print(f"FPs in subset failures: {len(fps_in_subset)}")
    print(f"FNs in subset failures: {len(fns_in_subset)}")
    print(f"FPs + FNs = {len(fps_in_subset) + len(fns_in_subset)}")
    
    # Verify no TPs or TNs
    non_failures_in_subset = df_subset_failures[~df_subset_failures["failure_type"].isin(["FP", "FN"])]
    print(f"Non-failures (TP or TN) in subset failures: {len(non_failures_in_subset)} (Expected: 0)")
    
    # Check category counts vs failure type
    print("\n--- Category Breakdown by Failure Type ---")
    for cat in cat_counts.index:
        cat_df = df_subset_failures[df_subset_failures["category"] == cat]
        types = cat_df["failure_type"].value_counts().to_dict()
        print(f"  {cat:<45} | Types: {types}")
        
    # Check reported statistics in failure_summary.md
    print("\n--- Verifying Reported Statistics in failure_summary.md ---")
    
    # Dominant Category 1: Quiet Sun False Alarm
    cat1_df = df_subset_failures[df_subset_failures["category"] == "Quiet Sun False Alarm"]
    if len(cat1_df) > 0:
        med_prob = cat1_df["prob_cal"].median()
        med_goes = cat1_df["long_flux"].median()
        med_dt = cat1_df["minutes_since_last_flare"].median()
        print("  Quiet Sun False Alarm:")
        print(f"    calibrated probability median: {med_prob:.6f} (Expected in report: 0.3553)")
        print(f"    median GOES long flux: {med_goes:.2e} (Expected in report: 9.03e-7)")
        print(f"    median minutes since last flare: {med_dt:.1f} (Expected in report: 376.5)")
        
    # Successful TN baseline for comparison
    tn_df = df_subset[(df_subset["target_6hr_binary"] == 0) & (df_subset["pred_binary"] == 0)]
    print("  True Negatives (baseline):")
    print(f"    median GOES long flux: {tn_df['long_flux'].median():.2e} (Expected in report: 8.30e-7)")
    print(f"    median minutes since last flare: {tn_df['minutes_since_last_flare'].median():.1f} (Expected in report: 4720.0)")
    print(f"    median uncertainty: {tn_df['uncertainty'].median():.6f} (Expected in report: 0.0034)")
    print(f"    Quiet Sun FPs median uncertainty: {cat1_df['uncertainty'].median():.6f} (Expected in report: 0.0026)")
    
    # Dominant Category 2: Weak Flare Miss
    cat2_df = df_subset_failures[df_subset_failures["category"] == "Weak Flare Miss"]
    if len(cat2_df) > 0:
        med_prob2 = cat2_df["prob_cal"].median()
        med_goes2 = cat2_df["long_flux"].median()
        med_dt2 = cat2_df["minutes_since_last_flare"].median()
        target_classes = cat2_df["target_6hr_class"].value_counts().to_dict()
        print("  Weak Flare Miss:")
        print(f"    calibrated probability median: {med_prob2:.6f} (Expected in report: 0.0810)")
        print(f"    median GOES long flux: {med_goes2:.2e} (Expected in report: 1.11e-6)")
        print(f"    median minutes since last flare: {med_dt2:.1f} (Expected in report: 3949.0)")
        print(f"    target classes: {target_classes} (Expected in report: 100% Class 1)")
        
    # Successful TP baseline for comparison
    tp_df = df_subset[(df_subset["target_6hr_binary"] == 1) & (df_subset["pred_binary"] == 1)]
    print("  True Positives (baseline):")
    print(f"    median GOES long flux: {tp_df['long_flux'].median():.2e} (Expected in report: 2.63e-6)")
    print(f"    median minutes since last flare: {tp_df['minutes_since_last_flare'].median():.1f} (Expected in report: 135.0)")
    
    # Dominant Category 3: Missing Sensor Information
    cat3_df = df_subset_failures[df_subset_failures["category"] == "Missing Sensor Information"]
    if len(cat3_df) > 0:
        med_solexs = cat3_df["solexs_rate_ch1"].median() # Note SoLEXS rate ch1 might be masked/nan
        med_prob3 = cat3_df["prob_cal"].median()
        med_unc3 = cat3_df["uncertainty"].median()
        print("  Missing Sensor Information:")
        print(f"    median SoLEXS rate ch1: {med_solexs} (Expected in report: 0.0 or nan)")
        print(f"    calibrated probability median: {med_prob3:.6f} (Expected in report: 0.3553)")
        print(f"    uncertainty median: {med_unc3:.6f} (Expected in report: 0.0026)")
        
    # 4. Verify representative examples belong to their assigned categories
    print("\n--- Verifying Representative Examples ---")
    df_rep = pd.read_csv("artifacts/sprint17a/representative_failures.csv")
    print(f"Loaded {len(df_rep)} representative examples.")
    
    # Check if each example in representative_failures.csv matches the computed categories
    mismatches = 0
    for idx, row in df_rep.iterrows():
        ts = row["Timestamp"]
        cat_rep = row["Category"]
        prob_rep = row["Calibrated_Probability"]
        
        # Look up this timestamp in df_subset_failures
        matching_rows = df_subset_failures[df_subset_failures["timestamp"] == ts]
        if len(matching_rows) == 0:
            # Maybe timestamp string format is slightly different
            matching_rows = df_subset_failures[df_subset_failures["timestamp"].astype(str) == ts]
            
        if len(matching_rows) == 0:
            print(f"  Warning: Example with timestamp {ts} not found in subset failures!")
            mismatches += 1
            continue
            
        row_subset = matching_rows.iloc[0]
        actual_cat = row_subset["category"]
        actual_prob = row_subset["prob_cal"]
        
        if actual_cat != cat_rep:
            print(f"  MISMATCH for example at {ts}: Reported Category='{cat_rep}', Actual Computed Category='{actual_cat}'")
            mismatches += 1
        else:
            prob_diff = abs(actual_prob - prob_rep)
            print(f"  MATCH: example at {ts} | Cat: '{cat_rep}' | Prob: {prob_rep:.6f} (subset prob: {actual_prob:.6f}, diff={prob_diff:.6e})")
            
    print(f"Total representative example mismatches: {mismatches}")

    # Load failure taxonomy JSON to check matching
    print("\n--- Verifying failure_taxonomy.json ---")
    tax_json_path = "artifacts/sprint17a/failure_taxonomy.json"
    if os.path.exists(tax_json_path):
        with open(tax_json_path) as f:
            tax_json = json.load(f)
        for cat, val in tax_json.items():
            cnt = val["count"]
            pct = val["percentage"]
            diff_cnt = abs(cnt - cat_counts.get(cat, 0))
            diff_pct = abs(pct - cat_pcts.get(cat, 0))
            print(f"  {cat:<45} | Count mismatch={diff_cnt} | Percentage mismatch={diff_pct:.4f}")
    else:
        print("  failure_taxonomy.json does not exist!")

if __name__ == "__main__":
    main()
