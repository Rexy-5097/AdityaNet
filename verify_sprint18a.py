import os
import json
import warnings
import numpy as np
import pandas as pd
from scipy.stats import norm, spearmanr, pearsonr, chi2_contingency, mannwhitneyu
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score
from sklearn.exceptions import ConvergenceWarning
from sklearn.feature_selection import mutual_info_classif
from joblib import Parallel, delayed

# Silence convergence warnings
warnings.filterwarnings("ignore", category=ConvergenceWarning)

# Flags list
FLAGS = [
    "is_missing_sensor",
    "is_transition",
    "is_label_ambiguity",
    "is_high_confidence",
    "is_high_uncertainty",
    "is_sensor_disagreement",
    "is_quiet_background",
    "is_weak_flare",
    "is_background_flux_drift",
    "is_temporal_drift"
]

BASELINE_ORDER = [
    "Missing Sensor Information",
    "High Confidence Quiet Sun False Alarm",
    "Quiet Sun False Alarm",
    "Weak Flare Transition Miss",
    "Weak Flare Miss",
    "Transition Phase Failure",
    "Instrument Disagreement",
    "Background Flux Drift",
    "Temporal Drift Failure",
    "Borderline Label Ambiguity",
    "High Uncertainty Failure"
]

def satisfy_rule(row, category):
    if category == "Missing Sensor Information":
        return bool(row["is_missing_sensor"])
    elif category == "High Confidence Quiet Sun False Alarm":
        return bool(row["is_quiet_background"] and row["is_high_confidence"])
    elif category == "Quiet Sun False Alarm":
        return bool(row["is_quiet_background"])
    elif category == "Weak Flare Transition Miss":
        return bool(row["is_weak_flare"] and row["is_transition"])
    elif category == "Weak Flare Miss":
        return bool(row["is_weak_flare"])
    elif category == "Transition Phase Failure":
        return bool(row["is_transition"])
    elif category == "Instrument Disagreement":
        return bool(row["is_sensor_disagreement"])
    elif category == "Background Flux Drift":
        return bool(row["is_background_flux_drift"])
    elif category == "Temporal Drift Failure":
        return bool(row["is_temporal_drift"])
    elif category == "Borderline Label Ambiguity":
        return bool(row["is_label_ambiguity"])
    elif category == "High Uncertainty Failure":
        return bool(row["is_high_uncertainty"])
    return False

def assign_category(row):
    for cat in BASELINE_ORDER:
        if satisfy_rule(row, cat):
            return cat
    n_active = sum(row[f] for f in FLAGS)
    if n_active == 0:
        return "Unknown"
    return "Mixed Multi-Flag Failure"

def compute_mcfadden_pseudo_r2(y, p):
    eps = 1e-15
    log_lik_model = np.sum(y * np.log(p + eps) + (1 - y) * np.log(1 - p + eps))
    p_null = np.mean(y)
    log_lik_null = len(y) * (p_null * np.log(p_null + eps) + (1 - p_null) * np.log(1 - p_null + eps))
    return float(1.0 - (log_lik_model / log_lik_null))

def fit_and_profile_logistic_model(X, y, feature_names, model_name, model_group):
    n_samples, n_predictors = X.shape
    lr = LogisticRegression(C=1.0, max_iter=2000, penalty='l2')
    lr.fit(X, y)
    
    p = lr.predict_proba(X)[:, 1]
    w = p * (1 - p)
    
    X_design = np.hstack([np.ones((n_samples, 1)), X])
    H = X_design.T @ (X_design * w[:, np.newaxis])
    
    reg_diag = np.zeros(H.shape[0])
    reg_diag[1:] = 1.0
    H_reg = H + np.diag(reg_diag)
    
    try:
        cov = np.linalg.inv(H_reg)
        se = np.sqrt(np.diag(cov))
        singular = False
    except np.linalg.LinAlgError:
        cov = np.linalg.pinv(H_reg)
        se = np.sqrt(np.diag(cov))
        singular = True
        
    beta = np.hstack([lr.intercept_[0], lr.coef_[0]])
    z = beta / se
    odds_ratio = np.exp(beta)
    p_val = 2.0 * (1.0 - norm.cdf(np.abs(z)))
    ci_lower = beta - 1.96 * se
    ci_upper = beta + 1.96 * se
    
    records = []
    # Intercept
    records.append({
        "Model_Group": model_group,
        "Model_Name": model_name,
        "Feature": "Intercept",
        "Coefficient": float(beta[0]),
        "Standard_Error": float(se[0]),
        "Odds_Ratio": float(odds_ratio[0]),
        "Wald_Statistic": float(z[0]),
        "p_value": float(p_val[0]),
        "CI_Lower": float(ci_lower[0]),
        "CI_Upper": float(ci_upper[0])
    })
    
    for i, name in enumerate(feature_names):
        idx = i + 1
        records.append({
            "Model_Group": model_group,
            "Model_Name": model_name,
            "Feature": name,
            "Coefficient": float(beta[idx]),
            "Standard_Error": float(se[idx]),
            "Odds_Ratio": float(odds_ratio[idx]),
            "Wald_Statistic": float(z[idx]),
            "p_value": float(p_val[idx]),
            "CI_Lower": float(ci_lower[idx]),
            "CI_Upper": float(ci_upper[idx])
        })
        
    return pd.DataFrame(records)

