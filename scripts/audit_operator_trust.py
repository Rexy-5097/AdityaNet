"""
scripts/audit_operator_trust.py

Sprint 5.6 — Task A: Threshold Leakage Audit

Reads source code of calibrate_model.py, optimize_operational_policy.py,
and refine_thresholds.py (if it exists) to determine which dataset was
used for calibration and which was used for threshold selection.

Produces:
    artifacts/operator_trust_audit.json

Rules:
    - No interpretation.
    - No conclusions.
    - Only records verbatim evidence from source code.
"""

import os
import sys
import ast
import json
import re

OUTPUT_PATH = os.path.join("artifacts", "operator_trust_audit.json")

SCRIPTS = {
    "calibrate_model.py":          os.path.join("scripts", "calibrate_model.py"),
    "optimize_operational_policy.py": os.path.join("scripts", "optimize_operational_policy.py"),
    "refine_thresholds.py":        os.path.join("scripts", "refine_thresholds.py"),
}

# Known artifact paths whose provenance is recorded in train_patchtst.py
ARTIFACT_PROVENANCE = {
    "artifacts/calibration/probs.npy": {
        "saved_by":    "scripts/train_patchtst.py",
        "saved_at_line": 328,
        "source_split": "test",
        "evidence": (
            "train_patchtst.py line 18 docstring: "
            "'artifacts/calibration/probs.npy  <- test sigmoid probabilities'. "
            "train_patchtst.py line 315: all_probs collected from trainer.evaluate_test(test_loader). "
            "train_patchtst.py line 328: np.save(os.path.join(CALIB_DIR, 'probs.npy'), all_probs)."
        ),
    },
    "artifacts/calibration/labels.npy": {
        "saved_by":    "scripts/train_patchtst.py",
        "saved_at_line": 329,
        "source_split": "test",
        "evidence": (
            "train_patchtst.py line 19 docstring: "
            "'artifacts/calibration/labels.npy <- test true labels'. "
            "train_patchtst.py line 329: np.save(os.path.join(CALIB_DIR, 'labels.npy'), all_labels)."
        ),
    },
}


def extract_string_literals(source: str, pattern: str) -> list[str]:
    """Extract all string literals from source that contain pattern."""
    found = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if pattern in node.value:
                found.append(node.value)
    return found


def extract_assignments(source: str, var_names: list[str]) -> dict[str, list[str]]:
    """Extract assigned values for named variables via regex (handles os.path.join etc.)."""
    results = {}
    for var in var_names:
        pattern = rf"^{re.escape(var)}\s*=\s*(.+)$"
        matches = re.findall(pattern, source, re.MULTILINE)
        results[var] = matches
    return results


def read_source(path: str) -> str | None:
    if not os.path.exists(path):
        return None
    with open(path, "r") as fh:
        return fh.read()


def audit_calibrate_model(source: str) -> dict:
    """
    Audit calibrate_model.py.

    Key questions:
      1. Which path is used to load probs.npy / labels.npy?
      2. Which dataset is the calibrator fitted on?
      3. Which dataset are metrics evaluated on?
    """
    evidence = []

    # Extract path variable assignments
    assignments = extract_assignments(source, [
        "VAL_PARQUET",
        "TEST_PROBS_PATH",
        "TEST_LABELS_PATH",
    ])
    for var, vals in assignments.items():
        for v in vals:
            evidence.append(f"calibrate_model.py assignment: {var} = {v.strip()}")

    # Extract comment-level descriptions
    for line_no, line in enumerate(source.splitlines(), start=1):
        stripped = line.strip()
        if any(kw in stripped for kw in [
            "probs.npy", "labels.npy", "validation", "test",
            "calibration data", "avoids test leakage", "clean evaluation",
        ]):
            evidence.append(f"calibrate_model.py line {line_no}: {stripped}")

    # Determine calibration dataset
    calibration_dataset = "unknown"
    threshold_dataset = "unknown"

    if "VAL_PARQUET" in source and "fit" in source:
        # Calibrator fit uses val_probs/val_labels
        if "val_probs, val_labels" in source or "val_labels" in source.split("fit(")[0][-200:] if "fit(" in source else "":
            calibration_dataset = "validation"
        for line in source.splitlines():
            if ".fit(" in line:
                if "val_" in line:
                    calibration_dataset = "validation"
                elif "test_" in line:
                    calibration_dataset = "test"

    # Threshold selection dataset
    if "val_probs_calibrated" in source and "sweep_data" in source:
        threshold_dataset = "validation"
    elif "test_probs" in source and ("sweep_data" in source or "threshold" in source.lower()):
        threshold_dataset = "test"

    # Final determination based on where threshold sweep operates
    if "val_probs_calibrated" in source:
        threshold_dataset = "validation"

    return {
        "calibration_dataset":   calibration_dataset,
        "threshold_dataset":     threshold_dataset,
        "evidence":              evidence,
    }


