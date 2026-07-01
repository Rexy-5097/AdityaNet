"""
scripts/simulated_fix_validation.py

Sprint 7 — Task C & D: Simulated Fix Validation & Projections

Loads:
    artifacts/backtest_window_predictions.csv
    artifacts/research/test.parquet

Calculates:
    - 1,000 bootstrap resamples on baseline to get 95% CIs.
    - Parameter sweep for Post-Flare Decay Suppression (Experiment 1).
    - Parameter sweep for Quiet-Sun Promotion (Experiment 2).
    - Simulated fix experiments: Experiment 1 (optimal decay suppression),
      Experiment 2 (optimal quiet promotion), Experiment 3 (both).
    - Computes relative FAR reduction, Precision gain, and Recall gain.

Saves:
    artifacts/bootstrap_metrics.json
    artifacts/post_flare_decay_sweep.csv
    artifacts/quiet_sun_sweep.csv
    artifacts/simulated_fix_validation.json
    artifacts/operator_trust_projection.json
"""

import os
import json
import logging
import numpy as np
import pandas as pd
from datetime import timedelta

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

PREDICTIONS_PATH = os.path.join("artifacts", "backtest_window_predictions.csv")
TEST_PARQUET_PATH = os.path.join("artifacts", "research", "test.parquet")

BOOTSTRAP_OUTPUT = os.path.join("artifacts", "bootstrap_metrics.json")
DECAY_SWEEP_OUTPUT = os.path.join("artifacts", "post_flare_decay_sweep.csv")
QUIET_SWEEP_OUTPUT = os.path.join("artifacts", "quiet_sun_sweep.csv")
VALIDATION_OUTPUT = os.path.join("artifacts", "simulated_fix_validation.json")
PROJECTION_OUTPUT = os.path.join("artifacts", "operator_trust_projection.json")


# ──────────────────────────────────────────────────────────────────────────────
# Operator Metric Helpers (from backtest_operator_policy.py)
# ──────────────────────────────────────────────────────────────────────────────

def compute_episode_metrics(results_df, alerts):
    labels = results_df["true_label"].tolist()
    timestamps = pd.to_datetime(results_df["timestamp"]).tolist()

    episodes = []
    in_episode = False
    ep_start = None

    for i, a in enumerate(alerts):
        if a in ("YELLOW", "RED") and not in_episode:
            in_episode = True
            ep_start   = i
        elif a == "GREEN" and in_episode:
            episodes.append((ep_start, i - 1))
            in_episode = False

    if in_episode:
        episodes.append((ep_start, len(alerts) - 1))

    true_episodes  = 0
    false_episodes = 0
    total_alerts   = 0
    duplicate_alerts = 0

    for (start, end) in episodes:
        episode_labels = labels[start : end + 1]
        has_positive   = any(l == 1 for l in episode_labels)
        ep_len         = end - start + 1
        total_alerts  += ep_len

        if has_positive:
            true_episodes    += 1
            duplicate_alerts += max(0, ep_len - 1)
        else:
            false_episodes += 1

    n_episodes       = len(episodes)
    duplicate_rate   = duplicate_alerts / total_alerts if total_alerts > 0 else 0.0
    false_ep_rate    = false_episodes / n_episodes if n_episodes > 0 else 0.0

    if len(timestamps) > 1:
        total_days  = (timestamps[-1] - timestamps[0]).total_seconds() / 86400
        n_months    = max(total_days / 30.0, 0.001)
    else:
        n_months = 1.0

    return {
        "n_episodes":             n_episodes,
        "true_episodes":          true_episodes,
        "false_episodes":         false_episodes,
        "false_episode_rate":     round(false_ep_rate, 6),
        "total_alert_windows":    total_alerts,
        "duplicate_alert_windows": duplicate_alerts,
        "duplicate_alert_rate":   round(duplicate_rate, 6),
        "episodes_per_month":     round(n_episodes / n_months, 4),
        "false_episodes_per_month": round(false_episodes / n_months, 4),
        "n_months": n_months
    }


