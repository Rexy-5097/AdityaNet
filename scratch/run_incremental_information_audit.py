import os
import json
import logging
import numpy as np
import pandas as pd
import scipy.stats
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.feature_selection import mutual_info_classif
from sklearn.metrics import roc_auc_score

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Paths
MASTER_PARQUET = "artifacts/aditya_l1/master_feature_table.parquet"
FLARES_PARQUET = "artifacts/research/flares_full.parquet"
FEATURE_PARQUET = "artifacts/feature_dataset.parquet"
OUTPUT_DIR = "artifacts/aditya_l1"

def get_memory_usage_mb() -> float:
    try:
        import resource
        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
    except Exception:
        return 0.0

def main():
    logger.info("Initializing Sprint 10G-N: Incremental Information Audit")
    start_mem = get_memory_usage_mb()
    
    # 1. Ingest Data
    if not os.path.exists(MASTER_PARQUET):
        raise FileNotFoundError(f"Master feature table not found: {MASTER_PARQUET}")
    df_master = pd.read_parquet(MASTER_PARQUET)
    logger.info(f"Loaded master feature table: {df_master.shape[0]} rows, {df_master.shape[1]} columns")
    
    channels = [f"solexs_sdd2_spec_counts_ch{i}" for i in range(13, 38)]
    df_channels = df_master[channels].interpolate(method="linear").fillna(0.0)
    
    # Standardize channels and compute PCA
    scaler = StandardScaler()
    X_std = scaler.fit_transform(df_channels.values)
    pca = PCA(n_components=25, random_state=42)
    pca.fit(X_std)
    PC_scores = pca.transform(X_std)
    
    # Construct compressed features
    soft_band = [f"solexs_sdd2_spec_counts_ch{i}" for i in range(14, 29)] # ch14-28 inclusive
    hard_band = [f"solexs_sdd2_spec_counts_ch{i}" for i in range(29, 38)] # ch29-37 inclusive
    
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
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    df_compressed.to_parquet(os.path.join(OUTPUT_DIR, "compressed_solexs_features.parquet"))
    logger.info("Saved compressed SoLEXS features to compressed_solexs_features.parquet")
    
    # 2. Ingest Target
    if not os.path.exists(FLARES_PARQUET):
        raise FileNotFoundError(f"Flares full parquet not found: {FLARES_PARQUET}")
    df_flares = pd.read_parquet(FLARES_PARQUET, columns=["start_time", "flare_class"])
    c_flares = df_flares[df_flares["flare_class"].str[0].isin(["C", "M", "X"])].copy()
    c_flare_times = pd.to_datetime(c_flares["start_time"]).dt.floor("Min")
    
    time_grid = pd.to_datetime(df_master["timestamp"])
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
    
    # 3. Load GOES history features
    if not os.path.exists(FEATURE_PARQUET):
        raise FileNotFoundError(f"Feature dataset not found: {FEATURE_PARQUET}")
        
    history_cols = [
        "minutes_since_last_flare",
        "mean_60m",
        "mean_15m",
        "long_flux",
        "peak_30m"
    ]
    df_features = pd.read_parquet(FEATURE_PARQUET, columns=["timestamp"] + history_cols)
    df_features["timestamp"] = pd.to_datetime(df_features["timestamp"])
    
    # Join features
    df_combined = pd.merge(df_compressed, df_features, on="timestamp", how="inner")
    df_combined["target"] = target_6hr_binary_c.values
    logger.info(f"Aligned dataset size: {df_combined.shape[0]} rows")
    
    # Standardize baseline columns
    scaler_hist = StandardScaler()
    df_combined[history_cols] = scaler_hist.fit_transform(df_combined[history_cols].fillna(0.0).values)
    
    # 4. Incremental Information & Conditional MI Analysis
    horizons = [5, 15, 30, 60, 180, 360]
    comp_features = ["soft_band_mean", "hard_band_mean", "hard_soft_ratio", "pc1_projection", "pc2_projection"]
    
    audit_results = {}
    
    for feat in comp_features:
        logger.info(f"Auditing compressed feature: {feat}...")
        audit_results[feat] = {}
        
        for h in horizons:
            # Shift features
            feat_shifted = df_combined[feat].shift(h)
            hist_shifted = df_combined[history_cols].shift(h)
            
            # Mask NaNs
            mask = feat_shifted.notna() & hist_shifted.notna().all(axis=1)
            X_feat = feat_shifted[mask].values
            X_hist = hist_shifted[mask].values
            Y = df_combined.loc[mask, "target"].values
            
            if len(Y) < 100:
                logger.warning(f"Not enough valid rows for feature {feat} at horizon {h}m")
                continue
                
            # Unconditional Metrics
            pearson_val, _ = scipy.stats.pearsonr(X_feat, Y)
            spearman_val, _ = scipy.stats.spearmanr(X_feat, Y)
            mi_uncond = float(mutual_info_classif(X_feat.reshape(-1, 1), Y, random_state=42)[0])
            
            # Conditional MI using I(X; Y | Z) = I(X, Z; Y) - I(Z; Y)
            X_joint = np.column_stack((X_feat, X_hist))
            mi_joint = float(mutual_info_classif(X_joint, Y, random_state=42)[0])
            mi_base = float(mutual_info_classif(X_hist, Y, random_state=42)[0])
            cmi = max(0.0, mi_joint - mi_base)
            
            # Logistic Regression ROC-AUC increment
            model_base = LogisticRegression(max_iter=1000, random_state=42)
            model_base.fit(X_hist, Y)
            auc_base = float(roc_auc_score(Y, model_base.predict_proba(X_hist)[:, 1]))
            
            model_aug = LogisticRegression(max_iter=1000, random_state=42)
            model_aug.fit(X_joint, Y)
            auc_aug = float(roc_auc_score(Y, model_aug.predict_proba(X_joint)[:, 1]))
            delta_auc = auc_aug - auc_base
            
            # 5. Permutation Significance (100 permutations)
            np.random.seed(42)
            shuffled_pearsons = []
            shuffled_cmis = []
            shuffled_delta_aucs = []
            
            for perm in range(100):
                Y_shuffled = np.random.permutation(Y)
                
                # Shuffled Pearson
                sh_p, _ = scipy.stats.pearsonr(X_feat, Y_shuffled)
                shuffled_pearsons.append(abs(sh_p))
                
                # Shuffled CMI
                sh_mi_joint = float(mutual_info_classif(X_joint, Y_shuffled, random_state=42)[0])
                sh_mi_base = float(mutual_info_classif(X_hist, Y_shuffled, random_state=42)[0])
                shuffled_cmis.append(max(0.0, sh_mi_joint - sh_mi_base))
                
                # Shuffled Delta-AUC
                sh_model_base = LogisticRegression(max_iter=1000, random_state=42)
                sh_model_base.fit(X_hist, Y_shuffled)
                sh_auc_base = float(roc_auc_score(Y_shuffled, sh_model_base.predict_proba(X_hist)[:, 1]))
                
                sh_model_aug = LogisticRegression(max_iter=1000, random_state=42)
                sh_model_aug.fit(X_joint, Y_shuffled)
                sh_auc_aug = float(roc_auc_score(Y_shuffled, sh_model_aug.predict_proba(X_joint)[:, 1]))
                shuffled_delta_aucs.append(sh_auc_aug - sh_auc_base)
                
            # Empirical p-values
            p_pearson = float((np.sum(np.array(shuffled_pearsons) >= abs(pearson_val)) + 1) / 101.0)
            p_cmi = float((np.sum(np.array(shuffled_cmis) >= cmi) + 1) / 101.0)
            p_delta_auc = float((np.sum(np.array(shuffled_delta_aucs) >= delta_auc) + 1) / 101.0)
            
            audit_results[feat][f"horizon_{h}m"] = {
                "pearson": float(pearson_val),
                "spearman": float(spearman_val),
                "mutual_information": mi_uncond,
                "conditional_mutual_information": cmi,
                "baseline_auc": auc_base,
                "augmented_auc": auc_aug,
                "delta_auc": delta_auc,
                "p_value_pearson": p_pearson,
                "p_value_cmi": p_cmi,
                "p_value_delta_auc": p_delta_auc
            }
            logger.info(f"Horizon {h}m - CMI: {cmi:.4f} (p={p_cmi:.3f}), Delta-AUC: {delta_auc:.4f} (p={p_delta_auc:.3f})")
            
    # 6. Incremental Utility Ranking & Classification
    ranking_data = []
    for feat in comp_features:
        # Find peak lead horizon by Conditional MI
        peak_h = None
        peak_cmi = -1.0
        peak_metrics = {}
        
        for h in horizons:
            h_name = f"horizon_{h}m"
            if h_name in audit_results[feat]:
                metrics = audit_results[feat][h_name]
                if metrics["conditional_mutual_information"] > peak_cmi:
                    peak_cmi = metrics["conditional_mutual_information"]
                    peak_h = h
                    peak_metrics = metrics
                    
        # Classification
        p_cmi = peak_metrics.get("p_value_cmi", 1.0)
        p_delta_auc = peak_metrics.get("p_value_delta_auc", 1.0)
        cmi_val = peak_metrics.get("conditional_mutual_information", 0.0)
        
        if cmi_val > 0.01 and p_cmi < 0.01 and p_delta_auc < 0.01:
            cls = "Class A"
        elif cmi_val > 0.0 and p_cmi < 0.05 and p_delta_auc < 0.05:
            cls = "Class B"
        else:
            cls = "Class C"
            
        ranking_data.append({
            "feature": feat,
            "peak_lead_m": peak_h,
            "pearson": peak_metrics.get("pearson", 0.0),
            "mutual_information": peak_metrics.get("mutual_information", 0.0),
            "conditional_mutual_information": cmi_val,
            "delta_auc": peak_metrics.get("delta_auc", 0.0),
            "p_value_cmi": p_cmi,
            "p_value_delta_auc": p_delta_auc,
            "classification": cls
        })
        
    # Sort ranking
    ranking_data = sorted(ranking_data, key=lambda x: x["conditional_mutual_information"], reverse=True)
    
    end_mem = get_memory_usage_mb()
    
    # Save JSON results
    output_json = {
        "metadata": {
            "sample_count": df_combined.shape[0],
            "history_baseline_features": history_cols,
            "runtime_seconds": 0.0,
            "peak_memory_mb": end_mem - start_mem
        },
        "feature_audit_detail": audit_results,
        "incremental_utility_ranking": ranking_data
    }
    
    # Save json file
    json_path = os.path.join(OUTPUT_DIR, "incremental_information_audit.json")
    with open(json_path, "w") as fh:
        json.dump(output_json, fh, indent=2)
    logger.info("Saved incremental information audit JSON to incremental_information_audit.json")
    
if __name__ == "__main__":
    import time
    t0 = time.time()
    main()
    t1 = time.time()
    # Read output json and inject real runtime
    json_path = os.path.join(OUTPUT_DIR, "incremental_information_audit.json")
    if os.path.exists(json_path):
        with open(json_path, "r") as fh:
            data = json.load(fh)
        data["metadata"]["runtime_seconds"] = t1 - t0
        with open(json_path, "w") as fh:
            json.dump(data, fh, indent=2)
    logger.info(f"Done. Completed in {t1 - t0:.2f} seconds.")
