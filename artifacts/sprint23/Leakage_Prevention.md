# Sprint 23 — Leakage Prevention

**Conclusion:** The Sprint 5.5 leak is now structurally unrepeatable through five independent layers, each mapped to the specific failure that Sprint 22.5 proved. The load-bearing defence is dataset-fingerprint verification (the leak was *proven* by fingerprint identity, so fingerprint identity is what the system now re-verifies at every startup); string/token checks are tripwires layered on top. Gate 4 demonstrated all six rejection pathways fire (output in `Validation_Report.md`).

## How the original leak happened (Sprint 22.5, condensed)

1. `train_patchtst.py` saved held-out-split predictions to `artifacts/calibration/probs.npy`/`labels.npy` (lines 315, 327–329).
2. `optimize_operational_policy.py` swept those arrays (its docstring says so, line 6) and wrote `operator_thresholds.json`.
3. `inference.py` loaded that file by default (line 86); the no-arg endpoint instantiation sealed it.
4. A validation-only fix was computed 37 minutes later (Sprint 5.6) and never wired in.
5. Nothing at any point *checked* what data a policy came from.

## The five layers, mapped to the failure each prevents

| Layer | Mechanism | Sprint 5.5 failure it closes |
|-------|-----------|------------------------------|
| **1. Structural generation** | Generators have no dataset parameter: the path is a module constant built from `_REQUIRED_DATASET_BASENAME = "validation.parquet"`; `_assert_validation_only()` re-checks before any read and raises `NonValidationDatasetError` **naming the detected dataset**; output written only after all guards, atomically | Step 2 — a generator *could be pointed* at saved test arrays. Now there is nothing to point |
| **2. Declared provenance** | 13 mandatory fields; a policy without `dataset_used`, `dataset_fingerprint`, `generator_script`, `generator_commit` etc. cannot load (`PolicySchemaError`) | Step 5 — the leaked file carried no provenance at all, so nothing could have caught it |
| **3. Leakage guard (gen + load)** | (a) `QUARANTINE_REASON` marker → refuse; (b) `dataset_used` = /contains `"test"` → refuse; (c) fingerprint blocklist — **1,806,313 windows / 419,150 positives**, the exact proven-leaked fingerprint from `04_leakage_proof.md` Condition A → refuse even if `dataset_used` lies; (d) banned tokens in any policy string value; (e) banned tokens in the recorded generator's source: `evaluate_test(`, `test.parquet`, `calibration/probs.npy`, `calibration/labels.npy` — the four exact references in the proven chain (`01_dependency_graph.md` nodes 9–11) | Steps 1–2 — the specific arrays and calls the leak flowed through are now contraband |
| **4. Startup re-verification** | SHA256 of the dataset file recomputed from disk and compared to the policy's fingerprint; generator script hash recomputed and compared to `generator_commit`; versions and split identity checked; abort on first failure, exact condition logged | Step 3 — production consumed values with no idea where they came from |
| **5. Integrity sealing** | Self-hash over canonical JSON; any post-signing edit → `PolicyIntegrityError` | Step 4 analogue — silent in-place mutation of the "one mutable json" is impossible; changes require regeneration through layers 1–4 |

## Honest limitations (recorded so nobody over-trusts the tripwires)

- **Token scanning is a tripwire, not proof.** A determined actor could generate from test data without banned tokens. That is why layer 4's fingerprint verification is the load-bearing check: the policy must name a dataset file whose bytes hash to the recorded value, and the blocklist rejects the known test fingerprint. Extending the blocklist when new splits are created is a maintenance duty (single constant: `LEAKED_TEST_FINGERPRINTS`).
- **The guard scans the recorded generator's source, not its imports.** Rationale documented in Sprint 22 planning: negative mentions (e.g., Sprint 5.6's own `_NOT_LOADED` exclusion list contains `test.parquet`) make deep source scanning false-positive-prone. The promotion script is therefore token-clean by construction, and the substantive lineage proof is the fingerprint plus the source artifact's verified `test_data_used: false` stamps.
- **`generator_commit` is a file hash, not a git commit** — the repository has no git (`MIGRATION_REPORT.md:39`). Initializing git (GAP-008) would strengthen this field.
- **Uncertainty tiers remain non-data-derived** Sprint 5.5 constants, now labelled as such in `tier_provenance` rather than laundered. Deriving them properly is Sprint 22 Phase-1 (WP4) work.

## Verified rejection pathways (Gate 4, all PASS)

1. Quarantined archived policy · 2. `dataset_used == "test"` · 3. `dataset_used` containing `"test"` · 4. known leaked fingerprint 1806313/419150 · 5. generator source containing `evaluate_test(` · 6. generation-time doc referencing `calibration/probs.npy`.
