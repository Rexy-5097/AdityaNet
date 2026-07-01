import os
import json
import logging
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Paths
MASTER_PARQUET = "artifacts/aditya_l1/master_feature_table.parquet"
FLARES_PARQUET = "artifacts/research/flares_full.parquet"
FEATURE_PARQUET = "artifacts/feature_dataset.parquet"

# Reference Audit Artifacts
REF_LINEAGE = "artifacts/aditya_l1/target_lineage_audit.json"
REF_SHIFT = "artifacts/aditya_l1/shift_direction_audit.json"
REF_OVERLAP = "artifacts/aditya_l1/window_overlap_audit.json"
REF_CAUSAL = "artifacts/aditya_l1/causal_ordering_audit.json"
REF_LEADLAG = "artifacts/aditya_l1/lead_lag_reconstruction.json"

TOLERANCE = 1e-6

def main():
    logger.info("Starting T-60 Hypothesis Independent Alignment Verification of Sprint 10G-OB")
    
    # 1. Ingest Data
    df_master = pd.read_parquet(MASTER_PARQUET)
    df_master["timestamp"] = pd.to_datetime(df_master["timestamp"])
    
    # 2. Recompute Compressed Features
    channels = [f"solexs_sdd2_spec_counts_ch{i}" for i in range(13, 38)]
    df_channels = df_master[channels].interpolate(method="linear").fillna(0.0)
    scaler_pca = StandardScaler()
    X_std = scaler_pca.fit_transform(df_channels.values)
    pca = PCA(n_components=25, random_state=42)
    PC_scores = pca.fit_transform(X_std)
    
    soft_band = [f"solexs_sdd2_spec_counts_ch{i}" for i in range(14, 29)]
    hard_band = [f"solexs_sdd2_spec_counts_ch{i}" for i in range(29, 38)]
    soft_band_mean = df_channels[soft_band].mean(axis=1).values
    hard_band_mean = df_channels[hard_band].mean(axis=1).values
    hard_soft_ratio = hard_band_mean / (soft_band_mean + 1e-9)
    
    df_compressed = pd.DataFrame({
        "timestamp": df_master["timestamp"],
        "soft_band_mean": soft_band_mean,
        "hard_band_mean": hard_band_mean,
        "hard_soft_ratio": hard_soft_ratio,
        "pc1_projection": PC_scores[:, 0],
        "pc2_projection": PC_scores[:, 1]
    })

    # 3. Target Lineage
    df_flares = pd.read_parquet(FLARES_PARQUET, columns=["start_time", "flare_class"])
    c_flares = df_flares[df_flares["flare_class"].str[0].isin(["C", "M", "X"])].copy()
    c_flare_times = pd.to_datetime(c_flares["start_time"]).dt.floor("Min").unique()
    c_indicator = pd.Series(0, index=df_master.index)
    c_indicator.loc[df_master[df_master["timestamp"].isin(c_flare_times)].index] = 1
    
    target_6hr = (
        c_indicator
        .iloc[::-1]
        .rolling(window=361, min_periods=1)
        .max()
        .iloc[::-1]
        .fillna(0)
        .astype(int)
    )
    df_compressed["target"] = target_6hr.values
    
    # 4. History Features
    history_cols = ["minutes_since_last_flare", "mean_60m", "mean_15m", "long_flux", "peak_30m"]
    df_features_hist = pd.read_parquet(FEATURE_PARQUET, columns=["timestamp"] + history_cols)
    df_features_hist["timestamp"] = pd.to_datetime(df_features_hist["timestamp"])
    
    df_merged = pd.merge(df_compressed, df_features_hist, on="timestamp", how="inner")
    
    # Lead-Lag Reconstruction
    lead_lag_discrepancies = []
    with open(REF_LEADLAG, "r") as f:
        ref_leadlag = json.load(f)
        
    for feat in ["hard_soft_ratio", "soft_band_mean", "pc1_projection", "pc2_projection"]:
        for offset_key, offset_data in ref_leadlag[feat].items():
            h = offset_data["offset"]
            
            # Hypothesis: 
            # Baseline uses History @ T-60.
            # Augmented uses History @ T-60 AND Feature @ (T-60 + h).
            # Target is @ T.
            # Mask must account for History @ T-60 and Feature @ T-60+h.
            
            # Since h is offset from 0m, and 0m matches T-60, 
            # then offset h means Feature @ T-60+h.
            
            hist_lagged = df_merged[history_cols].shift(60)
            feat_shifted = df_merged[feat].shift(60 - h)
            
            mask = hist_lagged.notna().all(axis=1) & feat_shifted.notna()
            
            X_feat = feat_shifted[mask].values
            X_hist_raw = hist_lagged[mask].values
            Y = df_merged.loc[mask, "target"].values
            
            if len(np.unique(Y)) < 2:
                continue
                
            X_hist = StandardScaler().fit_transform(X_hist_raw)
            X_joint = StandardScaler().fit_transform(np.column_stack((X_feat, X_hist_raw)))
            
            lr_base = LogisticRegression(max_iter=1000, random_state=42).fit(X_hist, Y)
            auc_base = roc_auc_score(Y, lr_base.predict_proba(X_hist)[:, 1])
            
            lr_aug = LogisticRegression(max_iter=1000, random_state=42).fit(X_joint, Y)
            auc_aug = roc_auc_score(Y, lr_aug.predict_proba(X_joint)[:, 1])
            
            if abs(auc_base - offset_data["baseline"]["auc"]) > TOLERANCE:
                lead_lag_discrepancies.append(f"LEAD-LAG BASE AUC DISCREPANCY: {feat}.{offset_key} | Audit={offset_data['baseline']['auc']} | Recomputed={auc_base}")
            if abs(auc_aug - offset_data["augmented"]["auc"]) > TOLERANCE:
                lead_lag_discrepancies.append(f"LEAD-LAG AUG AUC DISCREPANCY: {feat}.{offset_key} | Audit={offset_data['augmented']['auc']} | Recomputed={auc_aug}")

    # Report
    print(f"Total Discrepancies: {len(lead_lag_discrepancies)}")
    for d in lead_lag_discrepancies:
        print(d)
        
    if len(lead_lag_discrepancies) == 0:
        print("VERDICT: PASS")
    else:
        print("VERDICT: FAIL")

if __name__ == "__main__":
    main()
