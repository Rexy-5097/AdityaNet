import numpy as np
import pandas as pd

# Load test data and subset indices
cache = np.load("scratch/sprint16a/cached_predictions.npz")
df_test = pd.read_parquet("artifacts/sprint14c/s2_test.parquet")
subset_indices = cache["subset_indices"]
df_subset = df_test.iloc[360:].iloc[subset_indices].copy()

# Features in question
features = ["variance_15m", "variance_60m"]
for f in features:
    if f in df_subset.columns:
        print(f"{f}: std = {df_subset[f].std():.6e}, min = {df_subset[f].min():.6e}, max = {df_subset[f].max():.6e}")
    else:
        print(f"{f} NOT in columns!")
