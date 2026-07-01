"""
scripts/backtest_operator_policy.py

Sprint 5.6 — Task F: Test-Split Backtest

Loads thresholds from:
    artifacts/operator_thresholds_validation_only.json

Evaluates ONLY on:
    artifacts/research/test.parquet

Does NOT read:
    artifacts/calibration/probs.npy
    artifacts/calibration/labels.npy

Produces:
    artifacts/operator_backtest.json

Containing: Precision, Recall, F1, TSS, FAR, LeadTime, TP, FP, FN, TN.
"""

import os
import sys
import json
import logging
import pickle
import numpy as np
import pandas as pd
import torch
from datetime import timedelta
from scipy.stats import linregress

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.ml.model import PatchTST, predict_with_uncertainty

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Paths
# ──────────────────────────────────────────────────────────────────────────────
TEST_PARQUET_PATH    = os.path.join("artifacts", "research", "test.parquet")
MODEL_PATH           = os.path.join("artifacts", "models", "patchtst_best.pt")
CALIBRATOR_PATH      = os.path.join("artifacts", "calibrator.pkl")
THRESHOLDS_PATH      = os.path.join("artifacts", "operator_thresholds_validation_only.json")
FEATURE_COLS_PATH    = os.path.join("artifacts", "feature_columns.json")
BACKTEST_OUTPUT_PATH = os.path.join("artifacts", "operator_backtest.json")

# Explicitly list what is NOT loaded
_NOT_LOADED = [
    "artifacts/calibration/probs.npy",
    "artifacts/calibration/labels.npy",
]


# ──────────────────────────────────────────────────────────────────────────────
# Metric Helpers
# ──────────────────────────────────────────────────────────────────────────────

def compute_confusion(y_true, y_pred):
    tp = int(((y_pred == 1) & (y_true == 1)).sum())
    fp = int(((y_pred == 1) & (y_true == 0)).sum())
    fn = int(((y_pred == 0) & (y_true == 1)).sum())
    tn = int(((y_pred == 0) & (y_true == 0)).sum())
    return tp, fp, fn, tn


def compute_metrics_from_cm(tp, fp, fn, tn):
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall    = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1        = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    pod       = recall
    pofd      = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    tss       = pod - pofd
    far       = fp / (tp + fp) if (tp + fp) > 0 else 0.0
    return {
        "precision": round(precision, 8),
        "recall":    round(recall,    8),
        "f1":        round(f1,        8),
        "tss":       round(tss,       8),
        "far":       round(far,       8),
    }


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


def evaluate_policy(results_df, alerts):
    y_true = results_df["true_label"].values
    y_pred = pd.Series(alerts).isin(["YELLOW", "RED"]).astype(int).values
    
    tp, fp, fn, tn = compute_confusion(y_true, y_pred)
    metrics = compute_metrics_from_cm(tp, fp, fn, tn)
    
    lead_time = compute_lead_time(results_df, alerts)
    event_recall = compute_event_recall(results_df, alerts)
    ep_metrics = compute_episode_metrics(results_df, alerts)
    
    return {
        "TP": tp,
        "FP": fp,
        "FN": fn,
        "TN": tn,
        "Precision": metrics["precision"],
        "Recall": metrics["recall"],
        "F1": metrics["f1"],
        "TSS": metrics["tss"],
        "FAR": metrics["far"],
        "LeadTime": lead_time,
        "EventRecall": event_recall,
        "FalseEpisodesPerMonth": ep_metrics["false_episodes_per_month"]
    }


# ──────────────────────────────────────────────────────────────────────────────
# Alert Logic
# ──────────────────────────────────────────────────────────────────────────────

def determine_raw_alert(prob, yellow_t, red_t):
    if prob < yellow_t:
        return "GREEN"
    elif prob < red_t:
        return "YELLOW"
    return "RED"


