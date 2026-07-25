"""
app/services/ml/policy.py

Sprint 23 — Versioned Operator Policy System.

Replaces the single mutable artifacts/operator_thresholds.json (proven test-set
leaked in artifacts/sprint22_5/04_leakage_proof.md) with a provenance-tracked,
integrity-checked, leakage-gated policy artifact.

Design anchors (Sprint 22.5):
  - The leak was proven via dataset fingerprint (N=1,806,313 / 419,150 positives
    == test split) and exact metric reproduction. The load-bearing defence here
    is therefore fingerprint verification, not string matching.
  - The leaked generator chain used evaluate_test() output saved to
    artifacts/calibration/*.npy. Those exact references are banned tokens in any
    policy generator source.
  - No policy loads without complete provenance metadata, a valid self-hash,
    and a passing leakage guard. Startup additionally verifies the dataset
    fingerprint, split identity, generator version, schema version, and
    scientific version — and aborts loudly on any failure.

This module is deliberately stdlib-only (no torch/pandas) so the policy layer
can be tested without the ML runtime.
"""

import os
import json
import hashlib
import logging

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────────────

SCHEMA_VERSION = "1.0"
SUPPORTED_SCHEMA_VERSIONS = {"1.0"}

# Scientific version binds a policy to a model+calibrator generation.
# V1-2026.06 = patchtst_best.pt (epoch 3) + calibrator.pkl (isotonic,
# validation-fit), both of 2026-06-15.
SUPPORTED_SCIENTIFIC_VERSIONS = {"V1-2026.06"}

SUPPORTED_OPERATOR_VERSION_MAJOR = 2

ACTIVE_POLICY_PATH = os.path.join("artifacts", "policies", "operator_policy_v2.json")

EXPECTED_DATASET_IDENTITY = "validation"
EXPECTED_SPLIT_IDENTIFIER = "research_v1_validation_2020-01-01_2022-12-31"

# The 13 provenance fields every policy artifact must carry (Sprint 23 brief).
REQUIRED_PROVENANCE_FIELDS = (
    "policy_id",
    "creation_timestamp",
    "generator_script",
    "generator_commit",
    "dataset_used",
    "dataset_fingerprint",
    "calibration_source",
    "threshold_generation_method",
    "validation_split_identifier",
    "approval_status",
    "scientific_version",
    "operator_version",
    "sha256",
)

REQUIRED_THRESHOLD_KEYS = (
    "yellow_threshold",
    "red_threshold",
    "uncertainty_suppress_red_to_yellow",
    "uncertainty_suppress_yellow_to_green",
    "uncertainty_suppress_all_to_green",
    "confidence_high_prob_min",
    "confidence_high_unc_max",
    "confidence_medium_prob_min",
    "confidence_medium_unc_max",
)

REQUIRED_FINGERPRINT_KEYS = ("path", "sha256", "n_windows", "n_positive_windows")

# Known-leak blocklist: the exact fingerprint of the test-split arrays that
# produced the quarantined Sprint 5.5 policy (artifacts/sprint22_5/04_leakage_proof.md,
# Condition A: N=1,806,313 windows, 419,150 positives).
LEAKED_TEST_FINGERPRINTS = (
    {"n_windows": 1806313, "n_positive_windows": 419150},
)

# Banned source tokens: the exact references through which the Sprint 5.5 leak
# flowed (see artifacts/sprint22_5/01_dependency_graph.md). Any policy whose
# recorded generator source contains one of these is rejected.
BANNED_GENERATOR_TOKENS = (
    "evaluate_test(",
    "test.parquet",
    "calibration/probs.npy",
    "calibration/labels.npy",
)


# ──────────────────────────────────────────────────────────────────────────────
# Exceptions
# ──────────────────────────────────────────────────────────────────────────────

class PolicyError(Exception):
    """Base class for all operator-policy failures."""


class PolicySchemaError(PolicyError):
    """Policy artifact is structurally invalid (missing fields, bad schema version)."""


