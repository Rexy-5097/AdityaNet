<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Sprint 32 — consolidated execution/experiment record. -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-12 -->

# Sprint 32 — Experiment Report

**Two experiments resolved the Sprint 31 era-confound. F3 (late-fusion architecture, `LateFusionPatchTST`) and EraMatchedGOES (the era-matched GOES-only control) were built, trained sealed, and evaluated through the frozen Sprint 24 harness on the S2 span. Outcome: F3 is the worst arm (TSS 0.3952) and EraMatchedGOES is the best (0.4383); the de-confounded Aditya effect is negative (−0.0388), the era effect is positive (+0.0315). The ISRO hypothesis is NOT SUPPORTED (`FINAL_VERDICT.md`). Governing rules held: no threshold moved after results, nothing was rerun, and no test metric was seen before Phase 4 (sealed runners; analysis pre-committed at `28b25b4`).**

## Phase record

- **Phase 0 (PASS):** 8/8 fingerprints verified and recorded to `verification.json` (V3 checkpoint + s2_test, Sprint 24 harness, Sprint 23 policy 9/9, Sprint 30 F0 baseline, both V4 dataset manifests, Sprint 31 sealed records). No mismatch → no blocker.
- **Phase 1 (COMPLETE, TDD):** `LateFusionPatchTST` — two independent PatchTST encoders (GOES-17 / Aditya-19), fusion after pooling, 1,661,185 params (1.915× F2); 11 contract tests written first, all pass; stream isolation proven by perturbation. `Architecture_Report.md`.
- **Phase 2 (COMPLETE, delegated):** subagent wrote `EraMatchedGOES_Protocol.md` — GOES-17 subset of the F2 dataset (byte-identical GOES values), one deliberate difference (no Aditya), verified line-by-line against F2's config; scaler constants confirmed against the manifest.
- **Phase 3 (COMPLETE):** F3 seeds 42/43/44 → auto-escalation fired (range > 0.015) → 45/46; EraMatchedGOES seeds 42/43/44 → no escalation (range 0.0109). Sealed evaluations only. All runs early-stopped at epoch 4, best epoch 1 (the S2 small-data overfitting pattern seen since Sprint 31).
- **Phase 4 (COMPLETE):** `analyze_s2.py` (pre-committed) — four paired comparisons, block sensitivity 1440/2880/5760, Cohen's d, per-seed CIs and p-values. `Statistical_Analysis.md`.
- **Phase 5 (COMPLETE):** six questions answered; late fusion NOT SUPPORTED, Aditya value NOT SUPPORTED, GOES sufficiency SUPPORTED, ISRO NOT SUPPORTED. Pre-registered tree annotated with measured outcomes. `Scientific_Conclusion.md`, `Decision_Tree_Update.md`.
- **Phase 6 (COMPLETE):** F3 dominated on every operational axis; recommendation keep F0, promote EraMatchedGOES via powered confirmation. `Operator_Report.md`.

## Consolidated seed / arm table (OBSERVED)

| Arm | Seeds | Params | Best epoch | Val TSS (mean) | Test TSS mean ± std | Wall (min/seed) |
|-----|-------|--------|-----------|----------------|----------------------|------------------|
| F3 late fusion | 42–46 (escalated) | 1,661,185 | 1 (all) | 0.498 | 0.3952 ± 0.0142 | ~26 |
| EraMatchedGOES | 42,43,44 | 828,545 | 1 (all) | 0.529 | 0.4383 ± 0.0055 | ~17 |
| F2 (Sprint 31) | 42–46 | 867,457 | 1 (all) | 0.446 | 0.4022 ± 0.0151 | ~13 |
| F0 (frozen ref) | — | 822,401 | 8 | 0.605 | 0.4068 | — |

## Deviations and flags (complete list)

1. Analysis-plan path (`sprint28/07_...`) does not exist; Sprint 25 plan of record applied (as Sprints 30–31).
2. Late-fusion model width is 36 input channels split 17/19 internally; the 4 disclosure channels route to the Aditya encoder per the "identically to Sprint 31" clause (Architecture_Report flag 2).
3. One legitimate CI lint fix during quality gates: removed an unused `import pytest` from `tests/test_model_f3.py` (behavior-neutral; not a test-tuning change). CI re-run green (70 tests).
4. EraMatchedGOES vs F0 carries a minor 14-vs-17 GOES-feature difference on top of era (protocol §5); the Aditya comparison (F2 vs EraMatchedGOES) is clean.
5. No rerun; no threshold change; seeds exactly 42–46; the era-matched control that overturned the Sprint 31 reading was a pre-committed design, not a post-hoc addition.
6. No comparison reaches per-seed 95% significance (S2 span ~90 blocks); the NOT SUPPORTED verdict rests on the pre-registered positive-Aditya test failing 0/3 with a stable negative sign, not on a significant negative.

## Runtime

~3.5 h: 5 F3 trainings (~26 min each, 2× F2 for the second encoder), 3 EraMatchedGOES trainings (~17 min), 8 sealed evaluations (~6 min each), analysis 5 s (×2 for the determinism gate). Runs under `artifacts/sprint32/runs/`, logs under `artifacts/sprint32/logs/`.
