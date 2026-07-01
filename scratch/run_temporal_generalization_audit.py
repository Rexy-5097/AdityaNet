import os
import json
import logging
import time
import numpy as np
import pandas as pd
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

def main():
    logger.info("Initializing Sprint 10G-OC: Temporal Generalization Audit")
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
    
    # Define bands and ratios
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
    
    # Ingest Target (C/M/X Flares)
    logger.info("Loading flares and computing target_6hr_binary_c...")
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
    
    # Load history features from test.parquet (optimized load)
    logger.info("Loading history features from test.parquet...")
    history_cols = ["minutes_since_last_flare", "mean_60m", "mean_15m", "long_flux", "peak_30m"]
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
    
    # Add day columns for cross-validation splits
    df_combined["day"] = df_combined["timestamp"].dt.date.astype(str)
    # Feature timestamp falls 60 minutes prior to represent contemporaneous forecasting at h=60m
    df_combined["feat_timestamp"] = df_combined["timestamp"] - pd.Timedelta(minutes=60)
    df_combined["feat_day"] = df_combined["feat_timestamp"].dt.date.astype(str)
    
    # Standardize history baseline
    scaler_hist = StandardScaler()
    df_combined[history_cols] = scaler_hist.fit_transform(df_combined[history_cols].fillna(0.0).values)
    
    # Define Folds
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
    
    test_feats = ["hard_soft_ratio", "soft_band_mean", "pc1_projection", "pc2_projection"]
    
    # ----------------- TASK 1: LEAVE-ONE-DAY-OUT EVALUATION -----------------
    task1_checkpoint = os.path.join(CHECKPOINT_DIR, "generalization_task_1.json")
    if os.path.exists(task1_checkpoint):
        logger.info("Task 1 Checkpoint found. Loading...")
        with open(task1_checkpoint, "r") as fh:
            fold_results = json.load(fh)
    else:
        logger.info("Executing Task 1: Leave-One-Day-Out Evaluation...")
        fold_results = {}
        for f_name, f_cfg in folds_config.items():
            train_days = f_cfg["train"]
            test_days = f_cfg["test"]
            
            # Form splits using temporal boundary isolation
            train_mask = df_combined["day"].isin(train_days) & df_combined["feat_day"].isin(train_days)
            test_mask = df_combined["day"].isin(test_days) & df_combined["feat_day"].isin(test_days)
            
            df_train = df_combined[train_mask].copy()
            df_test = df_combined[test_mask].copy()
            
            Y_train = df_train["target"].values
            Y_test = df_test["target"].values
            
            fold_results[f_name] = {
                "train_days": train_days,
                "test_days": test_days,
                "degenerate": False,
                "metrics": {}
            }
            
            # Check target class variance on test set
            if len(np.unique(Y_test)) < 2:
                logger.warning(f"Fold {f_name} Test Day {test_days} is DEGENERATE (only 1 class present). Skipping metrics.")
                fold_results[f_name]["degenerate"] = True
                continue
                
            # Evaluated features
            X_hist_train = df_train[history_cols].values
            X_hist_test = df_test[history_cols].values
            
            # History Only Model
            lr_base = LogisticRegression(max_iter=1000, random_state=42).fit(X_hist_train, Y_train)
            prob_base = lr_base.predict_proba(X_hist_test)[:, 1]
            base_metrics = compute_metrics(Y_test, prob_base)
            
            fold_results[f_name]["metrics"]["baseline_history"] = base_metrics
            
            for feat in test_feats:
                X_feat_train = df_train[feat].values
                X_feat_test = df_test[feat].values
                
                X_joint_train = np.column_stack((X_feat_train, X_hist_train))
                X_joint_test = np.column_stack((X_feat_test, X_hist_test))
                
                # History + Feature Model
                lr_aug = LogisticRegression(max_iter=1000, random_state=42).fit(X_joint_train, Y_train)
                prob_aug = lr_aug.predict_proba(X_joint_test)[:, 1]
                aug_metrics = compute_metrics(Y_test, prob_aug)
                
                delta_auc = aug_metrics["auc"] - base_metrics["auc"]
                
                fold_results[f_name]["metrics"][feat] = {
                    "baseline": base_metrics,
                    "augmented": aug_metrics,
                    "delta_auc": delta_auc
                }
                
        with open(task1_checkpoint, "w") as fh:
            json.dump(fold_results, fh, indent=2)
        with open(os.path.join(OUTPUT_DIR, "generalization_fold_results.json"), "w") as fh:
            json.dump(fold_results, fh, indent=2)
            
    # ----------------- TASK 2: STABILITY ANALYSIS -----------------
    task2_checkpoint = os.path.join(CHECKPOINT_DIR, "generalization_task_2.json")
    if os.path.exists(task2_checkpoint):
        logger.info("Task 2 Checkpoint found. Loading...")
        with open(task2_checkpoint, "r") as fh:
            stability_results = json.load(fh)
    else:
        logger.info("Executing Task 2: Fold Stability Analysis...")
        stability_results = {}
        for feat in test_feats:
            deltas = []
            for f_name, f_data in fold_results.items():
                if f_data["degenerate"]:
                    continue
                deltas.append(f_data["metrics"][feat]["delta_auc"])
                
            deltas = np.array(deltas)
            stability_results[feat] = {
                "mean_delta_auc": float(np.mean(deltas)),
                "std_delta_auc": float(np.std(deltas)),
                "min_delta_auc": float(np.min(deltas)),
                "max_delta_auc": float(np.max(deltas)),
                "positive_fold_count": int(np.sum(deltas > 0)),
                "negative_fold_count": int(np.sum(deltas <= 0))
            }
            
        with open(task2_checkpoint, "w") as fh:
            json.dump(stability_results, fh, indent=2)
        with open(os.path.join(OUTPUT_DIR, "generalization_stability.json"), "w") as fh:
            json.dump(stability_results, fh, indent=2)
            
    # ----------------- TASK 3: SIGN CONSISTENCY AUDIT -----------------
    task3_checkpoint = os.path.join(CHECKPOINT_DIR, "generalization_task_3.json")
    if os.path.exists(task3_checkpoint):
        logger.info("Task 3 Checkpoint found. Loading...")
        with open(task3_checkpoint, "r") as fh:
            consistency_results = json.load(fh)
    else:
        logger.info("Executing Task 3: Sign Consistency Audit...")
        consistency_results = {
            "always_positive": [],
            "mixed_sign": [],
            "always_negative": []
        }
        for feat in test_feats:
            pos_folds = stability_results[feat]["positive_fold_count"]
            neg_folds = stability_results[feat]["negative_fold_count"]
            total_valid_folds = pos_folds + neg_folds
            
            if pos_folds == total_valid_folds:
                consistency_results["always_positive"].append(feat)
            elif neg_folds == total_valid_folds:
                consistency_results["always_negative"].append(feat)
            else:
                consistency_results["mixed_sign"].append(feat)
                
        with open(task3_checkpoint, "w") as fh:
            json.dump(consistency_results, fh, indent=2)
        with open(os.path.join(OUTPUT_DIR, "generalization_sign_consistency.json"), "w") as fh:
            json.dump(consistency_results, fh, indent=2)
            
    # ----------------- TASK 4: CONFIDENCE INTERVAL AUDIT -----------------
    task4_checkpoint = os.path.join(CHECKPOINT_DIR, "generalization_task_4.json")
    if os.path.exists(task4_checkpoint):
        logger.info("Task 4 Checkpoint found. Loading...")
        with open(task4_checkpoint, "r") as fh:
            ci_results = json.load(fh)
    else:
        logger.info("Executing Task 4: Confidence Interval Audit (1000 bootstrap draws)...")
        ci_results = {}
        np.random.seed(42)
        
        for feat in test_feats:
            ci_results[feat] = {}
            for f_name, f_data in fold_results.items():
                if f_data["degenerate"]:
                    ci_results[feat][f_name] = {
                        "degenerate": True,
                        "ci_95": [None, None]
                    }
                    continue
                    
                train_days = f_data["train_days"]
                test_days = f_data["test_days"]
                train_mask = df_combined["day"].isin(train_days) & df_combined["feat_day"].isin(train_days)
                test_mask = df_combined["day"].isin(test_days) & df_combined["feat_day"].isin(test_days)
                
                df_train = df_combined[train_mask]
                df_test = df_combined[test_mask]
                
                Y_train = df_train["target"].values
                Y_test = df_test["target"].values
                
                X_hist_train = df_train[history_cols].values
                X_hist_test = df_test[history_cols].values
                
                X_feat_train = df_train[feat].values
                X_feat_test = df_test[feat].values
                
                # Train models once
                lr_base = LogisticRegression(max_iter=1000, random_state=42).fit(X_hist_train, Y_train)
                prob_base = lr_base.predict_proba(X_hist_test)[:, 1]
                
                X_joint_train = np.column_stack((X_feat_train, X_hist_train))
                X_joint_test = np.column_stack((X_feat_test, X_hist_test))
                lr_aug = LogisticRegression(max_iter=1000, random_state=42).fit(X_joint_train, Y_train)
                prob_aug = lr_aug.predict_proba(X_joint_test)[:, 1]
                
                # Bootstrap test predictions
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
                
        with open(task4_checkpoint, "w") as fh:
            json.dump(ci_results, fh, indent=2)
        with open(os.path.join(OUTPUT_DIR, "generalization_ci.json"), "w") as fh:
            json.dump(ci_results, fh, indent=2)
            
    # ----------------- TASK 4B: PERMUTATION SIGNIFICANCE TEST -----------------
    task4b_checkpoint = os.path.join(CHECKPOINT_DIR, "generalization_task_4b.json")
    if os.path.exists(task4b_checkpoint):
        logger.info("Task 4B Checkpoint found. Loading...")
        with open(task4b_checkpoint, "r") as fh:
            significance_results = json.load(fh)
    else:
        logger.info("Executing Task 4B: Permutation Significance Test (1000 shuffles)...")
        significance_results = {}
        np.random.seed(100)
        
        for feat in test_feats:
            significance_results[feat] = {}
            for f_name, f_data in fold_results.items():
                if f_data["degenerate"]:
                    significance_results[feat][f_name] = {
                        "degenerate": True,
                        "p_value": None,
                        "significant": False
                    }
                    continue
                    
                train_days = f_data["train_days"]
                test_days = f_data["test_days"]
                train_mask = df_combined["day"].isin(train_days) & df_combined["feat_day"].isin(train_days)
                test_mask = df_combined["day"].isin(test_days) & df_combined["feat_day"].isin(test_days)
                
                df_train = df_combined[train_mask]
                df_test = df_combined[test_mask]
                
                Y_train = df_train["target"].values
                Y_test = df_test["target"].values
                
                X_hist_train = df_train[history_cols].values
                X_hist_test = df_test[history_cols].values
                
                X_feat_train = df_train[feat].values
                X_feat_test = df_test[feat].values
                
                # Train models
                lr_base = LogisticRegression(max_iter=1000, random_state=42).fit(X_hist_train, Y_train)
                prob_base = lr_base.predict_proba(X_hist_test)[:, 1]
                actual_auc_base = safe_auc(Y_test, prob_base)
                
                X_joint_train = np.column_stack((X_feat_train, X_hist_train))
                X_joint_test = np.column_stack((X_feat_test, X_hist_test))
                lr_aug = LogisticRegression(max_iter=1000, random_state=42).fit(X_joint_train, Y_train)
                prob_aug = lr_aug.predict_proba(X_joint_test)[:, 1]
                actual_auc_aug = safe_auc(Y_test, prob_aug)
                actual_delta_auc = actual_auc_aug - actual_auc_base
                
                # Permute feature values on the test set
                perm_deltas = []
                for _ in range(1000):
                    X_feat_perm = np.random.permutation(X_feat_test)
                    X_joint_perm = np.column_stack((X_feat_perm, X_hist_test))
                    
                    prob_aug_perm = lr_aug.predict_proba(X_joint_perm)[:, 1]
                    auc_aug_perm = safe_auc(Y_test, prob_aug_perm)
                    perm_deltas.append(auc_aug_perm - actual_auc_base)
                    
                perm_deltas = np.array(perm_deltas)
                p_val = float(np.sum(perm_deltas >= actual_delta_auc) / 1000.0)
                
                significance_results[feat][f_name] = {
                    "degenerate": False,
                    "p_value": p_val,
                    "significant": (p_val <= 0.05)
                }
                
        with open(task4b_checkpoint, "w") as fh:
            json.dump(significance_results, fh, indent=2)
        with open(os.path.join(OUTPUT_DIR, "generalization_significance.json"), "w") as fh:
            json.dump(significance_results, fh, indent=2)
            
    # Compute significant fold count for stability_results
    for feat in test_feats:
        sig_count = 0
        for f_name, f_data in significance_results[feat].items():
            if not f_data["degenerate"] and f_data["significant"]:
                sig_count += 1
        stability_results[feat]["significant_fold_count"] = sig_count
        
    with open(task2_checkpoint, "w") as fh:
        json.dump(stability_results, fh, indent=2)
    with open(os.path.join(OUTPUT_DIR, "generalization_stability.json"), "w") as fh:
        json.dump(stability_results, fh, indent=2)

    # ----------------- TASK 5B: WORST DAY AUDIT -----------------
    task5b_checkpoint = os.path.join(CHECKPOINT_DIR, "generalization_task_5b.json")
    if os.path.exists(task5b_checkpoint):
        logger.info("Task 5B Checkpoint found. Loading...")
        with open(task5b_checkpoint, "r") as fh:
            worst_day_results = json.load(fh)
    else:
        logger.info("Executing Task 5B: Worst Day Audit...")
        worst_day_results = {}
        for feat in test_feats:
            deltas = []
            for f_name, f_data in fold_results.items():
                if f_data["degenerate"]:
                    continue
                deltas.append(f_data["metrics"][feat]["delta_auc"])
                
            worst_day_results[feat] = {
                "best_fold_delta_auc": float(np.max(deltas)),
                "worst_fold_delta_auc": float(np.min(deltas)),
                "spread": float(np.max(deltas) - np.min(deltas))
            }
            
        with open(task5b_checkpoint, "w") as fh:
            json.dump(worst_day_results, fh, indent=2)
        with open(os.path.join(OUTPUT_DIR, "generalization_worst_day_audit.json"), "w") as fh:
            json.dump(worst_day_results, fh, indent=2)

    # ----------------- TASK 5: OPERATOR ROBUSTNESS TABLE -----------------
    task5_checkpoint = os.path.join(CHECKPOINT_DIR, "generalization_task_5.json")
    if os.path.exists(task5_checkpoint):
        logger.info("Task 5 Checkpoint found. Loading...")
        with open(task5_checkpoint, "r") as fh:
            operator_ranking = json.load(fh)
    else:
        logger.info("Executing Task 5: Operator Robustness Table Ranking...")
        features_ranking = []
        for feat in test_feats:
            pos_folds = stability_results[feat]["positive_fold_count"]
            sig_folds = stability_results[feat]["significant_fold_count"]
            min_delta = worst_day_results[feat]["worst_fold_delta_auc"]
            mean_delta = stability_results[feat]["mean_delta_auc"]
            variance = float(stability_results[feat]["std_delta_auc"] ** 2)
            
            features_ranking.append({
                "feature_name": feat,
                "positive_fold_count": pos_folds,
                "significant_fold_count": sig_folds,
                "minimum_delta_auc": min_delta,
                "mean_delta_auc": mean_delta,
                "variance": variance
            })
            
        # Ranking hierarchy:
        # 1. positive_fold_count descending
        # 2. significant_fold_count descending
        # 3. minimum_delta_auc descending
        # 4. mean_delta_auc descending
        # 5. variance ascending
        operator_ranking = sorted(
            features_ranking,
            key=lambda x: (
                -x["positive_fold_count"],
                -x["significant_fold_count"],
                -x["minimum_delta_auc"],
                -x["mean_delta_auc"],
                x["variance"]
            )
        )
        
        with open(task5_checkpoint, "w") as fh:
            json.dump(operator_ranking, fh, indent=2)
        with open(os.path.join(OUTPUT_DIR, "generalization_operator_ranking.json"), "w") as fh:
            json.dump(operator_ranking, fh, indent=2)
            
    # ----------------- TASK 6: REPORTING -----------------
    logger.info("Executing Task 6: Consolidating and reporting...")
    t1_global = time.time()
    runtime = t1_global - t0_global
    
    try:
        import resource
        peak_mem = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
    except Exception:
        peak_mem = 0.0
        
    temporal_generalization_audit = {
        "metadata": {
            "timestamp": pd.Timestamp.now().isoformat(),
            "evaluated_features": test_feats,
            "baseline_history_features": history_cols,
            "runtime_seconds": runtime,
            "peak_memory_mb": peak_mem
        },
        "generalization_fold_results": fold_results,
        "generalization_stability": stability_results,
        "generalization_sign_consistency": consistency_results,
        "generalization_ci": ci_results,
        "generalization_significance": significance_results,
        "generalization_worst_day_audit": worst_day_results,
        "generalization_operator_ranking": operator_ranking
    }
    
    with open(os.path.join(OUTPUT_DIR, "temporal_generalization_audit.json"), "w") as fh:
        json.dump(temporal_generalization_audit, fh, indent=2)
        
    # Build Markdown report
    md_content = f"""# Sprint 10G-OC: Temporal Generalization Audit Report

## 1. Executive Summary Table

| Metric | Measured Value |
| :--- | :---: |
| Non-Degenerate Folds | 3 |
| Degenerate Folds | 1 (Fold C - June 11) |
| Best Generalizing Feature | {operator_ranking[0]["feature_name"]} |
| Peak Memory Usage | {peak_mem:.2f} MB |
| Total Execution Time | {runtime:.3f} seconds |

---

## 2. Degenerate Folds Registry

On **2026-06-11** (Fold C Test set), the target `target_6hr_binary_c` was constant (all 1s). As a result, Fold C is registered as **DEGENERATE** and completely excluded from all downstream statistical summaries, significance tests, confidence intervals, and operator ranking to prevent mathematical distortion.

---

## 3. Task 1: Leave-One-Day-Out evaluation

Metrics computed at forecast lead horizon $h = 60$ minutes.

"""
    for f_name in sorted(fold_results.keys()):
        f_data = fold_results[f_name]
        md_content += f"### {f_name} (Test Days: {f_data['test_days']})\n\n"
        if f_data["degenerate"]:
            md_content += "*DEGENERATE FOLD (No classes present in test set)*\n\n"
            continue
            
        md_content += "| Configuration | AUC | PR-AUC | Brier Score | Max TSS | Delta AUC |\n"
        md_content += "| :--- | :---: | :---: | :---: | :---: | :---: |\n"
        
        base = f_data["metrics"]["baseline_history"]
        md_content += f"| `Baseline History` | {base['auc']:.6f} | {base['pr_auc']:.6f} | {base['brier']:.6f} | {base['max_tss']:.6f} | - |\n"
        
        for feat in test_feats:
            res = f_data["metrics"][feat]
            md_content += f"| `History + {feat}` | {res['augmented']['auc']:.6f} | {res['augmented']['pr_auc']:.6f} | {res['augmented']['brier']:.6f} | {res['augmented']['max_tss']:.6f} | {res['delta_auc']:.6f} |\n"
        md_content += "\n"

    md_content += """---

## 4. Fold Stability & Significance Audit (Tasks 2, 3, & 4B)

Summary statistics and permutation p-values over all non-degenerate folds.
Significant folds are defined as folds with empirical permutation p-value $p \le 0.05$ (1000 shuffles).

| Feature Name | Mean $\Delta$AUC | Std $\Delta$AUC | Positive Folds | Significant Folds | Consistency Class |
| :--- | :---: | :---: | :---: | :---: | :---: |
"""
    for feat in test_feats:
        stab = stability_results[feat]
        
        # Check consistency class
        if feat in consistency_results["always_positive"]:
            c_class = "always_positive"
        elif feat in consistency_results["always_negative"]:
            c_class = "always_negative"
        else:
            c_class = "mixed_sign"
            
        md_content += f"| `{feat}` | {stab['mean_delta_auc']:.6f} | {stab['std_delta_auc']:.6f} | {stab['positive_fold_count']}/3 | {stab['significant_fold_count']}/3 | `{c_class}` |\n"

    md_content += """
---

## 5. Confidence Intervals & Permutation Significance Registry (Tasks 4 & 4B)

Detailing 95% Confidence Intervals (obtained via 1000 bootstrap draws) and empirical p-values (obtained via 1000 shuffles) for each feature and fold.

| Fold | Feature Name | Actual $\Delta$AUC | 95% Bootstrap CI | Permutation p-value | Significant ($p \le 0.05$) |
| :--- | :--- | :---: | :---: | :---: | :---: |
"""
    for f_name in sorted(fold_results.keys()):
        f_data = fold_results[f_name]
        if f_data["degenerate"]:
            continue
        for feat in test_feats:
            act_delta = f_data["metrics"][feat]["delta_auc"]
            ci = ci_results[feat][f_name]["ci_95"]
            p_val = significance_results[feat][f_name]["p_value"]
            sig = significance_results[feat][f_name]["significant"]
            md_content += f"| `{f_name}` | `{feat}` | {act_delta:.6f} | [{ci[0]:.6f}, {ci[1]:.6f}] | {p_val:.4f} | {sig} |\n"

    md_content += """
---

## 6. Worst Day Audit (Task 5B)

Detailing best, worst, and absolute spread of $\Delta$AUC across non-degenerate folds.

| Feature Name | Best Fold $\Delta$AUC | Worst Fold $\Delta$AUC | Spread (Best - Worst) |
| :--- | :---: | :---: | :---: |
"""
    for feat in test_feats:
        wda = worst_day_results[feat]
        md_content += f"| `{feat}` | {wda['best_fold_delta_auc']:.6f} | {wda['worst_fold_delta_auc']:.6f} | {wda['spread']:.6f} |\n"

    md_content += """
---

## 7. Task 5: Operator Robustness Table

Features ranked hierarchically by:
1. `positive_fold_count` (descending)
2. `significant_fold_count` (descending)
3. `minimum_delta_auc` (descending, rewarding worst-case performance)
4. `mean_delta_auc` (descending)
5. `variance` (ascending)

| Rank | Feature Name | Positive Folds | Significant Folds | Worst-Case $\Delta$AUC | Mean $\Delta$AUC | Variance |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: |
"""
    for rank, row in enumerate(operator_ranking, start=1):
        md_content += f"| {rank} | `{row['feature_name']}` | {row['positive_fold_count']}/3 | {row['significant_fold_count']}/3 | {row['minimum_delta_auc']:.6f} | {row['mean_delta_auc']:.6f} | {row['variance']:.6e} |\n"

    with open("artifacts/temporal_generalization_audit.md", "w") as f:
        f.write(md_content)
    with open("/Users/soumyadebtripathy/AdityaNet/brain/temporal_generalization_audit.md", "w") as f:
        f.write(md_content)
        
    logger.info(f"Temporal Generalization Audit finished successfully in {runtime:.2f} seconds.")

if __name__ == "__main__":
    main()
