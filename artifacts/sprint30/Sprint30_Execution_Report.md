<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Sprint 30 execution record — phases, deviations, integrity measures. -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-11 -->

# Sprint 30 — Execution Report ("The Fair Test, Part 1")

**All phases executed; the pre-registered F1-vs-F0 experiment completed with verdict FAILURE (F1 does not improve on F0; `Decision_Tree_Update.md`). The governing integrity rules held throughout: no experiment was rerun, nothing was tuned after results, and no test-set metric was inspected before the formal Phase 5 analysis — enforced structurally by an evaluation runner that writes results to disk without printing them, plus analysis code whose interpretation rules were git-committed before any result existed (`3bf2ee8`, `89a688d`).**

## Phase-by-phase record

**Phase 0 — Readiness (PASS).** All Sprint 29 fingerprints re-verified: Version 3 stage-2 checkpoint and s2_test dataset vs `benchmark_manifest.json`; V1 checkpoint structure (epoch 3, 828,161 state tensors); isotonic calibrator; Sprint 24 harness SHA vs `artifacts/sprint26/phase1_fingerprints.json`; policy system 9/9 startup checks; the full 59-test suite; physics-feature real-data validation record. The one open Sprint 29 gap — the unexercised remote push — was closed: the remote had a benign security commit (`c95be90`, config-password removal, no ML code), merged and pushed successfully (`996d42a`). The other two Sprint 29 F1 gaps (dataset build, driver parameterization) were this sprint's scheduled Phases 1–2, not blockers.

**Phase 1 — Dataset (COMPLETE).** `dataset_v4.0.0` built by `scripts/sprint30/build_dataset_v4.py`; 15/15 validation checks pass; frozen split timestamps/targets byte-identical; robust scaling fit on train only; provenance manifest with tamper detection. Details: `Dataset_Validation_Report.md`.

**Phase 2 — Driver (COMPLETE).** `scripts/sprint30/train_driver.py` = the frozen Sprint 26 driver + exactly two changes (feature-list parameter; model width follows it). Validation output: default-width state dict matches the frozen V1 checkpoint (828,161 tensors, keys identical); 17-feature forward pass correct (828,545 parameters); V4 dataset windows shaped (360, 17) with labels identical to the frozen split; 100-step smoke run on V4 data (seed 999) trained with finite loss and was discarded.

**Phase 3 — F0 (COMPLETE).** Executed per `F0.json` as the untrained frozen reference (the brief's per-seed wording was resolved in the contract's favor — flagged in `Sprint30_F0_Report.md`). Sealed re-evaluation reproduced the pre-registered reference TSS exactly (0.3940129618 vs 0.3940).

**Phase 4 — F1 (COMPLETE).** Seeds 42/43/44 trained and sealed-evaluated with zero failures; after the escalation rule fired at Phase 5, seeds 45/46 likewise. No reruns, no tuning. Details: `Sprint30_F1_Report.md`.

**Phase 5 — Analysis (COMPLETE).** Pre-registered plan applied (`artifacts/sprint25/07_preregistered_analysis_plan.md`; the brief's cited path `artifacts/sprint28/07_preregistered_analysis_plan.md` does not exist — flagged, Sprint 25 document used as the plan of record). Primary endpoint failed 0/5 seeds; block-size robustness confirmed at 1,440/2,880/5,760; secondaries reported without promotion. Details: `Statistical_Analysis.md`, `Seed_Variance_Report.md`.

**Phase 6 — Decision tree (RESOLVED: FAILURE).** First branch measured false; Path A foreclosed; F2 (Sprint 31) determines Path B/C/D. Details: `Decision_Tree_Update.md`.

## Deviations and flags (complete list)

1. **F0 "seeds" conflict** — brief wording vs `F0.json:"training": "NONE"`; contract followed (conservative; the alternative would have replaced a pre-registered arm post-registration).
2. **Analysis-plan path** — brief cited a nonexistent `sprint28/07_preregistered_analysis_plan.md`; the Sprint 25 plan (which Sprint 28's spec itself cites) was applied.
3. **Escalation to 5 seeds** — mandated by `F1.json` when the 3-seed range hit 0.0426 > 0.015; the 5-seed majority criterion was pre-declared and committed before seeds 45/46 ran. This is protocol compliance, not a deviation, but it exceeds the brief's literal "seeds 42, 43, 44".
4. **Two build-script check-bound corrections** (analytic cubic range; degenerate-IQR features) — validation assertions fixed, pipeline/features/scaler untouched (`Dataset_Validation_Report.md`).
5. **Attribution caveat** — F1 vs F0 measures features + V4 preprocessing jointly, as the pre-registration specified; recorded in all result documents.

## Runtime and artifacts

Total compute: ~4.3 h (F0 eval 10 min; five F1 trainings 24.9/24.1/23.8/41.0/14.0 min; five sealed evals ~11 min each; dataset build ~6 min; analysis ~8 s ×2). All run records under `artifacts/sprint30/runs/`, logs under `artifacts/sprint30/logs/`, machine-readable analysis in `artifacts/sprint30/analysis.json`.
