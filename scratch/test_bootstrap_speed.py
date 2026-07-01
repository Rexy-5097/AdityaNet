import time
import numpy as np
import pandas as pd
from verify_sprint18a import run_parallel_bootstrap

# Setup datasets
cache = np.load("scratch/sprint16a/cached_predictions.npz")
df_test = pd.read_parquet("artifacts/sprint14c/s2_test.parquet")
best_th = float(cache["validation_threshold"])

df_aligned = df_test.iloc[360:].copy().reset_index(drop=True)
df_aligned["prob_cal"] = cache["test_probs_cal_iso"]
df_aligned["pred_binary"] = (df_aligned["prob_cal"] >= best_th).astype(int)

subset_indices = cache["subset_indices"]
df_subset = df_aligned.iloc[subset_indices].copy().reset_index(drop=True)
df_subset["uncertainty"] = cache["subset_uncertainty"]

subset_b = df_subset[df_subset["target_6hr_binary"] == 1].copy().reset_index(drop=True)
y_b = (subset_b["pred_binary"] == 0).astype(int).values

# Let's use a small features list
features = ["short_flux", "long_flux", "log_long_flux"]
X = subset_b[features].values

# Run a quick test of 100 iterations
start = time.time()
df_boot = run_parallel_bootstrap(X, y_b, features, "Model_1_Physical", "Model_B", n_iterations=100, n_jobs=6)
end = time.time()
print(f"Time for 100 iterations: {end - start:.2f} seconds")
