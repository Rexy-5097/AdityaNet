# Sprint 23 — Policy Architecture

**Conclusion:** The decision layer is now a three-stage pipeline — **generate → load → startup-validate** — in which every stage can abort and no stage can be skipped: generators refuse non-validation data structurally, the loader refuses schema-incomplete/tampered/leaked artifacts, and service startup refuses anything whose provenance cannot be re-verified against the filesystem. The single mutable `operator_thresholds.json` is gone.

## Policy artifact schema (v1.0)

Every policy artifact carries **all 13 mandatory provenance fields** (brief, component 1) plus `schema_version`, a `thresholds` block, and an optional `lineage` block:

| Field | Deployed value (operator_policy_v2.0.0) |
|-------|------------------------------------------|
| `policy_id` | `operator_policy_v2.0.0` |
| `creation_timestamp` | 2026-07-03T…Z (UTC ISO-8601) |
| `generator_script` | `scripts/sprint23/promote_sprint56_policy.py` |
| `generator_commit` | `sha256:46209ddd…` (file hash — repo has no git, per Sprint 22.5 `02_threshold_provenance.md`) |
| `dataset_used` | `validation` |
| `dataset_fingerprint` | `{path: artifacts/research/validation.parquet, sha256: 9c1b770f…, parquet_rows: 1568759, n_windows: 1568399, n_positive_windows: 63849}` |
| `calibration_source` | `artifacts/calibrator.pkl` (isotonic, validation-fit — `calibrate_model.py:191–202`) |
| `threshold_generation_method` | validation-only trust-score sweep (Sprint 5.6 Task E), promoted per 06_fix_specification Variant A |
| `validation_split_identifier` | `research_v1_validation_2020-01-01_2022-12-31` |
| `approval_status` | `approved` |
| `scientific_version` | `V1-2026.06` (binds policy to patchtst_best.pt + calibrator.pkl generation) |
| `operator_version` | `2.0.0` |
| `sha256` | self-hash (see below) |

**Interpretation note:** "must contain exactly" is implemented as a completeness requirement — all 13 fields present and non-empty (`load_policy` refuses otherwise); the artifact additionally carries `schema_version`, `thresholds`, and `lineage`.

**Self-hash convention:** `sha256` = SHA256 over the canonical JSON serialization (`sort_keys=True`, compact separators) of the document with its own `sha256` field set to `""`. Any post-signing edit is detected at load (`PolicyIntegrityError`).

**Thresholds block:** `yellow_threshold`, `red_threshold`, three uncertainty-suppression tiers, four confidence cutoffs, and `tier_provenance` — which records honestly that the tiers (0.10/0.15/0.20) are Sprint 5.5 hardcoded design constants, **not data-derived** (they were hardcoded in `optimize_operational_policy.py:267–269`; carrying them without annotation would launder their provenance).

## Load pipeline (`load_policy`)

```
read JSON
 → QUARANTINE_REASON present?            → PolicyLeakageError   (checked first: archived leaked
                                                                  artifacts fail with the leakage
                                                                  error, not an incidental one)
 → schema_version supported?             → PolicySchemaError
 → all 13 provenance fields non-empty?   → PolicySchemaError
 → fingerprint + thresholds keys present → PolicySchemaError
 → self-hash matches?                    → PolicyIntegrityError
 → leakage_guard (5 checks)              → PolicyLeakageError
 → OperatorPolicy(doc)  — exposes .metadata, .thresholds, .policy_id
```

## Startup pipeline (`validate_policy_at_startup`) — component 3

Nine checks, executed in order, each logged; the first failure raises with the exact failing condition and the service never starts degraded:

1. **dataset_identity** — `dataset_used == "validation"`
2. **split_identity** — `validation_split_identifier` equals the expected constant
3. **dataset_fingerprint** — SHA256 of the dataset file **recomputed from disk** and compared (the load-bearing check: Sprint 22.5 proved the leak via fingerprint identity, so fingerprint identity is what startup re-proves; ~0.4 s for the 138 MB parquet)
4. **generator_version** — SHA256 of the generator script recomputed and compared to `generator_commit` (any post-generation edit to the generator invalidates the policy — regeneration required, by design)
5. **schema_version** · 6. **scientific_version** · 6b. **operator_version major** · 7. **approval_status** · 8. **leakage_guard** (defence in depth)

## Consumption (production)

`SuryaNetInferenceService.__init__` (`app/services/ml/inference.py`): default `thresholds_path = ACTIVE_POLICY_PATH` (`artifacts/policies/operator_policy_v2.json`) → `load_policy` → `validate_policy_at_startup` → thresholds mapped to the unchanged alert logic. The service exposes `policy_metadata` and `policy_startup_report`, so `/predict` responses can be extended to cite policy provenance (future work). The endpoint's no-arg instantiation (`app/api/v1/endpoints/inference.py:38`) — the exact hole through which the leaked default flowed (Sprint 22.5 Condition B) — is now safe by construction: the default is the gated path.

## Module dependencies

`policy.py` is stdlib-only (json/hashlib/os/logging) — deliberately importable and testable without torch/pandas, which is why the 15-test regression suite runs in 0.2 s under system Python while the integration test exercises the full torch stack under the venv.
