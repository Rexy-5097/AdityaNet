import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu

# Load predictions cache and parquet test set
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

subset_indices = cache["subset_indices"]
uncertainty_subset = cache["subset_uncertainty"]

df_subset = df_aligned.iloc[subset_indices].copy().reset_index(drop=True)
df_subset["uncertainty"] = uncertainty_subset

tp_group = df_subset[(df_subset["target_6hr_binary"] == 1) & (df_subset["pred_binary"] == 1)]
fp_group = df_subset[(df_subset["target_6hr_binary"] == 0) & (df_subset["pred_binary"] == 1)]
tn_group = df_subset[(df_subset["target_6hr_binary"] == 0) & (df_subset["pred_binary"] == 0)]
fn_group = df_subset[(df_subset["target_6hr_binary"] == 1) & (df_subset["pred_binary"] == 0)]

print(f"Lengths: TP={len(tp_group)}, FP={len(fp_group)}, TN={len(tn_group)}, FN={len(fn_group)}")

# Check solexs_rate_ch1 TN vs FN
feat = "solexs_rate_ch1"
v1 = tn_group[feat].values
v2 = fn_group[feat].values

u_stat, mw_p = mannwhitneyu(v1, v2, alternative='two-sided')
print(f"Computed U: {u_stat}, p: {mw_p}")

# Load reported effect sizes
df_effects = pd.read_csv("artifacts/sprint18a/effect_sizes.csv")
rep_row = df_effects[(df_effects["Feature"] == feat) & (df_effects["Comparison"] == "TN_vs_FN")]
print("Reported Row:")
print(rep_row)
