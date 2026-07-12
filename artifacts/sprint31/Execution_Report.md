<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Sprint 31 execution record — phases, integrity measures, deviations. -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-12 -->

# Sprint 31 — Execution Report ("The Fair Test, Part 2")

**All seven phases executed under the two governing rules — no threshold moved after results, nothing rerun for being disappointing. Verdict chain: primary endpoint (F2 > F1-on-S2) PASSED 3/5 seeds → decision tree Case A / Path B, F3 mandated → but the pre-committed F2-vs-F0 comparison showed no gain over the GOES-only baseline, making the headline verdict PARTIALLY SUPPORTED (`FINAL_VERDICT.md`). Integrity was structural throughout: sealed evaluation runners that never print a test metric, an escalation decision taken by script with the values unread, and analysis rules committed before any result existed (`30d4f23`).**

## Phase record

**Phase 0 (PASS):** 8/8 fingerprints (V3 checkpoint + s2_test vs `benchmark_manifest.json`; Sprint 24 harness SHA; Sprint 23 policy 9/9; Sprint 30 F0 baseline checkpoint and eval record; dataset_v4.0.0 manifest; all five F1 checkpoints) + 59/59 regression tests. One false alarm during verification: the venv Python lacks pytest, so the first subprocess run failed on interpreter choice, not on any fingerprint — re-run with system `python3` (the CI's own interpreter) passed. No blocker.

**Phase 1 (COMPLETE):** `dataset_v4.1.0-s2` built (`scripts/sprint31/build_dataset_v4_s2.py`), 18/18 checks. Key measured fact: SoLEXS's 24.4% unavailability is entirely 1–9-minute micro-gaps — 100% inside the ≤15-min fill regime. Four reports: `Dataset_Report.md`, `Feature_Distribution_Report.md`, `Feature_Correlation_Report.md`, `Missing_Data_Report.md`.

**Phase 2 (COMPLETE, delegated):** run by a subagent in parallel with Phase 1 as instructed. Formula conformance 15/15 exact (independent reimplementation, max diff 0.0), causality (truncation invariance), determinism, label isolation, train-only threshold provenance all PASS; two flagged items were data findings, not pipeline defects (quiet-sun zero hard-band ratios; no SoLEXS flare response at GOES peaks). Records: `phase2_feature_validation.{json,md}`.

**Phase 3 (COMPLETE):** F2 trained at seeds 42/43/44; `auto_escalate.py` fired on range 0.0153 > 0.015 (values sealed) and seeds 45/46 trained automatically in the same chain. All runs early-stopped at epoch 4, best epoch 1 (`Training_Report.md`).

**Phase 4 (COMPLETE):** eleven sealed evaluations (5 F2, F0-on-S2, 5 F1-on-S2) through the frozen harness instantiated on the S2 span (the one pre-registered evaluator modification), floors recomputed (persistence 0.3368, climatology 0.0), all ten required metrics per seed including RED duty cycle and the pre-declared Operator Utility; block bootstrap at 1,440/2,880/5,760 with 2,880 authoritative.

**Phase 5 (COMPLETE):** `analyze_s2.py` (pre-committed). Primary MET 3/5; F2-vs-F0 null 0/5; stratification degenerate as pre-declared; borderline seeds (42, 45) reported as borderline. `Statistical_Analysis.md`, `Seed_Variance_Report.md`.

**Phase 6 (RESOLVED):** Case A → Path B, F3 mandated; two measured caveats bound to the resolution. `Decision_Tree_Update.md`.

**Phase 7 (COMPLETE):** eight questions answered with labels — 3 SUPPORTED BY EVIDENCE (in part), 2 NOT SUPPORTED, 4 AMBIGUOUS with named resolving experiments. `Scientific_Conclusion.md`.

## Deviations and flags (complete list)

1. The brief's analysis-plan path (`sprint28/07_preregistered_analysis_plan.md`) does not exist; the Sprint 25 plan of record was applied (same resolution as Sprint 30, flagged in `Statistical_Analysis.md`).
2. Model input width 36, not 32: the four §3 availability/staleness channels are appended per the flagged conservative interpretation in `Dataset_Report.md` (excluding them would rebuild the Sprint 27 zero-fill defect V4 exists to fix). The 32 "Version 4 inputs" of the feature spec are all present, unmodified.
3. "Operator Utility" has no repository definition; the parameter-free Richardson-2000 V_max = TSS was pre-declared in commit `30d4f23` before results.
4. The escalation rule was stated as "Sprint 25" in the brief; the operative registrations are F1.json/04 (identical rule); applied automatically.
5. No experiment was rerun; no threshold changed; seeds exactly 42–46; the F2-vs-F0 and F1-vs-F0 comparisons that complicate the verdict were pre-committed parts of the analysis, not post-hoc additions.

## Runtime

~2.6 h total: 5 F2 trainings (12.9–13.9 min each), 11 sealed evaluations (~6 min each), dataset build ~4 min, analysis 2.5 s (×2 for the deterministic-rerun gate). Runs under `artifacts/sprint31/runs/`, logs under `artifacts/sprint31/logs/`.
