"""
scripts/sprint23/promote_sprint56_policy.py

Sprint 23 — Promote the Sprint 5.6 validation-only thresholds into the
versioned, provenance-tracked operator policy system (schema 1.0).

Per artifacts/sprint22_5/06_fix_specification.md (Variant A): the Sprint 5.6
artifact artifacts/operator_thresholds_validation_only.json was derived
exclusively from validation predictions (scripts/refine_thresholds.py,
Sprint 5.6 Task E) and honestly backtested (artifacts/operator_backtest.json).
This script wraps those values in the Sprint 23 policy schema with complete
provenance metadata, verifies every stamp, and refuses to produce output if
any check fails.

NOTE ON SOURCE HYGIENE: this file is recorded as the policy's generator_script
and its source is scanned at every policy load for banned test-data tokens
(app/services/ml/policy.py BANNED_GENERATOR_TOKENS). It must never reference
the leaked prediction arrays or the held-out split's parquet.
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
    PolicyProvenanceError,
    canonical_policy_sha256,
    leakage_guard,
    load_policy,
    sha256_of_file,
    validate_policy_at_startup,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

SOURCE_POLICY_PATH = os.path.join("artifacts", "operator_thresholds_validation_only.json")
BACKTEST_PATH = os.path.join("artifacts", "operator_backtest.json")
_REQUIRED_DATASET_BASENAME = "validation.parquet"
DATASET_PATH = os.path.join("artifacts", "research", _REQUIRED_DATASET_BASENAME)
SEQ_LEN = 360


def _assert_validation_only(path: str) -> None:
    """Whitelist guard: the only dataset this promotion may fingerprint is the
    validation parquet. Raises with the detected dataset name otherwise."""
    base = os.path.basename(path)
    if base != _REQUIRED_DATASET_BASENAME or "validation" not in path:
        raise NonValidationDatasetError(
            f"Non-validation dataset detected: {base!r} (path: {path}). "
            "Promotion aborted; no output produced."
        )


def _verify_source_stamps(src: dict) -> None:
    """The Sprint 5.6 artifact self-stamps its data isolation. Verify every stamp."""
    if src.get("data_used_for_selection") != "validation":
        raise PolicyProvenanceError(
            f"Source policy stamp data_used_for_selection="
            f"{src.get('data_used_for_selection')!r}, expected 'validation'. Aborting."
        )
    if src.get("test_data_used") is not False:
        raise PolicyProvenanceError(
            f"Source policy stamp test_data_used={src.get('test_data_used')!r}, "
            "expected False. Aborting."
        )
    if src.get("validation_parquet") != DATASET_PATH:
        raise PolicyProvenanceError(
            f"Source policy references dataset {src.get('validation_parquet')!r}, "
            f"expected {DATASET_PATH!r}. Aborting."
        )


def _cross_check_counts(src: dict, parquet_rows: int) -> tuple[int, int]:
    """Derive window/positive counts from the source's confusion matrices and
    cross-check them against each other and the parquet row count."""
    y = src["yellow_selection_metrics"]
    r = src["red_selection_metrics"]

    n_windows_y = y["tp"] + y["fp"] + y["fn"] + y["tn"]
    n_windows_r = r["tp"] + r["fp"] + r["fn"] + r["tn"]
    n_pos_y = y["tp"] + y["fn"]
    n_pos_r = r["tp"] + r["fn"]

    if n_windows_y != n_windows_r or n_pos_y != n_pos_r:
        raise PolicyProvenanceError(
            f"Source confusion matrices disagree: windows {n_windows_y} vs "
            f"{n_windows_r}, positives {n_pos_y} vs {n_pos_r}. Aborting."
        )
    if n_windows_y != src["n_validation_windows"]:
        raise PolicyProvenanceError(
            f"Confusion-matrix window count {n_windows_y} != recorded "
            f"n_validation_windows {src['n_validation_windows']}. Aborting."
        )
    if parquet_rows - SEQ_LEN != n_windows_y:
        raise PolicyProvenanceError(
            f"Dataset rows {parquet_rows} - seq_len {SEQ_LEN} = "
            f"{parquet_rows - SEQ_LEN} != window count {n_windows_y}. Aborting."
        )
    return n_windows_y, n_pos_y


def main() -> None:
    print("=" * 70)
    print("Sprint 23 — Promotion of Sprint 5.6 validation-only policy to v2 schema")
    print("=" * 70)

    # 1. Load and verify the Sprint 5.6 source artifact
    with open(SOURCE_POLICY_PATH, "r") as f:
        src = json.load(f)
    _verify_source_stamps(src)
    logger.info("Source stamps verified: data_used_for_selection=validation, "
                "test_data_used=False")

    # 2. Fingerprint the validation dataset (whitelist-guarded)
    _assert_validation_only(DATASET_PATH)
    import pyarrow.parquet as pq
    parquet_rows = pq.ParquetFile(DATASET_PATH).metadata.num_rows
    logger.info(f"Hashing dataset {DATASET_PATH} ({parquet_rows:,} rows)...")
    dataset_sha = sha256_of_file(DATASET_PATH)
    n_windows, n_positive = _cross_check_counts(src, parquet_rows)
    logger.info(f"Cross-checks passed: {n_windows:,} windows, {n_positive:,} positives")

    # 3. Backtest lineage (honest, hourly-stride evaluation of these thresholds)
    with open(BACKTEST_PATH, "r") as f:
        backtest = json.load(f)
    if backtest.get("thresholds_source") != SOURCE_POLICY_PATH:
        raise PolicyProvenanceError(
            f"Backtest thresholds_source={backtest.get('thresholds_source')!r} "
            f"does not match {SOURCE_POLICY_PATH!r}. Aborting."
        )

    # 4. Build the v2 policy document
    generator_rel = os.path.join("scripts", "sprint23", "promote_sprint56_policy.py")
    doc = {
        "schema_version": SCHEMA_VERSION,
        "policy_id": "operator_policy_v2.0.0",
        "creation_timestamp": datetime.now(timezone.utc).isoformat(),
        "generator_script": generator_rel,
        "generator_commit": "sha256:" + sha256_of_file(os.path.abspath(__file__)),
        "dataset_used": "validation",
        "dataset_fingerprint": {
            "path": DATASET_PATH,
            "sha256": dataset_sha,
            "parquet_rows": parquet_rows,
            "n_windows": n_windows,
            "n_positive_windows": n_positive,
        },
        "calibration_source": (
            "artifacts/calibrator.pkl (isotonic; fit on validation predictions, "
            "scripts/calibrate_model.py lines 191-202; selection on validation "
            "Brier, lines 222-262)"
        ),
        "threshold_generation_method": (
            "Validation-only trust-score sweep 0.05-0.95 step 0.01 on calibrated "
            "validation probabilities; trust_score = "
            + src["trust_score_formula"]
            + "; red constraint relaxation: " + src["red_constraint_relaxation"]
            + " (Sprint 5.6 Task E, scripts/refine_thresholds.py). Promoted per "
            "artifacts/sprint22_5/06_fix_specification.md Variant A."
        ),
        "validation_split_identifier": EXPECTED_SPLIT_IDENTIFIER,
        "approval_status": "approved",
        "scientific_version": "V1-2026.06",
        "operator_version": "2.0.0",
        "thresholds": {
            "yellow_threshold": src["yellow_threshold"],
            "red_threshold": src["red_threshold"],
            # Uncertainty tiers and confidence cutoffs are Sprint 5.5 design
            # constants (hardcoded in the original inference service), NOT
            # data-derived. Carried forward per 06_fix_specification.md Variant A
            # with that provenance made explicit here.
            "uncertainty_suppress_red_to_yellow": 0.10,
            "uncertainty_suppress_yellow_to_green": 0.15,
            "uncertainty_suppress_all_to_green": 0.20,
            "confidence_high_prob_min": src["red_threshold"],
            "confidence_high_unc_max": 0.05,
            "confidence_medium_prob_min": src["yellow_threshold"],
            "confidence_medium_unc_max": 0.10,
            "tier_provenance": "hardcoded_design_constants_sprint_5.5_not_data_derived",
        },
        "lineage": {
            "source_artifact": SOURCE_POLICY_PATH,
            "source_generator": "scripts/refine_thresholds.py (Sprint 5.6 Task E)",
            "calibrator_method": src["calibrator_method"],
            "yellow_selection_metrics_validation": src["yellow_selection_metrics"],
            "red_selection_metrics_validation": src["red_selection_metrics"],
            "honest_backtest": {
                "artifact": BACKTEST_PATH,
                "TSS": backtest["TSS"],
                "Precision": backtest["Precision"],
                "Recall": backtest["Recall"],
                "EventRecall": backtest["EventRecall"],
                "FalseEpisodesPerMonth": backtest["FalseEpisodesPerMonth"],
                "n_windows_evaluated": backtest["n_windows_evaluated"],
                "hourly_stride_minutes": backtest["hourly_stride_minutes"],
            },
            "known_limitations": (
                "red_threshold=0.95 produced 0 RED alerts in the honest backtest "
                "(alert_distribution RED: 0) — the RED tier is effectively "
                "disabled at this operating point. Accepted as stopgap per "
                "06_fix_specification.md Variant A; the Sprint 22 cost-loss "
                "policy (Variant B) is the planned successor."
            ),
        },
    }

    # 5. Sign, guard, and self-validate BEFORE any file is written
    doc["sha256"] = canonical_policy_sha256(doc)
    leakage_guard(doc, repo_root=".")
    logger.info("Generation-time leakage guard: PASS")

    # 6. Atomic write: temp file, full load + startup validation, then rename
    os.makedirs(os.path.dirname(ACTIVE_POLICY_PATH), exist_ok=True)
    tmp_path = ACTIVE_POLICY_PATH + ".tmp"
    with open(tmp_path, "w") as f:
        json.dump(doc, f, indent=2)

    policy = load_policy(tmp_path)
    report = validate_policy_at_startup(policy)
    os.replace(tmp_path, ACTIVE_POLICY_PATH)

    print(f"\nPromoted policy written → {ACTIVE_POLICY_PATH}")
    print(f"policy_id          : {doc['policy_id']}")
    print(f"dataset_used       : {doc['dataset_used']}")
    print(f"dataset sha256     : {dataset_sha[:32]}…")
    print(f"windows/positives  : {n_windows:,} / {n_positive:,}")
    print(f"yellow/red         : {doc['thresholds']['yellow_threshold']} / "
          f"{doc['thresholds']['red_threshold']}")
    print(f"startup validation : {report}")


if __name__ == "__main__":
    main()
