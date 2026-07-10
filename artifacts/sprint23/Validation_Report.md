# Sprint 23 — Validation Report (Quality Gates)

**Conclusion: all five quality gates PASS.** Actual captured output for each gate follows. Gates were run in order; none failed, so no stop condition was triggered.

## Gate 1 — Unit / regression tests (system Python 3.14.4, pytest 9.0.2)

Command: `python3 -m pytest tests/test_policy_system.py -v` (cwd = repo root)

```
collected 15 items

tests/test_policy_system.py::test_valid_policy_loads_and_exposes_metadata PASSED [  6%]
tests/test_policy_system.py::test_startup_validation_passes_on_deployed_policy PASSED [ 13%]
tests/test_policy_system.py::test_startup_rejects_invalid_dataset_fingerprint PASSED [ 20%]
tests/test_policy_system.py::test_loader_rejects_dataset_equal_to_test PASSED [ 26%]
tests/test_policy_system.py::test_loader_rejects_dataset_containing_test PASSED [ 33%]
tests/test_policy_system.py::test_loader_rejects_known_leaked_fingerprint PASSED [ 40%]
tests/test_policy_system.py::test_loader_rejects_missing_provenance_field PASSED [ 46%]
tests/test_policy_system.py::test_loader_rejects_unsupported_schema_version PASSED [ 53%]
tests/test_policy_system.py::test_loader_rejects_tampered_content PASSED [ 60%]
tests/test_policy_system.py::test_leakage_guard_rejects_generator_referencing_test_data PASSED [ 66%]
tests/test_policy_system.py::test_startup_rejects_unsupported_scientific_version PASSED [ 73%]
tests/test_policy_system.py::test_startup_rejects_incompatible_operator_major_version PASSED [ 80%]
tests/test_policy_system.py::test_quarantined_leaked_policy_cannot_load PASSED [ 86%]
tests/test_policy_system.py::test_generator_dataset_guard_aborts_on_non_validation_dataset PASSED [ 93%]
tests/test_policy_system.py::test_generator_dataset_guard_accepts_validation_dataset PASSED [100%]

============================== 15 passed in 0.20s ==============================
```

## Gate 2 — Integration test (venv Python 3.12.12, torch 2.12.1, real model + calibrator)

Command: `./venv/bin/python tests/integration_service_init.py`

```
[1] SuryaNetInferenceService() with defaults (versioned clean policy)
  PASS  policy_id == operator_policy_v2.0.0
  PASS  dataset_used == validation
  PASS  all 13 provenance fields exposed
  PASS  yellow_threshold == 0.14
  PASS  red_threshold == 0.95
  PASS  startup report all PASS
  PASS  model on device
  PASS  calibrator loaded (isotonic)
  startup report: {'dataset_identity': 'PASS', 'split_identity': 'PASS', 'dataset_fingerprint': 'PASS',
                   'generator_version': 'PASS', 'schema_version': 'PASS', 'scientific_version': 'PASS',
                   'operator_version': 'PASS', 'approval_status': 'PASS', 'leakage_guard': 'PASS'}
  generator: scripts/sprint23/promote_sprint56_policy.py (sha256:46209ddd619917c2…)

[2] SuryaNetInferenceService(thresholds_path=<quarantined leaked file>)
  PASS  refused with PolicyLeakageError: Refusing to load artifacts/archive/operator_thresholds.json:
        QUARANTINE_REASON='LEAKED_TEST_DERIVED' (see artifacts/archive/README.md).

INTEGRATION RESULT: PASS (clean policy loads; leaked policy refused)
```

## Gate 3 — Provenance validation of the deployed policy

```
GATE 3 — PROVENANCE VALIDATION of artifacts/policies/operator_policy_v2.json
  PASS  dataset_identity
  PASS  split_identity
  PASS  dataset_fingerprint
  PASS  generator_version
  PASS  schema_version
  PASS  scientific_version
  PASS  operator_version
  PASS  approval_status
  PASS  leakage_guard
  policy_id=operator_policy_v2.0.0 | dataset=validation | split=research_v1_validation_2020-01-01_2022-12-31
  dataset fingerprint sha256=9c1b770f22684abc0a21fb5ba3233cf8… (1,568,399 windows / 63,849 positives)
GATE 3 RESULT: PASS
```

## Gate 4 — Leakage validation (all rejection pathways)

```
GATE 4 — LEAKAGE VALIDATION
  PASS  quarantined leaked policy (archive)
  PASS  dataset_used == "test"
  PASS  dataset_used contains "test"
  PASS  known leaked test fingerprint 1806313/419150
  PASS  generator source references evaluate_test()
  PASS  generation-time guard: doc references calibration/probs.npy
GATE 4 RESULT: PASS (6/6 leakage pathways rejected)
```

## Gate 5 — Repository validation (AgentOS)

Command: `python3 tools/scripts/validate_agentos.py`

```
Warnings                : 0
Overall Grade           : 100/100
Final Status            : PASS
```

## Generation-time evidence (promotion run, 2026-07-03 18:52)

```
Source stamps verified: data_used_for_selection=validation, test_data_used=False
Hashing dataset artifacts/research/validation.parquet (1,568,759 rows)...
Cross-checks passed: 1,568,399 windows, 63,849 positives
Generation-time leakage guard: PASS
Policy startup validation PASSED for operator_policy_v2.0.0 (9 checks)
Promoted policy written → artifacts/policies/operator_policy_v2.json
```
