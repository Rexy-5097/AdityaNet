import os
import sys
import json
import logging
import pickle
import numpy as np
import pandas as pd
import torch
import matplotlib.pyplot as plt
from sklearn.linear_model import LogisticRegression
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import brier_score_loss, roc_auc_score, average_precision_score

# Ensure project root is in python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.ml.dataset import SolarFlareWindowDataset, make_eval_loader
from app.services.ml.model import PatchTST
from app.services.ml.metrics import compute_metrics, compute_prob_metrics
from app.services.ml.inference import CalibratorWrapper

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Paths
VAL_PARQUET = os.path.join("artifacts", "research", "validation.parquet")
BEST_MODEL_PATH = os.path.join("artifacts", "models", "patchtst_best.pt")
TEST_PROBS_PATH = os.path.join("artifacts", "calibration", "probs.npy")
TEST_LABELS_PATH = os.path.join("artifacts", "calibration", "labels.npy")

CALIB_DIR = os.path.join("artifacts", "calibration")
REPORT_PATH = os.path.join(CALIB_DIR, "calibration_report.json")
THRESH_REPORT_PATH = os.path.join(CALIB_DIR, "threshold_report.csv")
CALIBRATOR_PKL_PATH = os.path.join("artifacts", "calibrator.pkl")
THRESH_JSON_PATH = os.path.join("artifacts", "operational_thresholds.json")

os.makedirs(CALIB_DIR, exist_ok=True)


# ──────────────────────────────────────────────────────────────────────────────
# Expected Calibration Error (ECE, 10 Bins)
# ──────────────────────────────────────────────────────────────────────────────
def compute_ece(probs: np.ndarray, labels: np.ndarray, n_bins: int = 10) -> float:
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    n_samples = len(probs)
    for i in range(n_bins):
        bin_lower = bin_boundaries[i]
        bin_upper = bin_boundaries[i + 1]
        
        # Include upper boundary in the last bin
        if i == n_bins - 1:
            in_bin = (probs >= bin_lower) & (probs <= bin_upper)
        else:
            in_bin = (probs >= bin_lower) & (probs < bin_upper)
            
        prop_in_bin = np.mean(in_bin)
        if prop_in_bin > 0:
            accuracy_in_bin = np.mean(labels[in_bin])
            avg_confidence_in_bin = np.mean(probs[in_bin])
            ece += prop_in_bin * np.abs(avg_confidence_in_bin - accuracy_in_bin)
    return float(ece)


# ──────────────────────────────────────────────────────────────────────────────
# Reliability Diagram Plotting
# ──────────────────────────────────────────────────────────────────────────────
def plot_reliability_diagram(
    probs: np.ndarray,
    labels: np.ndarray,
    title: str,
    save_path: str,
    n_bins: int = 10,
):
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    bin_centers = 0.5 * (bin_boundaries[:-1] + bin_boundaries[1:])
    
    bin_accuracies = []
    bin_confidences = []
    bin_counts = []
    
    for i in range(n_bins):
        bin_lower = bin_boundaries[i]
        bin_upper = bin_boundaries[i + 1]
        
        if i == n_bins - 1:
            in_bin = (probs >= bin_lower) & (probs <= bin_upper)
        else:
            in_bin = (probs >= bin_lower) & (probs < bin_upper)
            
        if np.sum(in_bin) > 0:
            bin_accuracies.append(np.mean(labels[in_bin]))
            bin_confidences.append(np.mean(probs[in_bin]))
            bin_counts.append(np.sum(in_bin))
        else:
            bin_accuracies.append(0.0)
            bin_confidences.append(bin_centers[i])
            bin_counts.append(0)
            
    ece = compute_ece(probs, labels, n_bins)
    brier = brier_score_loss(labels, probs)
    
    plt.figure(figsize=(6, 6))
    # Plot perfect calibration reference line
    plt.plot([0, 1], [0, 1], linestyle="--", color="gray", label="Perfect Calibration")
    # Plot bin accuracies
    plt.bar(
        bin_centers,
        bin_accuracies,
        width=0.08,
        color="royalblue",
        edgecolor="black",
        alpha=0.7,
        label="Observed Accuracy"
    )
    plt.plot(bin_confidences, bin_accuracies, marker="o", color="blue")
    
    plt.xlim(0.0, 1.0)
    plt.ylim(0.0, 1.0)
    plt.xlabel("Mean Predicted Probability (Confidence)")
    plt.ylabel("Fraction of Positives (Accuracy)")
    plt.title(f"{title}\nBrier: {brier:.4f} | ECE: {ece:.4f}")
    plt.legend(loc="upper left")
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    plt.close()


