import os
import sys
import json
import logging
import pickle
import numpy as np
import pandas as pd
import torch
from datetime import timedelta

# Ensure project root is in python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.ml.model import PatchTST, predict_with_uncertainty
from app.services.ml.features import compute_features
from app.services.ml.metrics import compute_metrics, compute_prob_metrics
from app.services.ml.inference import CalibratorWrapper

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

TEST_PARQUET_PATH = os.path.join("artifacts", "research", "test.parquet")
BEST_MODEL_PATH = os.path.join("artifacts", "models", "patchtst_best.pt")
CALIBRATOR_PATH = os.path.join("artifacts", "calibrator.pkl")
THRESHOLDS_PATH = os.path.join("artifacts", "operational_thresholds.json")
FEATURE_COLS_PATH = os.path.join("artifacts", "feature_columns.json")

OPERATIONAL_REPORT_PATH = os.path.join("artifacts", "operational_report.json")
EXAMPLES_DIR = os.path.join("artifacts", "inference_examples")

os.makedirs(EXAMPLES_DIR, exist_ok=True)

def main():
    print("==================================================")
    print("SuryaNet: Sprint 5 Operational Alert Backtesting")
    print("==================================================")

    # Validate that required files exist
    for p in [TEST_PARQUET_PATH, BEST_MODEL_PATH, CALIBRATOR_PATH, THRESHOLDS_PATH, FEATURE_COLS_PATH]:
        if not os.path.exists(p):
            logger.error(f"Missing required file: {p}")
            sys.exit(1)

    # 1. Load configuration and model metadata
    logger.info("Loading feature columns...")
    with open(FEATURE_COLS_PATH, "r") as f:
        feature_cols = json.load(f)

    logger.info("Loading thresholds...")
    with open(THRESHOLDS_PATH, "r") as f:
        thresholds_data = json.load(f)
    yellow_threshold = thresholds_data["yellow_threshold"]
    red_threshold = thresholds_data["red_threshold"]
    uncertainty_threshold = thresholds_data.get("uncertainty_threshold", 0.08)

    logger.info("Loading calibrator...")
    with open(CALIBRATOR_PATH, "rb") as f:
        calibrator = pickle.load(f)

    logger.info("Loading PatchTST model...")
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    checkpoint = torch.load(BEST_MODEL_PATH, map_location="cpu", weights_only=True)
    model = PatchTST()
    model.load_state_dict(checkpoint["model"])
    model.to(device)
    model.eval()

    # 2. Load test set Parquet (including feature columns to avoid feature mismatch)
    logger.info("Loading test dataset Parquet...")
    load_cols = list(dict.fromkeys(["timestamp", "short_flux", "long_flux", "target_6hr_binary"] + feature_cols))
    test_df = pd.read_parquet(TEST_PARQUET_PATH, columns=load_cols)
    test_df["timestamp"] = pd.to_datetime(test_df["timestamp"])
    total_len = len(test_df)
    logger.info(f"Loaded test set with {total_len:,} rows.")

    # 3. Retrieve physics-aware features directly from Parquet
    logger.info("Retrieving pre-computed features from test dataset Parquet...")
    features_array = test_df[feature_cols].values.astype(np.float32)
    features_array = np.nan_to_num(features_array, nan=0.0, posinf=0.0, neginf=0.0)

    # 4. Slice windows for hourly nowcasting (stride = 60 minutes)
    stride = 60
    # Start at 362 to ensure we can have consecutive checks ending at idx
    indices = np.arange(362, total_len, stride)
    logger.info(f"Slicing {len(indices):,} hourly windows...")

    X_all = np.stack([features_array[i - 360 : i] for i in indices])  # [N_windows, 360, 14]
    
    # 5. Batched Inference with MC Dropout
    batch_size = 512
    n_windows = len(X_all)
    mean_probs = []
    std_probs = []

    logger.info(f"Running batched model inference (n_samples=50, batch_size={batch_size}) on {device}...")
    for start_idx in range(0, n_windows, batch_size):
        end_idx = min(n_windows, start_idx + batch_size)
        X_batch = torch.from_numpy(X_all[start_idx:end_idx]).to(device)
        
        # predict_with_uncertainty returns tensors of shape [batch]
        res = predict_with_uncertainty(model, X_batch, n_samples=50)
        mean_probs.append(res["mean_prob"].cpu().numpy())
        std_probs.append(res["std_prob"].cpu().numpy())

    mean_probs = np.concatenate(mean_probs)
    std_probs = np.concatenate(std_probs)
    logger.info("Batched inference completed.")

    # 6. Apply Calibrator
    cal_probs = calibrator(mean_probs)

    # 7. Apply Alert Logic & Uncertainty Suppression
    # Green < yellow, Yellow: yellow <= prob < red, Red: prob >= red
    # Uncertainty > 0.08 downgrades alert level by one tier
    alerts = []
    for i in range(len(cal_probs)):
        p = cal_probs[i]
        unc = std_probs[i]
        
        if p < yellow_threshold:
            raw_alert = "GREEN"
        elif p < red_threshold:
            raw_alert = "YELLOW"
        else:
            raw_alert = "RED"
            
        # Uncertainty suppression
        if unc > uncertainty_threshold:
            if raw_alert == "RED":
                raw_alert = "YELLOW"
            elif raw_alert == "YELLOW":
                raw_alert = "GREEN"
                
        alerts.append(raw_alert)

    # 8. Apply Consecutive Alert Confirmation
    # Red alert only if 3 consecutive hourly windows are RED
    final_alerts = []
    for j in range(len(alerts)):
        curr_a = alerts[j]
        confidence = "CONFIRMED"
        
        if curr_a == "RED":
            if j >= 2:
                # Check if previous two hourly steps were also RED
                if alerts[j-1] != "RED" or alerts[j-2] != "RED":
                    curr_a = "YELLOW"
                    confidence = "UNCONFIRMED"
            else:
                curr_a = "YELLOW"
                confidence = "UNCONFIRMED"
                
        final_alerts.append((curr_a, confidence))

    # Compile results DataFrame
    results_list = []
    for idx_in_loop, global_idx in enumerate(indices):
        true_label = int(test_df.iloc[global_idx - 1]["target_6hr_binary"])
        timestamp_str = str(test_df.iloc[global_idx - 1]["timestamp"])
        curr_a, confidence = final_alerts[idx_in_loop]
        
        results_list.append({
            "timestamp": timestamp_str,
            "true_label": true_label,
            "raw_prob": float(mean_probs[idx_in_loop]),
            "cal_prob": float(cal_probs[idx_in_loop]),
            "unc_std": float(std_probs[idx_in_loop]),
            "alert_level": curr_a,
            "confidence": confidence,
            "global_idx": int(global_idx)
        })

    results_df = pd.DataFrame(results_list)

    # 9. Save Operational Examples (Green, Yellow, Red cases)
    logger.info("Saving case examples for operational payloads...")
    green_cases = results_df[results_df["alert_level"] == "GREEN"]
    yellow_cases = results_df[results_df["alert_level"] == "YELLOW"]
    red_cases = results_df[results_df["alert_level"] == "RED"]
    
    logger.info(f"Alert distribution: GREEN={len(green_cases)}, YELLOW={len(yellow_cases)}, RED={len(red_cases)}")

    def save_case_payload(subset, filename):
        if len(subset) > 0:
            # Sort by highest/lowest calibrated probability to get typical examples
            if filename == "green_case.json":
                # Typical green: very low probability
                row = subset.sort_values("cal_prob").iloc[0]
            elif filename == "yellow_case.json":
                # Typical yellow: middle probability
                row = subset.sort_values("cal_prob", ascending=False).iloc[len(subset)//2]
            else:
                # Typical red: highest probability, confirmed
                row = subset[subset["confidence"] == "CONFIRMED"].sort_values("cal_prob", ascending=False).iloc[0]
                
            orig_idx = int(row["global_idx"])
            # Extract 362 rows ending at this index
            window = test_df.iloc[orig_idx - 361 : orig_idx + 1]
            
            payload = {
                "flux_history": [
                    {
                        "timestamp": str(r["timestamp"]),
                        "short_flux": float(r["short_flux"]),
                        "long_flux": float(r["long_flux"])
                    }
                    for _, r in window.iterrows()
                ]
            }
            path = os.path.join(EXAMPLES_DIR, filename)
            with open(path, "w") as f:
                json.dump(payload, f, indent=2)
            logger.info(f"Saved {filename} → {path} (Calibrated Prob={row['cal_prob']:.4f}, Alert={row['alert_level']})")
        else:
            logger.warning(f"No examples found for alert category to save as {filename}.")

    save_case_payload(green_cases, "green_case.json")
    save_case_payload(yellow_cases, "yellow_case.json")
    save_case_payload(red_cases, "red_case.json")

    # 10. Evaluate Alert-based Metrics
    logger.info("Evaluating operational alert-based metrics...")
    y_true = results_df["true_label"].values
    
    # An alert is positive if it is YELLOW or RED
    y_pred_alert = results_df["alert_level"].isin(["YELLOW", "RED"]).astype(int).values
    
    hard_metrics = compute_metrics(y_true, y_pred_alert)
    prob_metrics = compute_prob_metrics(y_true, results_df["cal_prob"].values)
    
    tp = hard_metrics["confusion_matrix"]["tp"]
    fp = hard_metrics["confusion_matrix"]["fp"]
    fn = hard_metrics["confusion_matrix"]["fn"]
    tn = hard_metrics["confusion_matrix"]["tn"]
    
    precision = hard_metrics["precision"]
    recall = hard_metrics["recall"]
    far = hard_metrics["far"]
    tss = hard_metrics["tss"]
    f1 = hard_metrics["f1"]

    # 11. Compute Warning Lead Time
    # Average warning lead time (hours from first RED alert to actual flare start)
    lead_times = []
    in_block = False
    block_start_idx = None
    
    for idx, row in results_df.iterrows():
        if row["true_label"] == 1 and not in_block:
            in_block = True
            block_start_idx = idx
        elif row["true_label"] == 0 and in_block:
            # End of positive block. Check if any alert was issued during this block or shortly before it
            # Standard flare forecast warning lookahead is 6 hours (6 steps in hourly stride)
            search_start = max(0, block_start_idx - 6)
            block_alerts = results_df.iloc[search_start : block_start_idx + 1]
            active_alerts = block_alerts[block_alerts["alert_level"].isin(["YELLOW", "RED"])]
            
            if len(active_alerts) > 0:
                first_alert_ts = pd.to_datetime(active_alerts.iloc[0]["timestamp"])
                block_start_ts = pd.to_datetime(results_df.loc[block_start_idx, "timestamp"])
                approx_event_ts = block_start_ts + timedelta(hours=6)
                
                lead_time_hrs = (approx_event_ts - first_alert_ts).total_seconds() / 3600.0
                lead_times.append(lead_time_hrs)
                
            in_block = False
            
    avg_lead_time = float(np.mean(lead_times)) if len(lead_times) > 0 else 0.0

    # 12. Print and Save Backtest Results
    print("\n" + "=" * 60)
    print("OPERATIONAL ALERT SYSTEM BACKTEST RESULTS")
    print("=" * 60)
    print(f"Total simulated steps:        {len(results_df):,} (hourly nowcasts)")
    print(f"Alert level rates:            GREEN={len(green_cases)/len(results_df)*100:.2f}%, "
          f"YELLOW={len(yellow_cases)/len(results_df)*100:.2f}%, RED={len(red_cases)/len(results_df)*100:.2f}%")
    print(f"Confirmed alerts (TP):        {tp}")
    print(f"False alarms (FP):            {fp}")
    print(f"Missed events (FN):           {fn}")
    print(f"Operator Trust Score (Prec):  {precision*100:.2f}%")
    print(f"True Skill Score (TSS):       {tss:.4f}")
    print(f"Probability of Detection:     {recall*100:.2f}%")
    print(f"False Alarm Ratio (FAR):      {far*100:.2f}%")
    print(f"F1 Score:                     {f1:.4f}")
    print(f"Average Warning Lead Time:    {avg_lead_time:.2f} hours")
    print("=" * 60)

    # Success Criteria check
    print("\n--- Success Criteria Check ---")
    prec_ok = precision > 0.40
    f1_ok = f1 > 0.50
    far_ok = far < 0.60
    tss_ok = tss > 0.30
    
    print(f"Test Set Precision > 40%:      {'✅ PASS' if prec_ok else '❌ FAIL'} ({precision*100:.2f}%)")
    print(f"Test Set F1 > 0.50:            {'✅ PASS' if f1_ok else '❌ FAIL'} ({f1:.4f})")
    print(f"Test Set FAR < 60%:            {'✅ PASS' if far_ok else '❌ FAIL'} ({far*100:.2f}%)")
    print(f"Test Set TSS > 0.30:           {'✅ PASS' if tss_ok else '❌ FAIL'} ({tss:.4f})")

    # Save operational report
    report = {
        "raw_precision": 0.286490,  # from audit_report
        "calibrated_precision": precision,
        "raw_f1": 0.437886,
        "calibrated_f1": f1,
        "raw_far": 0.713510,
        "calibrated_far": far,
        "recommended_threshold": yellow_threshold,
        "red_threshold": red_threshold,
        "operator_trust_score": precision,
        "true_skill_score": tss,
        "probability_of_detection": recall,
        "average_warning_lead_time_hours": avg_lead_time,
        "confusion_matrix": {
            "tp": int(tp),
            "fp": int(fp),
            "fn": int(fn),
            "tn": int(tn)
        },
        "criteria_checks": {
            "precision_ok": bool(prec_ok),
            "f1_ok": bool(f1_ok),
            "far_ok": bool(far_ok),
            "tss_ok": bool(tss_ok)
        }
    }

    with open(OPERATIONAL_REPORT_PATH, "w") as f:
        json.dump(report, f, indent=2)
    logger.info(f"Saved operational report → {OPERATIONAL_REPORT_PATH}")

if __name__ == "__main__":
    main()