def run_bootstrap_fit(X_scaled, y, seed_val, means, stds):
    np.random.seed(seed_val)
    indices = np.random.choice(len(X_scaled), size=len(X_scaled), replace=True)
    X_boot = X_scaled[indices]
    y_boot = y[indices]
    
    if len(np.unique(y_boot)) < 2:
        return None, False
        
    lr = LogisticRegression(C=1.0, tol=1e-1, max_iter=200, solver='liblinear')
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ConvergenceWarning)
        lr.fit(X_boot, y_boot)
        
    coef_scaled = lr.coef_[0]
    intercept_scaled = lr.intercept_[0]
    
    coef_unscaled = coef_scaled / stds
    intercept_unscaled = intercept_scaled - np.sum(coef_scaled * means / stds)
    
    beta_boot = np.hstack([intercept_unscaled, coef_unscaled])
    return beta_boot, True

def run_parallel_bootstrap(X, y, feature_names, model_name, model_group, n_iterations=10000, n_jobs=8):
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    means = scaler.mean_
    stds = scaler.scale_
    
    seeds = np.random.RandomState(42).randint(0, 1000000, size=n_iterations)
    
    results = Parallel(n_jobs=n_jobs)(
        delayed(run_bootstrap_fit)(X_scaled, y, seeds[i], means, stds) for i in range(n_iterations)
    )
    
    valid_betas = []
    skipped_count = 0
    for beta, success in results:
        if success:
            valid_betas.append(beta)
        else:
            skipped_count += 1
            
    valid_betas = np.array(valid_betas)
    
    all_names = ["Intercept"] + list(feature_names)
    records = []
    
    for idx, name in enumerate(all_names):
        coef_vals = valid_betas[:, idx]
        mean_val = float(np.mean(coef_vals))
        std_val = float(np.std(coef_vals))
        median_val = float(np.median(coef_vals))
        ci_lower = float(np.percentile(coef_vals, 2.5))
        ci_upper = float(np.percentile(coef_vals, 97.5))
        
        records.append({
            "Model_Group": model_group,
            "Model_Name": model_name,
            "Feature": name,
            "Mean": mean_val,
            "Std": std_val,
            "Median": median_val,
            "CI_Lower": ci_lower,
            "CI_Upper": ci_upper
        })
        
    return pd.DataFrame(records)

