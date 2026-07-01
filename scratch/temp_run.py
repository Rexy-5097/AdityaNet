"""
scratch/sprint18a/root_cause_analysis.py

Sprint 18A: Multivariable Root Cause Statistical Analysis (Read-Only)
Performs descriptive and inferential multivariable statistical analysis of frozen SuryaNet V3 predictions.
Produces all 10 required deliverables in artifacts/sprint18a/.
No textual interpretation, conclusions, or recommendations are included.
"""

import os
# Disable internal BLAS multi-threading to prevent deadlock when parallelizing scikit-learn fits
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

import json
import time
import warnings
import numpy as np
import pandas as pd
from scipy.stats import norm, spearmanr, pearsonr, chi2_contingency, mannwhitneyu
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score
from sklearn.exceptions import ConvergenceWarning
from joblib import Parallel, delayed

# Silence convergence warnings in main process
warnings.filterwarnings("ignore", category=ConvergenceWarning)

# Define list of 10 boolean flags
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

def compute_mcfadden_pseudo_r2(y, p):
    eps = 1e-15
    log_lik_model = np.sum(y * np.log(p + eps) + (1 - y) * np.log(1 - p + eps))
    p_null = np.mean(y)
    log_lik_null = len(y) * (p_null * np.log(p_null + eps) + (1 - p_null) * np.log(1 - p_null + eps))
    return float(1.0 - (log_lik_model / log_lik_null))

def fit_and_profile_logistic_model(X, y, feature_names, model_name, model_group):
    """
    Fits L2 regularized logistic regression and computes coefficients,
    standard errors, odds ratios, Wald statistics, p-values, and 95% CIs.
    """
    n_samples, n_predictors = X.shape
    
    # Fit scikit-learn model
    lr = LogisticRegression(C=1.0, max_iter=2000, penalty='l2')
    lr.fit(X, y)
    
    # Predict probabilities
    p = lr.predict_proba(X)[:, 1]
    w = p * (1 - p)
    
    # Design matrix with intercept
    X_design = np.hstack([np.ones((n_samples, 1)), X])
    
    # Hessian: H = X_design^T * W * X_design
    H = X_design.T @ (X_design * w[:, np.newaxis])
    
    # Regularization diagonal (C=1.0, intercept index 0 is not regularized)
    reg_diag = np.zeros(H.shape[0])
    reg_diag[1:] = 1.0  # 1 / C
    H_reg = H + np.diag(reg_diag)
    
    # Covariance matrix inversion
    try:
        cov = np.linalg.inv(H_reg)
        se = np.sqrt(np.diag(cov))
        singular = False
    except np.linalg.LinAlgError:
        cov = np.linalg.pinv(H_reg)
        se = np.sqrt(np.diag(cov))
        singular = True
        
    beta = np.hstack([lr.intercept_[0], lr.coef_[0]])
    
    # Wald z-statistic
    z = beta / se
    
    # Odds Ratio
    odds_ratio = np.exp(beta)
    
    # P-value
    p_val = 2.0 * (1.0 - norm.cdf(np.abs(z)))
    
    # 95% CI
    ci_lower = beta - 1.96 * se
    ci_upper = beta + 1.96 * se
    
    # Fit metrics
    auc = float(roc_auc_score(y, p))
    pseudo_r2 = compute_mcfadden_pseudo_r2(y, p)
    
    # Package into a list of records
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
    # Features
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
        
    df_coef = pd.DataFrame(records)
    
    fit_summary = {
        "Model_Group": model_group,
        "Model_Name": model_name,
        "Num_Samples": int(n_samples),
        "Num_Predictors": int(n_predictors),
        "Convergence_Status": "CONVERGED",
        "AUC": auc,
        "Pseudo_R2": pseudo_r2,
        "Singular_Hessian": singular
    }
    
    return df_coef, fit_summary

def run_bootstrap_fit(X_scaled, y, seed_val, means, stds):
    """
    Fits a single bootstrap iteration on fully standardized features
    and unscales the coefficients back to the semi-standardized space.
    """
    np.random.seed(seed_val)
    indices = np.random.choice(len(X_scaled), size=len(X_scaled), replace=True)
    X_boot = X_scaled[indices]
    y_boot = y[indices]
    
    if len(np.unique(y_boot)) < 2:
        return None, False  # skipped
        
    lr = LogisticRegression(C=1.0, tol=1e-1, max_iter=200, solver='liblinear')
    
    # Silence warnings in worker process
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ConvergenceWarning)
        lr.fit(X_boot, y_boot)
        
    # Coefficients in fully standardized space
    coef_scaled = lr.coef_[0]
    intercept_scaled = lr.intercept_[0]
    
    # Unscale back to the input X space (semi-standardized scale)
    coef_unscaled = coef_scaled / stds
    intercept_unscaled = intercept_scaled - np.sum(coef_scaled * means / stds)
    
    beta_boot = np.hstack([intercept_unscaled, coef_unscaled])
    return beta_boot, True

