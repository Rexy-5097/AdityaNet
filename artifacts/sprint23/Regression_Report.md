# Sprint 23 — Regression Report

**Conclusion: 15/15 regression tests PASS** (plus the integration test — output in `Validation_Report.md` Gate 2). Every case the sprint brief required is covered, and each test maps to a specific defence layer and, where applicable, to the Sprint 22.5 finding it guards against regressing.

## Coverage map

| Brief requirement | Test(s) | Result | What would regress if it failed |
|-------------------|---------|--------|--------------------------------|
| Provenance validation passes for a valid policy | `test_valid_policy_loads_and_exposes_metadata`, `test_startup_validation_passes_on_deployed_policy` | PASS | Deployed clean policy unloadable → production down (correctly, but urgently) |
| Startup rejects invalid fingerprint | `test_startup_rejects_invalid_dataset_fingerprint` | PASS | A policy could claim any dataset unverified — the exact blindness that hid the Sprint 5.5 leak |
| Startup/loader rejects test-derived policy | `test_loader_rejects_dataset_equal_to_test`, `test_loader_rejects_dataset_containing_test`, `test_loader_rejects_known_leaked_fingerprint` | PASS | Re-introduction of a test-tuned policy; the fingerprint variant specifically pins the proven 1,806,313/419,150 leak (Sprint 22.5 Condition A) |
| Loader raises on schema mismatch | `test_loader_rejects_missing_provenance_field`, `test_loader_rejects_unsupported_schema_version` | PASS | Provenance-free policies (like the leaked one) become loadable again |
| Leakage guard rejects generator referencing test data | `test_leakage_guard_rejects_generator_referencing_test_data` | PASS | A generator calling `evaluate_test()` — the original leak's node 10 — could produce loadable policies |
| Version compatibility check | `test_startup_rejects_unsupported_scientific_version`, `test_startup_rejects_incompatible_operator_major_version` | PASS | A policy tuned for a different model/calibrator generation could silently drive alerts |
| (Additional) integrity sealing | `test_loader_rejects_tampered_content` | PASS | Silent hand-edits to the "one mutable json" — the pre-Sprint-23 failure mode |
| (Additional) quarantine enforcement | `test_quarantined_leaked_policy_cannot_load` | PASS | The archived leaked file becoming consumable |
| (Additional) generator structural guard | `test_generator_dataset_guard_aborts_on_non_validation_dataset`, `..._accepts_validation_dataset` | PASS | The from-scratch generator becoming pointable at the held-out split |

## Actual output

Command: `python3 -m pytest tests/test_policy_system.py -v` · platform darwin, Python 3.14.4, pytest 9.0.2 · cwd = repository root

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

## Notes

- These are the repository's **first automated tests** (GAP-001 in `context/state.md` was "zero tests"); the policy layer now has coverage, the rest of the codebase still does not.
- Tests requiring dataset hashing use the real 138 MB validation parquet (sub-second); version tests isolate their check with `verify_dataset_hash=False`.
- The suite runs without torch by design (`policy.py` is stdlib-only); the torch path is covered by `tests/integration_service_init.py` under the venv.
