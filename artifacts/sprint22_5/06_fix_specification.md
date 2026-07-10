# 06 — Fix Specification (Specify Only — No Implementation This Sprint)

**Conclusion:** The fix is a three-commit change: (1) quarantine the leaked policy file with a deprecation record, (2) deploy a provenance-stamped policy derived from validation data — either the existing, already-backtested `operator_thresholds_validation_only.json` as an immediate stopgap, or the Sprint 22 cost-loss policy as the proper replacement — and (3) pin the production loader to the new file with regression tests and a provenance check that refuses to load any policy lacking a clean-provenance stamp. Rollback is a one-line path revert. This specification supersedes and narrows `artifacts/sprint22/Sprint22_Implementation_Plan.md` WP1/WP6 with the proof-level details established in this investigation.

---

## Fix F1 — Quarantine the leaked artifact

**Files:**
- CREATE `artifacts/policy_archive/operator_thresholds_v1_TEST_LEAKED.json` — byte-copy of the current `artifacts/operator_thresholds.json` plus an appended `_deprecation` block: `{reason: "thresholds selected on test split", generator: "scripts/optimize_operational_policy.py", generator_docstring_line: 6, inputs: ["artifacts/calibration/probs.npy", "artifacts/calibration/labels.npy"], input_fingerprint: {n: 1806313, positives: 419150}, proof: "artifacts/sprint22_5/04_leakage_proof.md", quarantined_on: <date>}`.
- MODIFY `artifacts/operator_thresholds.json` — do **not** delete (verifier scripts hash it: `scratch/compute_hashes.py:8`); replace contents with a tombstone: `{"status": "DEPRECATED_TEST_LEAKED", "see": "artifacts/policy_archive/...", "successor": "artifacts/operator_policy_v2.json"}`. Any consumer that still loads it must fail loudly (see F3 schema check) rather than silently use stale values.

**Validation criterion:** loading the tombstone through `SuryaNetInferenceService` raises a clear error naming the successor file (test T3 below).

## Fix F2 — Produce the replacement policy (two acceptable variants)

**Variant A — immediate stopgap (hours):** promote the existing `artifacts/operator_thresholds_validation_only.json` (yellow=0.14, red=0.95; provenance already self-stamped `test_data_used: false`) into the v2 schema. Its honest test performance is already known: TSS 0.38172, Recall 0.72265, EventRecall 0.69634, FalseEpisodes/month 6.92 (`artifacts/operator_backtest.json`), with bootstrap CIs in `artifacts/bootstrap_metrics.json`. Limitation to record in the artifact: red=0.95 produced 0 RED alerts in the backtest (`operator_backtest.json` alert_distribution RED: 0) — the RED tier is effectively disabled; acceptable as a stopgap, not as the end state.

**Variant B — proper replacement (days):** the Sprint 22 cost-loss, episode-level policy per `artifacts/sprint22/Sprint22_Implementation_Plan.md` WP2–WP4 (validation inference regeneration, episode module, cost-loss frontier, uncertainty-tier re-derivation). Note the uncertainty tiers 0.10/0.15/0.20 in the leaked file were hardcoded constants (`optimize_operational_policy.py:267–269`), never data-derived — Variant B must derive them; Variant A may carry them forward with a `provenance: "hardcoded, Sprint 5.5"` annotation.

**Output (either variant):** `artifacts/operator_policy_v2.json` with mandatory keys: `policy_version`, `derived_from: "validation"`, `test_data_used: false`, `selection_script`, `selection_inputs` (paths + row counts + positive counts), `thresholds`, `uncertainty_tiers` (+ provenance per tier), `confidence_cutoffs`, `derived_on`.

## Fix F3 — Repoint and harden the production loader

**File:** `app/services/ml/inference.py`
- Line 86: default `thresholds_path` → `os.path.join("artifacts", "operator_policy_v2.json")`.
- Loader block (121–142): add a provenance gate — refuse to initialize unless the loaded JSON contains `test_data_used: false` and `derived_from: "validation"`; raise `ValueError` naming this investigation otherwise. This makes re-introduction of a leaked policy a startup failure instead of a silent regression.

**File:** `app/api/v1/endpoints/inference.py` — no change (no-arg instantiation is now safe by construction).

## Tests (CREATE `tests/test_policy_provenance.py`, `tests/test_alert_policy.py`)

| ID | Test | Pass criterion |
|----|------|----------------|
| T1 | v2 policy file schema: all mandatory provenance keys present; `test_data_used is False` | Schema-valid |
| T2 | Service init with v2 file succeeds; loaded attributes equal file values | Exact equality |
| T3 | Service init with the tombstoned v1 file raises with successor guidance | Raises `ValueError` |
| T4 | Service init with a synthetic policy lacking provenance keys raises | Raises `ValueError` |
| T5 | Alert tiering table-driven: prob/uncertainty grid × suppression tiers × RED confirmation state machine reproduces expected alerts at v2 boundary values | All cases match |
| T6 | Leak regression guard: assert no file under `app/` references `artifacts/operator_thresholds.json` except via the archive/tombstone constant | Grep-based, zero matches |

## Expected outputs

1. `artifacts/policy_archive/operator_thresholds_v1_TEST_LEAKED.json` (quarantine record)
2. Tombstoned `artifacts/operator_thresholds.json`
3. `artifacts/operator_policy_v2.json` (Variant A immediately; superseded by Variant B when Sprint 22 WP2–WP4 complete)
4. Modified `app/services/ml/inference.py` (path + provenance gate)
5. `tests/test_policy_provenance.py`, `tests/test_alert_policy.py`
6. One honest headline set for the submission deck, drawn only from `operator_backtest.json` + `bootstrap_metrics.json` (Variant A) or the WP5 pre-registered evaluation (Variant B)

## Validation criteria & quality gates

- **QG-004 (research validation):** provenance gate demonstrated (T3/T4); v2 derivation reproducible from its recorded inputs; for Variant B, the single pre-registered test evaluation protocol of `Sprint22_Implementation_Plan.md` WP5 applies unchanged.
- **QG-007 (bug fix):** leak closed with the quarantine + repoint pair as evidence; T6 green.
- **QG-002 (PR):** diff reviewed against this specification; no consumer of the tombstoned file remains except verifier scripts (whose hash baselines must be re-recorded — `scratch/compute_hashes.py`, `artifacts/sprint10l/repository_fingerprint_v1.json` will legitimately change).
- **Documentation sweep:** correct every item in `05_impact_analysis.md` §A/§B/§D, including `context/workflow.md` Rule 3 (currently instructs *using* the leaked values) and the bootstrap-CI attribution error in the Sprint 22 documents.

## Runtime / resources

Variant A: no model execution — file operations, one service-init smoke test, unit tests; minutes. Variant B: per `Sprint22_Implementation_Plan.md` (≈6–9 h MPS compute, ≤8 GB unified memory, no retraining).

## Rollback plan

- All changes additive or single-line: revert `inference.py` path constant + restore v1 JSON from the byte-copy in `artifacts/policy_archive/` → exact pre-fix behavior.
- The provenance gate is introduced in the same commit as the repoint; reverting one reverts both (no half-state where the gate rejects the restored v1).
- Verifier-script hash baselines are updated in a separate commit so rollback of the policy change does not orphan them.
