"""
tests/integration_service_init.py

Sprint 23 integration test — runs under the project venv (torch required).

  1. Instantiate SuryaNetInferenceService with defaults: it must load the
     versioned clean policy (artifacts/policies/operator_policy_v2.json),
     expose complete provenance metadata, and carry the validation-derived
     thresholds (yellow=0.14, red=0.95).
  2. Instantiate it against the quarantined leaked artifact: it must refuse
     with PolicyLeakageError before the service comes up.

Run:  ./venv/bin/python tests/integration_service_init.py   (cwd = repo root)
Exit code 0 only if both behaviours hold.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.ml.policy import REQUIRED_PROVENANCE_FIELDS, PolicyLeakageError
from app.services.ml.inference import SuryaNetInferenceService

ARCHIVED = os.path.join("artifacts", "archive", "operator_thresholds.json")
failures = []

# ── 1. Clean policy loads into the real production service ───────────────────
print("=" * 70)
print("[1] SuryaNetInferenceService() with defaults (versioned clean policy)")
print("=" * 70)
service = SuryaNetInferenceService()

md = service.policy_metadata
missing = [f for f in REQUIRED_PROVENANCE_FIELDS if not md.get(f)]
checks = [
    ("policy_id == operator_policy_v2.0.0", md.get("policy_id") == "operator_policy_v2.0.0"),
    ("dataset_used == validation",           md.get("dataset_used") == "validation"),
    ("all 13 provenance fields exposed",     not missing),
    ("yellow_threshold == 0.14",             service.yellow_threshold == 0.14),
    ("red_threshold == 0.95",                service.red_threshold == 0.95),
    ("startup report all PASS",              all(v == "PASS" for v in service.policy_startup_report.values())),
    ("model on device",                      service.model is not None),
    ("calibrator loaded (isotonic)",         service.calibrator.method == "isotonic"),
]
for name, ok in checks:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    if not ok:
        failures.append(name)
print(f"  startup report: {service.policy_startup_report}")
print(f"  generator: {md['generator_script']} ({md['generator_commit'][:23]}…)")

# ── 2. Quarantined leaked artifact must be refused ────────────────────────────
print()
print("=" * 70)
print("[2] SuryaNetInferenceService(thresholds_path=<quarantined leaked file>)")
print("=" * 70)
try:
    SuryaNetInferenceService(thresholds_path=ARCHIVED)
    print("  FAIL  quarantined policy was accepted — leakage gate broken")
    failures.append("quarantined policy rejected")
except PolicyLeakageError as exc:
    print(f"  PASS  refused with PolicyLeakageError: {exc}")

print()
if failures:
    print(f"INTEGRATION RESULT: FAIL ({len(failures)} failed): {failures}")
    sys.exit(1)
print("INTEGRATION RESULT: PASS (clean policy loads; leaked policy refused)")
