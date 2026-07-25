"""
scripts/run_calibration_verification.py

Sprint 5.6 — Tasks B, C, D

Task B: Calibration Audit
    Loads probs.npy, labels.npy, calibrator.pkl.
    Computes Raw and Calibrated: Brier Score, ECE (10 bins), ROC-AUC, PR-AUC.
    Saves: artifacts/calibration_audit.json
    Saves: artifacts/calibration_sample.csv (>=10000 rows)

Task C: Precision-Recall Threshold Sweep
    Sweeps 0.05 → 0.95 step 0.01 on calibrated probs.
    Computes per threshold: TP, FP, FN, TN, Precision, Recall, F1, TSS, FAR.
    Saves: artifacts/full_threshold_sweep.csv

Task D: High Confidence Verification
    Extracts top 100, top 500, top 1000 highest calibrated probability predictions.
    Computes: Precision, Recall, Positive count for each group.
    Saves: artifacts/high_confidence_verification.json
"""

import os
import sys
import json
import pickle
import numpy as np
import pandas as pd
from sklearn.metrics import (
    brier_score_loss,
    roc_auc_score,
    average_precision_score,
)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ──────────────────────────────────────────────────────────────────────────────
# Paths
# ──────────────────────────────────────────────────────────────────────────────
PROBS_PATH      = os.path.join("artifacts", "calibration", "probs.npy")
LABELS_PATH     = os.path.join("artifacts", "calibration", "labels.npy")
CALIBRATOR_PATH = os.path.join("artifacts", "calibrator.pkl")

CALIB_AUDIT_PATH   = os.path.join("artifacts", "calibration_audit.json")
CALIB_SAMPLE_PATH  = os.path.join("artifacts", "calibration_sample.csv")
SWEEP_PATH         = os.path.join("artifacts", "full_threshold_sweep.csv")
HC_VERIFY_PATH     = os.path.join("artifacts", "high_confidence_verification.json")


# ──────────────────────────────────────────────────────────────────────────────
# Metric Helpers
# ──────────────────────────────────────────────────────────────────────────────

def compute_ece(probs: np.ndarray, labels: np.ndarray, n_bins: int = 10) -> float:
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    n = len(probs)
    for i in range(n_bins):
        lo = bin_boundaries[i]
        hi = bin_boundaries[i + 1]
        in_bin = (probs >= lo) & (probs < hi) if i < n_bins - 1 else (probs >= lo) & (probs <= hi)
        prop = np.mean(in_bin)
        if prop > 0:
            acc  = np.mean(labels[in_bin])
            conf = np.mean(probs[in_bin])
            ece += prop * abs(conf - acc)
    return float(ece)


