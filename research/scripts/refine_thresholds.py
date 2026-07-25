"""
scripts/refine_thresholds.py

Sprint 5.6 — Task E: Validation-Only Threshold Optimization

IMPORTANT: This script never reads test.parquet, probs.npy, or labels.npy.
All threshold selection is performed exclusively on the validation split.

Procedure:
  1. Load validation.parquet.
  2. Run model inference on all validation windows (no MC Dropout — deterministic,
     model.eval(), no_grad).
  3. Apply the saved calibrator (fitted on validation; calibrator.pkl was selected
     using validation Brier Score in calibrate_model.py).
  4. Sweep thresholds 0.05 → 0.95 step 0.01 on calibrated validation probabilities.
  5. Compute per-threshold: TP, FP, FN, TN, Precision, Recall, F1, TSS, FAR.
  6. Select yellow_threshold and red_threshold using the trust_score formula.
  7. Save artifacts/operator_thresholds_validation_only.json

Selection rules:
  yellow_threshold:
    Maximise trust_score = 0.55*precision + 0.25*tss + 0.15*f1 + 0.05*recall
    Subject to: recall >= 0.30

  red_threshold:
    Maximise trust_score
    Subject to: threshold > yellow_threshold
                AND precision >= 0.50
                AND recall    >= 0.30
                AND tss       >= 0.35
    (cascade-relaxes if no candidate satisfies all constraints)
"""

import os
import sys
import json
import pickle
import logging
import numpy as np
import pandas as pd
import torch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.ml.dataset import SolarFlareWindowDataset, make_eval_loader
from app.services.ml.model import PatchTST

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Paths
# ──────────────────────────────────────────────────────────────────────────────
VAL_PARQUET      = os.path.join("artifacts", "research", "validation.parquet")
MODEL_PATH       = os.path.join("artifacts", "models", "patchtst_best.pt")
CALIBRATOR_PATH  = os.path.join("artifacts", "calibrator.pkl")
FEATURE_COLS_PATH = os.path.join("artifacts", "feature_columns.json")
OUTPUT_PATH      = os.path.join("artifacts", "operator_thresholds_validation_only.json")

# Explicitly list what is NOT loaded to make isolation auditable
_NOT_LOADED = [
    "artifacts/research/test.parquet",
    "artifacts/calibration/probs.npy",
    "artifacts/calibration/labels.npy",
]


# ──────────────────────────────────────────────────────────────────────────────
# Metric Helpers (identical to audit scripts — no shared state)
# ──────────────────────────────────────────────────────────────────────────────

def _tss(tp, fp, fn, tn):
    pod  = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    pofd = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    return pod - pofd


