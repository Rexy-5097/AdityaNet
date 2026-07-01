import os
import json
import logging
import numpy as np
import pandas as pd
import scipy.stats
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, precision_recall_curve, auc, brier_score_loss
from sklearn.feature_selection import mutual_info_classif

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Paths
MASTER_PARQUET = "artifacts/aditya_l1/master_feature_table.parquet"
FLARES_PARQUET = "artifacts/research/flares_full.parquet"
FEATURE_PARQUET = "artifacts/feature_dataset.parquet"

# Reference Artifacts
REF_LEAKAGE = "artifacts/aditya_l1/leakage_kill_test.json"
REF_STABILITY = "artifacts/aditya_l1/temporal_stability_audit.json"
REF_CONTRIB = "artifacts/aditya_l1/feature_contribution_audit.json"

TOLERANCE = 1e-6

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

def compare_dicts(d1, d2, path=""):
    discrepancies = []
    for k in d1:
        if k not in d2:
            discrepancies.append(f"MISSING KEY: {path}.{k}")
            continue
        
        v1 = d1[k]
        v2 = d2[k]
        
        if isinstance(v1, dict):
            discrepancies.extend(compare_dicts(v1, v2, f"{path}.{k}"))
        elif isinstance(v1, (float, int)):
            if np.isnan(v1) and np.isnan(v2):
                continue
            if abs(v1 - v2) > TOLERANCE:
                discrepancies.append(f"VALUE DISCREPANCY: {path}.{k} | Audit={v1} | Recomputed={v2} | Diff={abs(v1-v2)}")
        elif v1 != v2:
             discrepancies.append(f"TYPE/VALUE DISCREPANCY: {path}.{k} | Audit={v1} | Recomputed={v2}")
    return discrepancies

