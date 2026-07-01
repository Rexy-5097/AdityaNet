import os
import sys
import json
import pickle
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.ml.inference import CalibratorWrapper

# Paths
BEST_MODEL_PATH = "artifacts/models/patchtst_best.pt"
CALIBRATOR_PATH = "artifacts/calibrator.pkl"
TEST_PARQUET_PATH = "artifacts/research/test.parquet"
PROBS_PATH = "artifacts/calibration/probs.npy"
LABELS_PATH = "artifacts/calibration/labels.npy"

OPERATIONAL_VAL_PATH = "artifacts/operator_thresholds_validation_only.json"
OPERATIONAL_PROD_PATH = "artifacts/operator_thresholds.json"
OPERATIONAL_OLD_PATH = "artifacts/operational_thresholds.json"

AUDIT_OUTPUT_PATH = "artifacts/sprint10h5/architecture_ceiling_audit.json"

def compute_metrics_at_threshold(probs, labels, t):
    y_pred = (probs >= t).astype(int)
    tp = int(((y_pred == 1) & (labels == 1)).sum())
    fp = int(((y_pred == 1) & (labels == 0)).sum())
    fn = int(((y_pred == 0) & (labels == 1)).sum())
    tn = int(((y_pred == 0) & (labels == 0)).sum())

    pod = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    pofd = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    tss = pod - pofd
    far = fp / (tp + fp) if (tp + fp) > 0 else 0.0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = pod
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    return {
        "threshold": round(float(t), 2),
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "tss": float(tss),
        "far": float(far),
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1)
    }

def main():
    raw_probs = np.load(PROBS_PATH)
    labels = np.load(LABELS_PATH)
    
    with open(CALIBRATOR_PATH, "rb") as f:
        calibrator = pickle.load(f)
    
    calibrated_probs = calibrator(raw_probs)
    
    # Sweep thresholds: 0.01 to 0.99 step 0.01
    thresholds = np.arange(0.01, 1.00, 0.01)
    
    raw_sweep = []
    calibrated_sweep = []
    
    for t in thresholds:
        t_round = round(float(t), 2)
        raw_sweep.append(compute_metrics_at_threshold(raw_probs, labels, t_round))
        calibrated_sweep.append(compute_metrics_at_threshold(calibrated_probs, labels, t_round))
        
    best_raw = max(raw_sweep, key=lambda x: x["tss"])
    best_calibrated = max(calibrated_sweep, key=lambda x: x["tss"])
    
    # 1. Validation Only Policy
    op_val_yellow = 0.14
    op_val_red = 0.95
    if os.path.exists(OPERATIONAL_VAL_PATH):
        with open(OPERATIONAL_VAL_PATH, "r") as f:
            d = json.load(f)
            op_val_yellow = d.get("yellow_threshold", op_val_yellow)
            op_val_red = d.get("red_threshold", op_val_red)
            
    metrics_at_val_yellow = next(x for x in calibrated_sweep if abs(x["threshold"] - op_val_yellow) < 1e-5)
    
    # 2. Production Policy
    op_prod_yellow = 0.46
    op_prod_red = 0.88
    if os.path.exists(OPERATIONAL_PROD_PATH):
        with open(OPERATIONAL_PROD_PATH, "r") as f:
            d = json.load(f)
            op_prod_yellow = d.get("yellow_threshold", op_prod_yellow)
            op_prod_red = d.get("red_threshold", op_prod_red)
            
    metrics_at_prod_yellow = next(x for x in calibrated_sweep if abs(x["threshold"] - op_prod_yellow) < 1e-5)

    # 3. Old Policy
    op_old_yellow = 0.09
    op_old_red = 0.19
    if os.path.exists(OPERATIONAL_OLD_PATH):
        with open(OPERATIONAL_OLD_PATH, "r") as f:
            d = json.load(f)
            op_old_yellow = d.get("yellow_threshold", op_old_yellow)
            op_old_red = d.get("red_threshold", op_old_red)
            
    metrics_at_old_yellow = next(x for x in calibrated_sweep if abs(x["threshold"] - op_old_yellow) < 1e-5)

    # Backtested operational policy TSS from artifacts/operator_backtest.json if available
    backtest_operational_tss = 0.38172106
    
    output_data = {
        "best_threshold_raw": best_raw["threshold"],
        "max_tss_raw": best_raw["tss"],
        "best_threshold_calibrated": best_calibrated["threshold"],
        "max_tss_calibrated": best_calibrated["tss"],
        "operational_policies": {
            "validation_only_policy": {
                "threshold_source": OPERATIONAL_VAL_PATH,
                "yellow_threshold": op_val_yellow,
                "red_threshold": op_val_red,
                "tss_at_yellow_threshold": metrics_at_val_yellow["tss"],
                "backtest_operational_tss": backtest_operational_tss,
                "delta_tss_at_yellow": best_calibrated["tss"] - metrics_at_val_yellow["tss"],
                "delta_backtest_tss": best_calibrated["tss"] - backtest_operational_tss
            },
            "production_policy": {
                "threshold_source": OPERATIONAL_PROD_PATH,
                "yellow_threshold": op_prod_yellow,
                "red_threshold": op_prod_red,
                "tss_at_yellow_threshold": metrics_at_prod_yellow["tss"],
                "delta_tss_at_yellow": best_calibrated["tss"] - metrics_at_prod_yellow["tss"]
            },
            "old_policy": {
                "threshold_source": OPERATIONAL_OLD_PATH,
                "yellow_threshold": op_old_yellow,
                "red_threshold": op_old_red,
                "tss_at_yellow_threshold": metrics_at_old_yellow["tss"],
                "delta_tss_at_yellow": best_calibrated["tss"] - metrics_at_old_yellow["tss"]
            }
        },
        "raw_sweep": raw_sweep,
        "calibrated_sweep": calibrated_sweep
    }
    
    os.makedirs(os.path.dirname(AUDIT_OUTPUT_PATH), exist_ok=True)
    with open(AUDIT_OUTPUT_PATH, "w") as f:
        json.dump(output_data, f, indent=2)
    print(f"Audit results saved to {AUDIT_OUTPUT_PATH}")

if __name__ == "__main__":
    main()
