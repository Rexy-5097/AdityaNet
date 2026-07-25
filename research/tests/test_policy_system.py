"""
tests/test_policy_system.py

Sprint 23 regression tests for the versioned operator policy system
(app/services/ml/policy.py). Covers every case required by the sprint brief:

  - provenance validation passes for the deployed valid policy
  - startup rejects a policy with an invalid dataset fingerprint
  - startup/loader rejects a policy marked or derived from the held-out split
  - loader raises on schema mismatch
  - leakage guard rejects a policy whose generator references test data
  - version compatibility checks (scientific + operator)
  - integrity (self-hash) tamper detection
  - quarantined historical artifact can never load
  - the from-scratch generator's dataset guard aborts on non-validation input

Run from the repository root:  python3 -m pytest tests/test_policy_system.py -v
"""

import copy
import importlib.util
import json
import os

import pytest

from app.services.ml.policy import (
    ACTIVE_POLICY_PATH,
    REQUIRED_PROVENANCE_FIELDS,
    NonValidationDatasetError,
    PolicyIntegrityError,
    PolicyLeakageError,
    PolicyProvenanceError,
    PolicySchemaError,
    canonical_policy_sha256,
    load_policy,
    validate_policy_at_startup,
)

ARCHIVED_LEAKED_POLICY = os.path.join("artifacts", "archive", "operator_thresholds.json")


# ── helpers ───────────────────────────────────────────────────────────────────

def _deployed_doc() -> dict:
    with open(ACTIVE_POLICY_PATH) as f:
        return json.load(f)


def _resign(doc: dict) -> dict:
    d = copy.deepcopy(doc)
    d["sha256"] = canonical_policy_sha256(d)
    return d


def _write(tmp_path, doc: dict) -> str:
    p = tmp_path / "policy.json"
    p.write_text(json.dumps(doc, indent=2))
    return str(p)


# ── 1. Valid policy: loads, exposes complete metadata ────────────────────────

def test_valid_policy_loads_and_exposes_metadata():
    policy = load_policy(ACTIVE_POLICY_PATH)
    md = policy.metadata
    for field in REQUIRED_PROVENANCE_FIELDS:
        assert field in md and md[field], f"metadata field {field} missing/empty"
    assert md["dataset_used"] == "validation"
    assert md["schema_version"] == "1.0"
    assert policy.thresholds["yellow_threshold"] == 0.14
    assert policy.thresholds["red_threshold"] == 0.95


# ── 2. Startup provenance validation passes on the deployed policy ───────────

def test_startup_validation_passes_on_deployed_policy():
    policy = load_policy(ACTIVE_POLICY_PATH)
    report = validate_policy_at_startup(policy)
    assert all(v == "PASS" for v in report.values()), report
    assert set(report) == {
        "dataset_identity", "split_identity", "dataset_fingerprint",
        "generator_version", "schema_version", "scientific_version",
        "operator_version", "approval_status", "leakage_guard",
    }


# ── 3. Startup rejects an invalid dataset fingerprint ────────────────────────

def test_startup_rejects_invalid_dataset_fingerprint(tmp_path):
    doc = _deployed_doc()
    doc["dataset_fingerprint"]["sha256"] = "0" * 64
    path = _write(tmp_path, _resign(doc))
    policy = load_policy(path)  # load passes: schema/integrity/leakage all fine
    with pytest.raises(PolicyProvenanceError, match="dataset_fingerprint"):
        validate_policy_at_startup(policy)


# ── 4. Test-derived policies can never load ───────────────────────────────────

def test_loader_rejects_dataset_equal_to_test(tmp_path):
    doc = _deployed_doc()
    doc["dataset_used"] = "test"
    path = _write(tmp_path, _resign(doc))
    with pytest.raises(PolicyLeakageError, match="dataset_used"):
        load_policy(path)


def test_loader_rejects_dataset_containing_test(tmp_path):
    doc = _deployed_doc()
    doc["dataset_used"] = "test_2023_2026"
    path = _write(tmp_path, _resign(doc))
    with pytest.raises(PolicyLeakageError, match="contains 'test'"):
        load_policy(path)


