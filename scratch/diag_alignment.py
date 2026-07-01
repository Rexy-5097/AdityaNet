import os
import json
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

# Paths
MASTER_PARQUET = "artifacts/aditya_l1/master_feature_table.parquet"
FLARES_PARQUET = "artifacts/research/flares_full.parquet"
FEATURE_PARQUET = "artifacts/feature_dataset.parquet"

def main():
    df_master = pd.read_parquet(MASTER_PARQUET)
    df_master["timestamp"] = pd.to_datetime(df_master["timestamp"])
    
    df_flares = pd.read_parquet(FLARES_PARQUET, columns=["start_time", "flare_class"])
    c_flares = df_flares[df_flares["flare_class"].str[0].isin(["C", "M", "X"])].copy()
    c_flare_times = pd.to_datetime(c_flares["start_time"]).dt.floor("Min").unique()
    c_indicator = pd.Series(0, index=df_master.index)
    c_indicator.loc[df_master[df_master["timestamp"].isin(c_flare_times)].index] = 1
    
    # 10G-OA Target
    target_6hr = (
        c_indicator.shift(-1)
        .iloc[::-1]
        .rolling(window=360, min_periods=1)
        .max()
        .iloc[::-1]
        .fillna(0)
        .astype(int)
    )
    
    history_cols = ["minutes_since_last_flare", "mean_60m", "mean_15m", "long_flux", "peak_30m"]
    df_features_hist = pd.read_parquet(FEATURE_PARQUET, columns=["timestamp"] + history_cols)
    df_features_hist["timestamp"] = pd.to_datetime(df_features_hist["timestamp"])
    
    df_merged = pd.merge(df_master[["timestamp"]], df_features_hist, on="timestamp", how="inner")
    df_merged["target"] = target_6hr.values
    
    hist_lagged = df_merged[history_cols].shift(60)
    history_not_nan = hist_lagged.notna().all(axis=1)
    
    for h in [0]:
        mask = history_not_nan
        X_hist_raw = hist_lagged[mask].values
        Y = df_merged.loc[mask, "target"].values
        X_hist = StandardScaler().fit_transform(X_hist_raw)
        lr = LogisticRegression(max_iter=1000, random_state=42).fit(X_hist, Y)
        auc = roc_auc_score(Y, lr.predict_proba(X_hist)[:, 1])
        print(f"h={h}m (10G-OA target): Base AUC = {auc}")

if __name__ == "__main__":
    main()