def apply_tiered_uncertainty_suppression(alert, unc, tier_r2y, tier_y2g, tier_a2g):
    if unc > tier_a2g:
        return "GREEN"
    if unc > tier_y2g and alert in ("YELLOW", "RED"):
        return "GREEN"
    if unc > tier_r2y and alert == "RED":
        return "YELLOW"
    return alert


def check_red_confirmation(j, cal_probs, red_threshold):
    if j < 2:
        return False
    last3 = cal_probs[j - 2 : j + 1]
    mean_p = float(np.mean(last3))
    slope, _, _, _, _ = linregress(np.arange(3, dtype=float), last3)
    return (mean_p > red_threshold) and (slope > 0.0)


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("SuryaNet Sprint 5.7 — Dual-Instrument Coincidence Verification Backtest")
    print("=" * 60)
    print("Files explicitly NOT loaded:")
    for f in _NOT_LOADED:
        print(f"  {f}")

    for p in [TEST_PARQUET_PATH, MODEL_PATH, CALIBRATOR_PATH,
              THRESHOLDS_PATH, FEATURE_COLS_PATH]:
        if not os.path.exists(p):
            logger.error(f"Missing required file: {p}")
            sys.exit(1)

    # 1. Load configuration
    with open(FEATURE_COLS_PATH, "r") as fh:
        feature_cols = json.load(fh)

    with open(THRESHOLDS_PATH, "r") as fh:
        td = json.load(fh)

    yellow_threshold = float(td["yellow_threshold"])
    red_threshold    = float(td["red_threshold"])
    tier_r2y = float(td.get("uncertainty_suppress_red_to_yellow",   0.10))
    tier_y2g = float(td.get("uncertainty_suppress_yellow_to_green", 0.15))
    tier_a2g = float(td.get("uncertainty_suppress_all_to_green",    0.20))

    logger.info(f"Thresholds (validation-only): yellow={yellow_threshold:.4f}, red={red_threshold:.4f}")
    logger.info(f"Uncertainty tiers: {tier_r2y}/{tier_y2g}/{tier_a2g}")

    with open(CALIBRATOR_PATH, "rb") as fh:
        calibrator = pickle.load(fh)

    # 2. Load model
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    checkpoint = torch.load(MODEL_PATH, map_location="cpu", weights_only=True)
    model = PatchTST()
    model.load_state_dict(checkpoint["model"])
    model.to(device)
    model.eval()
    logger.info(f"Model loaded onto {device}")

    # 3. Load test split
    logger.info(f"Loading test split from: {TEST_PARQUET_PATH}")
    load_cols = list(dict.fromkeys(
        ["timestamp", "short_flux", "long_flux", "target_6hr_binary", "target_6hr_class"] + feature_cols
    ))
    test_df = pd.read_parquet(TEST_PARQUET_PATH, columns=load_cols)
    test_df["timestamp"] = pd.to_datetime(test_df["timestamp"])
    total_len = len(test_df)
    logger.info(f"Test set: {total_len:,} rows")

    features_array = test_df[feature_cols].values.astype(np.float32)
    features_array = np.nan_to_num(features_array, nan=0.0, posinf=0.0, neginf=0.0)

    # 4. Slice hourly windows
    stride  = 60
    indices = np.arange(362, total_len, stride)
    logger.info(f"Evaluating {len(indices):,} hourly nowcast windows...")

    X_all = np.stack([features_array[i - 360 : i] for i in indices])

    # 5. Batched MC Dropout inference
    batch_size = 512
    mean_probs_list = []
    std_probs_list  = []

    logger.info(f"Running MC Dropout inference (n_samples=50, batch={batch_size}) on {device}...")
    for start in range(0, len(X_all), batch_size):
        end  = min(len(X_all), start + batch_size)
        X_b  = torch.from_numpy(X_all[start:end]).to(device)
        res  = predict_with_uncertainty(model, X_b, n_samples=50)
        mean_probs_list.append(res["mean_prob"].cpu().numpy())
        std_probs_list.append(res["std_prob"].cpu().numpy())

    mean_probs = np.concatenate(mean_probs_list)
    std_probs  = np.concatenate(std_probs_list)
    logger.info("Inference complete.")

    # 6. Calibrate
    cal_probs = calibrator(mean_probs)

    # 7. Apply baseline (Sprint 5.6) alert logic
    raw_alerts = []
    for i in range(len(cal_probs)):
        ra   = determine_raw_alert(cal_probs[i], yellow_threshold, red_threshold)
        supp = apply_tiered_uncertainty_suppression(ra, std_probs[i], tier_r2y, tier_y2g, tier_a2g)
        raw_alerts.append(supp)

    baseline_alerts = []
    for j, a in enumerate(raw_alerts):
        if a == "RED":
            confirmed = check_red_confirmation(j, cal_probs, red_threshold)
            if not confirmed:
                a = "YELLOW"
        baseline_alerts.append(a)

    # 8. Apply coincidence (Sprint 5.7) alert logic
    coincidence_alerts = []
    for j, a in enumerate(raw_alerts):
        if a == "RED":
            confirmed = check_red_confirmation(j, cal_probs, red_threshold)
            if not confirmed:
                a = "YELLOW"
            else:
                # Coincidence rules check
                global_idx = indices[j]
                
                # Slicing the 360-min window
                short_flux_window = test_df["short_flux"].iloc[global_idx - 360 : global_idx]
                ts_window = test_df["timestamp"].iloc[global_idx - 360 : global_idx]
                
                # Check for NaNs
                num_nans = int(short_flux_window.isna().sum())
                if num_nans > 0:
                    logger.warning(f"Found {num_nans} NaN values in window ending at {ts_window.iloc[-1]}. Interpolating...")
                    
                # Interpolation: forward-fill then backward-fill
                short_flux_filled = short_flux_window.ffill().bfill()
                
                # Cadence checks
                t_curr = ts_window.iloc[-1]
                t_5m = ts_window.iloc[-6]
                t_10m = ts_window.iloc[-11]
                
                dt = (t_curr - t_5m).total_seconds() / 60.0
                dt_prev = (t_5m - t_10m).total_seconds() / 60.0
                
                if dt <= 0.0 or dt_prev <= 0.0:
                    logger.warning(f"Invalid time delta detected (dt={dt:.2f}, dt_prev={dt_prev:.2f}) at {t_curr}. Falling back to 5.0 minutes.")
                    dt = 5.0
                    dt_prev = 5.0
                
                val_t = float(short_flux_filled.iloc[-1])
                val_t5 = float(short_flux_filled.iloc[-6])
                val_t10 = float(short_flux_filled.iloc[-11])
                
                grad = (val_t - val_t5) / dt
                grad_prev = (val_t5 - val_t10) / dt_prev
                acc = (grad - grad_prev) / ((dt + dt_prev) / 2.0)
                
                rules_passed = 0
                if grad > 0.0:
                    rules_passed += 1
                if acc > 0.0:
                    rules_passed += 1
                    
                if rules_passed < 2:
                    a = "YELLOW"
        coincidence_alerts.append(a)

    # 9. Compile results base
    rows = []
    for k, global_idx in enumerate(indices):
        rows.append({
            "timestamp":    str(test_df.iloc[global_idx - 1]["timestamp"]),
            "true_label":   int(test_df.iloc[global_idx - 1]["target_6hr_binary"]),
            "true_class":   int(test_df.iloc[global_idx - 1]["target_6hr_class"]),
            "raw_prob":     float(mean_probs[k]),
            "cal_prob":     float(cal_probs[k]),
            "unc_std":      float(std_probs[k]),
            "baseline_alert_level":    baseline_alerts[k],
            "coincidence_alert_level": coincidence_alerts[k],
            "global_idx":   int(global_idx),
        })
    results_df = pd.DataFrame(rows)

    # 10. Run policy evaluations
    logger.info("Evaluating Baseline (Sprint 5.6) policy...")
    baseline_metrics = evaluate_policy(results_df, baseline_alerts)
    
    logger.info("Evaluating Coincidence (Sprint 5.7) policy...")
    coincidence_metrics = evaluate_policy(results_df, coincidence_alerts)

    # Calculate Deltas (Coincidence - Baseline)
    delta_precision = coincidence_metrics["Precision"] - baseline_metrics["Precision"]
    delta_recall    = coincidence_metrics["Recall"] - baseline_metrics["Recall"]
    delta_f1        = coincidence_metrics["F1"] - baseline_metrics["F1"]
    delta_tss       = coincidence_metrics["TSS"] - baseline_metrics["TSS"]
    delta_far       = coincidence_metrics["FAR"] - baseline_metrics["FAR"]
    delta_false_episodes = coincidence_metrics["FalseEpisodesPerMonth"] - baseline_metrics["FalseEpisodesPerMonth"]

    # 11. Decision Logic (Safeguarded)
    accepted = (
        delta_far < 0.0
        and delta_precision > 0.0
        and delta_recall > -0.10
        and delta_false_episodes <= 0.0
    )
    
    rejection_reason = None
    if not accepted:
        reasons = []
        if not (delta_far < 0.0):
            reasons.append(f"FAR did not decrease (delta={delta_far:+.6f})")
        if not (delta_precision > 0.0):
            reasons.append(f"Precision did not increase (delta={delta_precision:+.6f})")
        if not (delta_recall > -0.10):
            reasons.append(f"Recall dropped too much (delta={delta_recall:+.6f})")
        if not (delta_false_episodes <= 0.0):
            reasons.append(f"False Episodes Per Month increased (delta={delta_false_episodes:+.6f})")
        rejection_reason = " AND ".join(reasons)

    # 12. Write Report (Task 3 & 4)
    comparison_report = {
        "baseline_metrics": baseline_metrics,
        "coincidence_metrics": coincidence_metrics,
        "delta_precision": round(float(delta_precision), 8),
        "delta_recall":    round(float(delta_recall), 8),
        "delta_f1":        round(float(delta_f1), 8),
        "delta_tss":       round(float(delta_tss), 8),
        "delta_far":       round(float(delta_far), 8),
        "delta_false_episodes_per_month": round(float(delta_false_episodes), 8),
        "coincidence_filter_accepted": bool(accepted),
        "rejection_reason": rejection_reason
    }

    report_path = os.path.join("artifacts", "dual_instrument_report.json")
    with open(report_path, "w") as fh:
        json.dump(comparison_report, fh, indent=2)
    logger.info(f"Saved comparative report → {report_path}")

    # Write final backtest file with coincidence results (Task 2 target)
    coincidence_report = {
        "thresholds_source":           THRESHOLDS_PATH,
        "test_data_file":              TEST_PARQUET_PATH,
        "files_not_loaded":            _NOT_LOADED,
        "n_windows_evaluated":         int(len(results_df)),
        "hourly_stride_minutes":       stride,
        "alert_distribution": {
            "GREEN":  int(pd.Series(coincidence_alerts).value_counts().get("GREEN", 0)),
            "YELLOW": int(pd.Series(coincidence_alerts).value_counts().get("YELLOW", 0)),
            "RED":    int(pd.Series(coincidence_alerts).value_counts().get("RED", 0)),
        },
        "confusion_matrix": {
            "tp": coincidence_metrics["TP"],
            "fp": coincidence_metrics["FP"],
            "fn": coincidence_metrics["FN"],
            "tn": coincidence_metrics["TN"],
        },
        "TP":        coincidence_metrics["TP"],
        "FP":        coincidence_metrics["FP"],
        "FN":        coincidence_metrics["FN"],
        "TN":        coincidence_metrics["TN"],
        "Precision": coincidence_metrics["Precision"],
        "Recall":    coincidence_metrics["Recall"],
        "F1":        coincidence_metrics["F1"],
        "TSS":       coincidence_metrics["TSS"],
        "FAR":       coincidence_metrics["FAR"],
        "LeadTime":  coincidence_metrics["LeadTime"],
        "EventRecall": coincidence_metrics["EventRecall"],
        "FalseEpisodesPerMonth": coincidence_metrics["FalseEpisodesPerMonth"],
        "thresholds": {
            "yellow":   yellow_threshold,
            "red":      red_threshold,
            "unc_tiers": {
                "red_to_yellow":   tier_r2y,
                "yellow_to_green": tier_y2g,
                "all_to_green":    tier_a2g,
            },
        },
    }

    # 12b. Compute and save Tier & Subgroup Metrics (Sprint 6 PART A)
    logger.info("Computing multi-tier and subgroup metrics...")
    y_true = results_df["true_label"].values
    
    # RED alert level:
    y_pred_red = (results_df["coincidence_alert_level"] == "RED").astype(int).values
    red_tp, red_fp, red_fn, red_tn = compute_confusion(y_true, y_pred_red)
    red_metrics = compute_metrics_from_cm(red_tp, red_fp, red_fn, red_tn)
    
    # YELLOW alert level:
    y_pred_yellow = (results_df["coincidence_alert_level"] == "YELLOW").astype(int).values
    yellow_tp, yellow_fp, yellow_fn, yellow_tn = compute_confusion(y_true, y_pred_yellow)
    yellow_metrics = compute_metrics_from_cm(yellow_tp, yellow_fp, yellow_fn, yellow_tn)
    
    # RED suppression metrics:
    supp_mask = (results_df["baseline_alert_level"] == "RED") & (results_df["coincidence_alert_level"] != "RED")
    suppressed_red_alerts = int(supp_mask.sum())
    suppressed_red_true_positives = int((supp_mask & (results_df["true_label"] == 1)).sum())
    suppressed_red_false_positives = int((supp_mask & (results_df["true_label"] == 0)).sum())
    
    # Subclass recall and share:
    m_mask = results_df["true_class"] == 1
    m_total = int(m_mask.sum())
    m_caught = int((m_mask & results_df["coincidence_alert_level"].isin(["YELLOW", "RED"])).sum())
    m_recall = m_caught / m_total if m_total > 0 else 0.0
    
    x_mask = results_df["true_class"] == 2
    x_total = int(x_mask.sum())
    x_caught = int((x_mask & results_df["coincidence_alert_level"].isin(["YELLOW", "RED"])).sum())
    x_recall = x_caught / x_total if x_total > 0 else 0.0
    
    pred_pos_mask = results_df["coincidence_alert_level"].isin(["YELLOW", "RED"])
    pred_pos_total = int(pred_pos_mask.sum())
    m_alert_share = int((pred_pos_mask & (results_df["true_class"] == 1)).sum()) / pred_pos_total if pred_pos_total > 0 else 0.0
    x_alert_share = int((pred_pos_mask & (results_df["true_class"] == 2)).sum()) / pred_pos_total if pred_pos_total > 0 else 0.0
    
    tier_metrics = {
        "RED_confusion_matrix": {
            "tp": red_tp,
            "fp": red_fp,
            "fn": red_fn,
            "tn": red_tn
        },
        "RED_metrics": {
            "precision": red_metrics["precision"],
            "recall": red_metrics["recall"],
            "far": red_metrics["far"]
        },
        "YELLOW_confusion_matrix": {
            "tp": yellow_tp,
            "fp": yellow_fp,
            "fn": yellow_fn,
            "tn": yellow_tn
        },
        "YELLOW_metrics": {
            "precision": yellow_metrics["precision"],
            "recall": yellow_metrics["recall"],
            "far": yellow_metrics["far"]
        },
        "suppression_metrics": {
            "suppressed_red_alerts": suppressed_red_alerts,
            "suppressed_red_true_positives": suppressed_red_true_positives,
            "suppressed_red_false_positives": suppressed_red_false_positives
        },
        "subclass_metrics": {
            "M_Recall": round(m_recall, 8),
            "X_Recall": round(x_recall, 8),
            "M_Alert_Share": round(m_alert_share, 8),
            "X_Alert_Share": round(x_alert_share, 8)
        }
    }
    
    tier_metrics_path = os.path.join("artifacts", "tier_metrics.json")
    with open(tier_metrics_path, "w") as fh:
        json.dump(tier_metrics, fh, indent=2)
    logger.info(f"Saved tier metrics report → {tier_metrics_path}")
    
    # Year-by-year partition (2023, 2024, 2025, 2026):
    error_by_year = {}
    results_df["timestamp_dt"] = pd.to_datetime(results_df["timestamp"])
    for year in [2023, 2024, 2025, 2026]:
        year_results = results_df[results_df["timestamp_dt"].dt.year == year].reset_index(drop=True)
        if len(year_results) == 0:
            logger.warning(f"No windows found for year {year}")
            continue
        year_alerts = year_results["coincidence_alert_level"].tolist()
        year_metrics = evaluate_policy(year_results, year_alerts)
        error_by_year[str(year)] = {
            "TP": year_metrics["TP"],
            "FP": year_metrics["FP"],
            "FN": year_metrics["FN"],
            "TN": year_metrics["TN"],
            "Precision": year_metrics["Precision"],
            "Recall": year_metrics["Recall"],
            "F1": year_metrics["F1"],
            "TSS": year_metrics["TSS"],
            "FAR": year_metrics["FAR"],
            "LeadTime": year_metrics["LeadTime"],
            "EventRecall": year_metrics["EventRecall"],
            "FalseEpisodesPerMonth": year_metrics["FalseEpisodesPerMonth"]
        }
        
    error_by_year_path = os.path.join("artifacts", "error_by_year.json")
    with open(error_by_year_path, "w") as fh:
        json.dump(error_by_year, fh, indent=2)
    logger.info(f"Saved year-by-year error report → {error_by_year_path}")

    predictions_path = os.path.join("artifacts", "backtest_window_predictions.csv")
    results_df.to_csv(predictions_path, index=False)
    logger.info(f"Saved window-level predictions → {predictions_path}")

    with open(BACKTEST_OUTPUT_PATH, "w") as fh:
        json.dump(coincidence_report, fh, indent=2)
    logger.info(f"Saved coincidence policy backtest report → {BACKTEST_OUTPUT_PATH}")

    # 13. Print results (no interpretation)
    print("\n" + "=" * 60)
    print("BACKTEST COMPARATIVE RESULTS (Sprint 5.6 vs Sprint 5.7)")
    print("=" * 60)
    print(f"Windows evaluated  : {len(results_df):,}")
    print(f"{'Metric':<25} | {'Baseline (5.6)':<15} | {'Coincidence (5.7)':<15} | {'Delta':<10}")
    print("-" * 75)
    for m in ["TP", "FP", "FN", "TN", "Precision", "Recall", "F1", "TSS", "FAR", "LeadTime", "EventRecall", "FalseEpisodesPerMonth"]:
        v_base = baseline_metrics[m]
        v_coin = coincidence_metrics[m]
        if isinstance(v_base, int):
            d = v_coin - v_base
            print(f"{m:<25} | {v_base:<15d} | {v_coin:<15d} | {d:+d}")
        else:
            d = v_coin - v_base
            print(f"{m:<25} | {v_base:<15.6f} | {v_coin:<15.6f} | {d:+.6f}")
    print("-" * 75)
    print(f"Filter Accepted    : {accepted}")
    if not accepted:
        print(f"Rejection Reason   : {rejection_reason}")
    print("=" * 60)


if __name__ == "__main__":
    main()
