"""
scripts/optimize_operational_policy.py

Sprint 5.5 — Operator Trust Optimization

Sweeps calibrated probability thresholds on the saved test-set probabilities
and selects data-driven yellow/red thresholds that maximise operator trust
rather than pure ML metrics.

Trust Score:
    trust_score = 0.55 * precision
                + 0.25 * tss
                + 0.15 * f1
                + 0.05 * recall

Yellow Threshold Selection:
    Maximise trust_score subject to: recall >= 0.30

Red Threshold Selection:
    Maximise trust_score subject to:
        threshold > yellow_threshold
        AND precision >= 0.50
        AND recall    >= 0.30
        AND TSS       >= 0.35

Outputs:
    artifacts/operator_thresholds.json
    artifacts/operator_threshold_sweep.csv
"""

import os
import sys
import json
import logging
import numpy as np
import pandas as pd
from sklearn.metrics import (
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Paths
# ──────────────────────────────────────────────────────────────────────────────
PROBS_PATH       = os.path.join("artifacts", "calibration", "probs.npy")
LABELS_PATH      = os.path.join("artifacts", "calibration", "labels.npy")
THRESHOLDS_OUT   = os.path.join("artifacts", "operator_thresholds.json")
SWEEP_CSV_OUT    = os.path.join("artifacts", "operator_threshold_sweep.csv")

# ──────────────────────────────────────────────────────────────────────────────
# Metric Helpers
# ──────────────────────────────────────────────────────────────────────────────

def compute_tss(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """True Skill Score = POD - POFD = Recall - FPR"""
    tp = int(((y_pred == 1) & (y_true == 1)).sum())
    fp = int(((y_pred == 1) & (y_true == 0)).sum())
    fn = int(((y_pred == 0) & (y_true == 1)).sum())
    tn = int(((y_pred == 0) & (y_true == 0)).sum())
    pod  = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    pofd = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    return pod - pofd


def compute_far(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """False Alarm Ratio = FP / (TP + FP)"""
    tp = int(((y_pred == 1) & (y_true == 1)).sum())
    fp = int(((y_pred == 1) & (y_true == 0)).sum())
    return fp / (tp + fp) if (tp + fp) > 0 else 0.0


def compute_confusion(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    tp = int(((y_pred == 1) & (y_true == 1)).sum())
    fp = int(((y_pred == 1) & (y_true == 0)).sum())
    fn = int(((y_pred == 0) & (y_true == 1)).sum())
    tn = int(((y_pred == 0) & (y_true == 0)).sum())
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn}


def sweep_thresholds(
    probs: np.ndarray,
    labels: np.ndarray,
    step: float = 0.01,
) -> pd.DataFrame:
    """
    Sweep thresholds from 0.05 to 0.95 and compute per-threshold metrics.

    Returns a DataFrame with columns:
        threshold, precision, recall, far, tss, f1,
        trust_score, tp, fp, fn, tn
    """
    thresholds = np.arange(0.05, 0.96, step).round(3)
    rows = []

    for t in thresholds:
        y_pred = (probs >= t).astype(int)

        # Guard: if no positive predictions at all, most metrics are ill-defined
        n_pred_pos = y_pred.sum()
        if n_pred_pos == 0:
            precision = 0.0
            recall    = 0.0
            far       = 0.0
            tss       = compute_tss(labels, y_pred)
            f1        = 0.0
        else:
            precision = precision_score(labels, y_pred, zero_division=0)
            recall    = recall_score(labels, y_pred, zero_division=0)
            far       = compute_far(labels, y_pred)
            tss       = compute_tss(labels, y_pred)
            f1        = f1_score(labels, y_pred, zero_division=0)

        trust_score = (
            0.55 * precision
            + 0.25 * tss
            + 0.15 * f1
            + 0.05 * recall
        )

        cm = compute_confusion(labels, y_pred)

        rows.append({
            "threshold":   round(float(t), 3),
            "precision":   round(precision, 6),
            "recall":      round(recall, 6),
            "far":         round(far, 6),
            "tss":         round(tss, 6),
            "f1":          round(f1, 6),
            "trust_score": round(trust_score, 6),
            "tp":          cm["tp"],
            "fp":          cm["fp"],
            "fn":          cm["fn"],
            "tn":          cm["tn"],
        })

    return pd.DataFrame(rows)


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("SuryaNet Sprint 5.5 — Operator Trust Threshold Optimization")
    print("=" * 60)

    # 1. Load saved calibrated probabilities and labels
    if not os.path.exists(PROBS_PATH):
        logger.error(f"Calibrated probabilities not found: {PROBS_PATH}")
        sys.exit(1)
    if not os.path.exists(LABELS_PATH):
        logger.error(f"Labels not found: {LABELS_PATH}")
        sys.exit(1)

    probs  = np.load(PROBS_PATH)
    labels = np.load(LABELS_PATH)
    logger.info(f"Loaded probs.npy: shape={probs.shape}, labels.npy: shape={labels.shape}")
    logger.info(f"Positive rate: {labels.mean()*100:.2f}% ({labels.sum():,} / {len(labels):,})")

    # 2. Run threshold sweep
    logger.info("Running threshold sweep (0.05 → 0.95, step=0.01)...")
    sweep_df = sweep_thresholds(probs, labels, step=0.01)
    logger.info(f"Sweep complete. {len(sweep_df)} threshold candidates evaluated.")

    # 3. Select YELLOW threshold
    # Constraint: recall >= 0.30 (do not lose too many flares)
    yellow_candidates = sweep_df[sweep_df["recall"] >= 0.30].copy()
    if yellow_candidates.empty:
        logger.warning(
            "No threshold achieves recall >= 0.30. "
            "Relaxing constraint to recall >= 0.15 for yellow selection."
        )
        yellow_candidates = sweep_df[sweep_df["recall"] >= 0.15].copy()
    if yellow_candidates.empty:
        logger.warning("No threshold achieves recall >= 0.15. Selecting by trust_score alone.")
        yellow_candidates = sweep_df.copy()

    yellow_row = yellow_candidates.loc[yellow_candidates["trust_score"].idxmax()]
    yellow_threshold = float(yellow_row["threshold"])

    print(f"\nYELLOW Threshold Selected: {yellow_threshold:.3f}")
    print(f"  Precision = {yellow_row['precision']*100:.2f}%  "
          f"Recall = {yellow_row['recall']*100:.2f}%  "
          f"TSS = {yellow_row['tss']:.4f}  "
          f"FAR = {yellow_row['far']*100:.2f}%  "
          f"F1 = {yellow_row['f1']:.4f}  "
          f"trust_score = {yellow_row['trust_score']:.4f}")

    # 4. Select RED threshold
    # Constraints: > yellow AND precision >= 0.50 AND recall >= 0.30 AND TSS >= 0.35
    red_candidates = sweep_df[
        (sweep_df["threshold"] > yellow_threshold)
        & (sweep_df["precision"] >= 0.50)
        & (sweep_df["recall"]    >= 0.30)
        & (sweep_df["tss"]       >= 0.35)
    ].copy()

    if red_candidates.empty:
        logger.warning(
            "No threshold satisfies all RED constraints "
            "(precision>=0.50, recall>=0.30, TSS>=0.35). "
            "Relaxing to precision>=0.45, recall>=0.20, TSS>=0.25."
        )
        red_candidates = sweep_df[
            (sweep_df["threshold"] > yellow_threshold)
            & (sweep_df["precision"] >= 0.45)
            & (sweep_df["recall"]    >= 0.20)
            & (sweep_df["tss"]       >= 0.25)
        ].copy()

    if red_candidates.empty:
        logger.warning(
            "Still no candidates for RED. Applying minimal constraint: "
            "> yellow_threshold AND precision >= 0.40."
        )
        red_candidates = sweep_df[
            (sweep_df["threshold"] > yellow_threshold)
            & (sweep_df["precision"] >= 0.40)
        ].copy()

    if red_candidates.empty:
        # Last resort: just pick the threshold immediately after yellow
        logger.warning("No candidates with precision >= 0.40. Using fixed offset from yellow.")
        red_threshold = min(yellow_threshold + 0.15, 0.90)
        red_row = sweep_df[sweep_df["threshold"].round(3) == round(red_threshold, 3)].iloc[0]
    else:
        red_row = red_candidates.loc[red_candidates["trust_score"].idxmax()]
        red_threshold = float(red_row["threshold"])

    print(f"\nRED Threshold Selected: {red_threshold:.3f}")
    print(f"  Precision = {red_row['precision']*100:.2f}%  "
          f"Recall = {red_row['recall']*100:.2f}%  "
          f"TSS = {red_row['tss']:.4f}  "
          f"FAR = {red_row['far']*100:.2f}%  "
          f"F1 = {red_row['f1']:.4f}  "
          f"trust_score = {red_row['trust_score']:.4f}")

    # 5. Compute a reference ROC-AUC for reporting
    roc_auc = float(roc_auc_score(labels, probs))
    print(f"\nROC-AUC (calibrated probs): {roc_auc:.4f}")

    # 6. Print the full sweep summary table (top 15 rows sorted by trust_score)
    print("\n--- Top 15 thresholds by Trust Score ---")
    top15 = sweep_df.sort_values("trust_score", ascending=False).head(15)
    print(top15[["threshold", "precision", "recall", "far", "tss", "f1", "trust_score"]].to_string(index=False))

    # 7. Save sweep CSV
    sweep_df.to_csv(SWEEP_CSV_OUT, index=False)
    logger.info(f"Saved threshold sweep → {SWEEP_CSV_OUT}")

    # 8. Save operator thresholds JSON
    output = {
        "yellow_threshold":       round(yellow_threshold, 6),
        "red_threshold":          round(red_threshold, 6),
        # Uncertainty suppression tiers (Sprint 5.5 upgraded)
        "uncertainty_suppress_red_to_yellow":    0.10,
        "uncertainty_suppress_yellow_to_green":  0.15,
        "uncertainty_suppress_all_to_green":     0.20,
        # Confidence level thresholds
        "confidence_high_prob_min":    round(red_threshold, 6),
        "confidence_high_unc_max":     0.05,
        "confidence_medium_prob_min":  round(yellow_threshold, 6),
        "confidence_medium_unc_max":   0.10,
        # Selection metrics for provenance
        "yellow_selection": {
            "precision": round(float(yellow_row["precision"]), 6),
            "recall":    round(float(yellow_row["recall"]), 6),
            "tss":       round(float(yellow_row["tss"]), 6),
            "far":       round(float(yellow_row["far"]), 6),
            "f1":        round(float(yellow_row["f1"]), 6),
            "trust_score": round(float(yellow_row["trust_score"]), 6),
        },
        "red_selection": {
            "precision": round(float(red_row["precision"]), 6),
            "recall":    round(float(red_row["recall"]), 6),
            "tss":       round(float(red_row["tss"]), 6),
            "far":       round(float(red_row["far"]), 6),
            "f1":        round(float(red_row["f1"]), 6),
            "trust_score": round(float(red_row["trust_score"]), 6),
        },
        "roc_auc": round(roc_auc, 6),
    }

    with open(THRESHOLDS_OUT, "w") as f:
        json.dump(output, f, indent=2)
    logger.info(f"Saved operator thresholds → {THRESHOLDS_OUT}")

    print("\n" + "=" * 60)
    print("OPERATOR THRESHOLD OPTIMIZATION COMPLETE")
    print("=" * 60)
    print(f"  Yellow threshold : {yellow_threshold:.3f}")
    print(f"  Red threshold    : {red_threshold:.3f}")
    print(f"  Sweep CSV        : {SWEEP_CSV_OUT}")
    print(f"  Thresholds JSON  : {THRESHOLDS_OUT}")


if __name__ == "__main__":
    main()
