<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Authoritative Version 3 timeline written at reconciliation (Sprint 23.5). -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-03 -->

# Version 3 — Scientific Timeline

**Conclusion:** Version 3's scientific history is six events spanning 2026-06-15 to 2026-07-03: implementation, an internally-detected-but-undeployed leakage fix, formal proof of the leak, structural correction, clean-policy promotion, and repository reconciliation. All dates are sourced from filesystem modification times (preserved through the 2026-07-01 rsync migration, per `MIGRATION_REPORT.md` line 45) or dated sprint reports.

---

## Event 1 — Original Version 3 implementation

**Date:** 2026-06-15 through 2026-06-21 (filesystem mtimes)
**Sprint reference:** Sprints 5 through 14c
**What changed:** The Version 3 platform came into being: the V1 production stack — PatchTST model trained (`artifacts/models/patchtst_best.pt`, mtime 2026-06-15 13:10), isotonic calibrator fit on validation (`artifacts/calibrator.pkl`, 2026-06-15 19:25), operator thresholds selected (Sprint 5.5, 2026-06-15 19:54) — and the V3 multi-instrument research model (LateFusionPatchTST, `app/services/ml/model_v3.py` mtime 2026-06-19; best checkpoint `artifacts/sprint14c/checkpoints/model_seed_42_stage2_best.pt` mtime 2026-06-21 16:09; independent audit `scientific_validation_report.md` dated 2026-06-21).
**Artifacts:** `artifacts/models/patchtst_best.pt`, `artifacts/calibrator.pkl`, `artifacts/sprint14c/` (checkpoints, `test_results_model_D_seed_42.json`, `experiment.log`), `scientific_validation_report.md`.
**Latent defect:** the Sprint 5.5 thresholds (yellow=0.46, red=0.88) were swept on saved test-set predictions — undetected as a deployment problem at the time, though Sprint 5.6 (same evening, 2026-06-15 20:11–20:31) built a validation-only replacement that was never wired into production.

## Event 2 — Leakage discovered (Sprint 22.5)

**Date:** 2026-07-03 (Sprint 22 planning surfaced the provenance question; the Sprint 22.5 investigation was commissioned the same day). An honest nuance: the repository *first* detected the problem internally on 2026-06-15 (Sprint 5.6, `scripts/refine_thresholds.py`, and `artifacts/operator_trust_audit.json` recording `test_data_used_for_optimization: true`) but the correction was never deployed; Sprint 22.5 is when the discovery became actionable.
**Sprint reference:** Sprint 22 (planning) → Sprint 22.5 (forensic investigation)
**What changed:** The deployed decision layer's provenance was traced end-to-end: `scripts/optimize_operational_policy.py` (docstring line 6) swept test-set arrays `artifacts/calibration/probs.npy`/`labels.npy` and wrote the file production `inference.py` loaded by default.
**Artifacts:** `artifacts/sprint22/` (six planning documents), `artifacts/sprint22_5/01_dependency_graph.md`, `02_threshold_provenance.md`, `03_execution_path.md`.

## Event 3 — Leakage formally proven (FINAL_VERDICT.md)

**Date:** 2026-07-03 14:35 (mtime of `artifacts/sprint22_5/FINAL_VERDICT.md`)
**Sprint reference:** Sprint 22.5
**What changed:** Verdict **LEAKAGE PROVEN** — all four required conditions confirmed simultaneously. Decisive quantitative evidence: the deployed policy's embedded selection metrics reproduce exactly (six decimal places) from the test arrays at t=0.46/0.88; array fingerprint N=1,806,313 / 419,150 positives equals the test split byte-count-exactly; no validation-only replacement ever entered the production path.
**Artifacts:** `artifacts/sprint22_5/FINAL_VERDICT.md`, `04_leakage_proof.md`, `05_impact_analysis.md` (blast radius), `06_fix_specification.md`.

## Event 4 — Leakage corrected (Sprint 23)

**Date:** 2026-07-03 18:48 (mtime of `app/services/ml/policy.py`)
**Sprint reference:** Sprint 23
**What changed:** The versioned policy system replaced the single mutable thresholds file: 13 mandatory provenance fields, self-hash integrity sealing, a five-layer leakage guard (quarantine marker, "test" dataset identity, known-leaked-fingerprint blocklist, banned generator tokens, generator source scan), and nine startup provenance checks with abort-on-failure wired into `app/services/ml/inference.py`. The leaked artifacts were quarantined to `artifacts/archive/` with `QUARANTINE_REASON: LEAKED_TEST_DERIVED` and evidence-continuity hashes. The repository's first automated test suite (15 regression tests + integration) pins the behavior.
**Artifacts:** `app/services/ml/policy.py`, `artifacts/archive/` (README + quarantined files), `tests/`, `artifacts/sprint23/` (eight reports incl. `Validation_Report.md` with all gate outputs).

## Event 5 — Clean policy promoted (Sprint 23)

**Date:** 2026-07-03 18:52 (mtime of `artifacts/policies/operator_policy_v2.json`; promotion log timestamped 18:52:25–26)
**Sprint reference:** Sprint 23, component 6 (per `artifacts/sprint22_5/06_fix_specification.md` Variant A)
**What changed:** The Sprint 5.6 validation-only thresholds (yellow=0.14, red=0.95) were promoted into policy `operator_policy_v2.0.0` by `scripts/sprint23/promote_sprint56_policy.py` after stamp verification, dataset fingerprinting (SHA256 9c1b770f…, 1,568,399 windows / 63,849 positives), and structural cross-checks. Production `inference.py` loads it by default; integration-verified with the real model and calibrator (9/9 startup checks PASS).
**Artifacts:** `artifacts/policies/operator_policy_v2.json`, `scripts/sprint23/promote_sprint56_policy.py`, `artifacts/sprint23/Deployment_Report.md`.

## Event 6 — Repository reconciled (this sprint)

**Date:** 2026-07-03 (Sprint 23.5)
**Sprint reference:** Sprint 23.5
**What changed:** Every document still presenting leaked-policy metrics as the current authoritative state received a VERSION STATUS annotation (original content preserved beneath — traceability, not deletion); `PROJECT_STATUS.md` was restructured into Current / Historical / Archived sections; the six Version 3 lock documents and this timeline were written; open items were tagged `[V4]`. Version 3 is frozen as the permanent research baseline for the ISRO submission.
**Artifacts:** `artifacts/sprint23_5/` (this file plus `VERSION3_FINAL_CERTIFICATE.md`, `VERSION3_CHANGELOG.md`, `VERSION3_SCIENTIFIC_BASELINE.md`, `VERSION3_DEPLOYMENT_BASELINE.md`, `VERSION3_LIMITATIONS.md`, `VERSION3_OPEN_RESEARCH.md`), annotated documents repository-wide, restructured `PROJECT_STATUS.md`.