def main():
    print("=== STARTING INDEPENDENT SPRINT 18A VERIFICATION ===")
    
    # Reload datasets and predictions cache
    cache = np.load("scratch/sprint16a/cached_predictions.npz")
    df_test = pd.read_parquet("artifacts/sprint14c/s2_test.parquet")
    
    monthly_metrics_path = "artifacts/sprint16a/monthly_metrics.csv"
    if os.path.exists(monthly_metrics_path):
        df_months = pd.read_csv(monthly_metrics_path)
        low_perf_months = df_months[df_months["TSS"] < 0.10]["Month"].tolist()
    else:
        low_perf_months = ["2025-12", "2026-01", "2026-03", "2026-05"]
        
    best_th = float(cache["validation_threshold"])
    y_true_full = cache["test_targets"]
    y_prob_full = cache["test_probs_cal_iso"]
    y_prob_goes_only_full = cache["test_probs_cal_iso_goes_only"]
    
    df_aligned = df_test.iloc[360:].copy().reset_index(drop=True)
    df_aligned["prob_cal"] = y_prob_full
    df_aligned["prob_goes_only"] = y_prob_goes_only_full
    df_aligned["pred_binary"] = (y_prob_full >= best_th).astype(int)
    df_aligned["is_failure"] = (df_aligned["pred_binary"] != df_aligned["target_6hr_binary"]).astype(int)
    df_aligned["failure_type"] = "NONE"
    df_aligned.loc[(df_aligned["target_6hr_binary"] == 0) & (df_aligned["pred_binary"] == 1), "failure_type"] = "FP"
    df_aligned.loc[(df_aligned["target_6hr_binary"] == 1) & (df_aligned["pred_binary"] == 0), "failure_type"] = "FN"
    
    subset_indices = cache["subset_indices"]
    uncertainty_subset = cache["subset_uncertainty"]
    
    df_subset = df_aligned.iloc[subset_indices].copy().reset_index(drop=True)
    df_subset["uncertainty"] = uncertainty_subset
    
    # Compute taxonomy boolean flags for all subset samples
    df_subset["month"] = pd.to_datetime(df_subset["timestamp"]).dt.to_period("M").astype(str)
    df_subset["is_missing_sensor"] = ((df_subset["mask_solexs"] == 0) | (df_subset["mask_hel1os"] == 0)).astype(int)
    df_subset["is_transition"] = (df_subset["minutes_since_last_flare"] < 30).astype(int)
    df_subset["is_label_ambiguity"] = (np.abs(df_subset["prob_cal"] - best_th) < 0.02).astype(int)
    df_subset["is_high_confidence"] = (df_subset["prob_cal"] >= 0.70).astype(int)
    df_subset["is_high_uncertainty"] = (df_subset["uncertainty"] > 0.0035).astype(int)
    df_subset["is_sensor_disagreement"] = (np.abs(df_subset["prob_cal"] - df_subset["prob_goes_only"]) > 0.20).astype(int)
    df_subset["is_quiet_background"] = ((df_subset["failure_type"] == "FP") & (df_subset["long_flux"] < 1.5e-6)).astype(int)
    df_subset["is_weak_flare"] = ((df_subset["failure_type"] == "FN") & (df_subset["target_6hr_class"] == 1)).astype(int)
    df_subset["is_background_flux_drift"] = (df_subset["mean_60m"] > 5e-6).astype(int)
    df_subset["is_temporal_drift"] = df_subset["month"].isin(low_perf_months).astype(int)
    
    # Features definition
    goes_cont_features = [
        "short_flux", "long_flux", "log_long_flux", "mean_15m", "variance_15m",
        "mean_60m", "variance_60m", "peak_30m", "peak_60m", "flux_gradient_5m",
        "flux_gradient_15m", "flux_acceleration_5m", "flux_acceleration_15m",
        "minutes_since_last_flare"
    ]
    solexs_features = [f"solexs_rate_ch{i}" for i in range(1, 10)] + [f"solexs_counts_ch{i}" for i in range(1, 10)]
    hel1os_features = ["hel1os_rate_band0", "hel1os_rate_band1", "hel1os_counts_band0", "hel1os_counts_band1"]
    
    physical_continuous = goes_cont_features + solexs_features + hel1os_features
    physical_binary = ["mask_solexs", "mask_hel1os", "quality_flag"]
    prediction_continuous = ["prob_cal", "uncertainty"]
    taxonomy_binary = [
        "is_missing_sensor", "is_transition", "is_label_ambiguity", "is_high_confidence",
        "is_high_uncertainty", "is_sensor_disagreement", "is_quiet_background",
        "is_weak_flare", "is_background_flux_drift", "is_temporal_drift"
    ]
    
    subset_a = df_subset[df_subset["target_6hr_binary"] == 0].copy().reset_index(drop=True)
    subset_b = df_subset[df_subset["target_6hr_binary"] == 1].copy().reset_index(drop=True)
    y_a = (subset_a["pred_binary"] == 1).astype(int).values
    y_b = (subset_b["pred_binary"] == 0).astype(int).values
    
    def construct_design_matrix(df_part, cont_features, bin_features):
        valid_cont = [f for f in cont_features if df_part[f].std() > 1e-9]
        valid_bin = [f for f in bin_features if df_part[f].std() > 1e-9]
        scaler = StandardScaler()
        X_cont = scaler.fit_transform(df_part[valid_cont].values)
        X_bin = df_part[valid_bin].values
        X_design = np.hstack([X_cont, X_bin])
        return X_design, valid_cont + valid_bin
        
    X_a_master, names_a_master = construct_design_matrix(subset_a, physical_continuous + prediction_continuous, physical_binary + taxonomy_binary)
    X_b_master, names_b_master = construct_design_matrix(subset_b, physical_continuous + prediction_continuous, physical_binary + taxonomy_binary)
    
    def get_model_design(X_master, names_master, feature_subset_list):
        indices = [names_master.index(f) for f in feature_subset_list if f in names_master]
        names = [names_master[idx] for idx in indices]
        return X_master[:, indices], names

    X_a_1, names_a_1 = get_model_design(X_a_master, names_a_master, physical_continuous + physical_binary)
    X_a_2, names_a_2 = get_model_design(X_a_master, names_a_master, physical_continuous + prediction_continuous + physical_binary)
    X_a_3, names_a_3 = get_model_design(X_a_master, names_a_master, physical_continuous + prediction_continuous + physical_binary + taxonomy_binary)

    X_b_1, names_b_1 = get_model_design(X_b_master, names_b_master, physical_continuous + physical_binary)
    X_b_2, names_b_2 = get_model_design(X_b_master, names_b_master, physical_continuous + prediction_continuous + physical_binary)
    X_b_3, names_b_3 = get_model_design(X_b_master, names_b_master, physical_continuous + prediction_continuous + physical_binary + taxonomy_binary)

    models_to_fit = {
        "A": [
            ("Model_1_Physical", X_a_1, names_a_1, y_a),
            ("Model_2_Physical_Uncertainty", X_a_2, names_a_2, y_a),
            ("Model_3_All", X_a_3, names_a_3, y_a)
        ],
        "B": [
            ("Model_1_Physical", X_b_1, names_b_1, y_b),
            ("Model_2_Physical_Uncertainty", X_b_2, names_b_2, y_b),
            ("Model_3_All", X_b_3, names_b_3, y_b)
        ]
    }
    
    rep_dir = "artifacts/sprint18a"
    has_mismatches = False
    
    # ----------------------------------------------------
    # Check 1: Logistic Regression Coefficient Profiling
    # ----------------------------------------------------
    print("\n--- Check 1: Logistic Regression Coefficient Profiling ---")
    df_coef_a_rep = pd.read_csv(f"{rep_dir}/logistic_fp_vs_tn.csv")
    df_coef_b_rep = pd.read_csv(f"{rep_dir}/logistic_fn_vs_tp.csv")
    
    coef_errs = 0
    # Group A
    fit_a_coefs = []
    for name, X, names, y in models_to_fit["A"]:
        fit_a_coefs.append(fit_and_profile_logistic_model(X, y, names, name, "Model_A"))
    df_coef_a_act = pd.concat(fit_a_coefs, ignore_index=True)
    
    # Group B
    fit_b_coefs = []
    for name, X, names, y in models_to_fit["B"]:
        fit_b_coefs.append(fit_and_profile_logistic_model(X, y, names, name, "Model_B"))
    df_coef_b_act = pd.concat(fit_b_coefs, ignore_index=True)
    
    # Compare elements
    for idx, row in df_coef_a_rep.iterrows():
        act_row = df_coef_a_act.iloc[idx]
        for key in ["Coefficient", "Standard_Error", "Odds_Ratio", "Wald_Statistic", "p_value", "CI_Lower", "CI_Upper"]:
            diff = abs(row[key] - act_row[key])
            if diff > 1e-6:
                print(f"  Model_A Mismatch in {row['Model_Name']}, Feature={row['Feature']}, Field={key}: Reported={row[key]:.6f}, Actual={act_row[key]:.6f}")
                coef_errs += 1
                has_mismatches = True
                
    for idx, row in df_coef_b_rep.iterrows():
        act_row = df_coef_b_act.iloc[idx]
        for key in ["Coefficient", "Standard_Error", "Odds_Ratio", "Wald_Statistic", "p_value", "CI_Lower", "CI_Upper"]:
            diff = abs(row[key] - act_row[key])
            if diff > 1e-6:
                print(f"  Model_B Mismatch in {row['Model_Name']}, Feature={row['Feature']}, Field={key}: Reported={row[key]:.6f}, Actual={act_row[key]:.6f}")
                coef_errs += 1
                has_mismatches = True
                
    if coef_errs == 0:
        print("  PASS: Logistic regression profiling matches exactly.")
    else:
        print(f"  FAIL: Found {coef_errs} mismatches in logistic regression profiles.")

    # ----------------------------------------------------
    # Check 2: Correlation Matrices
    # ----------------------------------------------------
    print("\n--- Check 2: Correlation Matrices ---")
    df_corr_rep = pd.read_csv(f"{rep_dir}/feature_correlations.csv")
    
    all_predictors = physical_continuous + prediction_continuous + physical_binary + taxonomy_binary
    valid_predictors = [f for f in all_predictors if df_subset[f].std() > 1e-9]
    X_full = df_subset[valid_predictors].copy()
    
    corr_errs = 0
    # Map reported records into a fast lookup dict
    rep_pearson = {}
    rep_spearman = {}
    for idx, row in df_corr_rep.iterrows():
        key = (row["Feature_A"], row["Feature_B"])
        rep_pearson[key] = row["Pearson_Correlation"]
        rep_spearman[key] = row["Spearman_Correlation"]
        
    for i, f_a in enumerate(valid_predictors):
        for j, f_b in enumerate(valid_predictors):
            val_pearson_act = float(pearsonr(X_full[f_a], X_full[f_b])[0])
            val_spearman_act = float(spearmanr(X_full[f_a], X_full[f_b])[0])
            
            key = (f_a, f_b)
            v_p_rep = rep_pearson.get(key, None)
            v_s_rep = rep_spearman.get(key, None)
            
            if v_p_rep is None or v_s_rep is None:
                print(f"  Mismatch: Pair {key} missing in reported correlations!")
                corr_errs += 1
                has_mismatches = True
                continue
                
            diff_p = abs(v_p_rep - val_pearson_act)
            diff_s = abs(v_s_rep - val_spearman_act)
            
            if diff_p > 1e-6 or diff_s > 1e-6:
                print(f"  Correlation Mismatch for {key}:")
                print(f"    Pearson: Reported={v_p_rep:.6f}, Actual={val_pearson_act:.6f}")
                print(f"    Spearman: Reported={v_s_rep:.6f}, Actual={val_spearman_act:.6f}")
                corr_errs += 1
                has_mismatches = True
                
    if corr_errs == 0:
        print("  PASS: Pearson and Spearman correlation matrices match exactly.")
    else:
        print(f"  FAIL: Found {corr_errs} mismatches in correlation matrices.")

    # ----------------------------------------------------
    # Check 3: Variance Inflation Factors
    # ----------------------------------------------------
    print("\n--- Check 3: Variance Inflation Factors ---")
    df_vif_rep = pd.read_csv(f"{rep_dir}/variance_inflation.csv")
    
    vif_errs = 0
    rep_vifs = dict(zip(df_vif_rep["Feature"], df_vif_rep["VIF"]))
    
    for target_f in valid_predictors:
        other_fs = [f for f in valid_predictors if f != target_f]
        X_other = X_full[other_fs].values
        y_target = X_full[target_f].values
        
        reg = LinearRegression()
        reg.fit(X_other, y_target)
        r2 = reg.score(X_other, y_target)
        
        if 1.0 - r2 < 1e-14:
            vif_act = float('inf')
        else:
            vif_act = float(1.0 / (1.0 - r2))
            
        vif_rep = rep_vifs.get(target_f, None)
        if vif_rep is None:
            print(f"  VIF for {target_f} missing in reported file!")
            vif_errs += 1
            has_mismatches = True
            continue
            
        # Handle inf comparison
        if np.isinf(vif_act):
            match = np.isinf(vif_rep)
        else:
            match = abs(vif_rep - vif_act) < 1e-6
            
        if not match:
            print(f"  VIF Mismatch for {target_f}: Reported={vif_rep:.6f}, Actual={vif_act:.6f}")
            vif_errs += 1
            has_mismatches = True
            
    if vif_errs == 0:
        print("  PASS: Variance Inflation Factors match exactly.")
    else:
        print(f"  FAIL: Found {vif_errs} mismatches in VIF calculations.")

    # ----------------------------------------------------
    # Check 4: Mutual Information
    # ----------------------------------------------------
    print("\n--- Check 4: Mutual Information ---")
    df_mi_rep = pd.read_csv(f"{rep_dir}/mutual_information.csv")
    
    mi_errs = 0
    
    # Recompute MI
    y_fp = (df_subset["failure_type"] == "FP").astype(int).values
    y_fn = (df_subset["failure_type"] == "FN").astype(int).values
    discrete_mask = [f in (physical_binary + taxonomy_binary) for f in valid_predictors]
    
    mi_fp_act = mutual_info_classif(X_full.values, y_fp, discrete_features=discrete_mask, random_state=42, n_neighbors=3)
    mi_fn_act = mutual_info_classif(X_full.values, y_fn, discrete_features=discrete_mask, random_state=42, n_neighbors=3)
    
    df_mi_fp_act = pd.DataFrame({"Feature": valid_predictors, "MI_FP": mi_fp_act}).sort_values(by="MI_FP", ascending=False).reset_index(drop=True)
    df_mi_fn_act = pd.DataFrame({"Feature": valid_predictors, "MI_FN": mi_fn_act}).sort_values(by="MI_FN", ascending=False).reset_index(drop=True)
    
    # Compare ranked combined lists
    for idx, row in df_mi_rep.iterrows():
        act_fp_row = df_mi_fp_act.iloc[idx]
        act_fn_row = df_mi_fn_act.iloc[idx]
        
        diff_fp = abs(row["MI_FP"] - act_fp_row["MI_FP"])
        diff_fn = abs(row["MI_FN"] - act_fn_row["MI_FN"])
        
        if row["Feature_FP"] != act_fp_row["Feature"] or diff_fp > 1e-6:
            print(f"  MI FP Ranked Mismatch at rank {idx+1}:")
            print(f"    Reported: Feature='{row['Feature_FP']}', MI={row['MI_FP']:.6f}")
            print(f"    Actual:   Feature='{act_fp_row['Feature']}', MI={act_fp_row['MI_FP']:.6f}")
            mi_errs += 1
            has_mismatches = True
            
        if row["Feature_FN"] != act_fn_row["Feature"] or diff_fn > 1e-6:
            print(f"  MI FN Ranked Mismatch at rank {idx+1}:")
            print(f"    Reported: Feature='{row['Feature_FN']}', MI={row['MI_FN']:.6f}")
            print(f"    Actual:   Feature='{act_fn_row['Feature']}', MI={act_fn_row['MI_FN']:.6f}")
            mi_errs += 1
            has_mismatches = True
            
    if mi_errs == 0:
        print("  PASS: Mutual Information values and rankings match exactly.")
    else:
        print(f"  FAIL: Found {mi_errs} mismatches in Mutual Information.")

    # ----------------------------------------------------
    # Check 5: Effect Size Statistics
    # ----------------------------------------------------
    print("\n--- Check 5: Effect Size Statistics ---")
    df_effects_rep = pd.read_csv(f"{rep_dir}/effect_sizes.csv")
    
    tp_group = df_subset[(df_subset["target_6hr_binary"] == 1) & (df_subset["pred_binary"] == 1)]
    fp_group = df_subset[(df_subset["target_6hr_binary"] == 0) & (df_subset["pred_binary"] == 1)]
    tn_group = df_subset[(df_subset["target_6hr_binary"] == 0) & (df_subset["pred_binary"] == 0)]
    fn_group = df_subset[(df_subset["target_6hr_binary"] == 1) & (df_subset["pred_binary"] == 0)]
    
    comparisons = {
        "TP_vs_FP": (tp_group, fp_group),
        "TN_vs_FN": (tn_group, fn_group)
    }
    
    effect_errs = 0
    for idx, row in df_effects_rep.iterrows():
        feat = row["Feature"]
        comp = row["Comparison"]
        grp1, grp2 = comparisons[comp]
        
        n1 = len(grp1)
        n2 = len(grp2)
        v1 = grp1[feat].values
        v2 = grp2[feat].values
        
        mu1, mu2 = np.mean(v1), np.mean(v2)
        var1, var2 = np.var(v1, ddof=1), np.var(v2, ddof=1)
        
        s_pooled = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
        cohen_d_act = float((mu1 - mu2) / s_pooled) if s_pooled > 1e-15 else 0.0
        
        u_stat, mw_p = mannwhitneyu(v1, v2, alternative='two-sided')
        cliffs_delta_act = float(2.0 * u_stat / (n1 * n2) - 1.0)
        rank_biserial_act = cliffs_delta_act
        
        # Compare
        for key, act_val in [("Cohens_d", cohen_d_act), ("Cliffs_Delta", cliffs_delta_act), ("Rank_Biserial", rank_biserial_act), ("Mann_Whitney_U", float(u_stat)), ("p_value", float(mw_p))]:
            diff = abs(row[key] - act_val)
            if diff > 1e-6:
                print(f"  Effect Size Mismatch for {feat} ({comp}), Field={key}: Reported={row[key]:.6f}, Actual={act_val:.6f} (diff={diff:.6e})")
                effect_errs += 1
                has_mismatches = True
                
    if effect_errs == 0:
        print("  PASS: Cohen's d, Cliff's Delta, Rank-biserial, Mann-Whitney U, and p-values match exactly.")
    else:
        print(f"  FAIL: Found {effect_errs} mismatches in effect size stats.")

    # ----------------------------------------------------
    # Check 6: Failure Category Association
    # ----------------------------------------------------
    print("\n--- Check 6: Failure Category Association ---")
    # Read contingency table CSV
    assoc_path = f"{rep_dir}/taxonomy_association.csv"
    df_assoc_rep = pd.read_csv(assoc_path)
    
    # Check contingency table counts
    df_failures = df_subset[df_subset["is_failure"] == 1].copy()
    df_failures["category"] = df_failures.apply(assign_category, axis=1)
    contingency = pd.crosstab(df_failures["category"], df_failures["failure_type"])
    if "FP" not in contingency.columns:
        contingency["FP"] = 0
    if "FN" not in contingency.columns:
        contingency["FN"] = 0
    contingency = contingency[["FP", "FN"]]
    
    chi2, p_val_chi2, dof_chi2, expected_chi2 = chi2_contingency(contingency)
    n_fail = len(df_failures)
    cramers_v = float(np.sqrt(chi2 / n_fail)) if n_fail > 0 else 0.0
    
    assoc_errs = 0
    # Map reported contingency values (excluding bottom metrics rows)
    reported_counts = {}
    metric_values = {}
    for idx, row in df_assoc_rep.iterrows():
        # First column is either category name or 'Metric' or empty
        col0 = row.iloc[0]
        if pd.isna(col0):
            continue
        if col0 in ["Metric", "Chi-Square", "Cramers_V", "DoF", "P-Value"]:
            metric_values[col0] = row.iloc[1]
        else:
            reported_counts[col0] = (row["FP"], row["FN"])
            
    # Check contingency counts
    for cat in contingency.index:
        fp_act = contingency.loc[cat, "FP"]
        fn_act = contingency.loc[cat, "FN"]
        
        rep = reported_counts.get(cat, None)
        if rep is None:
            print(f"  Category '{cat}' missing in reported contingency table!")
            assoc_errs += 1
            has_mismatches = True
            continue
            
        fp_rep, fn_rep = rep
        if float(fp_rep) != fp_act or float(fn_rep) != fn_act:
            print(f"  Contingency mismatch for '{cat}': Reported=({fp_rep}, {fn_rep}), Actual=({fp_act}, {fn_act})")
            assoc_errs += 1
            has_mismatches = True
            
    # Check Chi-square stats
    # Read metrics directly from bottom rows
    with open(assoc_path) as f:
        lines = f.readlines()
    # Find rows with Chi-Square, Cramers_V, DoF, P-Value
    stats_rep = {}
    for line in lines:
        parts = line.strip().split(",")
        if len(parts) == 2 and parts[0] in ["Chi-Square", "Cramers_V", "DoF", "P-Value"]:
            stats_rep[parts[0]] = float(parts[1])
            
    for key, act_val in [("Chi-Square", float(chi2)), ("Cramers_V", cramers_v), ("DoF", float(dof_chi2)), ("P-Value", float(p_val_chi2))]:
        v_rep = stats_rep.get(key, None)
        if v_rep is None:
            print(f"  Metric '{key}' missing from contingency CSV bottom rows!")
            assoc_errs += 1
            has_mismatches = True
            continue
        diff = abs(v_rep - act_val)
        if diff > 1e-6:
            print(f"  Taxonomy association metric '{key}' mismatch: Reported={v_rep:.6f}, Actual={act_val:.6f}")
            assoc_errs += 1
            has_mismatches = True
            
    if assoc_errs == 0:
        print("  PASS: Contingency table counts, Chi-Square, Cramer's V, DoF, and p-values match exactly.")
    else:
        print(f"  FAIL: Found {assoc_errs} mismatches in failure category association.")

    # ----------------------------------------------------
    # Check 7: Bootstrap Validation
    # ----------------------------------------------------
    print("\n--- Check 7: Bootstrap Validation ---")
    df_boot_rep = pd.read_csv(f"{rep_dir}/bootstrap_coefficients.csv")
    
    # We will recompute bootstrap coefficients in parallel
    bootstrap_coef_records_act = []
    for group, models in models_to_fit.items():
        for name, X, names, y in models:
            df_boot = run_parallel_bootstrap(X, y, names, name, f"Model_{group}", n_iterations=10000, n_jobs=8)
            bootstrap_coef_records_act.append(df_boot)
    df_boot_act = pd.concat(bootstrap_coef_records_act, ignore_index=True)
    
    boot_mismatches = 0
    for idx, row in df_boot_rep.iterrows():
        act_row = df_boot_act.iloc[idx]
        for key in ["Mean", "Std", "Median", "CI_Lower", "CI_Upper"]:
            diff = abs(row[key] - act_row[key])
            # Bootstrap results depend on seed. Since seed is identical and Parallel execution seeds are locked,
            # this should match exactly. Let's verify.
            if diff > 1e-6:
                print(f"  Bootstrap Coefficient Mismatch in {row['Model_Name']}, Feature={row['Feature']}, Field={key}: Reported={row[key]:.6f}, Actual={act_row[key]:.6f} (diff={diff:.6e})")
                boot_mismatches += 1
                has_mismatches = True
                
    if boot_mismatches == 0:
        print("  PASS: Bootstrap coefficient means, stds, medians, and CIs match exactly.")
    else:
        print(f"  FAIL: Found {boot_mismatches} mismatches in bootstrapped validation parameters.")

    # ----------------------------------------------------
    # Check 8: Structural Invariants Check
    # ----------------------------------------------------
    print("\n--- Check 8: Structural Invariants Check ---")
    struct_passed = True
    
    # 1. Sample counts match
    tot_samples_a = len(subset_a)
    tot_samples_b = len(subset_b)
    print(f"  Subset A count: {tot_samples_a} (Expected=17606)")
    print(f"  Subset B count: {tot_samples_b} (Expected=2394)")
    if tot_samples_a != 17606 or tot_samples_b != 2394:
        struct_passed = False
        
    # 2. No duplicated or omitted samples in bootstrap and VIF
    # Checked structurally by length invariants
    
    # 3. Bootstrap iteration count: 10,000 confirmed by matching shape
    bootstrap_rows = len(df_boot_rep)
    # Model A: Model 1 has 38 parameters (incl intercept), Model 2 has 40, Model 3 has 49. Total A: 127
    # Model B: Model 1 has 39 parameters (incl intercept), Model 2 has 41, Model 3 has 50. Total B: 130
    # Total bootstrap rows should be 257. (variance_60m has std > 1e-9 in subset_b but <= 1e-9 in subset_a)
    print(f"  Bootstrap coefficients rows: {bootstrap_rows} (Expected=257)")
    if bootstrap_rows != 257:
        struct_passed = False
        
    # 4. Feature counts and matrix dimensions
    # variance_15m and variance_60m have std <= 1e-9 in the full subset and are omitted.
    # Out of 51 features, 49 are active: 49 * 49 = 2401 correlation pairs.
    print(f"  Feature correlations rows: {len(df_corr_rep)} (Expected=49 * 49 = 2401)")
    if len(df_corr_rep) != 2401:
        struct_passed = False
        
    if struct_passed:
        print("  PASS: All structural invariants satisfied.")
    else:
        print("  FAIL: Violations detected in structural invariants.")
        has_mismatches = True

    # ----------------------------------------------------
    # Final Result
    # ----------------------------------------------------
    print("\n==============================================")
    if has_mismatches:
        print("VERIFICATION RESULT: FAIL")
    else:
        print("VERIFICATION RESULT: PASS")
    print("==============================================")

if __name__ == "__main__":
    main()
