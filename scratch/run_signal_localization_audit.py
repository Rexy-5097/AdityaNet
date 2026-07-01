import os
import json
import logging
import time
import numpy as np
import pandas as pd
import scipy.stats
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, precision_recall_curve, auc, brier_score_loss

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Paths
MASTER_PARQUET = "artifacts/aditya_l1/master_feature_table.parquet"
FLARES_PARQUET = "artifacts/research/flares_full.parquet"
TEST_PARQUET = "artifacts/research/test.parquet"
OUTPUT_DIR = "artifacts/aditya_l1"
CHECKPOINT_DIR = os.path.join(OUTPUT_DIR, "checkpoints")

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
    
    # Sweep thresholds to find Max TSS
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

# Define contiguous bands
bands_dict = {
    "band_A": [f"solexs_sdd2_spec_counts_ch{i}" for i in range(13, 19)],
    "band_B": [f"solexs_sdd2_spec_counts_ch{i}" for i in range(19, 25)],
    "band_C": [f"solexs_sdd2_spec_counts_ch{i}" for i in range(25, 31)],
    "band_D": [f"solexs_sdd2_spec_counts_ch{i}" for i in range(31, 38)]
}

soft_band = [f"solexs_sdd2_spec_counts_ch{i}" for i in range(14, 29)]
hard_band = [f"solexs_sdd2_spec_counts_ch{i}" for i in range(29, 38)]
history_cols = ["minutes_since_last_flare", "mean_60m", "mean_15m", "long_flux", "peak_30m"]