def audit_optimize_operational_policy(source: str) -> dict:
    """
    Audit optimize_operational_policy.py.

    Key question: what data does PROBS_PATH / LABELS_PATH point to?
    """
    evidence = []

    assignments = extract_assignments(source, ["PROBS_PATH", "LABELS_PATH"])
    for var, vals in assignments.items():
        for v in vals:
            evidence.append(f"optimize_operational_policy.py assignment: {var} = {v.strip()}")

    for line_no, line in enumerate(source.splitlines(), start=1):
        stripped = line.strip()
        if any(kw in stripped for kw in [
            "probs.npy", "labels.npy", "calibration", "test", "validation",
        ]):
            evidence.append(f"optimize_operational_policy.py line {line_no}: {stripped}")

    # Resolve provenance of PROBS_PATH
    probs_path_raw = None
    for line in source.splitlines():
        if line.strip().startswith("PROBS_PATH"):
            probs_path_raw = line.strip()

    resolved_dataset = "unknown"
    resolved_evidence = []

    if probs_path_raw and "calibration" in probs_path_raw and "probs.npy" in probs_path_raw:
        key = "artifacts/calibration/probs.npy"
        if key in ARTIFACT_PROVENANCE:
            prov = ARTIFACT_PROVENANCE[key]
            resolved_dataset = prov["source_split"]
            resolved_evidence.append(prov["evidence"])

    return {
        "threshold_dataset":          resolved_dataset,
        "probs_path_raw":             probs_path_raw,
        "provenance_chain":           resolved_evidence,
        "evidence":                   evidence,
    }


def audit_refine_thresholds(source: str | None, path: str) -> dict:
    if source is None:
        return {
            "file_exists":        False,
            "path_checked":       path,
            "threshold_dataset":  "file_not_found",
            "evidence":           [],
        }

    evidence = []
    for line_no, line in enumerate(source.splitlines(), start=1):
        stripped = line.strip()
        if any(kw in stripped for kw in [
            "probs.npy", "labels.npy", "validation", "test", "parquet",
            "threshold", "sweep",
        ]):
            evidence.append(f"refine_thresholds.py line {line_no}: {stripped}")

    threshold_dataset = "unknown"
    if "validation" in source.lower() and ("val_" in source or "val.parquet" in source or "validation.parquet" in source):
        threshold_dataset = "validation"
    elif "test" in source.lower() and ("test_" in source or "test.parquet" in source):
        threshold_dataset = "test"

    return {
        "file_exists":        True,
        "threshold_dataset":  threshold_dataset,
        "evidence":           evidence,
    }


def main():
    print("=" * 60)
    print("SuryaNet Sprint 5.6 — Task A: Threshold Leakage Audit")
    print("=" * 60)

    # Read all sources
    sources = {name: read_source(path) for name, path in SCRIPTS.items()}

    # Audit each script
    cal_audit   = audit_calibrate_model(sources["calibrate_model.py"] or "")
    opt_audit   = audit_optimize_operational_policy(sources["optimize_operational_policy.py"] or "")
    ref_audit   = audit_refine_thresholds(
        sources["refine_thresholds.py"],
        SCRIPTS["refine_thresholds.py"],
    )

    # Determine overall test_data_used_for_optimization
    # optimize_operational_policy.py loads artifacts/calibration/probs.npy
    # which is documented as TEST sigmoid probabilities in train_patchtst.py
    test_data_used_for_optimization = (
        opt_audit["threshold_dataset"] == "test"
    )

    # Build consolidated evidence list
    all_evidence = []

    # Provenance chain for probs.npy
    all_evidence.append(
        "PROVENANCE: train_patchtst.py line 18 (docstring): "
        "'artifacts/calibration/probs.npy  <- test sigmoid probabilities'"
    )
    all_evidence.append(
        "PROVENANCE: train_patchtst.py line 315: "
        "all_probs = trainer.evaluate_test(test_loader) [test split]"
    )
    all_evidence.append(
        "PROVENANCE: train_patchtst.py line 328: "
        "np.save(os.path.join(CALIB_DIR, 'probs.npy'), all_probs)"
    )
    all_evidence.append(
        "PROVENANCE: train_patchtst.py line 66: "
        "TEST_PARQUET = os.path.join('artifacts', 'research', 'test.parquet')"
    )

    # calibrate_model.py evidence
    all_evidence += cal_audit["evidence"]

    # optimize_operational_policy.py evidence
    all_evidence += opt_audit["evidence"]

    # refine_thresholds.py evidence
    all_evidence += ref_audit["evidence"]

    # Build final report
    report = {
        "calibration_dataset": cal_audit["calibration_dataset"],
        "threshold_dataset":   opt_audit["threshold_dataset"],
        "test_data_used_for_optimization": test_data_used_for_optimization,
        "scripts_audited": {
            "calibrate_model.py": {
                "exists":                SCRIPTS["calibrate_model.py"] and os.path.exists(SCRIPTS["calibrate_model.py"]),
                "calibration_dataset":   cal_audit["calibration_dataset"],
                "threshold_dataset":     cal_audit["threshold_dataset"],
            },
            "optimize_operational_policy.py": {
                "exists":               SCRIPTS["optimize_operational_policy.py"] and os.path.exists(SCRIPTS["optimize_operational_policy.py"]),
                "probs_path":           opt_audit.get("probs_path_raw", ""),
                "threshold_dataset":    opt_audit["threshold_dataset"],
                "provenance_chain":     opt_audit["provenance_chain"],
            },
            "refine_thresholds.py": {
                "exists":               ref_audit["file_exists"],
                "threshold_dataset":    ref_audit["threshold_dataset"],
            },
        },
        "artifact_provenance": {
            path: {
                "source_split": meta["source_split"],
                "saved_by":     meta["saved_by"],
                "saved_at_line": meta["saved_at_line"],
            }
            for path, meta in ARTIFACT_PROVENANCE.items()
        },
        "evidence": all_evidence,
    }

    os.makedirs("artifacts", exist_ok=True)
    with open(OUTPUT_PATH, "w") as fh:
        json.dump(report, fh, indent=2)

    print(f"calibration_dataset              : {report['calibration_dataset']}")
    print(f"threshold_dataset                : {report['threshold_dataset']}")
    print(f"test_data_used_for_optimization  : {report['test_data_used_for_optimization']}")
    print(f"evidence items recorded          : {len(all_evidence)}")
    print(f"Saved → {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
