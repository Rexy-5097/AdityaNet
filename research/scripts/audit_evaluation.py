import os
import sys
import json
import logging
import numpy as np
import pandas as pd
import torch

# Ensure project root is in python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.ml.dataset import SolarFlareWindowDataset, make_eval_loader
from app.services.ml.model import PatchTST
from app.services.ml.metrics import compute_metrics, compute_prob_metrics

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Paths
BEST_MODEL_PATH  = os.path.join("artifacts", "models", "patchtst_best.pt")
TEST_METRICS_PATH = os.path.join("artifacts", "test_metrics.json")
HISTORY_PATH      = os.path.join("artifacts", "training_history.json")
PROBS_PATH        = os.path.join("artifacts", "calibration", "probs.npy")
LABELS_PATH       = os.path.join("artifacts", "calibration", "labels.npy")
TEST_PARQUET_PATH = os.path.join("artifacts", "research", "test.parquet")

AUDIT_REPORT_PATH = os.path.join("artifacts", "evaluation_audit_report.json")
THRESH_CURVE_PATH = os.path.join("artifacts", "tss_threshold_curve.csv")

def extract_flat_metrics(metrics_dict: dict) -> dict:
    """Flatten metrics dictionary to flat fields."""
    flat = {}
    if "confusion_matrix" in metrics_dict:
        cm = metrics_dict["confusion_matrix"]
        flat["tp"] = cm["tp"]
        flat["fp"] = cm["fp"]
        flat["fn"] = cm["fn"]
        flat["tn"] = cm["tn"]
    else:
        for k in ["tp", "fp", "fn", "tn"]:
            if k in metrics_dict:
                flat[k] = metrics_dict[k]
    
    for k in ["pod", "pofd", "tss", "far", "precision", "recall", "f1", "roc_auc", "pr_auc", "brier_score"]:
        if k in metrics_dict:
            flat[k] = metrics_dict[k]
    return flat

