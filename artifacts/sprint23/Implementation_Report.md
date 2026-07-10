# Sprint 23 — Implementation Report

**Conclusion:** The corrupted decision layer is replaced. Production `inference.py` now loads a versioned, provenance-stamped, leakage-gated policy (`artifacts/policies/operator_policy_v2.json`, validation-derived, yellow=0.14/red=0.95) instead of the quarantined test-leaked `operator_thresholds.json`. All five quality gates pass with output on record: 15/15 regression tests, full-service integration (clean policy loads, leaked policy refused), 9/9 startup provenance checks, 6/6 leakage pathways rejected, AgentOS repository validation 100/100. No model weights, datasets, or calibration artifacts were touched.

## What was built

| # | Component | Artifact | Status |
|---|-----------|----------|--------|
| 1 | Versioned policy system | `app/services/ml/policy.py` (stdlib-only: schema 1.0, 13 mandatory provenance fields, self-hash integrity, `OperatorPolicy` object exposing metadata on load) | DONE |
| 2 | Validation-only generator | `scripts/sprint23/generate_validation_policy.py` (hardcoded dataset constant, no override parameter, `_assert_validation_only()` raises `NonValidationDatasetError` naming the detected dataset, atomic write only after all guards) | DONE (guard unit-tested; full regeneration not needed — promotion path used per brief) |
| 3 | Startup provenance enforcement | `validate_policy_at_startup()` — dataset fingerprint (SHA256 of dataset file recomputed), dataset identity, split identity, generator version (script hash vs `generator_commit`), schema version, scientific version, operator major version, approval status, leakage guard. Wired into `SuryaNetInferenceService.__init__` | DONE |
| 4 | Leakage guard (gen + load time) | `leakage_guard()` — quarantine marker, `dataset_used` = / contains "test", known-leaked-fingerprint blocklist (1,806,313/419,150 from Sprint 22.5 Condition A), banned tokens in policy strings and generator source (`evaluate_test(`, `test.parquet`, `calibration/probs.npy`, `calibration/labels.npy`) | DONE |
| 5 | Quarantine | `artifacts/archive/operator_thresholds.json` (moved + `QUARANTINE_REASON: LEAKED_TEST_DERIVED` injected, pre-injection SHA256 033063ef… preserved inside), `operator_threshold_sweep.csv` (moved byte-identical, SHA256 4e79cdaa…, sidecar `operator_threshold_sweep.QUARANTINE.json`), `artifacts/archive/README.md` | DONE |
| 6 | Clean policy deployed | Sprint 5.6 validation-only policy promoted by `scripts/sprint23/promote_sprint56_policy.py` → `artifacts/policies/operator_policy_v2.json`; `inference.py` default path = `ACTIVE_POLICY_PATH` | DONE |
| 7 | Regression tests | `tests/test_policy_system.py` (15 tests), `tests/integration_service_init.py`, `tests/conftest.py` | DONE — 15/15 + integration PASS |
| 8 | Quality gates | Gates 1–5 all run with output (see `Validation_Report.md`, `Regression_Report.md`) | DONE |

## Files changed/created

**Created:** `app/services/ml/policy.py` · `scripts/sprint23/promote_sprint56_policy.py` · `scripts/sprint23/generate_validation_policy.py` · `artifacts/policies/operator_policy_v2.json` · `artifacts/archive/{README.md, operator_thresholds.json, operator_threshold_sweep.csv, operator_threshold_sweep.QUARANTINE.json}` · `tests/{conftest.py, test_policy_system.py, integration_service_init.py}` · 8 docs under `artifacts/sprint23/`

**Modified:** `app/services/ml/inference.py` — docstring, policy-module import, default `thresholds_path = ACTIVE_POLICY_PATH`, section 4 replaced with `load_policy` + `validate_policy_at_startup`; service now exposes `self.policy`, `self.policy_metadata`, `self.policy_startup_report`. Alert logic (tiering, suppression, RED confirmation, coincidence filter) unchanged.

**Moved (not deleted):** `artifacts/operator_thresholds.json`, `artifacts/operator_threshold_sweep.csv` → `artifacts/archive/`.

**Untouched, verified:** model checkpoints, all datasets, `artifacts/calibrator.pkl`, all calibration artifacts, all historical reports.

## Sprint 22.5 traceability

Every architectural decision derives from a proven finding: the fingerprint-first defence and the 1,806,313/419,150 blocklist come from `04_leakage_proof.md` Condition A (the leak was proven by exactly that fingerprint plus exact metric reproduction); the four banned tokens are the exact code references the leak flowed through (`01_dependency_graph.md` nodes 9–11); promotion of the Sprint 5.6 policy is `06_fix_specification.md` Variant A; the quarantine format preserves pre-injection hashes because `02_threshold_provenance.md` established hash-based evidence continuity matters in a git-less repository.
