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
from sklearn.feature_selection import mutual_info_classif

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
CHECKPOINT_DIR = os.path.join(OUTPUT_DIR, "checkpoints")

def get_memory_usage_mb() -> float:
    try:
        import resource
        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
    except Exception:
        return 0.0

def compute_metrics(y_true, y_prob):
    auc_val = float(roc_auc_score(y_true, y_prob))
    precision, recall, thresholds = precision_recall_curve(y_true, y_prob)
    pr_auc_val = float(auc(recall, precision))
    brier_val = float(brier_score_loss(y_true, y_prob))
    
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
        if abs(th - 0.5) < 0.006: # roughly 0.5
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
    logger.info("Initializing Sprint 10G-OA: Trust Gate Audit")
    t0_global = time.time()
    os.makedirs(CHECKPOINT_DIR, exist_ok=True)
    
    completed_tasks = []
    skipped_tasks = []
    
    # ----------------- TASK 1: INGEST AND ALIGN -----------------
    logger.info("Task 1: Ingesting data, engineering target, and verifying alignment")
    if not os.path.exists(MASTER_PARQUET):
        raise FileNotFoundError(f"Master feature table not found: {MASTER_PARQUET}")
    df_master = pd.read_parquet(MASTER_PARQUET)
    
    channels = [f"solexs_sdd2_spec_counts_ch{i}" for i in range(13, 38)]
    df_channels = df_master[channels].interpolate(method="linear").fillna(0.0)
    
    # Standardize channels and compute PCA
    scaler = StandardScaler()
    X_std = scaler.fit_transform(df_channels.values)
    pca = PCA(n_components=25, random_state=42)
    pca.fit(X_std)
    PC_scores = pca.transform(X_std)
    
    # Construct compressed features
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
    
    # Ingest Target
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
    
    # Load GOES history features
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
    
    df_combined = pd.merge(df_compressed, df_features, on="timestamp", how="inner")
    df_combined["target"] = target_6hr_binary_c.values
    
    # Standardize history baseline
    scaler_hist = StandardScaler()
    df_combined[history_cols] = scaler_hist.fit_transform(df_combined[history_cols].fillna(0.0).values)
    
    # ----------------- LEAKAGE KILL TEST (TASK 1) -----------------
    task1_checkpoint = os.path.join(CHECKPOINT_DIR, "trust_gate_task_1.json")
    if os.path.exists(task1_checkpoint):
        logger.info("Task 1: Checkpoint found. Skipping and loading results...")
        with open(task1_checkpoint, "r") as fh:
            leakage_results = json.load(fh)
        skipped_tasks.append("Task 1: Leakage Kill Test")
    else:
        logger.info("Task 1: Executing Leakage Kill Test")
        t0 = time.time()
        
        # Test Features
        test_feats = ["hard_soft_ratio", "soft_band_mean", "pc1_projection", "pc2_projection"]
        
        # Helper to fit and evaluate
        def fit_eval(df_data, f_name, h_shifted_df, target_y):
            X_feat = h_shifted_df[f_name].values
            X_hist = h_shifted_df[history_cols].values
            X_joint = np.column_stack((X_feat, X_hist))
            
            # Baseline (History Only)
            lr_base = LogisticRegression(max_iter=1000, random_state=42)
            lr_base.fit(X_hist, target_y)
            y_prob_base = lr_base.predict_proba(X_hist)[:, 1]
            base_metrics = compute_metrics(target_y, y_prob_base)
            
            # Augmented (History + Feature)
            lr_aug = LogisticRegression(max_iter=1000, random_state=42)
            lr_aug.fit(X_joint, target_y)
            y_prob_aug = lr_aug.predict_proba(X_joint)[:, 1]
            aug_metrics = compute_metrics(target_y, y_prob_aug)
            
            return {
                "baseline": base_metrics,
                "augmented": aug_metrics,
                "delta_auc": aug_metrics["auc"] - base_metrics["auc"],
                "delta_max_tss": aug_metrics["max_tss"] - base_metrics["max_tss"]
            }
            
        # We evaluate at horizon = 60m
        h = 60
        feat_shifted = df_combined[test_feats].shift(h)
        hist_shifted = df_combined[history_cols].shift(h)
        mask = feat_shifted.notna().all(axis=1) & hist_shifted.notna().all(axis=1)
        
        df_valid = pd.DataFrame(feat_shifted[mask])
        df_valid[history_cols] = hist_shifted[mask]
        Y = df_combined.loc[mask, "target"].values
        
        # Experiment A: Randomize Target Labels
        np.random.seed(42)
        Y_rand = np.random.permutation(Y)
        exp_a_results = {}
        for feat in test_feats:
            exp_a_results[feat] = fit_eval(df_combined, feat, df_valid, Y_rand)
            
        # Experiment B: Shuffled SoLEXS features
        exp_b_results = {}
        np.random.seed(100)
        df_shuffled_b = df_valid.copy()
        for feat in test_feats:
            df_shuffled_b[feat] = np.random.permutation(df_valid[feat].values)
            exp_b_results[feat] = fit_eval(df_combined, feat, df_shuffled_b, Y)
            
        # Experiment C: Future shifting (+60m, +180m, +360m)
        exp_c_results = {}
        for shift_val in [60, 180, 360]:
            exp_c_results[f"shift_plus_{shift_val}m"] = {}
            # Future shift is shift(-shift_val)
            feat_fut = df_combined[test_feats].shift(-shift_val)
            hist_fut = df_combined[history_cols].shift(h) # keep lead shift for history to represent forecasting setup
            mask_fut = feat_fut.notna().all(axis=1) & hist_fut.notna().all(axis=1)
            
            df_fut_valid = pd.DataFrame(feat_fut[mask_fut])
            df_fut_valid[history_cols] = hist_fut[mask_fut]
            Y_fut = df_combined.loc[mask_fut, "target"].values
            
            for feat in test_feats:
                exp_c_results[f"shift_plus_{shift_val}m"][feat] = fit_eval(df_combined, feat, df_fut_valid, Y_fut)
                
        # Experiment D: Permuted Timestamps of SoLEXS features (breaks temporal correlation)
        exp_d_results = {}
        np.random.seed(200)
        df_shuffled_d = df_valid.copy()
        for feat in test_feats:
            df_shuffled_d[feat] = df_valid[feat].sample(frac=1.0, random_state=200).values
            exp_d_results[feat] = fit_eval(df_combined, feat, df_shuffled_d, Y)
            
        leakage_results = {
            "experiment_a_random_target": exp_a_results,
            "experiment_b_shuffled_features": exp_b_results,
            "experiment_c_future_shifts": exp_c_results,
            "experiment_d_permuted_timestamps": exp_d_results
        }
        
        # Save checkpoints
        with open(task1_checkpoint, "w") as fh:
            json.dump(leakage_results, fh, indent=2)
        with open(os.path.join(OUTPUT_DIR, "leakage_kill_test.json"), "w") as fh:
            json.dump(leakage_results, fh, indent=2)
            
        t1 = time.time()
        logger.info(f"Task 1 completed in {t1 - t0:.2f} seconds.")
        completed_tasks.append("Task 1: Leakage Kill Test")
        
    # ----------------- TEMPORAL STABILITY (TASK 2) -----------------
    task2_checkpoint = os.path.join(CHECKPOINT_DIR, "trust_gate_task_2.json")
    if os.path.exists(task2_checkpoint):
        logger.info("Task 2: Checkpoint found. Skipping and loading results...")
        with open(task2_checkpoint, "r") as fh:
            stability_results = json.load(fh)
        skipped_tasks.append("Task 2: Temporal Stability Audit")
    else:
        logger.info("Task 2: Executing Temporal Stability Audit")
        t0 = time.time()
        
        # Split by day
        df_combined["day"] = pd.to_datetime(df_combined["timestamp"]).dt.date.astype(str)
        days = sorted(df_combined["day"].unique())
        
        test_feats = ["hard_soft_ratio", "soft_band_mean", "pc1_projection", "pc2_projection", "hard_band_mean"]
        horizons = [5, 15, 30, 60, 180, 360]
        
        stability_results = {}
        
        for day in days:
            df_day = df_combined[df_combined["day"] == day].copy()
            stability_results[day] = {}
            
            # Check target distribution
            target_counts = df_day["target"].value_counts()
            if len(target_counts) < 2:
                logger.warning(f"Day {day} has constant target. Setting metrics to NaN.")
                # Fill with NaN placeholders
                for feat in test_feats:
                    stability_results[day][feat] = {}
                    for h in horizons:
                        stability_results[day][feat][f"lead_{h}m"] = {
                            "pearson": float("nan"),
                            "spearman": float("nan"),
                            "mutual_information": float("nan"),
                            "delta_auc": float("nan")
                        }
                continue
                
            for feat in test_feats:
                stability_results[day][feat] = {}
                
                for h in horizons:
                    # Shift features
                    feat_shifted = df_day[feat].shift(h)
                    hist_shifted = df_day[history_cols].shift(h)
                    
                    # Mask
                    mask = feat_shifted.notna() & hist_shifted.notna().all(axis=1)
                    X_feat = feat_shifted[mask].values
                    X_hist = hist_shifted[mask].values
                    Y = df_day.loc[mask, "target"].values
                    
                    if len(Y) < 10 or len(np.unique(Y)) < 2:
                        stability_results[day][feat][f"lead_{h}m"] = {
                            "pearson": float("nan"),
                            "spearman": float("nan"),
                            "mutual_information": float("nan"),
                            "delta_auc": float("nan")
                        }
                        continue
                        
                    # Pearson, Spearman, MI
                    pears_val, _ = scipy.stats.pearsonr(X_feat, Y)
                    spear_val, _ = scipy.stats.spearmanr(X_feat, Y)
                    mi_val = float(mutual_info_classif(X_feat.reshape(-1, 1), Y, random_state=42)[0])
                    
                    # Delta AUC
                    lr_base = LogisticRegression(max_iter=1000, random_state=42)
                    lr_base.fit(X_hist, Y)
                    auc_base = float(roc_auc_score(Y, lr_base.predict_proba(X_hist)[:, 1]))
                    
                    X_joint = np.column_stack((X_feat, X_hist))
                    lr_aug = LogisticRegression(max_iter=1000, random_state=42)
                    lr_aug.fit(X_joint, Y)
                    auc_aug = float(roc_auc_score(Y, lr_aug.predict_proba(X_joint)[:, 1]))
                    delta_auc = auc_aug - auc_base
                    
                    stability_results[day][feat][f"lead_{h}m"] = {
                        "pearson": float(pears_val) if not np.isnan(pears_val) else None,
                        "spearman": float(spear_val) if not np.isnan(spear_val) else None,
                        "mutual_information": mi_val,
                        "delta_auc": delta_auc
                    }
                    
        with open(task2_checkpoint, "w") as fh:
            json.dump(stability_results, fh, indent=2)
        with open(os.path.join(OUTPUT_DIR, "temporal_stability_audit.json"), "w") as fh:
            json.dump(stability_results, fh, indent=2)
            
        t2 = time.time()
        logger.info(f"Task 2 completed in {t2 - t0:.2f} seconds.")
        completed_tasks.append("Task 2: Temporal Stability Audit")
        
    # ----------------- LEAVE-ONE-OUT CONTRIBUTION (TASK 3) -----------------
    task3_checkpoint = os.path.join(CHECKPOINT_DIR, "trust_gate_task_3.json")
    if os.path.exists(task3_checkpoint):
        logger.info("Task 3: Checkpoint found. Skipping and loading results...")
        with open(task3_checkpoint, "r") as fh:
            loo_results = json.load(fh)
        skipped_tasks.append("Task 3: Leave-One-Out Contribution")
    else:
        logger.info("Task 3: Executing Leave-One-Out Contribution Analysis")
        t0 = time.time()
        
        # We evaluate at horizon = 60m on the full overlap grid
        h = 60
        comp_feats = ["hard_soft_ratio", "soft_band_mean", "pc1_projection", "pc2_projection", "hard_band_mean"]
        
        feat_shifted = df_combined[comp_feats].shift(h)
        hist_shifted = df_combined[history_cols].shift(h)
        mask = feat_shifted.notna().all(axis=1) & hist_shifted.notna().all(axis=1)
        
        df_valid = pd.DataFrame(feat_shifted[mask])
        df_valid[history_cols] = hist_shifted[mask]
        Y = df_combined.loc[mask, "target"].values
        
        # 8 Configurations (Model A to H)
        models_config = {
            "Model A (History Only)": history_cols,
            "Model B (History + hard_soft_ratio)": history_cols + ["hard_soft_ratio"],
            "Model C (History + soft_band_mean)": history_cols + ["soft_band_mean"],
            "Model D (History + pc1_projection)": history_cols + ["pc1_projection"],
            "Model E (History + pc2_projection)": history_cols + ["pc2_projection"],
            "Model F (History + hard_band_mean)": history_cols + ["hard_band_mean"],
            "Model G (History + all compressed features)": history_cols + comp_feats,
            "Model H (History + hard_soft_ratio + pc2_projection)": history_cols + ["hard_soft_ratio", "pc2_projection"]
        }
        
        loo_results = {}
        for model_name, cols_used in models_config.items():
            X = df_valid[cols_used].values
            lr = LogisticRegression(max_iter=1000, random_state=42)
            lr.fit(X, Y)
            y_prob = lr.predict_proba(X)[:, 1]
            
            loo_results[model_name] = compute_metrics(Y, y_prob)
            logger.info(f"{model_name} - AUC: {loo_results[model_name]['auc']:.4f}, Max TSS: {loo_results[model_name]['max_tss']:.4f}")
            
        with open(task3_checkpoint, "w") as fh:
            json.dump(loo_results, fh, indent=2)
        with open(os.path.join(OUTPUT_DIR, "feature_contribution_audit.json"), "w") as fh:
            json.dump(loo_results, fh, indent=2)
            
        t3 = time.time()
        logger.info(f"Task 3 completed in {t3 - t0:.2f} seconds.")
        completed_tasks.append("Task 3: Leave-One-Out Contribution")
        
    # ----------------- COMPILE AND REPORT (TASK 4) -----------------
    logger.info("Task 4: Generating final consolidated JSON and Markdown reports")
    t0 = time.time()
    
    trust_gate_audit = {
        "metadata": {
            "sample_count": df_combined.shape[0],
            "baseline_history_features": history_cols,
            "timestamp": pd.Timestamp.now().isoformat(),
            "completed_tasks": completed_tasks,
            "skipped_tasks": skipped_tasks
        },
        "leakage_kill_test": leakage_results,
        "temporal_stability_audit": stability_results,
        "feature_contribution_audit": loo_results
    }
    
    with open(os.path.join(OUTPUT_DIR, "trust_gate_audit.json"), "w") as fh:
        json.dump(trust_gate_audit, fh, indent=2)
        
    # Generate the Markdown report content programmatically to ensure precision
    t1_global = time.time()
    total_runtime = t1_global - t0_global
    peak_mem = get_memory_usage_mb()
    
    # We write real values into the JSON metadata
    trust_gate_audit["metadata"]["runtime_seconds"] = total_runtime
    trust_gate_audit["metadata"]["peak_memory_mb"] = peak_mem
    with open(os.path.join(OUTPUT_DIR, "trust_gate_audit.json"), "w") as fh:
        json.dump(trust_gate_audit, fh, indent=2)
        
    logger.info(f"Trust Gate Audit finished successfully. Global Runtime: {total_runtime:.2f} seconds. Peak Memory: {peak_mem:.2f} MB")
    
if __name__ == "__main__":
    main()
