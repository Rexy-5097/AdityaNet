Case A

<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Sprint 31 Phase 6 — decision tree resolution from Phase 5 measurements. -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-12 -->

# Sprint 31 — Decision Tree Update

**Case A: F2 significantly exceeds F1 on the primary endpoint — paired ΔTrue Skill Score ≥ +0.02 in 5 of 5 seeds with positive lower 95% bound in 3 of 5 (majority satisfied; bootstrap p 0.018/0.008/0.004; mean +0.0844; pre-onset recall improved, never degraded; `artifacts/sprint31/Statistical_Analysis.md`). Under `artifacts/sprint28/05_VERSION4_DECISION_TREE.md` this activates Path B — "Version 4 = the 32-feature concatenated single-encoder architecture (F2's own architecture), with fusion adopted only under Path D's condition" — and mandates the F3 experiment.**

## What F3 tests

F3 runs the same 32 Version-4 features plus per-timestep availability channels through the **late-fusion architecture** (per-instrument encoders with the window missing-token, per `03_DATASET_PIPELINE_V4.md` §3 and the F3 row of `04_FAIR_ADITYA_EXPERIMENT.md`), same Stage-2 splits, same frozen protocol, seeds 42/43/44 plus automatic escalation, sealed evaluation on the same S2 span. Pre-registered question: does cross-instrument *temporal* structure (the Neupert integral kernel; the measured −5-minute HEL1OS lead, `artifacts/aditya_l1/cross_instrument_confirmation_audit.json`) carry value the pooled concatenation cannot express? Path D (token-level cross-attention fusion) activates only if F3 beats F2 under the identical rule (ΔTSS ≥ +0.02, lower bound > 0, majority of seeds); otherwise Path B stands as the Version 4 architecture selection.

## Two measured caveats bound to this resolution (pre-registered comparisons, not post-hoc additions)

1. **F2 does not exceed F0 on the same span** (paired ΔTSS −0.0195..+0.0185, 0 of 5 seeds significant). Path B's rationale ("the value came from features") is only partially supported by the measurements: the F2−F1 margin decomposes almost entirely into the comparator's span-transfer collapse (F0−F1 ≈ +0.089) rather than skill above the GOES-only ceiling (F2−F0 ≈ −0.005). The tree pre-registered F2-vs-F1 as the branch condition and that condition is met — Case A is therefore the mechanical resolution — but "adopt F2 as Version 4" is an architecture-direction decision, NOT a deployment recommendation: the deployed V1/F0 model remains unbeaten at the window-TSS level on the operating span (`Operator_Report.md`).
2. **The design confounds Aditya features with training-era match** (F1 trains on 2010–2019, F2 on 2023–2025 — both as pre-registered in the arms table). The decisive de-confounding control — a 17-feature GOES-only arm trained on the Stage-2 boundaries — was not pre-registered in this tree and therefore requires a new pre-registration; it is the highest-value addition to Sprint 32 alongside F3 (`Scientific_Conclusion.md` Q1/Q5).

Sprint 30's resolution stands unchanged: Path A remains foreclosed (F1 failed against F0 on the V1 span).