def main():
    logger.info("Starting Independent Verification of Sprint 10G-OA")
    
    # Check artifacts
    missing = []
    for p in [REF_LEAKAGE, REF_STABILITY, REF_CONTRIB]:
        if not os.path.exists(p):
            missing.append(p)
    if missing:
        for p in missing:
            print(f"FILE NOT FOUND: {p}")
        return

    # Ingest Data
    df_master = pd.read_parquet(MASTER_PARQUET)
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
    
    history_cols = ["minutes_since_last_flare", "mean_60m", "mean_15m", "long_flux", "peak_30m"]
    df_features = pd.read_parquet(FEATURE_PARQUET, columns=["timestamp"] + history_cols)
    df_features["timestamp"] = pd.to_datetime(df_features["timestamp"])
    
    df_combined = pd.merge(df_compressed, df_features, on="timestamp", how="inner")
    df_combined["target"] = target_6hr_binary_c.values
    
    scaler_hist = StandardScaler()
    df_combined[history_cols] = scaler_hist.fit_transform(df_combined[history_cols].fillna(0.0).values)
    
    all_discrepancies = []

    # Task 1: Leakage Kill Test
    logger.info("Verifying Task 1: Leakage Kill Test")
    test_feats = ["hard_soft_ratio", "soft_band_mean", "pc1_projection", "pc2_projection"]
    comp_feats = ["hard_soft_ratio", "soft_band_mean", "pc1_projection", "pc2_projection", "hard_band_mean"]
    
    def fit_eval(f_name, h_shifted_df, target_y):
        X_feat = h_shifted_df[f_name].values
        X_hist = h_shifted_df[history_cols].values
        X_joint = np.column_stack((X_feat, X_hist))
        
        lr_base = LogisticRegression(max_iter=1000, random_state=42)
        lr_base.fit(X_hist, target_y)
        y_prob_base = lr_base.predict_proba(X_hist)[:, 1]
        base_metrics = compute_metrics(target_y, y_prob_base)
        
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
    
    h = 60
    feat_shifted = df_combined[comp_feats].shift(h)
    hist_shifted = df_combined[history_cols].shift(h)
    mask = feat_shifted.notna().all(axis=1) & hist_shifted.notna().all(axis=1)
    df_valid = pd.DataFrame(feat_shifted[mask])
    df_valid[history_cols] = hist_shifted[mask]
    Y = df_combined.loc[mask, "target"].values
    
    np.random.seed(42)
    Y_rand = np.random.permutation(Y)
    exp_a = {feat: fit_eval(feat, df_valid, Y_rand) for feat in test_feats}
    
    exp_b = {}
    np.random.seed(100)
    df_shuffled_b = df_valid.copy()
    for feat in test_feats:
        df_shuffled_b[feat] = np.random.permutation(df_valid[feat].values)
        exp_b[feat] = fit_eval(feat, df_shuffled_b, Y)
        
    exp_c = {}
    for shift_val in [60, 180, 360]:
        exp_c[f"shift_plus_{shift_val}m"] = {}
        feat_fut = df_combined[test_feats].shift(-shift_val)
        hist_fut = df_combined[history_cols].shift(h)
        mask_fut = feat_fut.notna().all(axis=1) & hist_fut.notna().all(axis=1)
        df_fut_valid = pd.DataFrame(feat_fut[mask_fut])
        df_fut_valid[history_cols] = hist_fut[mask_fut]
        Y_fut = df_combined.loc[mask_fut, "target"].values
        for feat in test_feats:
            exp_c[f"shift_plus_{shift_val}m"][feat] = fit_eval(feat, df_fut_valid, Y_fut)
            
    exp_d = {}
    np.random.seed(200)
    df_shuffled_d = df_valid.copy()
    for feat in test_feats:
        df_shuffled_d[feat] = df_valid[feat].sample(frac=1.0, random_state=200).values
        exp_d[feat] = fit_eval(feat, df_shuffled_d, Y)
        
    recomp_leakage = {
        "experiment_a_random_target": exp_a,
        "experiment_b_shuffled_features": exp_b,
        "experiment_c_future_shifts": exp_c,
        "experiment_d_permuted_timestamps": exp_d
    }
    
    with open(REF_LEAKAGE, "r") as f:
        ref_leakage_data = json.load(f)
    all_discrepancies.extend(compare_dicts(ref_leakage_data, recomp_leakage, "leakage_kill_test"))

    # Task 2: Temporal Stability
    logger.info("Verifying Task 2: Temporal Stability Audit")
    df_combined["day"] = pd.to_datetime(df_combined["timestamp"]).dt.date.astype(str)
    days = sorted(df_combined["day"].unique())
    test_feats_2 = ["hard_soft_ratio", "soft_band_mean", "pc1_projection", "pc2_projection", "hard_band_mean"]
    horizons = [5, 15, 30, 60, 180, 360]
    recomp_stability = {}
    
    for day in days:
        df_day = df_combined[df_combined["day"] == day].copy()
        recomp_stability[day] = {}
        target_counts = df_day["target"].value_counts()
        if len(target_counts) < 2:
            for feat in test_feats_2:
                recomp_stability[day][feat] = {f"lead_{h_val}m": {"pearson": float("nan"), "spearman": float("nan"), "mutual_information": float("nan"), "delta_auc": float("nan")} for h_val in horizons}
            continue
        for feat in test_feats_2:
            recomp_stability[day][feat] = {}
            for h_val in horizons:
                feat_shifted_d = df_day[feat].shift(h_val)
                hist_shifted_d = df_day[history_cols].shift(h_val)
                mask_d = feat_shifted_d.notna() & hist_shifted_d.notna().all(axis=1)
                X_feat_d = feat_shifted_d[mask_d].values
                X_hist_d = hist_shifted_d[mask_d].values
                Y_d = df_day.loc[mask_d, "target"].values
                if len(Y_d) < 10 or len(np.unique(Y_d)) < 2:
                    recomp_stability[day][feat][f"lead_{h_val}m"] = {"pearson": float("nan"), "spearman": float("nan"), "mutual_information": float("nan"), "delta_auc": float("nan")}
                    continue
                pears_val, _ = scipy.stats.pearsonr(X_feat_d, Y_d)
                spear_val, _ = scipy.stats.spearmanr(X_feat_d, Y_d)
                mi_val = float(mutual_info_classif(X_feat_d.reshape(-1, 1), Y_d, random_state=42)[0])
                lr_base_d = LogisticRegression(max_iter=1000, random_state=42).fit(X_hist_d, Y_d)
                auc_base_d = float(roc_auc_score(Y_d, lr_base_d.predict_proba(X_hist_d)[:, 1]))
                X_joint_d = np.column_stack((X_feat_d, X_hist_d))
                lr_aug_d = LogisticRegression(max_iter=1000, random_state=42).fit(X_joint_d, Y_d)
                auc_aug_d = float(roc_auc_score(Y_d, lr_aug_d.predict_proba(X_joint_d)[:, 1]))
                recomp_stability[day][feat][f"lead_{h_val}m"] = {
                    "pearson": float(pears_val) if not np.isnan(pears_val) else None,
                    "spearman": float(spear_val) if not np.isnan(spear_val) else None,
                    "mutual_information": mi_val,
                    "delta_auc": auc_aug_d - auc_base_d
                }
                
    with open(REF_STABILITY, "r") as f:
        ref_stability_data = json.load(f)
    all_discrepancies.extend(compare_dicts(ref_stability_data, recomp_stability, "temporal_stability_audit"))

    # Task 3: Feature Contribution
    logger.info("Verifying Task 3: Feature Contribution Audit")
    comp_feats_5 = ["hard_soft_ratio", "soft_band_mean", "pc1_projection", "pc2_projection", "hard_band_mean"]
    
    models_config = {
        "Model A (History Only)": history_cols,
        "Model B (History + hard_soft_ratio)": history_cols + ["hard_soft_ratio"],
        "Model C (History + soft_band_mean)": history_cols + ["soft_band_mean"],
        "Model D (History + pc1_projection)": history_cols + ["pc1_projection"],
        "Model E (History + pc2_projection)": history_cols + ["pc2_projection"],
        "Model F (History + hard_band_mean)": history_cols + ["hard_band_mean"],
        "Model G (History + all compressed features)": history_cols + comp_feats_5,
        "Model G_std (Standardized all)": history_cols + comp_feats_5,
        "Model H (History + hard_soft_ratio + pc2_projection)": history_cols + ["hard_soft_ratio", "pc2_projection"]
    }
    recomp_contrib = {}
    for model_name, cols_used in models_config.items():
        X = df_valid[cols_used].values
        if "std" in model_name:
            X = StandardScaler().fit_transform(X)
        lr = LogisticRegression(max_iter=1000, random_state=42).fit(X, Y)
        recomp_contrib[model_name] = compute_metrics(Y, lr.predict_proba(X)[:, 1])
        if "Model G" in model_name:
             logger.info(f"{model_name} AUC: {recomp_contrib[model_name]['auc']}")
        
    with open(REF_CONTRIB, "r") as f:
        ref_contrib_data = json.load(f)
    all_discrepancies.extend(compare_dicts(ref_contrib_data, recomp_contrib, "feature_contribution_audit"))

    # Final Output
    validation_results = {
        "total_discrepancies": len(all_discrepancies),
        "discrepancies": all_discrepancies,
        "recomputed_metrics": {
            "leakage_kill_test": recomp_leakage,
            "temporal_stability_audit": recomp_stability,
            "feature_contribution_audit": recomp_contrib
        }
    }
    
    os.makedirs("artifacts/aditya_l1", exist_ok=True)
    with open("artifacts/aditya_l1/trust_gate_validation.json", "w") as f:
        json.dump(validation_results, f, indent=2)
        
    print(f"Total Discrepancies: {len(all_discrepancies)}")
    for d in all_discrepancies:
        print(d)
        
    if len(all_discrepancies) == 0:
        print("VERDICT: PASS")
    else:
        print("VERDICT: FAIL")

if __name__ == "__main__":
    main()