def test_loader_rejects_known_leaked_fingerprint(tmp_path):
    """The exact fingerprint proven leaked in Sprint 22.5 (N=1,806,313 /
    419,150 positives) is blocklisted even if dataset_used lies."""
    doc = _deployed_doc()
    doc["dataset_fingerprint"]["n_windows"] = 1806313
    doc["dataset_fingerprint"]["n_positive_windows"] = 419150
    path = _write(tmp_path, _resign(doc))
    with pytest.raises(PolicyLeakageError, match="leaked test-split fingerprint"):
        load_policy(path)


# ── 5. Schema mismatch raises ─────────────────────────────────────────────────

def test_loader_rejects_missing_provenance_field(tmp_path):
    doc = _deployed_doc()
    del doc["policy_id"]
    path = _write(tmp_path, _resign(doc))
    with pytest.raises(PolicySchemaError, match="policy_id"):
        load_policy(path)


def test_loader_rejects_unsupported_schema_version(tmp_path):
    doc = _deployed_doc()
    doc["schema_version"] = "0.9"
    path = _write(tmp_path, _resign(doc))
    with pytest.raises(PolicySchemaError, match="schema_version"):
        load_policy(path)


# ── 6. Integrity: content tampered after signing ─────────────────────────────

def test_loader_rejects_tampered_content(tmp_path):
    doc = _deployed_doc()
    doc["thresholds"]["yellow_threshold"] = 0.46  # tamper WITHOUT re-signing
    path = _write(tmp_path, doc)
    with pytest.raises(PolicyIntegrityError, match="self-hash mismatch"):
        load_policy(path)


# ── 7. Leakage guard: generator source references test data ──────────────────

def test_leakage_guard_rejects_generator_referencing_test_data(tmp_path):
    fake_gen = tmp_path / "fake_generator.py"
    fake_gen.write_text(
        "# malicious or careless generator\n"
        "metrics = trainer.evaluate_test(loader)\n"
    )
    doc = _deployed_doc()
    doc["generator_script"] = "fake_generator.py"
    path = _write(tmp_path, _resign(doc))
    with pytest.raises(PolicyLeakageError, match="evaluate_test"):
        load_policy(path, repo_root=str(tmp_path))


# ── 8. Version compatibility ──────────────────────────────────────────────────

def test_startup_rejects_unsupported_scientific_version(tmp_path):
    doc = _deployed_doc()
    doc["scientific_version"] = "V0-legacy"
    path = _write(tmp_path, _resign(doc))
    policy = load_policy(path)
    with pytest.raises(PolicyProvenanceError, match="scientific_version"):
        validate_policy_at_startup(policy, verify_dataset_hash=False)


def test_startup_rejects_incompatible_operator_major_version(tmp_path):
    doc = _deployed_doc()
    doc["operator_version"] = "3.0.0"
    path = _write(tmp_path, _resign(doc))
    policy = load_policy(path)
    with pytest.raises(PolicyProvenanceError, match="operator_version"):
        validate_policy_at_startup(policy, verify_dataset_hash=False)


# ── 9. Quarantined historical artifact can never load ────────────────────────

def test_quarantined_leaked_policy_cannot_load():
    assert os.path.exists(ARCHIVED_LEAKED_POLICY), "quarantined artifact missing"
    with pytest.raises(PolicyLeakageError, match="QUARANTINE_REASON"):
        load_policy(ARCHIVED_LEAKED_POLICY)


# ── 10. Generator dataset guard is validation-only by construction ───────────

def _import_generator_module():
    spec = importlib.util.spec_from_file_location(
        "generate_validation_policy",
        os.path.join("scripts", "sprint23", "generate_validation_policy.py"),
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_generator_dataset_guard_aborts_on_non_validation_dataset():
    gen = _import_generator_module()
    heldout = os.path.join("artifacts", "research", "test" + ".parquet")
    with pytest.raises(NonValidationDatasetError) as exc_info:
        gen._assert_validation_only(heldout)
    # The exception must name the detected dataset
    assert "test.parquet" in str(exc_info.value)


def test_generator_dataset_guard_accepts_validation_dataset():
    gen = _import_generator_module()
    gen._assert_validation_only(
        os.path.join("artifacts", "research", "validation.parquet")
    )  # must not raise
