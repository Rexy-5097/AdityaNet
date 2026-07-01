import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

# Setup datasets like verify_sprint18a.py
cache = np.load("scratch/sprint16a/cached_predictions.npz")
df_test = pd.read_parquet("artifacts/sprint14c/s2_test.parquet")

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

subset_indices = cache["subset_indices"]
uncertainty_subset = cache["subset_uncertainty"]

df_subset = df_aligned.iloc[subset_indices].copy().reset_index(drop=True)
df_subset["uncertainty"] = uncertainty_subset

monthly_metrics_path = "artifacts/sprint16a/monthly_metrics.csv"
if pd.io.common.file_exists(monthly_metrics_path):
    df_months = pd.read_csv(monthly_metrics_path)
    low_perf_months = df_months[df_months["TSS"] < 0.10]["Month"].tolist()
else:
    low_perf_months = ["2025-12", "2026-01", "2026-03", "2026-05"]

# Flag definitions
df_subset["month"] = pd.to_datetime(df_subset["timestamp"]).dt.to_period("M").astype(str)
df_subset["is_missing_sensor"] = ((df_subset["mask_solexs"] == 0) | (df_subset["mask_hel1os"] == 0)).astype(int)
df_subset["is_transition"] = (df_subset["minutes_since_last_flare"] < 30).astype(int)
df_subset["is_label_ambiguity"] = (np.abs(df_subset["prob_cal"] - best_th) < 0.02).astype(int)
df_subset["is_high_confidence"] = (df_subset["prob_cal"] >= 0.70).astype(int)
df_subset["is_high_uncertainty"] = (df_subset["uncertainty"] > 0.0035).astype(int)
df_subset["is_sensor_disagreement"] = (np.abs(df_subset["prob_cal"] - df_subset["prob_goes_only"]) > 0.20).astype(int)
df_subset["is_quiet_background"] = ((df_subset["failure_type"] == "FP") & (df_subset["long_flux"] < 1.5e-6)).astype(int)
df_subset["is_weak_flare"] = ((df_subset["failure_type"] == "FN") & (df_subset["target_6hr_class"] == 1)).astype(int)
df_subset["is_background_flux_drift"] = (df_subset["mean_60m"] > 5e-6).astype(int)
df_subset["is_temporal_drift"] = df_subset["month"].isin(low_perf_months).astype(int)

goes_cont_features = [
    "short_flux", "long_flux", "log_long_flux", "mean_15m", "variance_15m",
    "mean_60m", "variance_60m", "peak_30m", "peak_60m", "flux_gradient_5m",
    "flux_gradient_15m", "flux_acceleration_5m", "flux_acceleration_15m",
    "minutes_since_last_flare"
]
solexs_features = [f"solexs_rate_ch{i}" for i in range(1, 10)] + [f"solexs_counts_ch{i}" for i in range(1, 10)]
hel1os_features = ["hel1os_rate_band0", "hel1os_rate_band1", "hel1os_counts_band0", "hel1os_counts_band1"]

physical_continuous = goes_cont_features + solexs_features + hel1os_features
physical_binary = ["mask_solexs", "mask_hel1os", "quality_flag"]
prediction_continuous = ["prob_cal", "uncertainty"]
taxonomy_binary = [
    "is_missing_sensor", "is_transition", "is_label_ambiguity", "is_high_confidence",
    "is_high_uncertainty", "is_sensor_disagreement", "is_quiet_background",
    "is_weak_flare", "is_background_flux_drift", "is_temporal_drift"
]

all_predictors = physical_continuous + prediction_continuous + physical_binary + taxonomy_binary
valid_predictors = [f for f in all_predictors if df_subset[f].std() > 1e-9]

print(f"Number of valid predictors: {len(valid_predictors)}")
print(f"variance_15m in valid_predictors: {'variance_15m' in valid_predictors}")
print(f"variance_60m in valid_predictors: {'variance_60m' in valid_predictors}")

# Load reported VIFs
df_vif_rep = pd.read_csv("artifacts/sprint18a/variance_inflation.csv")
rep_vifs = dict(zip(df_vif_rep["Feature"], df_vif_rep["VIF"]))

X_full = df_subset[valid_predictors].copy()

# Compute VIFs
diffs = []
for target_f in valid_predictors:
    other_fs = [f for f in valid_predictors if f != target_f]
    X_other = X_full[other_fs].values
    y_target = X_full[target_f].values
    
    reg = LinearRegression()
    reg.fit(X_other, y_target)
    r2 = reg.score(X_other, y_target)
    vif_act = 1.0 / (1.0 - r2) if 1.0 - r2 >= 1e-14 else float('inf')
    
    vif_rep = rep_vifs.get(target_f, None)
    if vif_rep is not None:
        diff = abs(vif_rep - vif_act)
        if diff > 1e-6:
            diffs.append((target_f, vif_rep, vif_act, diff))
            
print("\nMismatches found:")
for name, rep, act, diff in sorted(diffs, key=lambda x: x[3], reverse=True):
    print(f"{name}: Reported={rep:.6f}, Actual={act:.6f}, Diff={diff:.6e}")