def main():
    logger.info("Initializing Sprint 10G-OD: Signal Localization Audit")
    t0_global = time.time()
    os.makedirs(CHECKPOINT_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Ingest master feature table
    logger.info("Ingesting master feature table...")
    df_master = pd.read_parquet(MASTER_PARQUET)
    df_master["timestamp"] = pd.to_datetime(df_master["timestamp"])
    
    channels = [f"solexs_sdd2_spec_counts_ch{i}" for i in range(13, 38)]
    df_channels = df_master[channels].interpolate(method="linear").fillna(0.0)
    
    # Compute PCA Projections
    scaler = StandardScaler()
    X_std = scaler.fit_transform(df_channels.values)
    pca = PCA(n_components=25, random_state=42)
    pca.fit(X_std)
    PC_scores = pca.transform(X_std)
    
    # Define standard compressed features
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
    
    # Add raw channel telemetry columns
    for ch in channels:
        df_compressed[ch] = df_channels[ch].values
        
    # Precompute static physical band aggregations globally
    logger.info("Precomputing physical band aggregations...")
    for b_name, b_cols in bands_dict.items():
        df_compressed[f"{b_name}_mean"] = df_channels[b_cols].mean(axis=1).values
        df_compressed[f"{b_name}_median"] = df_channels[b_cols].median(axis=1).values
        df_compressed[f"{b_name}_trimmed_mean"] = scipy.stats.trim_mean(df_channels[b_cols].values, proportiontocut=0.1, axis=1)
        df_compressed[f"{b_name}_sum"] = df_channels[b_cols].sum(axis=1).values
        # Note: zscore_mean is dynamic per split, so it is computed inside evaluate_feature_fold
        
    # Precompute robust compression metrics
    df_compressed["robust_soft_mean"] = scipy.stats.trim_mean(df_channels[soft_band].values, proportiontocut=0.1, axis=1)
    df_compressed["robust_hard_mean"] = scipy.stats.trim_mean(df_channels[hard_band].values, proportiontocut=0.1, axis=1)
    df_compressed["median_ratio"] = df_channels[hard_band].median(axis=1).values / (df_channels[soft_band].median(axis=1).values + 1e-9)
    # Note: winsorized_ratio is dynamic per split
    
    # Ingest Target
    logger.info("Loading flares and target_6hr_binary_c...")
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
    
    # Load history features from test.parquet
    logger.info("Loading history features from test.parquet...")
    min_ts = df_master["timestamp"].min()
    max_ts = df_master["timestamp"].max()
    
    try:
        import pyarrow.parquet as pq
        table = pq.read_table(
            TEST_PARQUET,
            columns=["timestamp"] + history_cols,
            filters=[
                ("timestamp", ">=", min_ts),
                ("timestamp", "<=", max_ts)
            ]
        )
        df_features = table.to_pandas()
    except Exception as e:
        logger.warning(f"Pyarrow filter failed: {e}. Falling back to pandas.")
        df_features = pd.read_parquet(TEST_PARQUET, columns=["timestamp"] + history_cols)
        df_features["timestamp"] = pd.to_datetime(df_features["timestamp"])
        df_features = df_features[(df_features["timestamp"] >= min_ts) & (df_features["timestamp"] <= max_ts)]
        
    df_combined = pd.merge(df_compressed, df_features, on="timestamp", how="inner")
    df_combined["target"] = target_6hr_binary_c.values
    
    # Add day columns for LODO splits
    df_combined["day"] = df_combined["timestamp"].dt.date.astype(str)
    df_combined["feat_timestamp"] = df_combined["timestamp"] - pd.Timedelta(minutes=60)
    df_combined["feat_day"] = df_combined["feat_timestamp"].dt.date.astype(str)
    
    # List all features
    raw_ch_features = [f"solexs_sdd2_spec_counts_ch{i}" for i in range(13, 38)]
    band_features = []
    for b in ["band_A", "band_B", "band_C", "band_D"]:
        for agg in ["mean", "median", "trimmed_mean", "sum", "zscore_mean"]:
            band_features.append(f"{b}_{agg}")
            
    comp_features = [
        "soft_band_mean", "hard_band_mean", "hard_soft_ratio",
        "pc1_projection", "pc2_projection",
        "robust_soft_mean", "robust_hard_mean", "winsorized_ratio", "median_ratio"
    ]
    
    all_features = raw_ch_features + band_features + comp_features
    assert len(all_features) == 54
    
    # Folds
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
    
    # Checkpoints
    task1_checkpoint = os.path.join(CHECKPOINT_DIR, "localization_task_1.json")
    task2_checkpoint = os.path.join(CHECKPOINT_DIR, "localization_task_2.json")
    task3_checkpoint = os.path.join(CHECKPOINT_DIR, "localization_task_3.json")
    task3b_checkpoint = os.path.join(CHECKPOINT_DIR, "localization_task_3b.json")
    task4_checkpoint = os.path.join(CHECKPOINT_DIR, "localization_task_4.json")
    task5_checkpoint = os.path.join(CHECKPOINT_DIR, "localization_task_5.json")
    task5c_checkpoint = os.path.join(CHECKPOINT_DIR, "localization_task_5c.json")
    task6a_checkpoint = os.path.join(CHECKPOINT_DIR, "localization_task_6a.json")
    task6_checkpoint = os.path.join(CHECKPOINT_DIR, "localization_task_6.json")
    
    # Helper function to evaluate feature on a fold
    def evaluate_feature_fold(df_train, df_test, feat_name):
        Y_train = df_train["target"].values
        Y_test = df_test["target"].values
        
        if len(np.unique(Y_test)) < 2:
            return None
            
        X_hist_train = df_train[history_cols].values
        X_hist_test = df_test[history_cols].values
        
        # Dynamic Features
        if "zscore_mean" in feat_name:
            band_name = feat_name.split("_zscore_mean")[0]
            band_cols = bands_dict[band_name]
            scaler_band = StandardScaler()
            X_band_train = scaler_band.fit_transform(df_train[band_cols].values)
            X_feat_train = X_band_train.mean(axis=1)
            X_band_test = scaler_band.transform(df_test[band_cols].values)
            X_feat_test = X_band_test.mean(axis=1)
        elif feat_name == "winsorized_ratio":
            soft_train = df_train[soft_band].mean(axis=1).values
            hard_train = df_train[hard_band].mean(axis=1).values
            p_soft_5, p_soft_95 = np.percentile(soft_train, [5, 95])
            p_hard_5, p_hard_95 = np.percentile(hard_train, [5, 95])
            
            soft_train_wins = np.clip(soft_train, p_soft_5, p_soft_95)
            hard_train_wins = np.clip(hard_train, p_hard_5, p_hard_95)
            X_feat_train = hard_train_wins / (soft_train_wins + 1e-9)
            
            soft_test = df_test[soft_band].mean(axis=1).values
            hard_test = df_test[hard_band].mean(axis=1).values
            soft_test_wins = np.clip(soft_test, p_soft_5, p_soft_95)
            hard_test_wins = np.clip(hard_test, p_hard_5, p_hard_95)
            X_feat_test = hard_test_wins / (soft_test_wins + 1e-9)
        else:
            X_feat_train = df_train[feat_name].values
            X_feat_test = df_test[feat_name].values
            
        scaler_hist = StandardScaler()
        X_hist_train_scaled = scaler_hist.fit_transform(X_hist_train)
        X_hist_test_scaled = scaler_hist.transform(X_hist_test)
        
        # Train baseline
        lr_base = LogisticRegression(max_iter=1000, random_state=42).fit(X_hist_train_scaled, Y_train)
        prob_base = lr_base.predict_proba(X_hist_test_scaled)[:, 1]
        base_metrics = compute_metrics(Y_test, prob_base)
        
        # Train augmented
        X_joint_train = np.column_stack((X_feat_train, X_hist_train_scaled))
        X_joint_test = np.column_stack((X_feat_test, X_hist_test_scaled))
        
        lr_aug = LogisticRegression(max_iter=1000, random_state=42).fit(X_joint_train, Y_train)
        prob_aug = lr_aug.predict_proba(X_joint_test)[:, 1]
        aug_metrics = compute_metrics(Y_test, prob_aug)
        
        delta_auc = aug_metrics["auc"] - base_metrics["auc"]
        
        return {
            "baseline": base_metrics,
            "augmented": aug_metrics,
            "delta_auc": delta_auc,
            "prob_base": prob_base.tolist(),
            "prob_aug": prob_aug.tolist(),
            "X_feat_test": X_feat_test.tolist(),
            "X_hist_test_scaled": X_hist_test_scaled.tolist(),
            "model_aug": lr_aug
        }

    # Helper function to run folds for a list of features
    def run_folds_for_features(feat_list):
        results = {}
        for feat in feat_list:
            results[feat] = {}
            for f_name, f_cfg in folds_config.items():
                train_days = f_cfg["train"]
                test_days = f_cfg["test"]
                
                train_mask = df_combined["day"].isin(train_days) & df_combined["feat_day"].isin(train_days)
                test_mask = df_combined["day"].isin(test_days) & df_combined["feat_day"].isin(test_days)
                
                df_train = df_combined[train_mask]
                df_test = df_combined[test_mask]
                
                res = evaluate_feature_fold(df_train, df_test, feat)
                if res is None:
                    results[feat][f_name] = {"degenerate": True}
                else:
                    # Strip model object for JSON serialization
                    model_aug = res.pop("model_aug")
                    results[feat][f_name] = {
                        "degenerate": False,
                        "baseline": res["baseline"],
                        "augmented": res["augmented"],
                        "delta_auc": res["delta_auc"],
                        "prob_base": res["prob_base"],
                        "prob_aug": res["prob_aug"],
                        "X_feat_test": res["X_feat_test"],
                        "X_hist_test_scaled": res["X_hist_test_scaled"]
                    }
        return results

    # ----------------- TASK 1: RAW CHANNEL GENERALIZATION AUDIT -----------------
    if os.path.exists(task1_checkpoint):
        logger.info("Task 1 Checkpoint found. Loading...")
        with open(task1_checkpoint, "r") as fh:
            raw_channel_results = json.load(fh)
    else:
        logger.info("Executing Task 1: Raw Channel Generalization Audit...")
        raw_channel_results = run_folds_for_features(raw_ch_features)
        with open(task1_checkpoint, "w") as fh:
            json.dump(raw_channel_results, fh, indent=2)
        with open(os.path.join(OUTPUT_DIR, "raw_channel_generalization.json"), "w") as fh:
            json.dump(raw_channel_results, fh, indent=2)

    # ----------------- TASK 2: PHYSICAL BAND AUDIT -----------------
    if os.path.exists(task2_checkpoint):
        logger.info("Task 2 Checkpoint found. Loading...")
        with open(task2_checkpoint, "r") as fh:
            physical_band_results = json.load(fh)
    else:
        logger.info("Executing Task 2: Physical Band Audit...")
        physical_band_results = run_folds_for_features(band_features)
        with open(task2_checkpoint, "w") as fh:
            json.dump(physical_band_results, fh, indent=2)
        with open(os.path.join(OUTPUT_DIR, "physical_band_generalization.json"), "w") as fh:
            json.dump(physical_band_results, fh, indent=2)

    # ----------------- TASK 3: COMPRESSION AUDIT -----------------
    if os.path.exists(task3_checkpoint):
        logger.info("Task 3 Checkpoint found. Loading...")
        with open(task3_checkpoint, "r") as fh:
            compression_results = json.load(fh)
    else:
        logger.info("Executing Task 3: Compression Audit...")
        compression_results = run_folds_for_features(comp_features)
        with open(task3_checkpoint, "w") as fh:
            json.dump(compression_results, fh, indent=2)
        with open(os.path.join(OUTPUT_DIR, "compression_generalization.json"), "w") as fh:
            json.dump(compression_results, fh, indent=2)

    # Combine fold results for convenience
    fold_results = {}
    fold_results.update(raw_channel_results)
    fold_results.update(physical_band_results)
    fold_results.update(compression_results)

    # ----------------- TASK 3B: REPRODUCE 10G-N PROTOCOL -----------------
    if os.path.exists(task3b_checkpoint):
        logger.info("Task 3B Checkpoint found. Loading...")
        with open(task3b_checkpoint, "r") as fh:
            full_overlap_results = json.load(fh)
    else:
        logger.info("Executing Task 3B: Reproducing Sprint 10G-N Protocol...")
        df_full = df_combined.dropna(subset=["hard_soft_ratio"] + history_cols).copy()
        Y_full = df_full["target"].values
        X_hist_full = df_full[history_cols].values
        
        scaler_hist_full = StandardScaler()
        X_hist_full_scaled = scaler_hist_full.fit_transform(X_hist_full)
        
        lr_base_full = LogisticRegression(max_iter=1000, random_state=42).fit(X_hist_full_scaled, Y_full)
        prob_base_full = lr_base_full.predict_proba(X_hist_full_scaled)[:, 1]
        base_auc_full = safe_auc(Y_full, prob_base_full)
        
        full_overlap_results = {}
        for feat in all_features:
            if "zscore_mean" in feat:
                band_name = feat.split("_zscore_mean")[0]
                band_cols = bands_dict[band_name]
                scaler_band = StandardScaler()
                X_band = scaler_band.fit_transform(df_full[band_cols].values)
                X_feat_full = X_band.mean(axis=1)
            elif feat == "winsorized_ratio":
                soft = df_full[soft_band].mean(axis=1).values
                hard = df_full[hard_band].mean(axis=1).values
                p_soft_5, p_soft_95 = np.percentile(soft, [5, 95])
                p_hard_5, p_hard_95 = np.percentile(hard, [5, 95])
                soft_wins = np.clip(soft, p_soft_5, p_soft_95)
                hard_wins = np.clip(hard, p_hard_5, p_hard_95)
                X_feat_full = hard_wins / (soft_wins + 1e-9)
            else:
                X_feat_full = df_full[feat].values
                
            X_joint_full = np.column_stack((X_feat_full, X_hist_full_scaled))
            lr_aug_full = LogisticRegression(max_iter=1000, random_state=42).fit(X_joint_full, Y_full)
            prob_aug_full = lr_aug_full.predict_proba(X_joint_full)[:, 1]
            
            aug_auc_full = safe_auc(Y_full, prob_aug_full)
            delta_auc_full = aug_auc_full - base_auc_full
            
            full_overlap_results[feat] = {
                "baseline_auc": base_auc_full,
                "augmented_auc": aug_auc_full,
                "delta_auc": delta_auc_full
            }
            
        with open(task3b_checkpoint, "w") as fh:
            json.dump(full_overlap_results, fh, indent=2)
        with open(os.path.join(OUTPUT_DIR, "localization_vs_incremental.json"), "w") as fh:
            json.dump(full_overlap_results, fh, indent=2)

    # ----------------- TASK 4: STABILITY AUDIT -----------------
    if os.path.exists(task4_checkpoint):
        logger.info("Task 4 Checkpoint found. Loading...")
        with open(task4_checkpoint, "r") as fh:
            stability_results = json.load(fh)
    else:
        logger.info("Executing Task 4: Stability Audit...")
        stability_results = {}
        for feat in all_features:
            deltas = []
            for f_name, f_data in fold_results[feat].items():
                if f_data["degenerate"]:
                    continue
                deltas.append(f_data["delta_auc"])
                
            deltas = np.array(deltas)
            stability_results[feat] = {
                "mean_delta_auc": float(np.mean(deltas)),
                "std_delta_auc": float(np.std(deltas)),
                "variance_delta_auc": float(np.var(deltas)),
                "min_delta_auc": float(np.min(deltas)),
                "max_delta_auc": float(np.max(deltas)),
                "positive_fold_count": int(np.sum(deltas > 0)),
                "negative_fold_count": int(np.sum(deltas <= 0))
            }
            
        with open(task4_checkpoint, "w") as fh:
            json.dump(stability_results, fh, indent=2)
        with open(os.path.join(OUTPUT_DIR, "localization_stability.json"), "w") as fh:
            json.dump(stability_results, fh, indent=2)

    # ----------------- TASK 5: CONFIDENCE INTERVAL AUDIT -----------------
    if os.path.exists(task5_checkpoint):
        logger.info("Task 5 Checkpoint found. Loading...")
        with open(task5_checkpoint, "r") as fh:
            ci_results = json.load(fh)
    else:
        logger.info("Executing Task 5: Confidence Interval Audit (1000 bootstrap draws)...")
        ci_results = {}
        np.random.seed(42)
        
        for feat in all_features:
            ci_results[feat] = {}
            for f_name, f_data in fold_results[feat].items():
                if f_data["degenerate"]:
                    ci_results[feat][f_name] = {
                        "degenerate": True,
                        "ci_95": [None, None]
                    }
                    continue
                    
                Y_test = np.array(df_combined[df_combined["day"].isin(folds_config[f_name]["test"]) & df_combined["feat_day"].isin(folds_config[f_name]["test"])]["target"].values)
                prob_base = np.array(f_data["prob_base"])
                prob_aug = np.array(f_data["prob_aug"])
                
                deltas = []
                for _ in range(1000):
                    idx_boot = np.random.choice(len(Y_test), size=len(Y_test), replace=True)
                    Y_boot = Y_test[idx_boot]
                    if len(np.unique(Y_boot)) < 2:
                        continue
                    auc_base = safe_auc(Y_boot, prob_base[idx_boot])
                    auc_aug = safe_auc(Y_boot, prob_aug[idx_boot])
                    deltas.append(auc_aug - auc_base)
                    
                deltas = np.array(deltas)
                ci_lower = float(np.percentile(deltas, 2.5)) if len(deltas) > 0 else float("nan")
                ci_upper = float(np.percentile(deltas, 97.5)) if len(deltas) > 0 else float("nan")
                
                ci_results[feat][f_name] = {
                    "degenerate": False,
                    "ci_95": [ci_lower, ci_upper]
                }
                
        with open(task5_checkpoint, "w") as fh:
            json.dump(ci_results, fh, indent=2)
        with open(os.path.join(OUTPUT_DIR, "localization_ci.json"), "w") as fh:
            json.dump(ci_results, fh, indent=2)

    # ----------------- TASK 5C: SPREAD & SIGN MATRIX -----------------
    if os.path.exists(task5c_checkpoint):
        logger.info("Task 5C Checkpoint found. Loading...")
        with open(task5c_checkpoint, "r") as fh:
            spread_sign_results = json.load(fh)
    else:
        logger.info("Executing Task 5C: Spread & Sign Matrix...")
        spread_sign_results = {}
        for feat in all_features:
            fold_deltas = {}
            for f_name, f_data in fold_results[feat].items():
                if f_data["degenerate"]:
                    continue
                fold_deltas[f_name] = f_data["delta_auc"]
                
            best_fold = max(fold_deltas, key=fold_deltas.get)
            worst_fold = min(fold_deltas, key=fold_deltas.get)
            best_val = fold_deltas[best_fold]
            worst_val = fold_deltas[worst_fold]
            spread = best_val - worst_val
            
            signs = {}
            for f_name in ["Fold A", "Fold B", "Fold D"]:
                val = fold_deltas[f_name]
                if val > 1e-9:
                    signs[f_name] = "+"
                elif val < -1e-9:
                    signs[f_name] = "-"
                else:
                    signs[f_name] = "0"
                    
            spread_sign_results[feat] = {
                "best_fold": best_fold,
                "best_delta_auc": best_val,
                "worst_fold": worst_fold,
                "worst_delta_auc": worst_val,
                "spread": spread,
                "signs": signs
            }
            
        with open(task5c_checkpoint, "w") as fh:
            json.dump(spread_sign_results, fh, indent=2)
        with open(os.path.join(OUTPUT_DIR, "localization_spread_sign_audit.json"), "w") as fh:
            json.dump(spread_sign_results, fh, indent=2)

    # ----------------- TASK 6A: RAW CHANNEL LEADERBOARD -----------------
    if os.path.exists(task6a_checkpoint):
        logger.info("Task 6A Checkpoint found. Loading...")
        with open(task6a_checkpoint, "r") as fh:
            raw_channel_rankings = json.load(fh)
    else:
        logger.info("Executing Task 6A: Raw Channel Leaderboard...")
        raw_rankings_list = []
        for feat in raw_ch_features:
            stab = stability_results[feat]
            raw_rankings_list.append({
                "feature_name": feat,
                "positive_fold_count": stab["positive_fold_count"],
                "mean_delta_auc": stab["mean_delta_auc"],
                "variance": stab["variance_delta_auc"],
                "min_delta_auc": stab["min_delta_auc"]
            })
            
        raw_channel_rankings = sorted(
            raw_rankings_list,
            key=lambda x: (
                -x["positive_fold_count"],
                -x["mean_delta_auc"],
                x["variance"]
            )
        )
        
        with open(task6a_checkpoint, "w") as fh:
            json.dump(raw_channel_rankings, fh, indent=2)
        with open(os.path.join(OUTPUT_DIR, "raw_channel_rankings.json"), "w") as fh:
            json.dump(raw_channel_rankings, fh, indent=2)

    # ----------------- TASK 6: PURE RANKING GENERATION -----------------
    if os.path.exists(task6_checkpoint):
        logger.info("Task 6 Checkpoint found. Loading...")
        with open(task6_checkpoint, "r") as fh:
            localization_rankings = json.load(fh)
    else:
        logger.info("Executing Task 6: Pure Ranking Generation...")
        all_rankings_list = []
        for feat in all_features:
            stab = stability_results[feat]
            all_rankings_list.append({
                "feature_name": feat,
                "positive_fold_count": stab["positive_fold_count"],
                "mean_delta_auc": stab["mean_delta_auc"],
                "variance": stab["variance_delta_auc"],
                "min_delta_auc": stab["min_delta_auc"]
            })
            
        localization_rankings = sorted(
            all_rankings_list,
            key=lambda x: (
                -x["positive_fold_count"],
                -x["mean_delta_auc"],
                x["variance"]
            )
        )
        
        with open(task6_checkpoint, "w") as fh:
            json.dump(localization_rankings, fh, indent=2)
        with open(os.path.join(OUTPUT_DIR, "localization_rankings.json"), "w") as fh:
            json.dump(localization_rankings, fh, indent=2)

    # ----------------- TASK 7: REPORTING -----------------
    logger.info("Executing Task 7: Consolidating and reporting...")
    t1_global = time.time()
    runtime = t1_global - t0_global
    
    try:
        import resource
        peak_mem = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
    except Exception:
        peak_mem = 0.0
        
    signal_localization_audit = {
        "metadata": {
            "timestamp": pd.Timestamp.now().isoformat(),
            "evaluated_feature_count": len(all_features),
            "runtime_seconds": runtime,
            "peak_memory_mb": peak_mem
        },
        "raw_channel_generalization": raw_channel_results,
        "physical_band_generalization": physical_band_results,
        "compression_generalization": compression_results,
        "localization_vs_incremental": full_overlap_results,
        "localization_stability": stability_results,
        "localization_ci": ci_results,
        "localization_spread_sign_audit": spread_sign_results,
        "raw_channel_rankings": raw_channel_rankings,
        "localization_rankings": localization_rankings
    }
    
    with open(os.path.join(OUTPUT_DIR, "signal_localization_audit.json"), "w") as fh:
        json.dump(signal_localization_audit, fh, indent=2)
        
    # Generate Markdown report
    md_content = fr"""# Sprint 10G-OD: Signal Localization Audit Report

## 1. Executive Summary Table

| Metric | Measured Value |
| :--- | :---: |
| Total Features Evaluated | {len(all_features)} |
| Valid Folds | 3 |
| Degenerate Folds | 1 (Fold C - June 11) |
| Best Generalizing Feature | {localization_rankings[0]["feature_name"]} |
| Best Generalizing Raw Channel | {raw_channel_rankings[0]["feature_name"]} |
| Peak Memory Usage | {peak_mem:.2f} MB |
| Total Execution Time | {runtime:.3f} seconds |

---

## 2. Task 6A: Raw Channel Leaderboard

Top 10 raw spectral channels ranked by Positive Folds descending, Mean $\Delta$AUC descending, and Variance ascending.

| Rank | Channel Name | Positive Folds | Mean $\Delta$AUC | Variance | Worst $\Delta$AUC | 10G-N Full $\Delta$AUC |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: |
"""
    for rank, row in enumerate(raw_channel_rankings[:10], start=1):
        feat = row["feature_name"]
        full_val = full_overlap_results[feat]["delta_auc"]
        md_content += f"| {rank} | `{feat}` | {row['positive_fold_count']}/3 | {row['mean_delta_auc']:.6f} | {row['variance']:.6e} | {row['min_delta_auc']:.6f} | {full_val:.6f} |\n"

    md_content += r"""
---

## 3. Task 6: Pure Feature Ranking (Top 15)

Top 15 features across all types (raw, band, compression) ranked.

| Rank | Feature Name | Feature Type | Positive Folds | Mean $\Delta$AUC | Variance | Worst $\Delta$AUC | 10G-N Full $\Delta$AUC |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
"""
    for rank, row in enumerate(localization_rankings[:15], start=1):
        feat = row["feature_name"]
        full_val = full_overlap_results[feat]["delta_auc"]
        # Determine type
        if feat in raw_ch_features:
            f_type = "Raw Channel"
        elif feat in band_features:
            f_type = "Physical Band"
        else:
            f_type = "Compression"
        md_content += f"| {rank} | `{feat}` | {f_type} | {row['positive_fold_count']}/3 | {row['mean_delta_auc']:.6f} | {row['variance']:.6e} | {row['min_delta_auc']:.6f} | {full_val:.6f} |\n"

    md_content += r"""
---

## 4. Task 3B: Sprint 10G-N Protocol Reproduction Comparison

Comparison of Full Overlap $\Delta$AUC (Sprint 10G-N protocol) and LODO Mean $\Delta$AUC for all compression configurations and top ablated features.

| Feature Name | 10G-N Full Overlap $\Delta$AUC | LODO Mean $\Delta$AUC | Difference (LODO - 10G-N) |
| :--- | :---: | :---: | :---: |
"""
    for feat in comp_features:
        full_val = full_overlap_results[feat]["delta_auc"]
        mean_val = stability_results[feat]["mean_delta_auc"]
        md_content += f"| `{feat}` | {full_val:.6f} | {mean_val:.6f} | {mean_val - full_val:.6f} |\n"

    md_content += r"""
---

## 5. Task 5C: Spread & Daily Sign Matrix

Detailing best fold, worst fold, spread ($\Delta\text{AUC}_{\text{best}} - \Delta\text{AUC}_{\text{worst}}$), and daily fold signs for standard compression features, robust alternatives, and top bands.

| Feature Name | Best Fold | Worst Fold | Spread | Fold A Sign | Fold B Sign | Fold D Sign |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
"""
    for feat in comp_features + ["band_A_mean", "band_B_mean", "band_C_mean", "band_D_mean"]:
        res = spread_sign_results[feat]
        md_content += f"| `{feat}` | {res['best_fold']} ({res['best_delta_auc']:.4f}) | {res['worst_fold']} ({res['worst_delta_auc']:.4f}) | {res['spread']:.6f} | {res['signs']['Fold A']} | {res['signs']['Fold B']} | {res['signs']['Fold D']} |\n"

    md_content += r"""
---

## 6. Detailed Folds Registry (Folds A, B, & D)

Detailing actual test day $\Delta$AUC and 95% bootstrap confidence intervals for all compression features and robust alternatives.

| Fold | Feature Name | Actual $\Delta$AUC | 95% Bootstrap CI |
| :--- | :--- | :---: | :---: |
"""
    for f_name in ["Fold A", "Fold B", "Fold D"]:
        for feat in comp_features:
            act_val = fold_results[feat][f_name]["delta_auc"]
            ci = ci_results[feat][f_name]["ci_95"]
            md_content += f"| `{f_name}` | `{feat}` | {act_val:.6f} | [{ci[0]:.6f}, {ci[1]:.6f}] |\n"

    with open("artifacts/signal_localization_audit.md", "w") as f:
        f.write(md_content)
    with open("/Users/soumyadebtripathy/AdityaNet/brain/signal_localization_audit.md", "w") as f:
        f.write(md_content)
        
    logger.info(f"Signal Localization Audit finished successfully in {runtime:.2f} seconds.")

if __name__ == "__main__":
    main()