def threshold_metrics(probs: np.ndarray, labels: np.ndarray, t: float) -> dict:
    y_pred = (probs >= t).astype(int)
    tp = int(((y_pred == 1) & (labels == 1)).sum())
    fp = int(((y_pred == 1) & (labels == 0)).sum())
    fn = int(((y_pred == 0) & (labels == 1)).sum())
    tn = int(((y_pred == 0) & (labels == 0)).sum())

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall    = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1        = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    pod       = recall
    pofd      = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    tss       = pod - pofd
    far       = fp / (tp + fp) if (tp + fp) > 0 else 0.0

    return {
        "threshold": round(float(t), 3),
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "precision": round(precision, 8),
        "recall":    round(recall,    8),
        "f1":        round(f1,        8),
        "tss":       round(tss,       8),
        "far":       round(far,       8),
    }


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("SuryaNet Sprint 5.6 — Tasks B / C / D")
    print("=" * 60)

    # Validate inputs
    for p in [PROBS_PATH, LABELS_PATH, CALIBRATOR_PATH]:
        if not os.path.exists(p):
            print(f"ERROR: missing file {p}")
            sys.exit(1)

    # Load
    raw_probs = np.load(PROBS_PATH)
    labels    = np.load(LABELS_PATH)
    with open(CALIBRATOR_PATH, "rb") as fh:
        calibrator = pickle.load(fh)

    print(f"raw_probs shape : {raw_probs.shape}")
    print(f"labels shape    : {labels.shape}")
    print(f"positive rate   : {labels.mean()*100:.4f}%")
    print(f"calibrator type : {calibrator.method}")

    # Apply calibrator
    cal_probs = calibrator(raw_probs)

    # ── Task B ─────────────────────────────────────────────────────────────────
    print("\n--- Task B: Calibration Audit ---")

    raw_brier  = float(brier_score_loss(labels, raw_probs))
    cal_brier  = float(brier_score_loss(labels, cal_probs))
    raw_ece    = compute_ece(raw_probs, labels)
    cal_ece    = compute_ece(cal_probs, labels)
    raw_roc    = float(roc_auc_score(labels, raw_probs))
    cal_roc    = float(roc_auc_score(labels, cal_probs))
    raw_pr     = float(average_precision_score(labels, raw_probs))
    cal_pr     = float(average_precision_score(labels, cal_probs))

    calib_audit = {
        "n_samples":              int(len(labels)),
        "positive_rate":          float(labels.mean()),
        "calibrator_method":      calibrator.method,
        "probs_source_file":      PROBS_PATH,
        "labels_source_file":     LABELS_PATH,
        "raw_brier_score":        raw_brier,
        "calibrated_brier_score": cal_brier,
        "raw_ece":                raw_ece,
        "calibrated_ece":         cal_ece,
        "raw_roc_auc":            raw_roc,
        "calibrated_roc_auc":     cal_roc,
        "raw_pr_auc":             raw_pr,
        "calibrated_pr_auc":      cal_pr,
        "brier_delta":            float(cal_brier - raw_brier),
        "ece_delta":              float(cal_ece   - raw_ece),
        "roc_auc_delta":          float(cal_roc   - raw_roc),
        "pr_auc_delta":           float(cal_pr    - raw_pr),
    }

    with open(CALIB_AUDIT_PATH, "w") as fh:
        json.dump(calib_audit, fh, indent=2)
    print(f"Saved calibration_audit.json ({CALIB_AUDIT_PATH})")

    # calibration_sample.csv — at least 10000 rows
    # Stratified sample: keep all positives (if < 10000) + sample negatives
    pos_mask = labels == 1
    neg_mask = labels == 0
    n_pos = pos_mask.sum()
    n_neg_needed = max(10000 - n_pos, 5000)
    n_neg_available = neg_mask.sum()
    neg_indices = np.where(neg_mask)[0]
    rng = np.random.default_rng(seed=42)
    neg_sample = rng.choice(neg_indices, size=min(n_neg_needed, n_neg_available), replace=False)
    pos_indices = np.where(pos_mask)[0]
    all_indices = np.concatenate([pos_indices, neg_sample])
    all_indices.sort()

    sample_df = pd.DataFrame({
        "raw_probability":       raw_probs[all_indices].round(8),
        "calibrated_probability": cal_probs[all_indices].round(8),
        "label":                 labels[all_indices].astype(int),
    })
    sample_df.to_csv(CALIB_SAMPLE_PATH, index=False)
    print(f"Saved calibration_sample.csv — {len(sample_df):,} rows ({CALIB_SAMPLE_PATH})")

    # ── Task C ─────────────────────────────────────────────────────────────────
    print("\n--- Task C: Full Threshold Sweep ---")

    thresholds = np.arange(0.05, 0.96, 0.01).round(3)
    rows = [threshold_metrics(cal_probs, labels, t) for t in thresholds]
    sweep_df = pd.DataFrame(rows)
    sweep_df.to_csv(SWEEP_PATH, index=False)
    print(f"Saved full_threshold_sweep.csv — {len(sweep_df)} rows ({SWEEP_PATH})")

    # ── Task D ─────────────────────────────────────────────────────────────────
    print("\n--- Task D: High Confidence Verification ---")

    sorted_indices = np.argsort(cal_probs)[::-1]   # descending

    def group_metrics(n: int) -> dict:
        idx      = sorted_indices[:n]
        grp_lbl  = labels[idx]
        grp_prob = cal_probs[idx]
        n_pos    = int(grp_lbl.sum())
        n_neg    = n - n_pos
        precision = n_pos / n if n > 0 else 0.0
        recall    = n_pos / int(labels.sum()) if labels.sum() > 0 else 0.0
        return {
            "group_size":          n,
            "positive_count":      n_pos,
            "negative_count":      n_neg,
            "precision":           round(precision, 8),
            "recall":              round(recall,    8),
            "min_probability":     round(float(grp_prob.min()), 8),
            "max_probability":     round(float(grp_prob.max()), 8),
            "mean_probability":    round(float(grp_prob.mean()), 8),
        }

    hc_report = {
        "total_samples":      int(len(labels)),
        "total_positives":    int(labels.sum()),
        "top_100":            group_metrics(100),
        "top_500":            group_metrics(500),
        "top_1000":           group_metrics(1000),
    }

    with open(HC_VERIFY_PATH, "w") as fh:
        json.dump(hc_report, fh, indent=2)
    print(f"Saved high_confidence_verification.json ({HC_VERIFY_PATH})")

    # Print summary table
    print(f"\n{'Group':<10} {'Size':>6} {'TP':>8} {'Precision':>10} {'Recall':>10} {'Min P':>8} {'Max P':>8}")
    for k, v in [("top_100", hc_report["top_100"]),
                 ("top_500", hc_report["top_500"]),
                 ("top_1000", hc_report["top_1000"])]:
        print(f"{k:<10} {v['group_size']:>6} {v['positive_count']:>8} "
              f"{v['precision']:>10.4f} {v['recall']:>10.4f} "
              f"{v['min_probability']:>8.4f} {v['max_probability']:>8.4f}")

    print("\nDone.")


if __name__ == "__main__":
    main()
