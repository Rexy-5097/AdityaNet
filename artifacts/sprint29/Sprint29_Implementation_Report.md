<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Sprint 29 implementation report with requirement traceability and dependency graph. -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-05 -->

# Sprint 29 — Implementation Report

**All five phases complete; every component traces to a named Sprint 28 requirement; all quality gates pass (59/59 tests, six CI gates, AgentOS validator 100/100).** One material correction to the project record surfaced during Phase 1 and is documented below: the repository was already under git with a configured GitHub remote, contradicting the "no git" claim carried since the June migration report.

## Phase 0 — Frozen-baseline verification: PASS (22/22)

All fingerprints verified (`artifacts/sprint29/phase0_verification.json`): Version 3 checkpoints/datasets/calibrator (vs `benchmark_manifest.json`), the deployed operator policy (9/9 Sprint 23 startup checks), the Sprint 24 harness (SHA-256 identical to the Sprint 26 record; constants block=2880, seed=20260704), Sprint 26 baseline metrics (Baseline policy True Skill Score 0.3940 in `artifacts/sprint26a/runs/Baseline/eval.json`), and all eight Sprint 28 specifications (SHA-256s recorded, freezing them for this sprint).

## Component-to-requirement mapping (the Phase 0 task audit)

| Component | Sprint 28 requirement |
|-----------|----------------------|
| Git/remote/CI/lint/tests foundation (Phase 1) | `06_IMPLEMENTATION_ROADMAP.md` Sprint 29 goal ("git initialization with remote, continuous-integration run of the existing test suite, unit tests for the Version 4 feature builder"); `07_EXTERNAL_REVIEW.md` Reviewer-5 resolution |
| Feature framework: modular/deterministic/provenance-aware/stateless/inference-safe (Phase 2) | `02_FEATURE_PIPELINE_V4.md` (per-feature validation-test requirement); `03_DATASET_PIPELINE_V4.md` §6 (fitting excluded from features) |
| goes_T_iso, goes_EM, goes_dT_iso_15m (Phase 3) | `02_FEATURE_PIPELINE_V4.md` NEW rows 1–3, exactly and only |
| RobustScaler train-only (Phase 4) | `03_DATASET_PIPELINE_V4.md` §6 step 3 |
| Availability masks, gap policy, staleness (Phase 4) | `03_DATASET_PIPELINE_V4.md` §1–§3 (fix for `dataset_v3.py:110-111` scalar-mask collapse) |
| Quality score (Phase 4) | `03_DATASET_PIPELINE_V4.md` §5 |
| Provenance manifest schema/writer/verifier (Phase 4) | `03_DATASET_PIPELINE_V4.md` §7 |
| F0/F1 pre-registered configs + readiness checker (Phase 5) | `04_FAIR_ADITYA_EXPERIMENT.md` arms F0/F1, statistics, seeds, success/failure criteria, stopping rules |

No unmapped task existed; no blocker was raised.

## Dependency graph (Phases 0–5)

```
Phase 0 (verify frozen world)
  └─ Phase 1 (git/CI/lint substrate)            [gates: CI 6/6]
       └─ Phase 2 (feature framework, tests-first) [gates: 9/9 contract tests]
            └─ Phase 3 (3 GOES physics features)   [gates: 12/12 unit + real-data
                 │                                   validation: 77 X-events,
                 │                                   94% T-rise / 99% dT PASS]
                 └─ Phase 5 (F0/F1 scaffolding) ←─ Phase 4 (dataset infra,
                      [gates: 14/17 READY]           tests-first, 13/13)
```
Phase 4 depends only on Phase 1–2 (framework conventions); Phase 5 depends on Phases 3 and 4 outputs plus the frozen Sprint 24/25/26 artifacts.

## Delivered components (paths)

- `scripts/ci/run_ci.sh`, `.github/workflows/ci.yml`, `ruff.toml` — CI gates 1–6
- `app/services/ml/features_v4/framework.py` + `tests/test_features_v4_framework.py` (9 tests)
- `app/services/ml/features_v4/goes_physics.py` + `tests/test_features_v4_goes_physics.py` (12 tests) + `scripts/sprint29/validate_goes_physics.py` + `artifacts/sprint29/figures/goes_physics_vs_flux.png` + `artifacts/sprint29/goes_physics_validation.json`
- `app/services/ml/dataset_v4/{scaling,masks,manifest}.py` + `tests/test_dataset_v4_infrastructure.py` (13 tests)
- `artifacts/sprint29/experiments/{F0,F1}.json` + readiness checker output `artifacts/sprint29/readiness_items.json`
- ADR-0001 and ADR-0002 (`artifacts/decisions/`), indexed in `context/decisions.md`

## Corrections and flagged decisions

1. **Git status correction:** the repository has been a git repository with remote `https://github.com/Rexy-5097/AdityaNet.git` since 2026-07-01 (commits present, GitHub push certificate at root). Earlier sprint documents' "no git (GAP-008)" claims were stale inheritances from `MIGRATION_REPORT.md`; this sprint committed all session work (commit `66ae02e` and the Sprint 29 closing commit).
2. **Flagged decision D1 (lint scope):** Sprint 28 names CI and tests but no linter; ruff with error-level rules (E9, F) scoped to new V4 code and tests was adopted; the frozen Sprint 24 harness received a documented per-file exemption (`ruff.toml`) rather than an edit, preserving its fingerprint.
3. **Flagged ambiguity (physics coefficients):** Sprint 28 rows 1–2 name "the published polynomial" without coefficients; the Thomas-Starr-Crannell 1985 cubic and a T² emission-measure response proxy were adopted as the conservative interpretation, with absolute EM calibration explicitly marked NOT PROVEN (harmless under the pipeline's robust scaling) — details in `Feature_Validation_Report.md`.
4. **Scope boundary honored:** the Sprint 28 roadmap phrased Sprint 29 as including F1 runs; this sprint's brief drew the boundary at scaffolding — the brief governed, and no experiment was run.
5. **Historical runner lint fixes:** ruff auto-removed 11 unused imports across five historical runner scripts (behavior-neutral; frozen harness and hash-pinned promotion script untouched — verified by fingerprint re-check).
