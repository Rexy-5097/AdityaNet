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

goes_cont_features = [
    "short_flux", "long_flux", "log_long_flux", "mean_15m", "variance_15m",
    "mean_60m", "variance_60m", "peak_30m", "peak_60m", "flux_gradient_5m",
    "flux_gradient_15m", "flux_acceleration_5m", "flux_acceleration_15m",
    "minutes_since_last_flare"
]
solexs_features = [f"solexs_rate_ch{i}" for i in range(1, 10)] + [f"solexs_counts_ch{i}" for i in range(1, 10)]
hel1os_features = ["hel1os_rate_band0", "hel1os_rate_band1", "hel1os_counts_band0", "hel1os_counts_band1"]
prediction_continuous = ["prob_cal", "uncertainty"]

continuous_features_list = goes_cont_features + solexs_features + hel1os_features + prediction_continuous
continuous_features_list = [f for f in continuous_features_list if f in df_subset.columns]

comparisons = {
    "TP_vs_FP": (tp_group, fp_group),
    "TN_vs_FN": (tn_group, fn_group)
}

df_effects_rep = pd.read_csv("artifacts/sprint18a/effect_sizes.csv")

diffs = []
for idx, row in df_effects_rep.iterrows():
    feat = row["Feature"]
    comp = row["Comparison"]
    grp1, grp2 = comparisons[comp]
    
    n1 = len(grp1)
    n2 = len(grp2)
    v1 = grp1[feat].values
    v2 = grp2[feat].values
    
    u_stat, mw_p = mannwhitneyu(v1, v2, alternative='two-sided')
    diff_u = abs(row["Mann_Whitney_U"] - u_stat)
    diff_p = abs(row["p_value"] - mw_p)
    
    mu1, mu2 = np.mean(v1), np.mean(v2)
    var1, var2 = np.var(v1, ddof=1), np.var(v2, ddof=1)
    s_pooled = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
    cohen_d_act = float((mu1 - mu2) / s_pooled) if s_pooled > 1e-15 else 0.0
    diff_d = abs(row["Cohens_d"] - cohen_d_act)
    
    if diff_u > 1e-6 or diff_p > 1e-6 or diff_d > 1e-6:
        diffs.append((feat, comp, row["Mann_Whitney_U"], u_stat, diff_u, row["p_value"], mw_p, diff_p, row["Cohens_d"], cohen_d_act, diff_d))

print(f"Total rows with mismatches: {len(diffs)}")
for d in sorted(diffs, key=lambda x: x[4], reverse=True)[:20]:
    print(f"{d[0]} ({d[1]}): U_diff={d[4]:.1f} (Rep={d[2]}, Act={d[3]}), p_diff={d[7]:.2e}, d_diff={d[10]:.2e}")