def threshold_metrics_np(probs: np.ndarray, labels: np.ndarray, t: float) -> dict:
    y_pred = (probs >= t).astype(int)
    tp = int(((y_pred == 1) & (labels == 1)).sum())
    fp = int(((y_pred == 1) & (labels == 0)).sum())
    fn = int(((y_pred == 0) & (labels == 1)).sum())
    tn = int(((y_pred == 0) & (labels == 0)).sum())
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall    = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1        = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    tss_val   = _tss(tp, fp, fn, tn)
    far       = fp / (tp + fp) if (tp + fp) > 0 else 0.0
    trust     = 0.55 * precision + 0.25 * tss_val + 0.15 * f1 + 0.05 * recall
    return {
        "threshold": round(float(t), 3),
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "precision":   round(precision, 8),
        "recall":      round(recall,    8),
        "f1":          round(f1,        8),
        "tss":         round(tss_val,   8),
        "far":         round(far,       8),
        "trust_score": round(trust,     8),
    }


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("SuryaNet Sprint 5.6 — Task E: Validation-Only Thresholds")
    print("=" * 60)
    print("Files explicitly NOT loaded (test isolation):")
    for f in _NOT_LOADED:
        print(f"  {f}")

    for p in [VAL_PARQUET, MODEL_PATH, CALIBRATOR_PATH, FEATURE_COLS_PATH]:
        if not os.path.exists(p):
            logger.error(f"Missing required file: {p}")
            sys.exit(1)

    # 1. Load feature columns
    with open(FEATURE_COLS_PATH, "r") as fh:
        feature_cols = json.load(fh)

    # 2. Load validation dataset
    logger.info(f"Loading validation dataset from: {VAL_PARQUET}")
    val_ds = SolarFlareWindowDataset(
        parquet_path=VAL_PARQUET,
        seq_len=360,
        feature_cols=feature_cols,
        split_name="validation_sprint56",
    )
    val_loader = make_eval_loader(val_ds, batch_size=512, num_workers=0, shuffle=False)
    logger.info(f"Validation windows: {len(val_ds):,}")

    # 3. Load model (deterministic eval — no MC Dropout)
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    checkpoint = torch.load(MODEL_PATH, map_location="cpu", weights_only=True)
    model = PatchTST()
    model.load_state_dict(checkpoint["model"])
    model.to(device)
    model.eval()
    logger.info(f"Model loaded onto {device}")

    # 4. Inference on validation (deterministic, no_grad)
    val_probs_list  = []
    val_labels_list = []

    logger.info("Running validation inference (deterministic, model.eval(), no_grad)...")
    with torch.no_grad():
        for X, y in val_loader:
            X = X.to(device)
            logits = model(X)
            probs  = torch.sigmoid(logits).squeeze(-1)
            val_probs_list.append(probs.cpu().numpy())
            val_labels_list.append(y.numpy())

    val_probs  = np.concatenate(val_probs_list)
    val_labels = np.concatenate(val_labels_list)
    logger.info(f"Validation inference complete: N={len(val_probs):,}")
    logger.info(f"Val positive rate: {val_labels.mean()*100:.4f}%")

    # 5. Apply calibrator to validation probabilities
    with open(CALIBRATOR_PATH, "rb") as fh:
        calibrator = pickle.load(fh)

    cal_val_probs = calibrator(val_probs)
    logger.info(f"Calibrator method applied: {calibrator.method}")

    # 6. Threshold sweep on calibrated validation probabilities
    logger.info("Running threshold sweep 0.05 → 0.95 step=0.01 on validation...")
    thresholds = np.arange(0.05, 0.96, 0.01).round(3)
    rows = [threshold_metrics_np(cal_val_probs, val_labels, t) for t in thresholds]
    sweep_df = pd.DataFrame(rows)

    # 7. Select yellow_threshold
    yellow_candidates = sweep_df[sweep_df["recall"] >= 0.30].copy()
    if yellow_candidates.empty:
        logger.warning("No threshold achieves recall >= 0.30 on validation. Relaxing to recall >= 0.15.")
        yellow_candidates = sweep_df[sweep_df["recall"] >= 0.15].copy()
    if yellow_candidates.empty:
        logger.warning("No threshold achieves recall >= 0.15. Selecting by trust_score alone.")
        yellow_candidates = sweep_df.copy()

    yellow_row = yellow_candidates.loc[yellow_candidates["trust_score"].idxmax()]
    yellow_threshold = float(yellow_row["threshold"])

    # 8. Select red_threshold
    red_candidates = sweep_df[
        (sweep_df["threshold"] > yellow_threshold)
        & (sweep_df["precision"] >= 0.50)
        & (sweep_df["recall"]    >= 0.30)
        & (sweep_df["tss"]       >= 0.35)
    ].copy()

    relaxation_applied = None

    if red_candidates.empty:
        relaxation_applied = "relaxed_to: precision>=0.45, recall>=0.20, tss>=0.25"
        red_candidates = sweep_df[
            (sweep_df["threshold"] > yellow_threshold)
            & (sweep_df["precision"] >= 0.45)
            & (sweep_df["recall"]    >= 0.20)
            & (sweep_df["tss"]       >= 0.25)
        ].copy()

    if red_candidates.empty:
        relaxation_applied = "relaxed_to: precision>=0.40, no recall/tss constraint"
        red_candidates = sweep_df[
            (sweep_df["threshold"] > yellow_threshold)
            & (sweep_df["precision"] >= 0.40)
        ].copy()

    if red_candidates.empty:
        relaxation_applied = "fallback: yellow_threshold + 0.15 (no candidates)"
        red_threshold_val = min(float(yellow_threshold) + 0.15, 0.90)
        red_row = sweep_df[sweep_df["threshold"].round(3) == round(red_threshold_val, 3)].iloc[0]
    else:
        red_row = red_candidates.loc[red_candidates["trust_score"].idxmax()]
        red_threshold_val = float(red_row["threshold"])

    # 9. Save output
    output = {
        "data_used_for_selection":        "validation",
        "test_data_used":                 False,
        "files_explicitly_excluded": _NOT_LOADED,
        "validation_parquet":             VAL_PARQUET,
        "n_validation_windows":           int(len(val_probs)),
        "val_positive_rate":              round(float(val_labels.mean()), 8),
        "calibrator_method":              calibrator.method,
        "yellow_threshold":               round(yellow_threshold, 6),
        "red_threshold":                  round(red_threshold_val, 6),
        "yellow_selection_metrics": {
            "precision":   float(yellow_row["precision"]),
            "recall":      float(yellow_row["recall"]),
            "f1":          float(yellow_row["f1"]),
            "tss":         float(yellow_row["tss"]),
            "far":         float(yellow_row["far"]),
            "trust_score": float(yellow_row["trust_score"]),
            "tp": int(yellow_row["tp"]),
            "fp": int(yellow_row["fp"]),
            "fn": int(yellow_row["fn"]),
            "tn": int(yellow_row["tn"]),
        },
        "red_selection_metrics": {
            "precision":   float(red_row["precision"]),
            "recall":      float(red_row["recall"]),
            "f1":          float(red_row["f1"]),
            "tss":         float(red_row["tss"]),
            "far":         float(red_row["far"]),
            "trust_score": float(red_row["trust_score"]),
            "tp": int(red_row["tp"]),
            "fp": int(red_row["fp"]),
            "fn": int(red_row["fn"]),
            "tn": int(red_row["tn"]),
        },
        "red_constraint_relaxation": relaxation_applied,
        "trust_score_formula": "0.55*precision + 0.25*tss + 0.15*f1 + 0.05*recall",
    }

    with open(OUTPUT_PATH, "w") as fh:
        json.dump(output, fh, indent=2)

    print(f"\nyellow_threshold (val-only): {yellow_threshold:.4f}")
    print(f"  precision={yellow_row['precision']:.4f}  recall={yellow_row['recall']:.4f}  "
          f"tss={yellow_row['tss']:.4f}  f1={yellow_row['f1']:.4f}  trust={yellow_row['trust_score']:.4f}")
    print(f"\nred_threshold (val-only): {red_threshold_val:.4f}")
    print(f"  precision={red_row['precision']:.4f}  recall={red_row['recall']:.4f}  "
          f"tss={red_row['tss']:.4f}  f1={red_row['f1']:.4f}  trust={red_row['trust_score']:.4f}")
    if relaxation_applied:
        print(f"  red constraint relaxation: {relaxation_applied}")
    print(f"\nSaved → {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
