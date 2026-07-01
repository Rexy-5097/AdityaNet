import os
import json
import numpy as np
import pandas as pd
import scipy.stats
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, precision_recall_curve, auc, brier_score_loss

MASTER_PARQUET = "/Users/soumyadebtripathy/AdityaNet/artifacts/aditya_l1/master_feature_table.parquet"
FLARES_PARQUET = "/Users/soumyadebtripathy/AdityaNet/artifacts/research/flares_full.parquet"
TEST_PARQUET = "/Users/soumyadebtripathy/AdityaNet/artifacts/research/test.parquet"
AUDIT_JSON_PATH = "/Users/soumyadebtripathy/AdityaNet/artifacts/aditya_l1/signal_localization_audit.json"

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
    discrepancies = []
    
    print("Loading audit data...")
    if not os.path.exists(AUDIT_JSON_PATH):
        print("Audit JSON file does not exist!")
        return
        
    with open(AUDIT_JSON_PATH, "r") as fh:
        audit_data = json.load(fh)
        
    print("Ingesting raw datasets...")
    df_master = pd.read_parquet(MASTER_PARQUET)
    df_master["timestamp"] = pd.to_datetime(df_master["timestamp"])
    
    channels = [f"solexs_sdd2_spec_counts_ch{i}" for i in range(13, 38)]
    df_channels = df_master[channels].interpolate(method="linear").fillna(0.0)
    
    # 4. Compression features: Standard compressed features recomputation
    print("Recomputing global compressed features...")
    scaler = StandardScaler()
    X_std = scaler.fit_transform(df_channels.values)
    pca = PCA(n_components=25, random_state=42)
    pca.fit(X_std)
    PC_scores = pca.transform(X_std)
    
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
    
    for ch in channels:
        df_compressed[ch] = df_channels[ch].values
        
    # 3. Physical band features precomputation
    print("Precomputing physical band aggregations...")
    for b_name, b_cols in bands_dict.items():
        df_compressed[f"{b_name}_mean"] = df_channels[b_cols].mean(axis=1).values
        df_compressed[f"{b_name}_median"] = df_channels[b_cols].median(axis=1).values
        df_compressed[f"{b_name}_trimmed_mean"] = scipy.stats.trim_mean(df_channels[b_cols].values, proportiontocut=0.1, axis=1)
        df_compressed[f"{b_name}_sum"] = df_channels[b_cols].sum(axis=1).values
        
    # Robust compression features precomputation
    df_compressed["robust_soft_mean"] = scipy.stats.trim_mean(df_channels[soft_band].values, proportiontocut=0.1, axis=1)
    df_compressed["robust_hard_mean"] = scipy.stats.trim_mean(df_channels[hard_band].values, proportiontocut=0.1, axis=1)
    df_compressed["median_ratio"] = df_channels[hard_band].median(axis=1).values / (df_channels[soft_band].median(axis=1).values + 1e-9)
    
    print("Loading flares and constructing target...")
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
    
    print("Loading test dataset history features...")
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
    
    # 1. Fold Reconstruction Validation
    print("\nTask 1: Fold Reconstruction Validation...")
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
        
        act_train = len(df_train)
        act_test = len(df_test)
        
        exp_train = expected_rows[f_name]["train"]
        exp_test = expected_rows[f_name]["test"]
        
        if act_train != exp_train:
            discrepancies.append(f"{f_name} train row count mismatch: expected {exp_train}, got {act_train}")
        if act_test != exp_test:
            discrepancies.append(f"{f_name} test row count mismatch: expected {exp_test}, got {act_test}")
            
    print(f"  Folds assignments and row counts verified. Current discrepancy count: {len(discrepancies)}")
    
    # Evaluate feature on a fold helper
    def evaluate_feature_fold(df_train, df_test, feat_name):
        Y_train = df_train["target"].values
        Y_test = df_test["target"].values
        
        if len(np.unique(Y_test)) < 2:
            return None
            
        X_hist_train = df_train[history_cols].values
        X_hist_test = df_test[history_cols].values
        
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
            "prob_aug": prob_aug.tolist()
        }

    # Evaluate all features across all folds
    print("\nEvaluating all features across all folds...")
    recomputed_fold_results = {}
    for feat in all_features:
        recomputed_fold_results[feat] = {}
        for f_name, f_cfg in folds_config.items():
            train_days = f_cfg["train"]
            test_days = f_cfg["test"]
            train_mask = df_combined["day"].isin(train_days) & df_combined["feat_day"].isin(train_days)
            test_mask = df_combined["day"].isin(test_days) & df_combined["feat_day"].isin(test_days)
            df_train = df_combined[train_mask]
            df_test = df_combined[test_mask]
            
            res = evaluate_feature_fold(df_train, df_test, feat)
            if res is None:
                recomputed_fold_results[feat][f_name] = {"degenerate": True}
            else:
                recomputed_fold_results[feat][f_name] = {
                    "degenerate": False,
                    "baseline": res["baseline"],
                    "augmented": res["augmented"],
                    "delta_auc": res["delta_auc"],
                    "prob_base": res["prob_base"],
                    "prob_aug": res["prob_aug"]
                }
                
    # 2. Raw Channel Recalculation
    print("\nTask 2: Raw Channel Recalculation Verification...")
    audit_raw = audit_data["raw_channel_generalization"]
    for feat in raw_ch_features:
        for f_name in ["Fold A", "Fold B", "Fold D"]:
            audit_f = audit_raw.get(feat, {}).get(f_name, {})
            recon_f = recomputed_fold_results[feat][f_name]
            
            # Compare baseline auc
            if abs(audit_f["baseline"]["auc"] - recon_f["baseline"]["auc"]) > 1e-6:
                discrepancies.append(f"{feat} {f_name} raw channel baseline_auc mismatch: audit={audit_f['baseline']['auc']}, recomputed={recon_f['baseline']['auc']}")
            # Compare augmented auc
            if abs(audit_f["augmented"]["auc"] - recon_f["augmented"]["auc"]) > 1e-6:
                discrepancies.append(f"{feat} {f_name} raw channel augmented_auc mismatch: audit={audit_f['augmented']['auc']}, recomputed={recon_f['augmented']['auc']}")
            # Compare delta auc
            if abs(audit_f["delta_auc"] - recon_f["delta_auc"]) > 1e-6:
                discrepancies.append(f"{feat} {f_name} raw channel delta_auc mismatch: audit={audit_f['delta_auc']}, recomputed={recon_f['delta_auc']}")
                
    # 3. Physical Band Recalculation
    print("\nTask 3: Physical Band Recalculation Verification...")
    audit_band = audit_data["physical_band_generalization"]
    for feat in band_features:
        for f_name in ["Fold A", "Fold B", "Fold D"]:
            audit_f = audit_band.get(feat, {}).get(f_name, {})
            recon_f = recomputed_fold_results[feat][f_name]
            
            # Compare baseline auc
            if abs(audit_f["baseline"]["auc"] - recon_f["baseline"]["auc"]) > 1e-6:
                discrepancies.append(f"{feat} {f_name} band baseline_auc mismatch: audit={audit_f['baseline']['auc']}, recomputed={recon_f['baseline']['auc']}")
            # Compare augmented auc
            if abs(audit_f["augmented"]["auc"] - recon_f["augmented"]["auc"]) > 1e-6:
                discrepancies.append(f"{feat} {f_name} band augmented_auc mismatch: audit={audit_f['augmented']['auc']}, recomputed={recon_f['augmented']['auc']}")
            # Compare delta auc
            if abs(audit_f["delta_auc"] - recon_f["delta_auc"]) > 1e-6:
                discrepancies.append(f"{feat} {f_name} band delta_auc mismatch: audit={audit_f['delta_auc']}, recomputed={recon_f['delta_auc']}")

    # 4. Compression Recalculation
    print("\nTask 4: Compression Recalculation Verification...")
    audit_comp = audit_data["compression_generalization"]
    for feat in comp_features:
        for f_name in ["Fold A", "Fold B", "Fold D"]:
            audit_f = audit_comp.get(feat, {}).get(f_name, {})
            recon_f = recomputed_fold_results[feat][f_name]
            
            # Compare baseline auc
            if abs(audit_f["baseline"]["auc"] - recon_f["baseline"]["auc"]) > 1e-6:
                discrepancies.append(f"{feat} {f_name} compression baseline_auc mismatch: audit={audit_f['baseline']['auc']}, recomputed={recon_f['baseline']['auc']}")
            # Compare augmented auc
            if abs(audit_f["augmented"]["auc"] - recon_f["augmented"]["auc"]) > 1e-6:
                discrepancies.append(f"{feat} {f_name} compression augmented_auc mismatch: audit={audit_f['augmented']['auc']}, recomputed={recon_f['augmented']['auc']}")
            # Compare delta auc
            if abs(audit_f["delta_auc"] - recon_f["delta_auc"]) > 1e-6:
                discrepancies.append(f"{feat} {f_name} compression delta_auc mismatch: audit={audit_f['delta_auc']}, recomputed={recon_f['delta_auc']}")

    # 5. Stability Recalculation
    print("\nTask 5: Stability Recalculation Verification...")
    recomputed_stability = {}
    audit_stability = audit_data["localization_stability"]
    
    for feat in all_features:
        deltas = []
        for f_name, f_data in recomputed_fold_results[feat].items():
            if f_data["degenerate"]:
                continue
            deltas.append(f_data["delta_auc"])
            
        deltas = np.array(deltas)
        mean_d = float(np.mean(deltas))
        std_d = float(np.std(deltas))
        var_d = float(np.var(deltas))
        min_d = float(np.min(deltas))
        max_d = float(np.max(deltas))
        pos_c = int(np.sum(deltas > 0))
        neg_c = int(np.sum(deltas <= 0))
        
        recomputed_stability[feat] = {
            "mean_delta_auc": mean_d,
            "std_delta_auc": std_d,
            "variance_delta_auc": var_d,
            "min_delta_auc": min_d,
            "max_delta_auc": max_d,
            "positive_fold_count": pos_c,
            "negative_fold_count": neg_c
        }
        
        audit_f_stab = audit_stability.get(feat, {})
        if audit_f_stab:
            if audit_f_stab.get("positive_fold_count") != pos_c:
                discrepancies.append(f"{feat} positive_fold_count mismatch: audit={audit_f_stab.get('positive_fold_count')}, recomputed={pos_c}")
            if audit_f_stab.get("negative_fold_count") != neg_c:
                discrepancies.append(f"{feat} negative_fold_count mismatch: audit={audit_f_stab.get('negative_fold_count')}, recomputed={neg_c}")
            
            for k, val_recon in [
                ("mean_delta_auc", mean_d),
                ("std_delta_auc", std_d),
                ("variance_delta_auc", var_d),
                ("min_delta_auc", min_d),
                ("max_delta_auc", max_d)
            ]:
                if abs(audit_f_stab.get(k) - val_recon) > 1e-6:
                    discrepancies.append(f"{feat} stability {k} mismatch: audit={audit_f_stab.get(k)}, recomputed={val_recon}")

    # 6. Bootstrap Validation
    print("\nTask 6: Bootstrap Validation...")
    recomputed_ci = {}
    audit_ci = audit_data["localization_ci"]
    
    np.random.seed(42)  # Re-run bootstrap with exact same seed initialization
    
    for feat in all_features:
        recomputed_ci[feat] = {}
        for f_name, f_data in recomputed_fold_results[feat].items():
            if f_data["degenerate"]:
                recomputed_ci[feat][f_name] = {
                    "degenerate": True,
                    "ci_95": [None, None]
                }
                continue
                
            test_mask = df_combined["day"].isin(folds_config[f_name]["test"]) & df_combined["feat_day"].isin(folds_config[f_name]["test"])
            Y_test = df_combined[test_mask]["target"].values
            
            prob_base = np.array(f_data["prob_base"])
            prob_aug = np.array(f_data["prob_aug"])
            
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
            
            # Verify CI boundaries
            audit_ci_val = audit_ci.get(feat, {}).get(f_name, {}).get("ci_95", [None, None])
            if audit_ci_val != [None, None]:
                if abs(audit_ci_val[0] - ci_lower) > 1e-4:
                    discrepancies.append(f"{f_name} {feat} lower CI mismatch: audit={audit_ci_val[0]}, recomputed={ci_lower}")
                if abs(audit_ci_val[1] - ci_upper) > 1e-4:
                    discrepancies.append(f"{f_name} {feat} upper CI mismatch: audit={audit_ci_val[1]}, recomputed={ci_upper}")

    # 7. Ranking Validation
    print("\nTask 7: Ranking Validation...")
    all_rankings_list = []
    for feat in all_features:
        stab = recomputed_stability[feat]
        all_rankings_list.append({
            "feature_name": feat,
            "positive_fold_count": stab["positive_fold_count"],
            "mean_delta_auc": stab["mean_delta_auc"],
            "variance": stab["variance_delta_auc"],
            "min_delta_auc": stab["min_delta_auc"]
        })
        
    recomputed_rankings = sorted(
        all_rankings_list,
        key=lambda x: (
            -x["positive_fold_count"],
            -x["mean_delta_auc"],
            x["variance"]
        )
    )
    
    audit_rankings = audit_data["localization_rankings"]
    for idx, (audit_r, recon_r) in enumerate(zip(audit_rankings, recomputed_rankings)):
        if audit_r["feature_name"] != recon_r["feature_name"]:
            discrepancies.append(f"Ranking mismatch at index {idx}: audit={audit_r['feature_name']}, recomputed={recon_r['feature_name']}")
        for k in ["positive_fold_count"]:
            if audit_r.get(k) != recon_r.get(k):
                discrepancies.append(f"Ranking row {recon_r['feature_name']} {k} mismatch: audit={audit_r.get(k)}, recomputed={recon_r.get(k)}")
        for k in ["mean_delta_auc", "variance", "min_delta_auc"]:
            if abs(audit_r.get(k) - recon_r.get(k)) > 1e-6:
                discrepancies.append(f"Ranking row {recon_r['feature_name']} {k} mismatch: audit={audit_r.get(k)}, recomputed={recon_r.get(k)}")

    print(f"\nValidation completed. Total discrepancies: {len(discrepancies)}")
    for d in discrepancies:
        print(f"  - {d}")
        
    verdict = "PASS" if len(discrepancies) == 0 else "FAIL"
    
    validation_output = {
        "verdict": verdict,
        "discrepancy_count": len(discrepancies),
        "discrepancies": discrepancies,
        "recomputed_values": {
            "folds": {
                f_name: {
                    "train_rows": len(df_combined[df_combined["day"].isin(f_cfg["train"]) & df_combined["feat_day"].isin(f_cfg["train"])]),
                    "test_rows": len(df_combined[df_combined["day"].isin(f_cfg["test"]) & df_combined["feat_day"].isin(f_cfg["test"])]),
                    "degenerate": f_name == "Fold C"
                } for f_name, f_cfg in folds_config.items()
            },
            "stability": recomputed_stability,
            "ci": recomputed_ci,
            "rankings": recomputed_rankings
        }
    }
    
    # Save validation json
    validation_json_path = "/Users/soumyadebtripathy/AdityaNet/artifacts/aditya_l1/localization_validation.json"
    os.makedirs(os.path.dirname(validation_json_path), exist_ok=True)
    with open(validation_json_path, "w") as fh:
        json.dump(validation_output, fh, indent=2)
    print(f"Saved validation JSON to {validation_json_path}")
    
    # Save small summary file to read from Python
    with open("/Users/soumyadebtripathy/AdityaNet/scratch/localization_summary.json", "w") as fh:
        json.dump({"verdict": verdict, "discrepancies": discrepancies}, fh, indent=2)

if __name__ == "__main__":
    main()