class PolicyIntegrityError(PolicyError):
    """Policy artifact content does not match its recorded self-hash."""


class PolicyProvenanceError(PolicyError):
    """A startup provenance check failed (fingerprint, split, generator, version)."""


class PolicyLeakageError(PolicyError):
    """Policy is, or derives from, test-split data. Never loadable."""


class NonValidationDatasetError(PolicyError):
    """A policy generator was pointed at a non-validation dataset."""


# ──────────────────────────────────────────────────────────────────────────────
# Hashing
# ──────────────────────────────────────────────────────────────────────────────

def sha256_of_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_policy_sha256(doc: dict) -> str:
    """
    Self-hash convention: SHA256 over the canonical JSON serialization of the
    policy document with its own "sha256" field set to the empty string.
    """
    shadow = dict(doc)
    shadow["sha256"] = ""
    payload = json.dumps(shadow, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def sign_policy(doc: dict) -> dict:
    """Return a copy of the document with a freshly computed self-hash."""
    signed = dict(doc)
    signed["sha256"] = canonical_policy_sha256(doc)
    return signed


# ──────────────────────────────────────────────────────────────────────────────
# Leakage guard (component 4) — runs at generation time AND load time
# ──────────────────────────────────────────────────────────────────────────────

def _iter_strings(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for k, v in obj.items():
            yield from _iter_strings(k)
            yield from _iter_strings(v)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            yield from _iter_strings(v)


def leakage_guard(doc: dict, repo_root: str = ".") -> None:
    """
    Reject any policy that is or derives from test-split data.

    Checks (each raises PolicyLeakageError with the failing condition):
      1. Quarantine marker present.
      2. dataset_used equals "test" or contains "test" as a substring.
      3. dataset_fingerprint matches a known leaked test fingerprint.
      4. Any string value in the document contains a banned generator token.
      5. The recorded generator script's source (if present on disk) contains
         a banned generator token.
    """
    if "QUARANTINE_REASON" in doc:
        raise PolicyLeakageError(
            f"Policy carries QUARANTINE_REASON={doc['QUARANTINE_REASON']!r}: "
            "quarantined artifacts must never load."
        )

    dataset = str(doc.get("dataset_used", ""))
    if dataset.lower() == "test" or "test" in dataset.lower():
        raise PolicyLeakageError(
            f"dataset_used={dataset!r} is or contains 'test': test-derived "
            "policies are never loadable."
        )

    fp = doc.get("dataset_fingerprint") or {}
    for leaked in LEAKED_TEST_FINGERPRINTS:
        if (
            fp.get("n_windows") == leaked["n_windows"]
            and fp.get("n_positive_windows") == leaked["n_positive_windows"]
        ):
            raise PolicyLeakageError(
                f"dataset_fingerprint {fp.get('n_windows')}/{fp.get('n_positive_windows')} "
                "matches the proven leaked test-split fingerprint "
                "(artifacts/sprint22_5/04_leakage_proof.md, Condition A)."
            )

    for s in _iter_strings(doc):
        for token in BANNED_GENERATOR_TOKENS:
            if token in s:
                raise PolicyLeakageError(
                    f"Policy document contains banned test-data reference {token!r} "
                    f"in value {s!r}."
                )

    gen_rel = doc.get("generator_script", "")
    gen_path = os.path.join(repo_root, gen_rel) if gen_rel else ""
    if gen_path and os.path.exists(gen_path):
        with open(gen_path, "r", encoding="utf-8", errors="replace") as f:
            source = f.read()
        for token in BANNED_GENERATOR_TOKENS:
            if token in source:
                raise PolicyLeakageError(
                    f"Generator script {gen_rel} references banned test-data "
                    f"token {token!r}."
                )


# ──────────────────────────────────────────────────────────────────────────────
# Policy object + loader (component 1)
# ──────────────────────────────────────────────────────────────────────────────

class OperatorPolicy:
    """Loaded, schema-valid, integrity-checked, leakage-gated operator policy."""

    def __init__(self, doc: dict, path: str):
        self.raw = doc
        self.path = path
        self.thresholds = doc["thresholds"]

    @property
    def metadata(self) -> dict:
        md = {field: self.raw[field] for field in REQUIRED_PROVENANCE_FIELDS}
        md["schema_version"] = self.raw["schema_version"]
        return md

    @property
    def policy_id(self) -> str:
        return self.raw["policy_id"]

    def __repr__(self) -> str:
        return (
            f"OperatorPolicy(id={self.raw['policy_id']!r}, "
            f"dataset={self.raw['dataset_used']!r}, "
            f"operator_version={self.raw['operator_version']!r})"
        )


def load_policy(path: str, repo_root: str = ".") -> OperatorPolicy:
    """
    Load a policy artifact. Raises (never returns a degraded policy) on:
      PolicySchemaError    — missing/unsupported schema, missing provenance or
                             threshold fields
      PolicyIntegrityError — self-hash mismatch
      PolicyLeakageError   — any leakage-guard condition
    """
    if not os.path.exists(path):
        raise PolicySchemaError(f"Policy file not found: {path}")

    with open(path, "r") as f:
        try:
            doc = json.load(f)
        except json.JSONDecodeError as exc:
            raise PolicySchemaError(f"Policy file {path} is not valid JSON: {exc}")

    # Quarantine marker is checked before anything else so archived leaked
    # artifacts are rejected with the leakage error, not an incidental schema one.
    if "QUARANTINE_REASON" in doc:
        raise PolicyLeakageError(
            f"Refusing to load {path}: QUARANTINE_REASON="
            f"{doc['QUARANTINE_REASON']!r} (see artifacts/archive/README.md)."
        )

    schema = doc.get("schema_version")
    if schema not in SUPPORTED_SCHEMA_VERSIONS:
        raise PolicySchemaError(
            f"Unsupported or missing schema_version={schema!r} "
            f"(supported: {sorted(SUPPORTED_SCHEMA_VERSIONS)})."
        )

    missing = [f for f in REQUIRED_PROVENANCE_FIELDS if not doc.get(f)]
    if missing:
        raise PolicySchemaError(
            f"Policy is missing required provenance fields: {missing}. "
            "No policy without complete metadata may load."
        )

    fp = doc["dataset_fingerprint"]
    if not isinstance(fp, dict):
        raise PolicySchemaError("dataset_fingerprint must be an object.")
    fp_missing = [k for k in REQUIRED_FINGERPRINT_KEYS if k not in fp]
    if fp_missing:
        raise PolicySchemaError(f"dataset_fingerprint missing keys: {fp_missing}.")

    thresholds = doc.get("thresholds")
    if not isinstance(thresholds, dict):
        raise PolicySchemaError("Policy has no 'thresholds' object.")
    t_missing = [k for k in REQUIRED_THRESHOLD_KEYS if k not in thresholds]
    if t_missing:
        raise PolicySchemaError(f"thresholds missing keys: {t_missing}.")

    expected = canonical_policy_sha256(doc)
    if doc["sha256"] != expected:
        raise PolicyIntegrityError(
            f"Policy self-hash mismatch for {path}: recorded {doc['sha256'][:16]}…, "
            f"recomputed {expected[:16]}… — content was modified after signing."
        )

    leakage_guard(doc, repo_root=repo_root)

    return OperatorPolicy(doc, path)


# ──────────────────────────────────────────────────────────────────────────────
# Startup provenance enforcement (component 3)
# ──────────────────────────────────────────────────────────────────────────────

def validate_policy_at_startup(
    policy: OperatorPolicy,
    repo_root: str = ".",
    verify_dataset_hash: bool = True,
) -> dict:
    """
    Production startup validation. Verifies, in order:
      1. dataset identity   (dataset_used == "validation")
      2. split identity     (validation_split_identifier matches expected)
      3. dataset fingerprint (recomputed SHA256 of the dataset file matches)
      4. generator version  (recomputed SHA256 of generator script matches
                             generator_commit)
      5. schema version     (supported)
      6. scientific version (supported)
      7. approval status    (== "approved")
      8. leakage guard      (defence in depth; already ran at load)

    Raises PolicyProvenanceError / PolicyLeakageError naming the exact failing
    condition. Never continues to a degraded state.
    Returns a check report dict on success.
    """
    doc = policy.raw
    report = {}

    def _fail(condition: str, detail: str):
        logger.error(f"POLICY STARTUP VALIDATION FAILED — {condition}: {detail}")
        raise PolicyProvenanceError(f"{condition}: {detail}")

    # 1. dataset identity
    if doc["dataset_used"] != EXPECTED_DATASET_IDENTITY:
        _fail(
            "dataset_identity",
            f"dataset_used={doc['dataset_used']!r}, expected "
            f"{EXPECTED_DATASET_IDENTITY!r}",
        )
    report["dataset_identity"] = "PASS"

    # 2. split identity
    if doc["validation_split_identifier"] != EXPECTED_SPLIT_IDENTIFIER:
        _fail(
            "split_identity",
            f"validation_split_identifier={doc['validation_split_identifier']!r}, "
            f"expected {EXPECTED_SPLIT_IDENTIFIER!r}",
        )
    report["split_identity"] = "PASS"

    # 3. dataset fingerprint
    fp = doc["dataset_fingerprint"]
    ds_path = os.path.join(repo_root, fp["path"])
    if verify_dataset_hash:
        if not os.path.exists(ds_path):
            _fail("dataset_fingerprint", f"dataset file not found: {fp['path']}")
        actual = sha256_of_file(ds_path)
        if actual != fp["sha256"]:
            _fail(
                "dataset_fingerprint",
                f"SHA256 of {fp['path']} is {actual[:16]}…, policy records "
                f"{str(fp['sha256'])[:16]}…",
            )
    report["dataset_fingerprint"] = "PASS"

    # 4. generator version
    gen_path = os.path.join(repo_root, doc["generator_script"])
    if not os.path.exists(gen_path):
        _fail("generator_version", f"generator script not found: {doc['generator_script']}")
    gen_hash = "sha256:" + sha256_of_file(gen_path)
    if doc["generator_commit"] != gen_hash:
        _fail(
            "generator_version",
            f"generator script hash {gen_hash[:23]}… does not match recorded "
            f"generator_commit {str(doc['generator_commit'])[:23]}…",
        )
    report["generator_version"] = "PASS"

    # 5. schema version (re-checked here so the startup report is complete)
    if doc["schema_version"] not in SUPPORTED_SCHEMA_VERSIONS:
        _fail("schema_version", f"unsupported: {doc['schema_version']!r}")
    report["schema_version"] = "PASS"

    # 6. scientific version
    if doc["scientific_version"] not in SUPPORTED_SCIENTIFIC_VERSIONS:
        _fail(
            "scientific_version",
            f"{doc['scientific_version']!r} not in supported set "
            f"{sorted(SUPPORTED_SCIENTIFIC_VERSIONS)}",
        )
    report["scientific_version"] = "PASS"

    # 6b. operator version compatibility
    try:
        major = int(str(doc["operator_version"]).split(".")[0])
    except (ValueError, IndexError):
        _fail("operator_version", f"unparseable: {doc['operator_version']!r}")
    if major != SUPPORTED_OPERATOR_VERSION_MAJOR:
        _fail(
            "operator_version",
            f"major version {major} incompatible with supported major "
            f"{SUPPORTED_OPERATOR_VERSION_MAJOR}",
        )
    report["operator_version"] = "PASS"

    # 7. approval status
    if doc["approval_status"] != "approved":
        _fail("approval_status", f"{doc['approval_status']!r} != 'approved'")
    report["approval_status"] = "PASS"

    # 8. leakage guard (defence in depth)
    leakage_guard(doc, repo_root=repo_root)
    report["leakage_guard"] = "PASS"

    logger.info(
        f"Policy startup validation PASSED for {doc['policy_id']} "
        f"({len(report)} checks): {report}"
    )
    return report