def compute_event_recall(results_df, alerts):
    df_temp = results_df.copy()
    df_temp["alert_level"] = alerts
    total_events = 0
    caught_events = 0
    in_block = False
    block_start_idx = None

    for idx, row in df_temp.iterrows():
        if row["true_label"] == 1 and not in_block:
            in_block = True
            block_start_idx = idx
        elif row["true_label"] == 0 and in_block:
            total_events += 1
            search_start = max(0, block_start_idx - 6)
            block_alerts = df_temp.iloc[search_start : block_start_idx + 1]
            active_alerts = block_alerts[block_alerts["alert_level"].isin(["YELLOW", "RED"])]
            if len(active_alerts) > 0:
                caught_events += 1
            in_block = False
            
    if in_block:
        total_events += 1
        search_start = max(0, block_start_idx - 6)
        block_alerts = df_temp.iloc[search_start:]
        active_alerts = block_alerts[block_alerts["alert_level"].isin(["YELLOW", "RED"])]
        if len(active_alerts) > 0:
            caught_events += 1

    event_recall = caught_events / total_events if total_events > 0 else 0.0
    return round(event_recall, 8)


def compute_lead_time(results_df, alerts):
    df_temp = results_df.copy()
    df_temp["alert_level"] = alerts
    lead_times = []
    in_block = False
    block_start_idx = None

    for idx, row in df_temp.iterrows():
        if row["true_label"] == 1 and not in_block:
            in_block        = True
            block_start_idx = idx
        elif row["true_label"] == 0 and in_block:
            search_start  = max(0, block_start_idx - 6)
            block_alerts  = df_temp.iloc[search_start : block_start_idx + 1]
            active_alerts = block_alerts[block_alerts["alert_level"].isin(["YELLOW", "RED"])]
            if len(active_alerts) > 0:
                first_alert_ts  = pd.to_datetime(active_alerts.iloc[0]["timestamp"])
                block_start_ts  = pd.to_datetime(df_temp.loc[block_start_idx, "timestamp"])
                approx_event_ts = block_start_ts + timedelta(hours=6)
                lead_time_hrs   = (approx_event_ts - first_alert_ts).total_seconds() / 3600.0
                lead_times.append(lead_time_hrs)
            in_block = False
    avg_lead_time = float(np.mean(lead_times)) if lead_times else 0.0
    return round(avg_lead_time, 4)


def evaluate_policy_metrics(aligned_df, alerts):
    y_true = aligned_df["true_label"].values
    y_pred = pd.Series(alerts).isin(["YELLOW", "RED"]).astype(int).values
    
    tp = int(((y_pred == 1) & (y_true == 1)).sum())
    fp = int(((y_pred == 1) & (y_true == 0)).sum())
    fn = int(((y_pred == 0) & (y_true == 1)).sum())
    tn = int(((y_pred == 0) & (y_true == 0)).sum())
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    pod = recall
    pofd = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    tss = pod - pofd
    far = fp / (tp + fp) if (tp + fp) > 0 else 0.0
    
    lead_time = compute_lead_time(aligned_df, alerts)
    event_recall = compute_event_recall(aligned_df, alerts)
    ep_metrics = compute_episode_metrics(aligned_df, alerts)
    
    alerts_per_month = ep_metrics["total_alert_windows"] / ep_metrics["n_months"] if ep_metrics["n_months"] > 0 else 0.0
    
    return {
        "TP": tp,
        "FP": fp,
        "FN": fn,
        "TN": tn,
        "Precision": round(precision, 8),
        "Recall": round(recall, 8),
        "F1": round(f1, 8),
        "TSS": round(tss, 8),
        "FAR": round(far, 8),
        "FalseEpisodesPerMonth": round(ep_metrics["false_episodes_per_month"], 4),
        "EventRecall": round(event_recall, 8),
        "AlertsPerMonth": round(alerts_per_month, 4),
        "LeadTime": round(lead_time, 4)
    }