def main():
    print("==================================================")
    print("SuryaNet: Sprint 5 Calibration & Optimization Pipeline")
    print("==================================================")

    # Validate that required files exist
    for p in [VAL_PARQUET, BEST_MODEL_PATH, TEST_PROBS_PATH, TEST_LABELS_PATH]:
        if not os.path.exists(p):
            logger.error(f"Missing required file: {p}")
            sys.exit(1)

    # 1. Generate Validation predictions (stateless, avoids test leakage)
    logger.info("Generating predictions on the validation set...")
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    
    # Load feature columns
    with open(os.path.join("artifacts", "feature_columns.json"), "r") as f:
        feature_cols = json.load(f)

    val_ds = SolarFlareWindowDataset(
        parquet_path=VAL_PARQUET,
        seq_len=360,
        feature_cols=feature_cols,
        split_name="validation_calib",
    )
    val_loader = make_eval_loader(
        val_ds,
        batch_size=256,
        num_workers=0,
        shuffle=False,
    )

    checkpoint = torch.load(BEST_MODEL_PATH, map_location="cpu", weights_only=True)
    model = PatchTST()
    model.load_state_dict(checkpoint["model"])
    model.to(device)
    model.eval()

    val_probs = []
    val_labels = []

    with torch.no_grad():
        for X, y in val_loader:
            X = X.to(device)
            logits = model(X)
            probs = torch.sigmoid(logits).squeeze(-1)
            val_probs.append(probs.cpu().numpy())
            val_labels.append(y.numpy())

    val_probs = np.concatenate(val_probs)
    val_labels = np.concatenate(val_labels)
    logger.info(f"Generated validation predictions (N={len(val_probs):,})")

    # Load test set predictions (saved by trainer during test evaluation)
    test_probs = np.load(TEST_PROBS_PATH)
    test_labels = np.load(TEST_LABELS_PATH)
    logger.info(f"Loaded test predictions (N={len(test_probs):,})")

    # 2. Fit Calibrators on Validation predictions
    logger.info("Fitting Platt Scaling calibrator...")
    eps = 1e-7
    val_probs_clipped = np.clip(val_probs, eps, 1 - eps)
    val_logits = np.log(val_probs_clipped / (1 - val_probs_clipped)).reshape(-1, 1)

    lr_calib = LogisticRegression(C=1e5, solver="lbfgs")
    lr_calib.fit(val_logits, val_labels)

    logger.info("Fitting Isotonic Regression calibrator...")
    isotonic_calib = IsotonicRegression(out_of_bounds="clip")
    isotonic_calib.fit(val_probs, val_labels)

    # 3. Evaluate Calibrators on the Test predictions (clean evaluation)
    test_logits = np.log(np.clip(test_probs, eps, 1 - eps) / (1 - np.clip(test_probs, eps, 1 - eps))).reshape(-1, 1)
    
    test_probs_platt = lr_calib.predict_proba(test_logits)[:, 1]
    test_probs_isotonic = isotonic_calib.predict(test_probs)

    # Compute metrics for each variant
    def compute_all_metrics(probs, labels):
        brier = float(brier_score_loss(labels, probs))
        ece = float(compute_ece(probs, labels))
        roc_auc = float(roc_auc_score(labels, probs))
        pr_auc = float(average_precision_score(labels, probs))
        return {"brier": brier, "ece": ece, "roc_auc": roc_auc, "pr_auc": pr_auc}

    raw_metrics = compute_all_metrics(test_probs, test_labels)
    platt_metrics = compute_all_metrics(test_probs_platt, test_labels)
    iso_metrics = compute_all_metrics(test_probs_isotonic, test_labels)

    # 4. Automatically select the best calibrator on validation Brier/ECE
    # We compute validation metrics to choose the calibrator to avoid test set snooping
    val_logits_eval = val_logits
    val_probs_platt = lr_calib.predict_proba(val_logits_eval)[:, 1]
    val_probs_isotonic = isotonic_calib.predict(val_probs)

    val_raw_metrics = compute_all_metrics(val_probs, val_labels)
    val_platt_metrics = compute_all_metrics(val_probs_platt, val_labels)
    val_iso_metrics = compute_all_metrics(val_probs_isotonic, val_labels)

    logger.info("Choosing the best calibrator based on validation performance...")
    raw_val_roc = val_raw_metrics["roc_auc"]
    
    candidates = []
    # Candidate 1: Platt Scaling
    platt_val_roc_deg = (raw_val_roc - val_platt_metrics["roc_auc"]) / raw_val_roc if raw_val_roc > 0 else 0.0
    if platt_val_roc_deg < 0.01:
        candidates.append(("platt", lr_calib, val_platt_metrics))
        
    # Candidate 2: Isotonic Regression
    iso_val_roc_deg = (raw_val_roc - val_iso_metrics["roc_auc"]) / raw_val_roc if raw_val_roc > 0 else 0.0
    if iso_val_roc_deg < 0.01:
        candidates.append(("isotonic", isotonic_calib, val_iso_metrics))

    # Select candidate with lowest validation Brier Score
    best_method = "raw"
    winning_model = None
    best_val_brier = val_raw_metrics["brier"]
    best_val_ece = val_raw_metrics["ece"]

    for name, model_obj, m in candidates:
        if m["brier"] < best_val_brier:
            best_method = name
            winning_model = model_obj
            best_val_brier = m["brier"]
            best_val_ece = m["ece"]
        elif m["brier"] == best_val_brier and m["ece"] < best_val_ece:
            best_method = name
            winning_model = model_obj
            best_val_brier = m["brier"]
            best_val_ece = m["ece"]

    logger.info(f"Selected Calibration Method: {best_method.upper()}")

    # 5. Save winning calibrator
    winning_calibrator = CalibratorWrapper(best_method, winning_model)
    with open(CALIBRATOR_PKL_PATH, "wb") as f:
        pickle.dump(winning_calibrator, f)
    logger.info(f"Saved winning calibrator wrapper → {CALIBRATOR_PKL_PATH}")

    # Apply winning calibrator to validation probabilities for threshold optimization
    val_probs_calibrated = winning_calibrator(val_probs)

    # 6. Threshold sweeps with Precision floor constraints on validation
    logger.info("Optimizing thresholds on calibrated validation probabilities...")
    thresholds = np.arange(0.05, 0.95, 0.01)
    sweep_data = []
    
    best_yellow_score = -1.0
    yellow_threshold = 0.5
    
    best_red_score = -1.0
    red_threshold = 0.6
    
    # We find the best threshold using the Score function:
    # Score = 0.40 * Precision + 0.30 * TSS + 0.20 * F1 + 0.10 * Recall
    # Yellow constraints: Precision >= 0.40 (fallback to max Precision if none exist)
    # Red constraints: Precision >= 0.50 and red_threshold > yellow_threshold (fallback to yellow + 0.10)
    
    # First pass: calculate metrics for all thresholds
    for t in thresholds:
        preds = (val_probs_calibrated >= t).astype(int)
        m = compute_metrics(val_labels, preds)
        
        precision = m["precision"]
        tss = m["tss"]
        f1 = m["f1"]
        recall = m["recall"]
        far = m["far"]
        pofd = m["pofd"]
        
        score_yellow = 0.40 * precision + 0.30 * tss + 0.20 * f1 + 0.10 * recall
        score_red = 0.60 * precision + 0.20 * tss + 0.10 * f1 + 0.10 * recall
        
        sweep_data.append({
            "threshold": float(t),
            "tss": float(tss),
            "precision": float(precision),
            "recall": float(recall),
            "f1": float(f1),
            "far": float(far),
            "pofd": float(pofd),
            "score_yellow": float(score_yellow),
            "score_red": float(score_red)
        })

    sweep_df = pd.DataFrame(sweep_data)
    sweep_df.to_csv(THRESH_REPORT_PATH, index=False)
    logger.info(f"Saved threshold sweep report to {THRESH_REPORT_PATH}")

    # Optimize Yellow Threshold (operational_threshold)
    # Target joint constraints: Precision >= 0.40 and Recall >= 0.15 (to prevent 0% recall degenerate solutions)
    yellow_candidates = sweep_df[(sweep_df["precision"] >= 0.40) & (sweep_df["recall"] >= 0.15)]
    if len(yellow_candidates) > 0:
        best_yellow_idx = yellow_candidates["score_yellow"].idxmax()
        yellow_threshold = float(sweep_df.loc[best_yellow_idx, "threshold"])
    else:
        logger.warning("No threshold satisfied both Precision >= 0.40 and Recall >= 0.15. Falling back to Recall >= 0.15 candidates.")
        yellow_fallback = sweep_df[sweep_df["recall"] >= 0.15]
        if len(yellow_fallback) > 0:
            best_yellow_idx = yellow_fallback["score_yellow"].idxmax()
            yellow_threshold = float(sweep_df.loc[best_yellow_idx, "threshold"])
        else:
            yellow_threshold = float(sweep_df.loc[sweep_df["precision"].idxmax(), "threshold"])

    # Optimize Red Threshold
    # Target joint constraints: Precision >= 0.50 and Recall >= 0.10
    red_candidates = sweep_df[(sweep_df["precision"] >= 0.50) & (sweep_df["recall"] >= 0.10) & (sweep_df["threshold"] > yellow_threshold)]
    if len(red_candidates) > 0:
        best_red_idx = red_candidates["score_red"].idxmax()
        red_threshold = float(sweep_df.loc[best_red_idx, "threshold"])
    else:
        logger.warning("No threshold satisfied Red Alert criteria. Falling back to yellow_threshold + 0.10.")
        red_threshold = float(min(0.95, yellow_threshold + 0.10))

    logger.info(f"Optimized Decision Boundaries: Yellow={yellow_threshold:.2f}, Red={red_threshold:.2f}")

    # Save operational thresholds metadata
    thresholds_metadata = {
        "yellow_threshold": yellow_threshold,
        "red_threshold": red_threshold,
        "uncertainty_threshold": 0.08
    }
    with open(THRESH_JSON_PATH, "w") as f:
        json.dump(thresholds_metadata, f, indent=2)
    logger.info(f"Saved operational thresholds to {THRESH_JSON_PATH}")

    # 7. Generate and save Reliability curves
    logger.info("Generating and saving reliability plots...")
    plot_reliability_diagram(
        test_probs, test_labels,
        "Raw PatchTST Reliability Diagram (Test Set)",
        os.path.join(CALIB_DIR, "reliability_raw.png")
    )
    plot_reliability_diagram(
        test_probs_platt, test_labels,
        "Platt Scaled Reliability Diagram (Test Set)",
        os.path.join(CALIB_DIR, "reliability_platt.png")
    )
    plot_reliability_diagram(
        test_probs_isotonic, test_labels,
        "Isotonic Calibrated Reliability Diagram (Test Set)",
        os.path.join(CALIB_DIR, "reliability_isotonic.png")
    )
    logger.info(f"Reliability diagrams saved in {CALIB_DIR}/")

    # 8. Report and Success Criteria Check
    winner_test_metrics = platt_metrics if best_method == "platt" else (iso_metrics if best_method == "isotonic" else raw_metrics)
    
    brier_improvement = ((raw_metrics["brier"] - winner_test_metrics["brier"]) / raw_metrics["brier"]) * 100.0 if raw_metrics["brier"] > 0 else 0.0
    ece_improvement = ((raw_metrics["ece"] - winner_test_metrics["ece"]) / raw_metrics["ece"]) * 100.0 if raw_metrics["ece"] > 0 else 0.0
    roc_deg = ((raw_metrics["roc_auc"] - winner_test_metrics["roc_auc"]) / raw_metrics["roc_auc"]) * 100.0 if raw_metrics["roc_auc"] > 0 else 0.0

    print("\n" + "=" * 60)
    print("CALIBRATION COMPARISON TABLE (TEST SET)")
    print("=" * 60)
    print(f"{'Method':<12} | {'Brier':<8} | {'ECE':<8} | {'ROC-AUC':<8} | {'PR-AUC':<8}")
    print("-" * 60)
    print(f"{'RAW':<12} | {raw_metrics['brier']:.4f}   | {raw_metrics['ece']:.4f}   | {raw_metrics['roc_auc']:.4f}   | {raw_metrics['pr_auc']:.4f}")
    print(f"{'PLATT':<12} | {platt_metrics['brier']:.4f}   | {platt_metrics['ece']:.4f}   | {platt_metrics['roc_auc']:.4f}   | {platt_metrics['pr_auc']:.4f}")
    print(f"{'ISOTONIC':<12} | {iso_metrics['brier']:.4f}   | {iso_metrics['ece']:.4f}   | {iso_metrics['roc_auc']:.4f}   | {iso_metrics['pr_auc']:.4f}")
    print("=" * 60)
    print(f"Selected Calibration Method:  {best_method.upper()}")
    print(f"Brier Score Improvement:      {brier_improvement:+.2f}%")
    print(f"ECE Improvement:              {ece_improvement:+.2f}%")
    print(f"ROC-AUC Degradation:          {roc_deg:.2f}% (Cap: < 1.0%)")
    print("=" * 60)

    # 9. Save Calibration Report
    calibration_report = {
        "raw_metrics": raw_metrics,
        "platt_metrics": platt_metrics,
        "isotonic_metrics": iso_metrics,
        "selected_method": best_method,
        "brier_improvement_percent": float(brier_improvement),
        "ece_improvement_percent": float(ece_improvement),
        "roc_degradation_percent": float(roc_deg),
        "operational_thresholds": thresholds_metadata
    }
    with open(REPORT_PATH, "w") as f:
        json.dump(calibration_report, f, indent=2)
    logger.info(f"Saved calibration report → {REPORT_PATH}")


if __name__ == "__main__":
    main()
