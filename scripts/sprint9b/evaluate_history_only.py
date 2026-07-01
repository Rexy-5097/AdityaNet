"""
scripts/sprint9b/evaluate_history_only.py

Sprint 9B-B: Production-Parity Evaluation Correction
Evaluation: History-Only Model

Machine Safety Constraints:
- Apple Silicon M4 MacBook Air, 16 GB unified memory
- num_workers = 0, pin_memory = False
- Batch size = 32, Chunk size = 500
- MC Dropout samples = 5
- gc.collect() after every chunk
- torch.mps.empty_cache() after every chunk
"""

import os
import sys
import json
import logging
import gc
import pickle
import numpy as np
import pandas as pd
import torch
from scipy.stats import linregress
from sklearn.metrics import roc_auc_score, average_precision_score

# Ensure project root is in python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.services.ml.model import PatchTST
from app.services.ml.inference import CalibratorWrapper

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Paths
TEST_PARQUET     = os.path.join("artifacts", "research", "test.parquet")
OUTPUT_DIR       = os.path.join("artifacts", "sprint9b")
MODEL_PATH       = os.path.join(OUTPUT_DIR, "suryanet_history_only.pt")
CALIBRATOR_PATH  = os.path.join(OUTPUT_DIR, "calibrator_history_only.pkl")
THRESHOLDS_PATH  = os.path.join("artifacts", "operator_thresholds_validation_only.json")
METRICS_PATH     = os.path.join(OUTPUT_DIR, "metrics_history_only_corrected.json")

# Hyperparameters
SEQ_LEN = 360
BATCH_SIZE = 32
CHUNK_SIZE = 500
MC_SAMPLES = 5

def get_memory_usage_gb() -> float:
    try:
        import subprocess
        pid = os.getpid()
        out = subprocess.check_output(["ps", "-o", "rss=", "-p", str(pid)])
        rss_kb = int(out.strip())
        return rss_kb / (1024 * 1024)
    except Exception:
        import resource
        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (1024 * 1024 * 1024)

# Operational Policy Helpers
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