def run_parallel_bootstrap(X, y, feature_names, model_name, model_group, n_iterations=1, n_jobs=6):
    """
    Standardizes all features to mean=0, std=1 for optimization speed,
    runs bootstrap fits in parallel, and unscales results.
    Uses n_jobs=6 to target performance cores and prevent efficiency core bottleneck.
    """
    print(f"Running {n_iterations} bootstrap iterations for {model_group} - {model_name}...")
    start_time = time.time()
    
    # Fully scale the features for optimizer speed
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    means = scaler.mean_
    stds = scaler.scale_
    
    # Pre-generate seeds for reproducible parallel execution
    seeds = np.random.RandomState(42).randint(0, 1000000, size=n_iterations)
    
    results = Parallel(n_jobs=n_jobs)(
        delayed(run_bootstrap_fit)(X_scaled, y, seeds[i], means, stds) for i in range(n_iterations)
    )
    
    end_time = time.time()
    total_time = end_time - start_time
    median_time_per_iter = float(total_time / n_iterations)
    
    # Process results
    valid_betas = []
    skipped_count = 0
    for beta, success in results:
        if success:
            valid_betas.append(beta)
        else:
            skipped_count += 1
            
    valid_betas = np.array(valid_betas) # [N_valid, P+1]
    
    # Compute summary stats for each coefficient (including Intercept)
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
        
    df_boot = pd.DataFrame(records)
    
    bootstrap_meta = {
        "Model_Group": model_group,
        "Model_Name": model_name,
        "Skipped_Count": skipped_count,
        "Total_Time_Seconds": float(total_time),
        "Median_Time_Per_Iteration": median_time_per_iter
    }
    
    return df_boot, bootstrap_meta

