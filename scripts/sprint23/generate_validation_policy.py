"""
scripts/sprint23/generate_validation_policy.py

Sprint 23 — Validation-only operator policy generator (from scratch).

Generates thresholds exclusively from validation predictions and validation
labels. Structural guarantees that this generator cannot be pointed at the
held-out split by accident:

  1. The dataset path is a module constant assembled from
     _REQUIRED_DATASET_BASENAME = "validation.parquet". There is no CLI
     argument, environment variable, or parameter through which a caller can
     substitute a different dataset.
  2. _assert_validation_only() re-verifies the basename and path immediately
     before any data is read. On any mismatch it raises
     NonValidationDatasetError naming the detected dataset, and no output file
     is produced (the policy is only written after all guards pass, via an
     atomic temp-file rename).
  3. The generation-time leakage guard (app/services/ml/policy.py) runs on the
     constructed document AND on this file's own source before anything is
     written.

NOTE ON SOURCE HYGIENE: this file is recorded as generator_script in any policy
it produces and its source is scanned at every load for banned test-data tokens
(BANNED_GENERATOR_TOKENS in app/services/ml/policy.py). It must never reference
the held-out split's parquet or the leaked prediction arrays.

The Sprint 23 deployment used the promotion path
(scripts/sprint23/promote_sprint56_policy.py) because the Sprint 5.6
validation-only artifact exists and passes all checks; this generator is the
regeneration path for when no clean prior policy exists. Full inference over
the 1,568,399 validation windows takes on the order of hours on MPS.
"""

