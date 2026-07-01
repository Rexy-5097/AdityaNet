"""
scratch/sprint17a/failure_taxonomy.py

Sprint 17A: Failure Taxonomy.
Performs a rigorous, data-driven failure analysis on the frozen model predictions.
Groups failures by co-occurrence of 10 boolean flags, calculates detailed distributions,
compares failure classes against successful counterparts, and selects representative examples.
"""

import os
import json
import logging
import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

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

def compute_iqr(arr):
    q75, q25 = np.percentile(arr, [75, 25])
    return float(q75 - q25)

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
    logger.info("Loading predictions cache and parquet test set...")
    cache = np.load("scratch/sprint16a/cached_predictions.npz")
    df_test = pd.read_parquet("artifacts/sprint14c/s2_test.parquet")
    
    # Parse low-performance months dynamically
    monthly_metrics_path = "artifacts/sprint16a/monthly_metrics.csv"
    if os.path.exists(monthly_metrics_path):
        df_months = pd.read_csv(monthly_metrics_path)
        low_perf_months = df_months[df_months["TSS"] < 0.10]["Month"].tolist()
        logger.info(f"Dynamically identified low-performance months (TSS < 0.10): {low_perf_months}")
    else:
        low_perf_months = ["2025-12", "2026-01", "2026-03", "2026-05"]
        logger.info(f"Fallback low-performance months: {low_perf_months}")
        
    best_th = float(cache["validation_threshold"])
    y_true_full = cache["test_targets"]
    y_prob_full = cache["test_probs_cal_iso"]
    y_prob_goes_only_full = cache["test_probs_cal_iso_goes_only"]
    timestamps_full = pd.to_datetime(cache["test_timestamps"])
    
    # Align parquet (skip first 360 sequence windows)
    df_aligned = df_test.iloc[360:].copy().reset_index(drop=True)
    assert len(df_aligned) == len(y_true_full), "Alignment length mismatch!"
    
    # Add predictions to aligned dataframe
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
    
    # Create subset DataFrame
    df_subset = df_aligned.iloc[subset_indices].copy().reset_index(drop=True)
    df_subset["uncertainty"] = uncertainty_subset
    
    # 1. Representativeness check
    full_fp_rate = float(np.mean(df_aligned["failure_type"] == "FP"))
    full_fn_rate = float(np.mean(df_aligned["failure_type"] == "FN"))
    sub_fp_rate = float(np.mean(df_subset["failure_type"] == "FP"))
    sub_fn_rate = float(np.mean(df_subset["failure_type"] == "FN"))
    
    full_fp_flux_mean = float(df_aligned[df_aligned["failure_type"] == "FP"]["long_flux"].mean())
    sub_fp_flux_mean = float(df_subset[df_subset["failure_type"] == "FP"]["long_flux"].mean())
    full_fn_flux_mean = float(df_aligned[df_aligned["failure_type"] == "FN"]["long_flux"].mean())
    sub_fn_flux_mean = float(df_subset[df_subset["failure_type"] == "FN"]["long_flux"].mean())
    
    logger.info("=== REPRESENTATIVENESS VERIFICATION ===")
    logger.info(f"Full Test Set FP rate: {full_fp_rate:.4f} | Subset FP rate: {sub_fp_rate:.4f}")
    logger.info(f"Full Test Set FN rate: {full_fn_rate:.4f} | Subset FN rate: {sub_fn_rate:.4f}")
    logger.info(f"Full FP long_flux mean: {full_fp_flux_mean:.2e} | Subset FP long_flux mean: {sub_fp_flux_mean:.2e}")
    logger.info(f"Full FN long_flux mean: {full_fn_flux_mean:.2e} | Subset FN long_flux mean: {sub_fn_flux_mean:.2e}")
    
    # 2. Extract failures in the subset
    df_subset_failures = df_subset[df_subset["is_failure"] == 1].copy().reset_index(drop=True)
    logger.info(f"Extracted {len(df_subset_failures)} failure cases in subset for detailed analysis.")
    
    # 3. Compute boolean flags
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
    
    # 4. Map to emergent categories
    df_subset_failures["category"] = df_subset_failures.apply(get_category_name, axis=1)
    
    # Print co-occurrence combinations
    comb_counts = df_subset_failures["category"].value_counts()
    comb_pcts = df_subset_failures["category"].value_counts(normalize=True) * 100
    
    logger.info("=== EMERGENT FAILURE TAXONOMY ===")
    for cat, cnt in comb_counts.items():
        pct = comb_pcts[cat]
        logger.info(f"Category: {cat:<40} | Count: {cnt:<5} | Pct: {pct:.2f}%")
        
    # Save failure taxonomy JSON
    taxonomy_json = {}
    for cat, cnt in comb_counts.items():
        taxonomy_json[cat] = {
            "count": int(cnt),
            "percentage": float(comb_pcts[cat])
        }
    
    # 5. Compute full descriptive statistics for each category
    # Columns to profile
    profile_cols = [
        "prob_cal", "uncertainty", "long_flux", "minutes_since_last_flare",
        "solexs_rate_ch1", "hel1os_rate_band0"
    ]
    
    stats_records = []
    
    for cat in comb_counts.index:
        cat_df = df_subset_failures[df_subset_failures["category"] == cat]
        
        # Determine successful baseline group for comparison
        # FP categories are compared against True Negatives (TN)
        # FN categories are compared against True Positives (TP)
        is_fp_like = cat_df["failure_type"].iloc[0] == "FP" if len(cat_df) > 0 else True
        
        if is_fp_like:
            baseline_df = df_subset[(df_subset["target_6hr_binary"] == 0) & (df_subset["pred_binary"] == 0)]
            baseline_name = "True_Negatives"
        else:
            baseline_df = df_subset[(df_subset["target_6hr_binary"] == 1) & (df_subset["pred_binary"] == 1)]
            baseline_name = "True_Positives"
            
        for col in profile_cols:
            # Failure stats
            vals = cat_df[col].dropna().values
            # Successful baseline stats
            base_vals = baseline_df[col].dropna().values
            
            f_mean = float(np.mean(vals)) if len(vals) > 0 else 0.0
            f_med = float(np.median(vals)) if len(vals) > 0 else 0.0
            f_std = float(np.std(vals)) if len(vals) > 0 else 0.0
            f_iqr = compute_iqr(vals) if len(vals) > 0 else 0.0
            f_min = float(np.min(vals)) if len(vals) > 0 else 0.0
            f_max = float(np.max(vals)) if len(vals) > 0 else 0.0
            
            b_mean = float(np.mean(base_vals)) if len(base_vals) > 0 else 0.0
            b_med = float(np.median(base_vals)) if len(base_vals) > 0 else 0.0
            
            stats_records.append({
                "Category": cat,
                "Failure_Type": "FP" if is_fp_like else "FN",
                "Feature": col,
                "Count": len(vals),
                "Mean": f_mean,
                "Median": f_med,
                "Std": f_std,
                "IQR": f_iqr,
                "Min": f_min,
                "Max": f_max,
                "Baseline_Group": baseline_name,
                "Baseline_Mean": b_mean,
                "Baseline_Median": b_med,
                "Diff_vs_Baseline_Median": f_med - b_med
            })
            
    df_stats = pd.DataFrame(stats_records)
    
    # 6. Extract representative examples
    # For each category, select up to 3 examples closest to the median calibrated probability
    example_records = []
    
    for cat in comb_counts.index:
        cat_df = df_subset_failures[df_subset_failures["category"] == cat]
        if len(cat_df) == 0:
            continue
        
        median_prob = cat_df["prob_cal"].median()
        # Sort by distance to median prob
        cat_df = cat_df.iloc[(cat_df["prob_cal"] - median_prob).abs().argsort()]
        
        # Take top 3
        examples = cat_df.head(3)
        for _, row in examples.iterrows():
            example_records.append({
                "Category": cat,
                "Timestamp": str(row["timestamp"]),
                "Calibrated_Probability": float(row["prob_cal"]),
                "MC_Dropout_Uncertainty": float(row["uncertainty"]),
                "True_Class": int(row["target_6hr_class"]),
                "GOES_long_flux": float(row["long_flux"]),
                "SoLEXS_rate_ch1": float(row["solexs_rate_ch1"]) if pd.notna(row["solexs_rate_ch1"]) else None,
                "HEL1OS_rate_band0": float(row["hel1os_rate_band0"]) if pd.notna(row["hel1os_rate_band0"]) else None,
                "Failure_Type": str(row["failure_type"])
            })
            
    df_examples = pd.DataFrame(example_records)
    
    # Save deliverables
    os.makedirs("artifacts/sprint17a", exist_ok=True)
    
    with open("artifacts/sprint17a/failure_taxonomy.json", "w") as f:
        json.dump(taxonomy_json, f, indent=2)
        
    df_stats.to_csv("artifacts/sprint17a/failure_statistics.csv", index=False)
    df_examples.to_csv("artifacts/sprint17a/representative_failures.csv", index=False)
    
    logger.info("Sprint 17A failure taxonomy generation: PASS")

if __name__ == "__main__":
    main()