def main():
    print("==================================================")
    print("SuryaNet: Sprint 4.5 Evaluation Pipeline Audit")
    print("==================================================")

    # Check that required files exist
    for p in [BEST_MODEL_PATH, TEST_METRICS_PATH, HISTORY_PATH, PROBS_PATH, LABELS_PATH, TEST_PARQUET_PATH]:
        if not os.path.exists(p):
            logger.error(f"Missing required file: {p}")
            sys.exit(1)

    # 1. Load data
    logger.info("Loading checkpoints and outputs...")
    checkpoint = torch.load(BEST_MODEL_PATH, map_location="cpu", weights_only=True)
    ckpt_threshold = float(checkpoint.get("best_threshold", 0.5))
    logger.info(f"Loaded checkpoint best_threshold = {ckpt_threshold:.6f}")

    with open(TEST_METRICS_PATH, "r") as f:
        original_metrics_raw = json.load(f)
    original_threshold = float(original_metrics_raw.get("threshold", 0.5))
    logger.info(f"Loaded original test_metrics.json threshold = {original_threshold:.6f}")

    saved_probs = np.load(PROBS_PATH)
    saved_labels = np.load(LABELS_PATH)
    logger.info(f"Loaded saved probs shape = {saved_probs.shape}, labels shape = {saved_labels.shape}")

    # 2. Dataset Consistency Check
    logger.info("Verifying dataset consistency against test.parquet...")
    test_df = pd.read_parquet(TEST_PARQUET_PATH, columns=["target_6hr_binary"])
    test_parquet_labels = test_df["target_6hr_binary"].values[360:].astype(np.float32)
    
    parquet_total = len(test_parquet_labels)
    parquet_pos = int(test_parquet_labels.sum())
    parquet_neg = parquet_total - parquet_pos

    saved_total = len(saved_labels)
    saved_pos = int(saved_labels.sum())
    saved_neg = saved_total - saved_pos

    dataset_match = (parquet_total == saved_total) and (parquet_pos == saved_pos) and (parquet_neg == saved_neg)
    
    print("\n--- Dataset Consistency Summary ---")
    print(f"Parquet Test samples:  {parquet_total:,} (Pos: {parquet_pos:,}, Neg: {parquet_neg:,})")
    print(f"saved_labels.npy size:  {saved_total:,} (Pos: {saved_pos:,}, Neg: {saved_neg:,})")
    if dataset_match:
        print("✅ Dataset consistency check: PASS")
    else:
        print("❌ Dataset consistency check: FAIL (Mismatch detected!)")

    # 3. Threshold Sweep on Saved Probabilities
    logger.info("Running threshold sweep on saved probabilities...")
    thresholds = np.arange(0.05, 0.95, 0.01)
    sweep_results = []
    best_sweep_tss = -2.0
    best_sweep_thresh = 0.5

    for t in thresholds:
        preds_t = (saved_probs >= t).astype(int)
        cm_t = compute_metrics(saved_labels, preds_t)
        tss_t = cm_t["tss"]
        sweep_results.append((t, tss_t))
        if tss_t > best_sweep_tss:
            best_sweep_tss = tss_t
            best_sweep_thresh = t

    # Save to CSV
    sweep_df = pd.DataFrame(sweep_results, columns=["threshold", "tss"])
    sweep_df.to_csv(THRESH_CURVE_PATH, index=False)
    logger.info(f"Saved threshold-TSS sweep curve to {THRESH_CURVE_PATH}")
    print(f"Best threshold sweep on test set: {best_sweep_thresh:.2f} yielding TSS: {best_sweep_tss:.4f}")

    # 4. Recompute Metrics directly from saved probabilities
    logger.info(f"Recomputing metrics from saved probabilities using evaluation threshold: {original_threshold:.6f}...")
    saved_preds = (saved_probs >= original_threshold).astype(int)
    recomp_hard = compute_metrics(saved_labels, saved_preds)
    recomp_prob = compute_prob_metrics(saved_labels, saved_probs)
    recomp_metrics = {**recomp_hard, **recomp_prob}

    # 5. Recompute Metrics from a fresh model inference pass
    logger.info("Initializing model for fresh inference pass...")
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    logger.info(f"Using device: {device}")

    # Load feature columns to ensure correct input shape
    with open(os.path.join("artifacts", "feature_columns.json"), "r") as f:
        feature_cols = json.load(f)

    test_ds = SolarFlareWindowDataset(
        parquet_path=TEST_PARQUET_PATH,
        seq_len=360,
        feature_cols=feature_cols,
        split_name="audit_test",
    )
    test_loader = make_eval_loader(
        test_ds,
        batch_size=128,
        num_workers=0,
        shuffle=False,
    )

    model = PatchTST()
    model.load_state_dict(checkpoint["model"])
    model.to(device)
    model.eval()

    fresh_probs = []
    fresh_labels = []

    logger.info("Running inference pass...")
    with torch.no_grad():
        for X, y in test_loader:
            X = X.to(device)
            logits = model(X)
            probs = torch.sigmoid(logits).squeeze(-1)
            fresh_probs.append(probs.cpu().numpy())
            fresh_labels.append(y.numpy())

    fresh_probs = np.concatenate(fresh_probs)
    fresh_labels = np.concatenate(fresh_labels)

    fresh_preds = (fresh_probs >= original_threshold).astype(int)
    fresh_hard_metrics = compute_metrics(fresh_labels, fresh_preds)
    fresh_prob_metrics = compute_prob_metrics(fresh_labels, fresh_probs)
    fresh_metrics = {**fresh_hard_metrics, **fresh_prob_metrics}

    # 6. Mismatch and comparison analysis
    orig_flat = extract_flat_metrics(original_metrics_raw)
    recomp_flat = extract_flat_metrics(recomp_metrics)
    fresh_flat = extract_flat_metrics(fresh_metrics)

    all_keys = sorted(list(set(orig_flat.keys()) | set(recomp_flat.keys()) | set(fresh_flat.keys())))
    
    metric_differences = {}
    mismatch_detected = False
    tolerance = 0.001

    print("\n" + "=" * 80)
    print(f"{'Metric':<20} | {'Original (metrics.json)':<23} | {'Recomputed (probs.npy)':<23} | {'Fresh Inference':<20}")
    print("-" * 80)
    
    for k in all_keys:
        v_orig = orig_flat.get(k, float('nan'))
        v_recomp = recomp_flat.get(k, float('nan'))
        v_fresh = fresh_flat.get(k, float('nan'))
        
        diff_recomp = abs(v_orig - v_recomp) if not (np.isnan(v_orig) or np.isnan(v_recomp)) else 0.0
        diff_fresh = abs(v_orig - v_fresh) if not (np.isnan(v_orig) or np.isnan(v_fresh)) else 0.0
        max_diff = max(diff_recomp, diff_fresh)
        
        metric_differences[k] = {
            "orig_vs_recomp": float(diff_recomp),
            "orig_vs_fresh": float(diff_fresh),
            "max_diff": float(max_diff)
        }
        
        if max_diff > tolerance:
            mismatch_detected = True
            mark = "❌ Mismatch"
        else:
            mark = "✅"

        print(f"{k:<20} | {v_orig:<23.6f} | {v_recomp:<23.6f} | {v_fresh:<20.6f} {mark}")

    print("=" * 80)

    thresholds_match = abs(ckpt_threshold - original_threshold) < 1e-5
    if not thresholds_match:
        logger.warning(f"Threshold mismatch! Checkpoint: {ckpt_threshold}, test_metrics.json: {original_threshold}")
        mismatch_detected = True

    # Final Verdict
    if dataset_match and not mismatch_detected:
        verdict = "PASS"
        print("\n🏆 FINAL AUDIT VERDICT: PASS (All metrics and dataset counts agree within 0.001 tolerance)")
    else:
        verdict = "FAIL"
        print("\n❌ FINAL AUDIT VERDICT: FAIL (Significant mismatches or dataset inconsistencies detected)")

    # 7. Save audit report
    report = {
        "original_metrics": orig_flat,
        "recomputed_metrics": recomp_flat,
        "fresh_inference_metrics": fresh_flat,
        "threshold_used": original_threshold,
        "checkpoint_threshold": ckpt_threshold,
        "thresholds_match": thresholds_match,
        "dataset_consistency": {
            "test_parquet_total": int(parquet_total),
            "test_parquet_pos": int(parquet_pos),
            "test_parquet_neg": int(parquet_neg),
            "saved_labels_total": int(saved_total),
            "saved_labels_pos": int(saved_pos),
            "saved_labels_neg": int(saved_neg),
            "passed": bool(dataset_match)
        },
        "metric_differences": metric_differences,
        "pass_or_fail": verdict,
        "best_test_threshold_sweep": {
            "threshold": float(best_sweep_thresh),
            "tss": float(best_sweep_tss)
        }
    }

    with open(AUDIT_REPORT_PATH, "w") as f:
        json.dump(report, f, indent=2)
    logger.info(f"Saved audit report → {AUDIT_REPORT_PATH}")

    if verdict == "FAIL":
        sys.exit(1)

if __name__ == "__main__":
    main()