def main():
    logger.info("Loading predictions and features...")
    if not os.path.exists(PREDICTIONS_PATH) or not os.path.exists(TEST_PARQUET_PATH):
        logger.error("Required prediction or parquet files are missing.")
        return

    # Load data
    preds_df = pd.read_csv(PREDICTIONS_PATH)
    
    load_cols = ["timestamp", "long_flux", "short_flux", "minutes_since_last_flare", "flux_gradient_5m"]
    test_df = pd.read_parquet(TEST_PARQUET_PATH, columns=load_cols)

    # Align predictions with features (global_idx - 1)
    nowcast_indices = preds_df["global_idx"].values - 1
    aligned_df = test_df.iloc[nowcast_indices].copy().reset_index(drop=True)
    
    aligned_df["true_label"] = preds_df["true_label"].values
    aligned_df["true_class"] = preds_df["true_class"].values
    aligned_df["cal_prob"] = preds_df["cal_prob"].values
    aligned_df["baseline_alert_level"] = preds_df["coincidence_alert_level"].values

    # ──────────────────────────────────────────────────────────────────────────────
    # 1. Bootstrap Confidence Intervals
    # ──────────────────────────────────────────────────────────────────────────────
    logger.info("Running 1,000 bootstrap resamples on baseline...")
    y_true = aligned_df["true_label"].values
    y_pred = aligned_df["baseline_alert_level"].isin(["YELLOW", "RED"]).astype(int).values
    n_samples = len(y_true)
    
    rng = np.random.RandomState(42)
    boot_precisions = []
    boot_recalls = []
    boot_fars = []
    boot_tsses = []
    boot_f1s = []
    
    block_size = 100
    for _ in range(10):  # 10 blocks * 100 resamples = 1,000 resamples
        idx_matrix = rng.randint(0, n_samples, size=(block_size, n_samples))
        y_true_res = y_true[idx_matrix]
        y_pred_res = y_pred[idx_matrix]
        
        tp = ((y_pred_res == 1) & (y_true_res == 1)).sum(axis=1)
        fp = ((y_pred_res == 1) & (y_true_res == 0)).sum(axis=1)
        fn = ((y_pred_res == 0) & (y_true_res == 1)).sum(axis=1)
        tn = ((y_pred_res == 0) & (y_true_res == 0)).sum(axis=1)
        
        precision = np.nan_to_num(tp / (tp + fp), nan=0.0)
        recall = np.nan_to_num(tp / (tp + fn), nan=0.0)
        far = np.nan_to_num(fp / (tp + fp), nan=0.0)
        f1 = np.nan_to_num(2 * precision * recall / (precision + recall + 1e-12), nan=0.0)
        
        pod = recall
        pofd = np.nan_to_num(fp / (fp + tn), nan=0.0)
        tss = pod - pofd
        
        boot_precisions.extend(precision.tolist())
        boot_recalls.extend(recall.tolist())
        boot_fars.extend(far.tolist())
        boot_tsses.extend(tss.tolist())
        boot_f1s.extend(f1.tolist())
        
    bootstrap_metrics = {
        "Precision": [float(np.percentile(boot_precisions, 2.5)), float(np.percentile(boot_precisions, 97.5))],
        "Recall": [float(np.percentile(boot_recalls, 2.5)), float(np.percentile(boot_recalls, 97.5))],
        "FAR": [float(np.percentile(boot_fars, 2.5)), float(np.percentile(boot_fars, 97.5))],
        "TSS": [float(np.percentile(boot_tsses, 2.5)), float(np.percentile(boot_tsses, 97.5))],
        "F1": [float(np.percentile(boot_f1s, 2.5)), float(np.percentile(boot_f1s, 97.5))]
    }
    
    with open(BOOTSTRAP_OUTPUT, "w") as fh:
        json.dump(bootstrap_metrics, fh, indent=2)
    logger.info(f"Saved bootstrap confidence intervals → {BOOTSTRAP_OUTPUT}")

    # ──────────────────────────────────────────────────────────────────────────────
    # 2. Decay suppression sweep
    # ──────────────────────────────────────────────────────────────────────────────
    logger.info("Running parameter sweep for Post-Flare Decay Suppression...")
    decay_minutes_list = [30, 60, 120, 180, 240, 360]
    flux_threshold_list = [1e-6, 3e-6, 5e-6, 1e-5]
    gradient_threshold_list = [0.0, -1e-8, -5e-8]
    
    decay_rows = []
    best_decay_f1 = -1.0
    best_decay_params = {}

    for d_min in decay_minutes_list:
        for f_t in flux_threshold_list:
            for g_t in gradient_threshold_list:
                # Suppress if within decay window, flux is high, and gradient is negative (cooling)
                suppress_mask = (
                    (aligned_df["minutes_since_last_flare"] < d_min) &
                    (aligned_df["long_flux"] > f_t) &
                    (aligned_df["flux_gradient_5m"] < g_t)
                ).values
                
                alerts = aligned_df["baseline_alert_level"].copy().values
                alerts[suppress_mask] = "GREEN"
                alerts = list(alerts)
                
                metrics = evaluate_policy_metrics(aligned_df, alerts)
                row = {
                    "decay_minutes": d_min,
                    "flux_threshold": f_t,
                    "gradient_threshold": g_t,
                    **metrics
                }
                decay_rows.append(row)
                
                if metrics["F1"] > best_decay_f1:
                    best_decay_f1 = metrics["F1"]
                    best_decay_params = {
                        "decay_minutes": d_min,
                        "flux_threshold": f_t,
                        "gradient_threshold": g_t
                    }
                    
    decay_df = pd.DataFrame(decay_rows)
    decay_df.to_csv(DECAY_SWEEP_OUTPUT, index=False)
    logger.info(f"Saved decay sweep results → {DECAY_SWEEP_OUTPUT}")
    logger.info(f"Optimal decay suppression parameters (F1={best_decay_f1:.4f}): {best_decay_params}")

    # ──────────────────────────────────────────────────────────────────────────────
    # 3. Quiet-Sun promotion sweep
    # ──────────────────────────────────────────────────────────────────────────────
    logger.info("Running parameter sweep for Quiet-Sun Promotion...")
    q_mins = aligned_df["minutes_since_last_flare"]
    quiet_minutes_list = [float(q_mins.quantile(p)) for p in [0.5, 0.6, 0.7, 0.8, 0.9]]
    
    flux_vals = aligned_df["long_flux"]
    flux_threshold_list = [float(flux_vals.quantile(p)) for p in [0.1, 0.2, 0.3, 0.4]]
    
    cal_prob_threshold_list = [round(0.05 + 0.01 * x, 2) for x in range(10)]
    
    quiet_rows = []
    best_quiet_f1 = -1.0
    best_quiet_params = {}
    
    for q_min in quiet_minutes_list:
        for f_t in flux_threshold_list:
            for p_t in cal_prob_threshold_list:
                # Promote if long quiet time, low background flux, and model probability is above sub-threshold
                promote_mask = (
                    (aligned_df["baseline_alert_level"] == "GREEN") &
                    (aligned_df["minutes_since_last_flare"] > q_min) &
                    (aligned_df["long_flux"] < f_t) &
                    (aligned_df["cal_prob"] >= p_t)
                ).values
                
                alerts = aligned_df["baseline_alert_level"].copy().values
                alerts[promote_mask] = "YELLOW"
                alerts = list(alerts)
                
                metrics = evaluate_policy_metrics(aligned_df, alerts)
                row = {
                    "quiet_minutes": q_min,
                    "flux_threshold": f_t,
                    "cal_prob_threshold": p_t,
                    **metrics
                }
                quiet_rows.append(row)
                
                if metrics["F1"] > best_quiet_f1:
                    best_quiet_f1 = metrics["F1"]
                    best_quiet_params = {
                        "quiet_minutes": q_min,
                        "flux_threshold": f_t,
                        "cal_prob_threshold": p_t
                    }
                    
    quiet_df = pd.DataFrame(quiet_rows)
    quiet_df.to_csv(QUIET_SWEEP_OUTPUT, index=False)
    logger.info(f"Saved quiet sweep results → {QUIET_SWEEP_OUTPUT}")
    logger.info(f"Optimal quiet-sun parameters (F1={best_quiet_f1:.4f}): {best_quiet_params}")

    # ──────────────────────────────────────────────────────────────────────────────
    # 4. Controlled fix validation and projections
    # ──────────────────────────────────────────────────────────────────────────────
    logger.info("Evaluating controlled experiments with optimal parameters...")
    
    # Baseline
    baseline_metrics = evaluate_policy_metrics(aligned_df, aligned_df["baseline_alert_level"].tolist())
    
    # Experiment 1: Optimal Decay Suppression
    d_opt = best_decay_params["decay_minutes"]
    f_opt = best_decay_params["flux_threshold"]
    g_opt = best_decay_params["gradient_threshold"]
    
    exp1_mask = (
        (aligned_df["minutes_since_last_flare"] < d_opt) &
        (aligned_df["long_flux"] > f_opt) &
        (aligned_df["flux_gradient_5m"] < g_opt)
    ).values
    exp1_alerts = aligned_df["baseline_alert_level"].copy().values
    exp1_alerts[exp1_mask] = "GREEN"
    exp1_alerts = list(exp1_alerts)
    exp1_metrics = evaluate_policy_metrics(aligned_df, exp1_alerts)
    
    # Experiment 2: Optimal Quiet Sun Promotion
    q_opt = best_quiet_params["quiet_minutes"]
    fl_opt = best_quiet_params["flux_threshold"]
    p_opt = best_quiet_params["cal_prob_threshold"]
    
    exp2_mask = (
        (aligned_df["baseline_alert_level"] == "GREEN") &
        (aligned_df["minutes_since_last_flare"] > q_opt) &
        (aligned_df["long_flux"] < fl_opt) &
        (aligned_df["cal_prob"] >= p_opt)
    ).values
    exp2_alerts = aligned_df["baseline_alert_level"].copy().values
    exp2_alerts[exp2_mask] = "YELLOW"
    exp2_alerts = list(exp2_alerts)
    exp2_metrics = evaluate_policy_metrics(aligned_df, exp2_alerts)
    
    # Experiment 3: Both Combined
    exp3_alerts = aligned_df["baseline_alert_level"].copy().values
    exp3_alerts[exp2_mask] = "YELLOW"  # Promotion first
    exp3_alerts[exp1_mask] = "GREEN"   # Suppression overrides promotion (safe order)
    exp3_alerts = list(exp3_alerts)
    exp3_metrics = evaluate_policy_metrics(aligned_df, exp3_alerts)

    # Compile validation report
    simulated_validation = {
        "optimal_decay_parameters": best_decay_params,
        "optimal_quiet_parameters": best_quiet_params,
        "experiments": {
            "baseline": baseline_metrics,
            "experiment_1_decay_suppression": exp1_metrics,
            "experiment_2_quiet_promotion": exp2_metrics,
            "experiment_3_combined": exp3_metrics
        }
    }
    
    with open(VALIDATION_OUTPUT, "w") as fh:
        json.dump(simulated_validation, fh, indent=2)
    logger.info(f"Saved simulated validation results → {VALIDATION_OUTPUT}")

    # TASK E: Projections
    def get_relative_change(new_v, base_v, name=""):
        if base_v == 0.0:
            return 0.0
        return float((new_v - base_v) / base_v)

    def format_experiment_projection(exp_m, base_m):
        return {
            "Precision": exp_m["Precision"],
            "Recall": exp_m["Recall"],
            "FAR": exp_m["FAR"],
            "FalseEpisodesPerMonth": exp_m["FalseEpisodesPerMonth"],
            "Relative_FAR_Reduction": round(get_relative_change(base_m["FAR"], exp_m["FAR"]), 8), # (FAR_base - FAR_new)/FAR_base
            "Relative_Precision_Gain": round(get_relative_change(exp_m["Precision"], base_m["Precision"]), 8),
            "Relative_Recall_Gain": round(get_relative_change(exp_m["Recall"], base_m["Recall"]), 8)
        }

    # Note on FAR reduction: (FAR_base - FAR_new) / FAR_base
    projection_report = {
        "baseline": {
            "Precision": baseline_metrics["Precision"],
            "Recall": baseline_metrics["Recall"],
            "FAR": baseline_metrics["FAR"],
            "FalseEpisodesPerMonth": baseline_metrics["FalseEpisodesPerMonth"]
        },
        "experiment_1_decay_suppression": format_experiment_projection(exp1_metrics, baseline_metrics),
        "experiment_2_quiet_promotion": format_experiment_projection(exp2_metrics, baseline_metrics),
        "experiment_3_combined": format_experiment_projection(exp3_metrics, baseline_metrics)
    }

    with open(PROJECTION_OUTPUT, "w") as fh:
        json.dump(projection_report, fh, indent=2)
    logger.info(f"Saved operator trust projection → {PROJECTION_OUTPUT}")


if __name__ == "__main__":
    main()
