import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

import numpy as np
import pandas as pd
import time
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from joblib import Parallel, delayed

# Load predictions cache
cache = np.load("/Users/soumyadebtripathy/AdityaNet/scratch/sprint16a/cached_predictions.npz")
subset_indices = cache["subset_indices"]
y_prob = cache["test_probs_cal_iso"]
y_prob_goes_only = cache["test_probs_cal_iso_goes_only"]
y_true = cache["test_targets"]
best_th = float(cache["validation_threshold"])

# Load test parquet
df_test = pd.read_parquet("/Users/soumyadebtripathy/AdityaNet/artifacts/sprint14c/s2_test.parquet")
df_aligned = df_test.iloc[360:].copy().reset_index(drop=True)
df_subset = df_aligned.iloc[subset_indices].copy().reset_index(drop=True)

df_subset["prob_cal"] = y_prob[subset_indices]
df_subset["prob_goes_only"] = y_prob_goes_only[subset_indices]
df_subset["uncertainty"] = cache["subset_uncertainty"]
df_subset["pred_binary"] = (df_subset["prob_cal"] >= best_th).astype(int)
df_subset["is_failure"] = (df_subset["pred_binary"] != df_subset["target_6hr_binary"]).astype(int)

df_subset["failure_type"] = "NONE"
df_subset.loc[(df_subset["target_6hr_binary"] == 0) & (df_subset["pred_binary"] == 1), "failure_type"] = "FP"
df_subset.loc[(df_subset["target_6hr_binary"] == 1) & (df_subset["pred_binary"] == 0), "failure_type"] = "FN"

df_subset["month"] = pd.to_datetime(df_subset["timestamp"]).dt.to_period("M").astype(str)

low_perf_months = ["2025-12", "2026-01", "2026-03", "2026-05"]

# Compute taxonomy flags
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

# Identify features for Subset A (Model 1)
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

features = physical_continuous + physical_binary

subset_a = df_subset[df_subset["target_6hr_binary"] == 0]
X_a = subset_a[features].copy().values
y_a = (subset_a["pred_binary"] == 1).astype(int).values

scaler = StandardScaler()
X_a_scaled = scaler.fit_transform(X_a)

def fit_one(X, y):
    indices = np.random.choice(len(X), size=len(X), replace=True)
    X_boot = X[indices]
    y_boot = y[indices]
    lr = LogisticRegression(C=1.0, tol=1e-1, max_iter=200, solver='liblinear')
    lr.fit(X_boot, y_boot)
    return lr.coef_[0]

print("Benchmarking 500 iterations with OMP_NUM_THREADS=1 and n_jobs=6...")
start = time.time()
Parallel(n_jobs=6)(delayed(fit_one)(X_a_scaled, y_a) for _ in range(500))
print(f"Finished in {time.time() - start:.4f} seconds.")
