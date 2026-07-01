import os
import json
import logging
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, precision_recall_curve, auc, brier_score_loss

MASTER_PARQUET = "/Users/soumyadebtripathy/AdityaNet/artifacts/aditya_l1/master_feature_table.parquet"
FLARES_PARQUET = "/Users/soumyadebtripathy/AdityaNet/artifacts/research/flares_full.parquet"
TEST_PARQUET = "/Users/soumyadebtripathy/AdityaNet/artifacts/research/test.parquet"

def safe_auc(y_true, y_prob):
    if len(np.unique(y_true)) < 2:
        return float("nan")
    try:
        return float(roc_auc_score(y_true, y_prob))
    except Exception:
        return float("nan")

def compute_metrics(y_true, y_prob):
    auc_val = safe_auc(y_true, y_prob)
    try:
        precision, recall, thresholds = precision_recall_curve(y_true, y_prob)
        pr_auc_val = float(auc(recall, precision))
    except Exception:
        pr_auc_val = float("nan")
        
    try:
        brier_val = float(brier_score_loss(y_true, y_prob))
    except Exception:
        brier_val = float("nan")
    
    best_tss = -1.0
    best_thresh = 0.5
    tss_at_05 = 0.0
    
    threshold_grid = np.linspace(0.01, 0.99, 100)
    for th in threshold_grid:
        preds = (y_prob >= th).astype(int)
        tp = np.sum((preds == 1) & (y_true == 1))
        fp = np.sum((preds == 1) & (y_true == 0))
        fn = np.sum((preds == 0) & (y_true == 1))
        tn = np.sum((preds == 0) & (y_true == 0))
        
        tpr = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        tss = tpr - fpr
        
        if tss > best_tss:
            best_tss = tss
            best_thresh = th
        if abs(th - 0.5) < 0.006:
            tss_at_05 = tss
            
    return {
        "auc": auc_val,
        "pr_auc": pr_auc_val,
        "brier": brier_val,
        "tss_at_05": float(tss_at_05),
        "max_tss": float(best_tss),
        "optimal_threshold": float(best_thresh)
    }

def main():
    print("Ingesting master feature table...")
    df_master = pd.read_parquet(MASTER_PARQUET)
    df_master["timestamp"] = pd.to_datetime(df_master["timestamp"])
    print(f"Master feature table shape: {df_master.shape}")
    print(f"Master timestamp range: {df_master['timestamp'].min()} to {df_master['timestamp'].max()}")
    
    channels = [f"solexs_sdd2_spec_counts_ch{i}" for i in range(13, 38)]
    df_channels = df_master[channels].interpolate(method="linear").fillna(0.0)
    
    scaler = StandardScaler()
    X_std = scaler.fit_transform(df_channels.values)
    pca = PCA(n_components=25, random_state=42)
    pca.fit(X_std)
    PC_scores = pca.transform(X_std)
    
    soft_band = [f"solexs_sdd2_spec_counts_ch{i}" for i in range(14, 29)]
    hard_band = [f"solexs_sdd2_spec_counts_ch{i}" for i in range(29, 38)]
    
    soft_band_mean = df_channels[soft_band].mean(axis=1).values
    hard_band_mean = df_channels[hard_band].mean(axis=1).values
    hard_soft_ratio = hard_band_mean / (soft_band_mean + 1e-9)
    pc1_proj = PC_scores[:, 0]
    pc2_proj = PC_scores[:, 1]
    
    df_compressed = pd.DataFrame({
        "timestamp": df_master["timestamp"],
        "soft_band_mean": soft_band_mean,
        "hard_band_mean": hard_band_mean,
        "hard_soft_ratio": hard_soft_ratio,
        "pc1_projection": pc1_proj,
        "pc2_projection": pc2_proj
    })
    
    print("Loading flares...")
    df_flares = pd.read_parquet(FLARES_PARQUET, columns=["start_time", "flare_class"])
    c_flares = df_flares[df_flares["flare_class"].str[0].isin(["C", "M", "X"])].copy()
    c_flare_times = pd.to_datetime(c_flares["start_time"]).dt.floor("Min")
    
    time_grid = df_master["timestamp"]
    c_indicator = pd.Series(0, index=time_grid.index)
    c_indicator.loc[time_grid[time_grid.isin(c_flare_times)].index] = 1
    
    target_6hr_binary_c = (
        c_indicator.shift(-1)
        .iloc[::-1]
        .rolling(window=360, min_periods=1)
        .max()
        .iloc[::-1]
        .fillna(0)
        .astype(int)
    )
    
    print("Loading history features from test.parquet...")
    history_cols = ["minutes_since_last_flare", "mean_60m", "mean_15m", "long_flux", "peak_30m"]
    min_ts = df_master["timestamp"].min()
    max_ts = df_master["timestamp"].max()
    
    df_features = pd.read_parquet(TEST_PARQUET, columns=["timestamp"] + history_cols)
    df_features["timestamp"] = pd.to_datetime(df_features["timestamp"])
    df_features = df_features[(df_features["timestamp"] >= min_ts) & (df_features["timestamp"] <= max_ts)]
    
    df_combined = pd.merge(df_compressed, df_features, on="timestamp", how="inner")
    df_combined["target"] = target_6hr_binary_c.values
    
    df_combined["day"] = df_combined["timestamp"].dt.date.astype(str)
    df_combined["feat_timestamp"] = df_combined["timestamp"] - pd.Timedelta(minutes=60)
    df_combined["feat_day"] = df_combined["feat_timestamp"].dt.date.astype(str)
    
    scaler_hist = StandardScaler()
    df_combined[history_cols] = scaler_hist.fit_transform(df_combined[history_cols].fillna(0.0).values)
    
    print(f"Combined data shape: {df_combined.shape}")
    
    folds_config = {
        "Fold A": {
            "train": ["2026-06-10", "2026-06-11", "2026-06-12"],
            "test": ["2026-06-13"]
        },
        "Fold B": {
            "train": ["2026-06-10", "2026-06-11", "2026-06-13"],
            "test": ["2026-06-12"]
        },
        "Fold C": {
            "train": ["2026-06-10", "2026-06-12", "2026-06-13"],
            "test": ["2026-06-11"]
        },
        "Fold D": {
            "train": ["2026-06-11", "2026-06-12", "2026-06-13"],
            "test": ["2026-06-10"]
        }
    }
    
    for f_name, f_cfg in folds_config.items():
        train_days = f_cfg["train"]
        test_days = f_cfg["test"]
        
        train_mask = df_combined["day"].isin(train_days) & df_combined["feat_day"].isin(train_days)
        test_mask = df_combined["day"].isin(test_days) & df_combined["feat_day"].isin(test_days)
        
        df_train = df_combined[train_mask]
        df_test = df_combined[test_mask]
        
        print(f"\n{f_name}:")
        print(f"  Train days: {train_days}")
        print(f"  Test days: {test_days}")
        print(f"  Train rows: {len(df_train)}")
        print(f"  Test rows: {len(df_test)}")
        if len(df_test) > 0:
            target_unique = np.unique(df_test["target"].values)
            print(f"  Test target unique classes: {target_unique}")

if __name__ == "__main__":
    main()
