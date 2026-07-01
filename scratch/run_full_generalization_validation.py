import os
import json
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, precision_recall_curve, auc, brier_score_loss

MASTER_PARQUET = "/Users/soumyadebtripathy/AdityaNet/artifacts/aditya_l1/master_feature_table.parquet"
FLARES_PARQUET = "/Users/soumyadebtripathy/AdityaNet/artifacts/research/flares_full.parquet"
TEST_PARQUET = "/Users/soumyadebtripathy/AdityaNet/artifacts/research/test.parquet"
AUDIT_DIR = "/Users/soumyadebtripathy/AdityaNet/artifacts/aditya_l1"

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
    discrepancies = []
    
    # 6. Artifact Validation
    required_artifacts = [
        "generalization_fold_results.json",
        "generalization_stability.json",
        "generalization_sign_consistency.json",
        "generalization_ci.json",
        "generalization_operator_ranking.json",
        "temporal_generalization_audit.json"
    ]
    
    print("Task 6: Artifact Validation...")
    loaded_audit = {}
    for filename in required_artifacts:
        path = os.path.join(AUDIT_DIR, filename)
        if not os.path.exists(path):
            discrepancies.append(f"Artifact {filename} is missing.")
            print(f"  Missing: {filename}")
        else:
            try:
                with open(path, "r") as f:
                    loaded_audit[filename] = json.load(f)
                print(f"  Verified readability of {filename}")
            except Exception as e:
                discrepancies.append(f"Artifact {filename} is not readable. Error: {e}")
                print(f"  Unreadable: {filename} ({e})")
                
    # If files are missing or unreadable, we cannot proceed with some comparison, but we can load from what we have.
    # Load raw data and recompute everything
    print("\nIngesting datasets...")
    df_master = pd.read_parquet(MASTER_PARQUET)
    df_master["timestamp"] = pd.to_datetime(df_master["timestamp"])
    
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
    
    # Task 1 & 2: Reconstruct Folds and Recalculate Metrics
    print("\nTask 1 & 2: Recomputing folds and metrics...")
    
    recomputed_fold_results = {}
    audit_fold_results = loaded_audit.get("generalization_fold_results.json", {})
    
    # Expected row counts:
    # Fold A train: 4260, test: 1380
    # Fold B train: 4200, test: 1380
    # Fold C train: 4200, test: 1380 (degenerate)
    # Fold D train: 4260, test: 1380
    expected_rows = {
        "Fold A": {"train": 4260, "test": 1380},
        "Fold B": {"train": 4200, "test": 1380},
        "Fold C": {"train": 4200, "test": 1380},
        "Fold D": {"train": 4260, "test": 1380}
    }
    
    for f_name, f_cfg in folds_config.items():
        train_days = f_cfg["train"]
        test_days = f_cfg["test"]
        
        train_mask = df_combined["day"].isin(train_days) & df_combined["feat_day"].isin(train_days)
        test_mask = df_combined["day"].isin(test_days) & df_combined["feat_day"].isin(test_days)
        
        df_train = df_combined[train_mask]
        df_test = df_combined[test_mask]
        
        # Verify row counts and day assignments
        actual_train_rows = len(df_train)
        actual_test_rows = len(df_test)
        
        exp_train = expected_rows[f_name]["train"]
        exp_test = expected_rows[f_name]["test"]
        
        if actual_train_rows != exp_train:
            discrepancies.append(f"{f_name} train row count mismatch: expected {exp_train}, got {actual_train_rows}")
        if actual_test_rows != exp_test:
            discrepancies.append(f"{f_name} test row count mismatch: expected {exp_test}, got {actual_test_rows}")
            
        # Compare day assignments with audit
        audit_f = audit_fold_results.get(f_name, {})
        if audit_f:
            if audit_f.get("train_days") != train_days:
                discrepancies.append(f"{f_name} train_days mismatch: expected {train_days}, got {audit_f.get('train_days')}")
            if audit_f.get("test_days") != test_days:
                discrepancies.append(f"{f_name} test_days mismatch: expected {test_days}, got {audit_f.get('test_days')}")
        
        Y_train = df_train["target"].values
        Y_test = df_test["target"].values
        
        degenerate = len(np.unique(Y_test)) < 2
        
        if audit_f and audit_f.get("degenerate") != degenerate:
            discrepancies.append(f"{f_name} degenerate flag mismatch: expected {degenerate}, got {audit_f.get('degenerate')}")
            
        recomputed_fold_results[f_name] = {
            "train_days": train_days,
            "test_days": test_days,
            "degenerate": degenerate,
            "metrics": {}
        }
        
        if degenerate:
            continue
            
        X_hist_train = df_train[history_cols].values
        X_hist_test = df_test[history_cols].values
        
        lr_base = LogisticRegression(max_iter=1000, random_state=42).fit(X_hist_train, Y_train)
        prob_base = lr_base.predict_proba(X_hist_test)[:, 1]
        base_metrics = compute_metrics(Y_test, prob_base)
        
        recomputed_fold_results[f_name]["metrics"]["baseline_history"] = base_metrics
        
        # Compare baseline metrics
        if audit_f:
            audit_base = audit_f.get("metrics", {}).get("baseline_history", {})
            for m_key in ["auc", "pr_auc", "brier", "max_tss"]:
                val_audit = audit_base.get(m_key)
                val_recon = base_metrics.get(m_key)
                if abs(val_audit - val_recon) > 1e-6:
                    discrepancies.append(f"{f_name} baseline {m_key} mismatch: audit={val_audit}, recomputed={val_recon}")
                    
        for feat in test_feats:
            X_feat_train = df_train[feat].values
            X_feat_test = df_test[feat].values
            
            X_joint_train = np.column_stack((X_feat_train, X_hist_train))
            X_joint_test = np.column_stack((X_feat_test, X_hist_test))
            
            lr_aug = LogisticRegression(max_iter=1000, random_state=42).fit(X_joint_train, Y_train)
            prob_aug = lr_aug.predict_proba(X_joint_test)[:, 1]
            aug_metrics = compute_metrics(Y_test, prob_aug)
            
            delta_auc = aug_metrics["auc"] - base_metrics["auc"]
            
            recomputed_fold_results[f_name]["metrics"][feat] = {
                "baseline": base_metrics,
                "augmented": aug_metrics,
                "delta_auc": delta_auc
            }
            
            # Compare feature metrics
            if audit_f:
                audit_feat = audit_f.get("metrics", {}).get(feat, {})
                # Compare augmented metrics
                audit_aug = audit_feat.get("augmented", {})
                for m_key in ["auc", "pr_auc", "brier", "max_tss"]:
                    val_audit = audit_aug.get(m_key)
                    val_recon = aug_metrics.get(m_key)
                    if abs(val_audit - val_recon) > 1e-6:
                        discrepancies.append(f"{f_name} {feat} augmented {m_key} mismatch: audit={val_audit}, recomputed={val_recon}")
                # Compare delta auc
                val_audit_delta = audit_feat.get("delta_auc")
                if abs(val_audit_delta - delta_auc) > 1e-6:
                    discrepancies.append(f"{f_name} {feat} delta_auc mismatch: audit={val_audit_delta}, recomputed={delta_auc}")

    # Task 3: Sign Consistency Validation
    print("\nTask 3: Recomputing stability & sign consistency...")
    recomputed_stability = {}
    audit_stability = loaded_audit.get("generalization_stability.json", {})
    
    for feat in test_feats:
        deltas = []
        for f_name, f_data in recomputed_fold_results.items():
            if f_data["degenerate"]:
                continue
            deltas.append(f_data["metrics"][feat]["delta_auc"])
            
        deltas = np.array(deltas)
        pos_count = int(np.sum(deltas > 0))
        neg_count = int(np.sum(deltas <= 0))
        mean_delta = float(np.mean(deltas))
        std_delta = float(np.std(deltas))
        min_delta = float(np.min(deltas))
        max_delta = float(np.max(deltas))
        
        recomputed_stability[feat] = {
            "mean_delta_auc": mean_delta,
            "std_delta_auc": std_delta,
            "min_delta_auc": min_delta,
            "max_delta_auc": max_delta,
            "positive_fold_count": pos_count,
            "negative_fold_count": neg_count
        }
        
        if audit_stability:
            audit_f_stab = audit_stability.get(feat, {})
            if audit_f_stab:
                if audit_f_stab.get("positive_fold_count") != pos_count:
                    discrepancies.append(f"{feat} positive_fold_count mismatch: audit={audit_f_stab.get('positive_fold_count')}, recomputed={pos_count}")
                if audit_f_stab.get("negative_fold_count") != neg_count:
                    discrepancies.append(f"{feat} negative_fold_count mismatch: audit={audit_f_stab.get('negative_fold_count')}, recomputed={neg_count}")
                
                # Check metrics in stability
                for k in ["mean_delta_auc", "std_delta_auc", "min_delta_auc", "max_delta_auc"]:
                    if abs(audit_f_stab.get(k) - locals()[k.replace("delta", "deltas").split("_")[0] + "_delta"]) > 1e-6:
                        discrepancies.append(f"{feat} stability metric {k} mismatch: audit={audit_f_stab.get(k)}, recomputed={locals()[k.replace('delta', 'deltas').split('_')[0] + '_delta']}")
                        
    # Recompute Sign Consistency Classes
    recomputed_consistency = {
        "always_positive": [],
        "mixed_sign": [],
        "always_negative": []
    }
    for feat in test_feats:
        pos_folds = recomputed_stability[feat]["positive_fold_count"]
        neg_folds = recomputed_stability[feat]["negative_fold_count"]
        total_valid_folds = pos_folds + neg_folds
        
        if pos_folds == total_valid_folds:
            recomputed_consistency["always_positive"].append(feat)
        elif neg_folds == total_valid_folds:
            recomputed_consistency["always_negative"].append(feat)
        else:
            recomputed_consistency["mixed_sign"].append(feat)
            
    audit_consistency = loaded_audit.get("generalization_sign_consistency.json", {})
    if audit_consistency:
        for c_key in ["always_positive", "mixed_sign", "always_negative"]:
            if sorted(audit_consistency.get(c_key, [])) != sorted(recomputed_consistency[c_key]):
                discrepancies.append(f"Sign consistency category {c_key} mismatch: audit={audit_consistency.get(c_key)}, recomputed={recomputed_consistency[c_key]}")

    # Task 4: Bootstrap Validation
    print("\nTask 4: Recomputing confidence intervals via bootstrap...")
    recomputed_ci = {}
    audit_ci = loaded_audit.get("generalization_ci.json", {})
    
    np.random.seed(42)  # Re-run bootstrap with exact same global seed initialization
    
    for feat in test_feats:
        recomputed_ci[feat] = {}
        for f_name, f_data in recomputed_fold_results.items():
            if f_data["degenerate"]:
                recomputed_ci[feat][f_name] = {
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
            
            lr_base = LogisticRegression(max_iter=1000, random_state=42).fit(X_hist_train, Y_train)
            prob_base = lr_base.predict_proba(X_hist_test)[:, 1]
            
            X_joint_train = np.column_stack((X_feat_train, X_hist_train))
            X_joint_test = np.column_stack((X_feat_test, X_hist_test))
            lr_aug = LogisticRegression(max_iter=1000, random_state=42).fit(X_joint_train, Y_train)
            prob_aug = lr_aug.predict_proba(X_joint_test)[:, 1]
            
            boot_deltas = []
            for _ in range(1000):
                idx_boot = np.random.choice(len(Y_test), size=len(Y_test), replace=True)
                Y_boot = Y_test[idx_boot]
                
                if len(np.unique(Y_boot)) < 2:
                    continue
                    
                auc_base = safe_auc(Y_boot, prob_base[idx_boot])
                auc_aug = safe_auc(Y_boot, prob_aug[idx_boot])
                boot_deltas.append(auc_aug - auc_base)
                
            boot_deltas = np.array(boot_deltas)
            ci_lower = float(np.percentile(boot_deltas, 2.5)) if len(boot_deltas) > 0 else float("nan")
            ci_upper = float(np.percentile(boot_deltas, 97.5)) if len(boot_deltas) > 0 else float("nan")
            
            recomputed_ci[feat][f_name] = {
                "degenerate": False,
                "ci_95": [ci_lower, ci_upper]
            }
            
            # Verify bootstrap CI
            if audit_ci:
                audit_ci_val = audit_ci.get(feat, {}).get(f_name, {}).get("ci_95", [None, None])
                if audit_ci_val != [None, None]:
                    if abs(audit_ci_val[0] - ci_lower) > 1e-4:
                        discrepancies.append(f"{f_name} {feat} lower CI mismatch: audit={audit_ci_val[0]}, recomputed={ci_lower}")
                    if abs(audit_ci_val[1] - ci_upper) > 1e-4:
                        discrepancies.append(f"{f_name} {feat} upper CI mismatch: audit={audit_ci_val[1]}, recomputed={ci_upper}")

    # Task 5: Ranking Validation
    print("\nTask 5: Rebuilding operator ranking table...")
    # Recompute significance counts first
    # In run_temporal_generalization_audit.py, significance check sets seed 100
    np.random.seed(100)
    recomputed_significance = {}
    for feat in test_feats:
        recomputed_significance[feat] = {}
        sig_count = 0
        for f_name, f_data in recomputed_fold_results.items():
            if f_data["degenerate"]:
                recomputed_significance[feat][f_name] = {"degenerate": True, "significant": False}
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
            
            lr_base = LogisticRegression(max_iter=1000, random_state=42).fit(X_hist_train, Y_train)
            prob_base = lr_base.predict_proba(X_hist_test)[:, 1]
            actual_auc_base = safe_auc(Y_test, prob_base)
            
            X_joint_train = np.column_stack((X_feat_train, X_hist_train))
            X_joint_test = np.column_stack((X_feat_test, X_hist_test))
            lr_aug = LogisticRegression(max_iter=1000, random_state=42).fit(X_joint_train, Y_train)
            prob_aug = lr_aug.predict_proba(X_joint_test)[:, 1]
            actual_auc_aug = safe_auc(Y_test, prob_aug)
            actual_delta_auc = actual_auc_aug - actual_auc_base
            
            perm_deltas = []
            for _ in range(1000):
                X_feat_perm = np.random.permutation(X_feat_test)
                X_joint_perm = np.column_stack((X_feat_perm, X_hist_test))
                prob_aug_perm = lr_aug.predict_proba(X_joint_perm)[:, 1]
                auc_aug_perm = safe_auc(Y_test, prob_aug_perm)
                perm_deltas.append(auc_aug_perm - actual_auc_base)
                
            perm_deltas = np.array(perm_deltas)
            p_val = float(np.sum(perm_deltas >= actual_delta_auc) / 1000.0)
            significant = p_val <= 0.05
            if significant:
                sig_count += 1
                
        recomputed_stability[feat]["significant_fold_count"] = sig_count
        
    features_ranking = []
    for feat in test_feats:
        # Recompute worst day audit (minimum delta_auc across non-degenerate folds)
        deltas = []
        for f_name, f_data in recomputed_fold_results.items():
            if f_data["degenerate"]:
                continue
            deltas.append(f_data["metrics"][feat]["delta_auc"])
        min_delta = float(np.min(deltas))
        
        pos_folds = recomputed_stability[feat]["positive_fold_count"]
        sig_folds = recomputed_stability[feat]["significant_fold_count"]
        mean_delta = recomputed_stability[feat]["mean_delta_auc"]
        variance = float(recomputed_stability[feat]["std_delta_auc"] ** 2)
        
        features_ranking.append({
            "feature_name": feat,
            "positive_fold_count": pos_folds,
            "significant_fold_count": sig_folds,
            "minimum_delta_auc": min_delta,
            "mean_delta_auc": mean_delta,
            "variance": variance
        })
        
    recomputed_ranking = sorted(
        features_ranking,
        key=lambda x: (
            -x["positive_fold_count"],
            -x["significant_fold_count"],
            -x["minimum_delta_auc"],
            -x["mean_delta_auc"],
            x["variance"]
        )
    )
    
    audit_ranking = loaded_audit.get("generalization_operator_ranking.json", [])
    if audit_ranking:
        for idx, (audit_r, recon_r) in enumerate(zip(audit_ranking, recomputed_ranking)):
            if audit_r["feature_name"] != recon_r["feature_name"]:
                discrepancies.append(f"Ranking mismatch at index {idx}: audit={audit_r['feature_name']}, recomputed={recon_r['feature_name']}")
            for k in ["positive_fold_count", "significant_fold_count"]:
                if audit_r.get(k) != recon_r.get(k):
                    discrepancies.append(f"Ranking row {recon_r['feature_name']} {k} mismatch: audit={audit_r.get(k)}, recomputed={recon_r.get(k)}")
            for k in ["minimum_delta_auc", "mean_delta_auc", "variance"]:
                if abs(audit_r.get(k) - recon_r.get(k)) > 1e-6:
                    discrepancies.append(f"Ranking row {recon_r['feature_name']} {k} mismatch: audit={audit_r.get(k)}, recomputed={recon_r.get(k)}")
                    
    # Generate Outputs
    print(f"\nTotal Discrepancies Found: {len(discrepancies)}")
    for d in discrepancies:
        print(f"  - {d}")
        
    # Write json output
    validation_json_path = "/Users/soumyadebtripathy/AdityaNet/artifacts/aditya_l1/generalization_validation.json"
    verdict = "PASS" if len(discrepancies) == 0 else "FAIL"
    
    validation_result = {
        "verdict": verdict,
        "discrepancies": discrepancies,
        "discrepancy_count": len(discrepancies),
        "recomputed_values": {
            "folds": {
                f_name: {
                    "train_rows": len(df_combined[df_combined["day"].isin(f_cfg["train"]) & df_combined["feat_day"].isin(f_cfg["train"])]),
                    "test_rows": len(df_combined[df_combined["day"].isin(f_cfg["test"]) & df_combined["feat_day"].isin(f_cfg["test"])]),
                    "degenerate": recomputed_fold_results[f_name]["degenerate"]
                } for f_name, f_cfg in folds_config.items()
            },
            "metrics": {
                f_name: {
                    feat: {
                        "baseline_auc": recomputed_fold_results[f_name]["metrics"][feat]["baseline"]["auc"],
                        "augmented_auc": recomputed_fold_results[f_name]["metrics"][feat]["augmented"]["auc"],
                        "delta_auc": recomputed_fold_results[f_name]["metrics"][feat]["delta_auc"]
                    } for feat in test_feats
                } for f_name in ["Fold A", "Fold B", "Fold D"]  # omit degenerate Fold C
            },
            "stability": recomputed_stability,
            "consistency": recomputed_consistency,
            "ranking": recomputed_ranking
        }
    }
    
    os.makedirs(os.path.dirname(validation_json_path), exist_ok=True)
    with open(validation_json_path, "w") as fh:
        json.dump(validation_result, fh, indent=2)
    print(f"Saved JSON validation report to {validation_json_path}")
    
    # Save the discrepancies and details to a txt file so main python execution can report them
    with open("/Users/soumyadebtripathy/AdityaNet/scratch/validation_summary.json", "w") as fh:
        json.dump({"verdict": verdict, "discrepancies": discrepancies}, fh, indent=2)

if __name__ == "__main__":
    main()