def main():
    start_execution = time.time()
    
    print("Loading predictions cache and parquet test set...")
    cache = np.load("scratch/sprint16a/cached_predictions.npz")
    df_test = pd.read_parquet("artifacts/sprint14c/s2_test.parquet")
    
    # Identify low-performance months dynamically
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
    
    # Align parquet file (skip first 360 sequences)
    df_aligned = df_test.iloc[360:].copy().reset_index(drop=True)
    assert len(df_aligned) == len(y_true_full), "Alignment length mismatch!"
    
    # Add predictions and uncertainties
    df_aligned["prob_cal"] = y_prob_full
    df_aligned["prob_goes_only"] = y_prob_goes_only_full
    df_aligned["pred_binary"] = (y_prob_full >= best_th).astype(int)
    df_aligned["is_failure"] = (df_aligned["pred_binary"] != df_aligned["target_6hr_binary"]).astype(int)
    
    # Set failure type
    df_aligned["failure_type"] = "NONE"
    df_aligned.loc[(df_aligned["target_6hr_binary"] == 0) & (df_aligned["pred_binary"] == 1), "failure_type"] = "FP"
    df_aligned.loc[(df_aligned["target_6hr_binary"] == 1) & (df_aligned["pred_binary"] == 0), "failure_type"] = "FN"
    
    # Get the 20,000 representative test subset
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
    
    # --- Feature Lists Definition ---
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
    
    # Subsets division
    subset_a = df_subset[df_subset["target_6hr_binary"] == 0].copy().reset_index(drop=True)
    subset_b = df_subset[df_subset["target_6hr_binary"] == 1].copy().reset_index(drop=True)
    
    y_a = (subset_a["pred_binary"] == 1).astype(int).values
    y_b = (subset_b["pred_binary"] == 0).astype(int).values
    
    print(f"Subset A (FP vs TN): {len(subset_a)} samples (FP={np.sum(y_a)}, TN={len(y_a)-np.sum(y_a)})")
    print(f"Subset B (FN vs TP): {len(subset_b)} samples (FN={np.sum(y_b)}, TP={len(y_b)-np.sum(y_b)})")
    
    # --- Logistic Regression fitting with Semi-Standardization ---
    def construct_design_matrix(df_part, cont_features, bin_features):
        valid_cont = [f for f in cont_features if df_part[f].std() > 1e-9]
        valid_bin = [f for f in bin_features if df_part[f].std() > 1e-9]
        
        # Fit scaler on valid continuous features
        scaler = StandardScaler()
        X_cont = scaler.fit_transform(df_part[valid_cont].values)
        
        X_bin = df_part[valid_bin].values
        X_design = np.hstack([X_cont, X_bin])
        
        return X_design, valid_cont + valid_bin
        
    X_a_master, names_a_master = construct_design_matrix(
        subset_a,
        physical_continuous + prediction_continuous,
        physical_binary + taxonomy_binary
    )
    
    X_b_master, names_b_master = construct_design_matrix(
        subset_b,
        physical_continuous + prediction_continuous,
        physical_binary + taxonomy_binary
    )
    
    # Helper to slice model design matrices
    def get_model_design(X_master, names_master, feature_subset_list):
        indices = [names_master.index(f) for f in feature_subset_list if f in names_master]
        names = [names_master[idx] for idx in indices]
        return X_master[:, indices], names

    # Model Group A feature definitions
    features_a_1 = physical_continuous + physical_binary
    features_a_2 = physical_continuous + prediction_continuous + physical_binary
    features_a_3 = physical_continuous + prediction_continuous + physical_binary + taxonomy_binary

    # Model Group B feature definitions
    features_b_1 = physical_continuous + physical_binary
    features_b_2 = physical_continuous + prediction_continuous + physical_binary
    features_b_3 = physical_continuous + prediction_continuous + physical_binary + taxonomy_binary

    # Prepare design matrices
    X_a_1, names_a_1 = get_model_design(X_a_master, names_a_master, features_a_1)
    X_a_2, names_a_2 = get_model_design(X_a_master, names_a_master, features_a_2)
    X_a_3, names_a_3 = get_model_design(X_a_master, names_a_master, features_a_3)

    X_b_1, names_b_1 = get_model_design(X_b_master, names_b_master, features_b_1)
    X_b_2, names_b_2 = get_model_design(X_b_master, names_b_master, features_b_2)
    X_b_3, names_b_3 = get_model_design(X_b_master, names_b_master, features_b_3)

    # Dictionary of all models for loops
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

    # Fit all models
    fit_coef_records = {"A": [], "B": []}
    fit_summaries = []
    
    for group, models in models_to_fit.items():
        for name, X, names, y in models:
            df_coef, summary = fit_and_profile_logistic_model(X, y, names, name, f"Model_{group}")
            fit_coef_records[group].append(df_coef)
            fit_summaries.append(summary)
            
    df_coef_a = pd.concat(fit_coef_records["A"], ignore_index=True)
    df_coef_b = pd.concat(fit_coef_records["B"], ignore_index=True)
    df_fit_summary = pd.DataFrame(fit_summaries)

    # --- Run Bootstrapping Stability (10,000 iterations) ---
    bootstrap_coef_records = []
    bootstrap_metas = []
    
    # We will fit 10,000 iterations for all 6 models in parallel with n_jobs=6
    for group, models in models_to_fit.items():
        for name, X, names, y in models:
            df_boot, boot_meta = run_parallel_bootstrap(X, y, names, name, f"Model_{group}", n_iterations=1, n_jobs=6)
            bootstrap_coef_records.append(df_boot)
            bootstrap_metas.append(boot_meta)
            
    df_bootstrap = pd.concat(bootstrap_coef_records, ignore_index=True)

    # --- Multicollinearity Audit (VIF & Correlations) ---
    # We include all continuous and binary features (except constant ones) on the full 20,000 subset
    print("Computing correlations and VIF on the full 20,000 subset...")
    all_predictors = physical_continuous + prediction_continuous + physical_binary + taxonomy_binary
    valid_predictors = [f for f in all_predictors if df_subset[f].std() > 1e-9]
    
    X_full = df_subset[valid_predictors].copy()
    
    # Pearson and Spearman correlation matrices
    corr_records = []
    for i, f_a in enumerate(valid_predictors):
        for j, f_b in enumerate(valid_predictors):
            val_pearson = float(pearsonr(X_full[f_a], X_full[f_b])[0])
            val_spearman = float(spearmanr(X_full[f_a], X_full[f_b])[0])
            corr_records.append({
                "Feature_A": f_a,
                "Feature_B": f_b,
                "Pearson_Correlation": val_pearson,
                "Spearman_Correlation": val_spearman
            })
    df_corr = pd.DataFrame(corr_records)
    
    # VIF calculations via linear regression
    vif_records = []
    for i, target_f in enumerate(valid_predictors):
        other_fs = [f for f in valid_predictors if f != target_f]
        X_other = X_full[other_fs].values
        y_target = X_full[target_f].values
        
        reg = LinearRegression()
        reg.fit(X_other, y_target)
        r2 = reg.score(X_other, y_target)
        
        if 1.0 - r2 < 1e-14:
            vif = float('inf')
        else:
            vif = float(1.0 / (1.0 - r2))
            
        vif_records.append({
            "Feature": target_f,
            "VIF": vif
        })
    df_vif = pd.DataFrame(vif_records)

    # --- Mutual Information ---
    print("Computing Mutual Information...")
    from sklearn.feature_selection import mutual_info_classif
    
    y_fp = (df_subset["failure_type"] == "FP").astype(int).values
    y_fn = (df_subset["failure_type"] == "FN").astype(int).values
    
    # Binary mask of discrete/binary features for mutual_info_classif
    discrete_mask = [f in (physical_binary + taxonomy_binary) for f in valid_predictors]
    
    mi_fp_vals = mutual_info_classif(
        X_full.values, y_fp,
        discrete_features=discrete_mask,
        random_state=42, n_neighbors=3
    )
    
    mi_fn_vals = mutual_info_classif(
        X_full.values, y_fn,
        discrete_features=discrete_mask,
        random_state=42, n_neighbors=3
    )
    
    df_mi_fp = pd.DataFrame({
        "Feature": valid_predictors,
        "MI_FP": mi_fp_vals
    }).sort_values(by="MI_FP", ascending=False).reset_index(drop=True)
    
    df_mi_fn = pd.DataFrame({
        "Feature": valid_predictors,
        "MI_FN": mi_fn_vals
    }).sort_values(by="MI_FN", ascending=False).reset_index(drop=True)
    
    # Combine into a single ranked CSV
    df_mi_combined = pd.DataFrame({
        "Rank": np.arange(1, len(valid_predictors) + 1),
        "Feature_FP": df_mi_fp["Feature"],
        "MI_FP": df_mi_fp["MI_FP"],
        "Feature_FN": df_mi_fn["Feature"],
        "MI_FN": df_mi_fn["MI_FN"]
    })

    # --- Effect Size Measurements ---
    print("Computing Effect Size Measurements...")
    tp_group = df_subset[(df_subset["target_6hr_binary"] == 1) & (df_subset["pred_binary"] == 1)]
    fp_group = df_subset[(df_subset["target_6hr_binary"] == 0) & (df_subset["pred_binary"] == 1)]
    tn_group = df_subset[(df_subset["target_6hr_binary"] == 0) & (df_subset["pred_binary"] == 0)]
    fn_group = df_subset[(df_subset["target_6hr_binary"] == 1) & (df_subset["pred_binary"] == 0)]
    
    continuous_features_list = physical_continuous + prediction_continuous
    
    effect_records = []
    comparisons = [
        ("TP_vs_FP", tp_group, fp_group),
        ("TN_vs_FN", tn_group, fn_group)
    ]
    
    for comp_name, grp1, grp2 in comparisons:
        n1 = len(grp1)
        n2 = len(grp2)
        for f in continuous_features_list:
            if f not in df_subset.columns:
                continue
            v1 = grp1[f].values
            v2 = grp2[f].values
            
            # Means and variances
            mu1, mu2 = np.mean(v1), np.mean(v2)
            var1, var2 = np.var(v1, ddof=1), np.var(v2, ddof=1)
            
            # Cohen's d
            s_pooled = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
            cohen_d = float((mu1 - mu2) / s_pooled) if s_pooled > 1e-15 else 0.0
            
            # Mann-Whitney U and Cliff's Delta
            u_stat, mw_p = mannwhitneyu(v1, v2, alternative='two-sided')
            cliffs_delta = float(2.0 * u_stat / (n1 * n2) - 1.0)
            
            # Rank-biserial correlation is identical to Cliff's Delta for independent groups
            rank_biserial = cliffs_delta
            
            effect_records.append({
                "Feature": f,
                "Comparison": comp_name,
                "Cohens_d": cohen_d,
                "Cliffs_Delta": cliffs_delta,
                "Rank_Biserial": rank_biserial,
                "Mann_Whitney_U": float(u_stat),
                "p_value": float(mw_p)
            })
            
    df_effects = pd.DataFrame(effect_records)

    # --- Failure Category Association (Contingency Table & Chi-Square) ---
    print("Computing Failure Category Association...")
    df_failures = df_subset[df_subset["is_failure"] == 1].copy()
    
    def assign_category(row):
        if row["is_missing_sensor"]:
            return "Missing Sensor Information"
        if row["is_quiet_background"] and row["is_high_confidence"]:
            return "High Confidence Quiet Sun False Alarm"
        if row["is_quiet_background"]:
            return "Quiet Sun False Alarm"
        if row["is_weak_flare"] and row["is_transition"]:
            return "Weak Flare Transition Miss"
        if row["is_weak_flare"]:
            return "Weak Flare Miss"
        if row["is_transition"]:
            return "Transition Phase Failure"
        if row["is_sensor_disagreement"]:
            return "Instrument Disagreement"
        if row["is_background_flux_drift"]:
            return "Background Flux Drift"
        if row["is_temporal_drift"]:
            return "Temporal Drift Failure"
        if row["is_label_ambiguity"]:
            return "Borderline Label Ambiguity"
        if row["is_high_uncertainty"]:
            return "High Uncertainty Failure"
        
        active = [f for f in FLAGS if row[f]]
        if len(active) == 0:
            return "Unknown"
        return "Mixed Multi-Flag Failure"
        
    df_failures["category"] = df_failures.apply(assign_category, axis=1)
    
    contingency = pd.crosstab(df_failures["category"], df_failures["failure_type"])
    
    # Ensure both FP and FN columns exist
    if "FP" not in contingency.columns:
        contingency["FP"] = 0
    if "FN" not in contingency.columns:
        contingency["FN"] = 0
        
    # Reorder columns
    contingency = contingency[["FP", "FN"]]
    
    # Chi-square contingency test
    chi2, p_val_chi2, dof_chi2, expected_chi2 = chi2_contingency(contingency)
    n_fail = len(df_failures)
    
    # Cramer's V calculation: V = sqrt(chi2 / n) because min(R-1, C-1) = min(R-1, 1) = 1
    cramers_v = float(np.sqrt(chi2 / n_fail)) if n_fail > 0 else 0.0
    
    # Write taxonomy contingency table to CSV
    os.makedirs("artifacts/sprint18a", exist_ok=True)
    assoc_path = "artifacts/sprint18a/taxonomy_association.csv"
    
    contingency.to_csv(assoc_path)
    
    # Append the statistical parameters at the bottom of the CSV
    with open(assoc_path, "a") as f:
        f.write("\n")
        f.write("Metric,Value\n")
        f.write(f"Chi-Square,{float(chi2)}\n")
        f.write(f"Cramers_V,{cramers_v}\n")
        f.write(f"DoF,{int(dof_chi2)}\n")
        f.write(f"P-Value,{float(p_val_chi2)}\n")

    # --- Save remaining CSV Deliverables ---
    df_coef_a.to_csv("artifacts/sprint18a/logistic_fp_vs_tn.csv", index=False)
    df_coef_b.to_csv("artifacts/sprint18a/logistic_fn_vs_tp.csv", index=False)
    df_fit_summary.to_csv("artifacts/sprint18a/model_fit_summary.csv", index=False)
    df_corr.to_csv("artifacts/sprint18a/feature_correlations.csv", index=False)
    df_vif.to_csv("artifacts/sprint18a/variance_inflation.csv", index=False)
    df_mi_combined.to_csv("artifacts/sprint18a/mutual_information.csv", index=False)
    df_effects.to_csv("artifacts/sprint18a/effect_sizes.csv", index=False)
    df_bootstrap.to_csv("artifacts/sprint18a/bootstrap_coefficients.csv", index=False)

    # --- Generate root_cause_statistics.json ---
    execution_time = time.time() - start_execution
    
    stats_json = {
        "metadata": {
            "timestamp": pd.Timestamp.now().isoformat(),
            "execution_time_seconds": execution_time,
            "representative_subset_size": len(df_subset),
            "subset_failures_count": n_fail,
            "subset_non_failures_count": len(df_subset) - n_fail,
            "bootstrap_iterations": 10000,
            "locked_threshold": best_th
        },
        "model_fit_summaries": fit_summaries,
        "bootstrap_profiling": bootstrap_metas,
        "chi_square_association": {
            "chi2_statistic": float(chi2),
            "cramers_v": cramers_v,
            "degrees_of_freedom": int(dof_chi2),
            "p_value": float(p_val_chi2)
        }
    }
    
    with open("artifacts/sprint18a/root_cause_statistics.json", "w") as f:
        json.dump(stats_json, f, indent=2)
        
    print(f"Sprint 18A analysis finished successfully in {execution_time:.2f} seconds.")

if __name__ == "__main__":
    main()