def main():
    logger.info("Initializing Sprint 9B-B: Corrected History-Only Evaluation")
    
    device = torch.device("mps") if torch.backends.mps.is_available() else torch.device("cpu")
    logger.info(f"Using device: {device}")

    # Load thresholds from production artifacts
    if not os.path.exists(THRESHOLDS_PATH):
        raise FileNotFoundError(f"Thresholds JSON not found: {THRESHOLDS_PATH}")
    with open(THRESHOLDS_PATH, "r") as fh:
        td = json.load(fh)
    
    yellow_threshold = float(td["yellow_threshold"])
    red_threshold    = float(td["red_threshold"])
    tier_r2y = float(td.get("uncertainty_suppress_red_to_yellow",   0.10))
    tier_y2g = float(td.get("uncertainty_suppress_yellow_to_green", 0.15))
    tier_a2g = float(td.get("uncertainty_suppress_all_to_green",    0.20))

    # Define features: keep ONLY minutes_since_last_flare
    feature_cols = ["minutes_since_last_flare"]

    # Load test split
    logger.info("Loading test split dataframe...")
    test_df = pd.read_parquet(TEST_PARQUET, columns=["timestamp", "target_6hr_binary"] + feature_cols)
    test_df["timestamp"] = pd.to_datetime(test_df["timestamp"])
    total_len = len(test_df)

    # Window generation logic: Stride = 60 (hourly nowcasts), starting at index 362
    stride = 60
    indices = np.arange(362, total_len, stride)
    dataset_size = len(indices)

    # PHASE 2: Validation Checks
    print("dataset_size:", dataset_size)
    print("threshold source:", THRESHOLDS_PATH)
    print("threshold values: yellow =", yellow_threshold, ", red =", red_threshold)
    print("policy source: scripts/signal_audit/audit_helper.py / backtest_operator_policy.py")

    if dataset_size != 30106:
        raise RuntimeError(f"Dataset size mismatch: expected 30106, got {dataset_size}")

    # Slice input windows
    features_array = test_df[feature_cols].values.astype(np.float32)
    features_array = np.nan_to_num(features_array, nan=0.0, posinf=0.0, neginf=0.0)
    X_all = np.stack([features_array[i - 360 : i] for i in indices])

    # Label alignment: global_idx - 1 (production parity)
    y_true = test_df["target_6hr_binary"].values[indices - 1]

    # Load Model Checkpoint
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"Model checkpoint not found: {MODEL_PATH}")
    checkpoint = torch.load(MODEL_PATH, map_location=device, weights_only=True)
    model = PatchTST(seq_len=SEQ_LEN, n_features=len(feature_cols))
    model.load_state_dict(checkpoint["model"])
    model.to(device)
    model.eval()

    # Load Calibrator
    if not os.path.exists(CALIBRATOR_PATH):
        raise FileNotFoundError(f"Calibrator not found: {CALIBRATOR_PATH}")
    with open(CALIBRATOR_PATH, "rb") as f:
        calibrator = pickle.load(f)

    # Chunked evaluation loop
    mean_probs = np.zeros(len(indices), dtype=np.float32)
    std_probs = np.zeros(len(indices), dtype=np.float32)
    
    logger.info("Starting chunked MC Dropout evaluation...")
    for chunk_start in range(0, len(X_all), CHUNK_SIZE):
        chunk_end = min(len(X_all), chunk_start + CHUNK_SIZE)
        X_chunk = X_all[chunk_start:chunk_end]
        
        chunk_mean_list = []
        chunk_std_list = []
        
        # Process in batches of 32
        for start in range(0, len(X_chunk), BATCH_SIZE):
            end = min(len(X_chunk), start + BATCH_SIZE)
            X_batch = torch.from_numpy(X_chunk[start:end]).to(device)
            
            # Tile 5 times for 5 MC samples
            curr_batch_size = len(X_batch)
            X_batch_tiled = X_batch.repeat(MC_SAMPLES, 1, 1)  # [5 * B, 360, n_features]
            
            model.train()  # Keep dropout active
            with torch.no_grad():
                logits_tiled = model(X_batch_tiled)
                probs_tiled = torch.sigmoid(logits_tiled).squeeze(-1)  # [5 * B]
                
            probs_tiled = probs_tiled.view(MC_SAMPLES, curr_batch_size)
            mean_prob = probs_tiled.mean(dim=0).cpu().numpy()
            std_prob = probs_tiled.std(dim=0).cpu().numpy()
            
            chunk_mean_list.append(mean_prob)
            chunk_std_list.append(std_prob)
            
        mean_probs[chunk_start:chunk_end] = np.concatenate(chunk_mean_list)
        std_probs[chunk_start:chunk_end] = np.concatenate(chunk_std_list)
        
        # Clear memory
        del X_chunk, chunk_mean_list, chunk_std_list
        gc.collect()
        if device.type == "mps":
            torch.mps.empty_cache()
            
        mem_gb = get_memory_usage_gb()
        # Log memory usage as requested
        logger.info(json.dumps({"chunk_id": chunk_start // CHUNK_SIZE, "memory_gb": round(mem_gb, 4)}))

    model.eval()

    # Apply Calibration
    cal_probs = calibrator(mean_probs)

    # Apply Operational Policy Alert Logic
    raw_alerts = []
    for i in range(len(cal_probs)):
        ra = determine_raw_alert(cal_probs[i], yellow_threshold, red_threshold)
        supp = apply_tiered_uncertainty_suppression(ra, std_probs[i], tier_r2y, tier_y2g, tier_a2g)
        raw_alerts.append(supp)

    final_alerts = []
    for j, a in enumerate(raw_alerts):
        if a == "RED":
            confirmed = check_red_confirmation(j, cal_probs, red_threshold)
            if not confirmed:
                a = "YELLOW"
        final_alerts.append(a)

    # Map alerts to binary predictions: YELLOW or RED is positive
    y_pred = pd.Series(final_alerts).isin(["YELLOW", "RED"]).astype(int).values

    # Compute binary metrics
    tp = int(np.sum((y_true == 1) & (y_pred == 1)))
    fp = int(np.sum((y_true == 0) & (y_pred == 1)))
    fn = int(np.sum((y_true == 1) & (y_pred == 0)))
    tn = int(np.sum((y_true == 0) & (y_pred == 0)))
    
    precision = float(tp) / (tp + fp) if (tp + fp) > 0 else 0.0
    recall    = float(tp) / (tp + fn) if (tp + fn) > 0 else 0.0
    f1        = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    pod       = recall
    pofd      = float(fp) / (fp + tn) if (fp + tn) > 0 else 0.0
    tss       = pod - pofd
    far       = float(fp) / (tp + fp) if (tp + fp) > 0 else 0.0

    # Probability metrics
    roc_auc = float(roc_auc_score(y_true, cal_probs))
    pr_auc  = float(average_precision_score(y_true, cal_probs))

    metrics = {
        "dataset_size": dataset_size,
        "TP": tp,
        "FP": fp,
        "FN": fn,
        "TN": tn,
        "Precision": round(precision, 6),
        "Recall": round(recall, 6),
        "F1": round(f1, 6),
        "TSS": round(tss, 6),
        "FAR": round(far, 6),
        "ROC-AUC": round(roc_auc, 6),
        "PR-AUC": round(pr_auc, 6),
        "thresholds_used": {
            "yellow_threshold": yellow_threshold,
            "red_threshold": red_threshold,
            "suppression_red_to_yellow": tier_r2y,
            "suppression_yellow_to_green": tier_y2g,
            "suppression_all_to_green": tier_a2g
        },
        "policy_source": "operator_thresholds_validation_only.json + tiered uncertainty suppression + RED rolling confirmation"
    }

    # Save metrics JSON
    with open(METRICS_PATH, "w") as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Saved corrected evaluation metrics to {METRICS_PATH}")
    logger.info(f"History-only TSS = {tss:.4f} | F1 = {f1:.4f} | ROC-AUC = {roc_auc:.4f}")

if __name__ == "__main__":
    main()