import os
import sys
import json
import logging
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.services.ml.policy import (
    ACTIVE_POLICY_PATH,
    EXPECTED_SPLIT_IDENTIFIER,
    SCHEMA_VERSION,
    NonValidationDatasetError,
    canonical_policy_sha256,
    leakage_guard,
    load_policy,
    sha256_of_file,
    validate_policy_at_startup,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

# The ONLY dataset this generator can read. No override mechanism exists.
_REQUIRED_DATASET_BASENAME = "validation.parquet"
DATASET_PATH = os.path.join("artifacts", "research", _REQUIRED_DATASET_BASENAME)

MODEL_PATH = os.path.join("artifacts", "models", "patchtst_best.pt")
CALIBRATOR_PATH = os.path.join("artifacts", "calibrator.pkl")
FEATURE_COLS_PATH = os.path.join("artifacts", "feature_columns.json")
SEQ_LEN = 360

# Selection rules — identical to Sprint 5.6 Task E (scripts/refine_thresholds.py)
TRUST_SCORE_FORMULA = "0.55*precision + 0.25*tss + 0.15*f1 + 0.05*recall"


def _assert_validation_only(path: str) -> None:
    """
    Abort immediately (raising with the detected dataset name) if this
    generator is pointed at anything other than the validation parquet.
    Runs before any data is read; on failure no output file is produced.
    """
    base = os.path.basename(path)
    if base != _REQUIRED_DATASET_BASENAME:
        raise NonValidationDatasetError(
            f"Non-validation dataset detected: {base!r} (path: {path}). "
            f"This generator only accepts {_REQUIRED_DATASET_BASENAME!r}. "
            "Generation aborted; no output produced."
        )
    if "validation" not in path:
        raise NonValidationDatasetError(
            f"Non-validation dataset detected: {path!r} does not contain "
            "'validation'. Generation aborted; no output produced."
        )


def _trust_score(precision: float, tss: float, f1: float, recall: float) -> float:
    return 0.55 * precision + 0.25 * tss + 0.15 * f1 + 0.05 * recall


def _threshold_metrics(probs, labels, t: float) -> dict:
    import numpy as np
    y_pred = (probs >= t).astype(int)
    tp = int(((y_pred == 1) & (labels == 1)).sum())
    fp = int(((y_pred == 1) & (labels == 0)).sum())
    fn = int(((y_pred == 0) & (labels == 1)).sum())
    tn = int(((y_pred == 0) & (labels == 0)).sum())
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    pofd = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    tss = recall - pofd
    return {
        "threshold": round(float(t), 3), "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "precision": precision, "recall": recall, "f1": f1, "tss": tss,
        "far": fp / (tp + fp) if (tp + fp) > 0 else 0.0,
        "trust_score": _trust_score(precision, tss, f1, recall),
    }


def _run_validation_inference():
    """Deterministic inference over every validation window. Torch is imported
    lazily so the module (and its guards) can be imported without the ML runtime."""
    import numpy as np
    import torch
    from app.services.ml.dataset import SolarFlareWindowDataset, make_eval_loader
    from app.services.ml.model import PatchTST
    import pickle

    with open(FEATURE_COLS_PATH) as f:
        feature_cols = json.load(f)

    ds = SolarFlareWindowDataset(
        parquet_path=DATASET_PATH, seq_len=SEQ_LEN,
        feature_cols=feature_cols, split_name="validation_sprint23_generator",
    )
    loader = make_eval_loader(ds, batch_size=512, num_workers=0, shuffle=False)

    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    checkpoint = torch.load(MODEL_PATH, map_location="cpu", weights_only=True)
    model = PatchTST()
    model.load_state_dict(checkpoint["model"])
    model.to(device)
    model.eval()

    probs_list, labels_list = [], []
    with torch.no_grad():
        for X, y in loader:
            probs = torch.sigmoid(model(X.to(device))).squeeze(-1)
            probs_list.append(probs.cpu().numpy())
            labels_list.append(y.numpy())
    probs = np.concatenate(probs_list)
    labels = np.concatenate(labels_list)

    with open(CALIBRATOR_PATH, "rb") as f:
        calibrator = pickle.load(f)
    return calibrator(probs), labels, calibrator.method


def _select_thresholds(cal_probs, labels):
    """Sprint 5.6 selection rules on calibrated validation probabilities."""
    import numpy as np
    sweep = [_threshold_metrics(cal_probs, labels, t)
             for t in np.arange(0.05, 0.96, 0.01).round(3)]

    yellow_cands = [r for r in sweep if r["recall"] >= 0.30] \
        or [r for r in sweep if r["recall"] >= 0.15] or sweep
    yellow = max(yellow_cands, key=lambda r: r["trust_score"])

    relaxation = None
    red_cands = [r for r in sweep if r["threshold"] > yellow["threshold"]
                 and r["precision"] >= 0.50 and r["recall"] >= 0.30 and r["tss"] >= 0.35]
    if not red_cands:
        relaxation = "relaxed_to: precision>=0.45, recall>=0.20, tss>=0.25"
        red_cands = [r for r in sweep if r["threshold"] > yellow["threshold"]
                     and r["precision"] >= 0.45 and r["recall"] >= 0.20 and r["tss"] >= 0.25]
    if not red_cands:
        relaxation = "relaxed_to: precision>=0.40, no recall/tss constraint"
        red_cands = [r for r in sweep if r["threshold"] > yellow["threshold"]
                     and r["precision"] >= 0.40]
    if not red_cands:
        relaxation = "fallback: yellow_threshold + 0.15"
        target = min(yellow["threshold"] + 0.15, 0.90)
        red_cands = [r for r in sweep if r["threshold"] == round(target, 3)]
    red = max(red_cands, key=lambda r: r["trust_score"])
    return yellow, red, relaxation


def main() -> None:
    print("=" * 70)
    print("Sprint 23 — Validation-only policy generation (from scratch)")
    print("=" * 70)

    # Guard BEFORE any data is read; abort produces no output file.
    _assert_validation_only(DATASET_PATH)

    import pyarrow.parquet as pq
    parquet_rows = pq.ParquetFile(DATASET_PATH).metadata.num_rows
    logger.info(f"Dataset guard passed: {DATASET_PATH} ({parquet_rows:,} rows)")

    cal_probs, labels, calibrator_method = _run_validation_inference()
    n_windows = int(len(labels))
    n_positive = int(labels.sum())
    if parquet_rows - SEQ_LEN != n_windows:
        raise NonValidationDatasetError(
            f"Window count {n_windows} inconsistent with dataset rows "
            f"{parquet_rows} - {SEQ_LEN}: wrong dataset detected. Aborting."
        )
    logger.info(f"Validation inference complete: {n_windows:,} windows, "
                f"{n_positive:,} positives ({100*n_positive/n_windows:.2f}%)")

    yellow, red, relaxation = _select_thresholds(cal_probs, labels)
    logger.info(f"Selected yellow={yellow['threshold']}, red={red['threshold']} "
                f"(relaxation: {relaxation})")

    logger.info("Hashing dataset for fingerprint...")
    dataset_sha = sha256_of_file(DATASET_PATH)

    generator_rel = os.path.join("scripts", "sprint23", "generate_validation_policy.py")
    doc = {
        "schema_version": SCHEMA_VERSION,
        "policy_id": "operator_policy_v2.1.0",
        "creation_timestamp": datetime.now(timezone.utc).isoformat(),
        "generator_script": generator_rel,
        "generator_commit": "sha256:" + sha256_of_file(os.path.abspath(__file__)),
        "dataset_used": "validation",
        "dataset_fingerprint": {
            "path": DATASET_PATH, "sha256": dataset_sha,
            "parquet_rows": parquet_rows,
            "n_windows": n_windows, "n_positive_windows": n_positive,
        },
        "calibration_source": (
            "artifacts/calibrator.pkl (" + calibrator_method + "; fit on validation "
            "predictions, scripts/calibrate_model.py lines 191-202)"
        ),
        "threshold_generation_method": (
            "Validation-only trust-score sweep 0.05-0.95 step 0.01 on calibrated "
            "validation probabilities; trust_score = " + TRUST_SCORE_FORMULA
            + ("; red constraint relaxation: " + relaxation if relaxation else "")
        ),
        "validation_split_identifier": EXPECTED_SPLIT_IDENTIFIER,
        "approval_status": "approved",
        "scientific_version": "V1-2026.06",
        "operator_version": "2.1.0",
        "thresholds": {
            "yellow_threshold": yellow["threshold"],
            "red_threshold": red["threshold"],
            "uncertainty_suppress_red_to_yellow": 0.10,
            "uncertainty_suppress_yellow_to_green": 0.15,
            "uncertainty_suppress_all_to_green": 0.20,
            "confidence_high_prob_min": red["threshold"],
            "confidence_high_unc_max": 0.05,
            "confidence_medium_prob_min": yellow["threshold"],
            "confidence_medium_unc_max": 0.10,
            "tier_provenance": "hardcoded_design_constants_sprint_5.5_not_data_derived",
        },
        "lineage": {
            "yellow_selection_metrics_validation": yellow,
            "red_selection_metrics_validation": red,
        },
    }

    doc["sha256"] = canonical_policy_sha256(doc)
    leakage_guard(doc, repo_root=".")
    logger.info("Generation-time leakage guard: PASS")

    os.makedirs(os.path.dirname(ACTIVE_POLICY_PATH), exist_ok=True)
    tmp_path = ACTIVE_POLICY_PATH + ".tmp"
    with open(tmp_path, "w") as f:
        json.dump(doc, f, indent=2)
    policy = load_policy(tmp_path)
    report = validate_policy_at_startup(policy)
    os.replace(tmp_path, ACTIVE_POLICY_PATH)

    print(f"\nGenerated policy written → {ACTIVE_POLICY_PATH}")
    print(f"startup validation : {report}")


if __name__ == "__main__":
    main()
