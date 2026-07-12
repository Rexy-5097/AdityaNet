<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Sprint 32 — one-page summary of the decisive Aditya-L1 result. -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-12 -->

# Sprint 32 — Summary

**The ISRO hypothesis is NOT SUPPORTED. Sprint 32 removed the Sprint 31 era-confound with two additions — F3 (late-fusion architecture) and EraMatchedGOES (a GOES-only control trained on the same recent era as F2) — and the answer is unambiguous: once training era is held fixed, GOES-only is the best configuration and the Aditya-L1 channels subtract skill.**

## The four arms on the S2 test span (OBSERVED)

| Arm | What it is | TSS |
|-----|-----------|-----|
| **EraMatchedGOES** | GOES-only, recent (Stage-2) era | **0.4383 ± 0.0055** ← best |
| F0 | GOES-only, original era (deployed) | 0.4068 |
| F2 | GOES + Aditya-L1, recent era | 0.4022 ± 0.0151 |
| F3 | GOES + Aditya-L1, late fusion | 0.3952 ± 0.0142 ← worst |

## The decisive numbers (OBSERVED, `analysis.json`)

- **Aditya effect (era-controlled):** ΔTSS(F2 − EraMatchedGOES) = **−0.0388**, negative in 3/3 seeds, 0/3 passing the +0.02 success test → Aditya adds no value; the estimate is that it removes skill.
- **Late-fusion effect:** ΔTSS(F3 − F2) = **−0.0070**, 0/5 significant → late fusion does not help; F3 is the worst arm.
- **Era effect:** ΔTSS(EraMatchedGOES − F0) = **+0.0315**, positive in 3/3 seeds → the Sprint 31 "improvement" was training on recent data, achievable with GOES alone.

## What it means

1. **ISRO hypothesis NOT SUPPORTED** — Aditya-L1 gives no statistically significant incremental value beyond GOES for operational flare forecasting under a fair, physics-engineered, era-controlled test.
2. **Decision tree:** Path D foreclosed (F3 ≤ F2), Path B premise falsified (F2 ≤ era-matched GOES), all Aditya branches closed. Version 4 direction = single-encoder GOES-only retrained on recent data (EraMatchedGOES), operator-policy program continuing.
3. **Deployment:** keep F0; do NOT deploy F3 (dominated); promote EraMatchedGOES via a powered confirmation.
4. **The campaign's real lever:** data recency, not instruments/features/architecture — the only change that improved on the deployed baseline was retraining GOES on the current solar cycle.

## Deliverables (all under `artifacts/sprint32/`)

`FINAL_VERDICT.md`, `Statistical_Analysis.md`, `Scientific_Conclusion.md`, `Operator_Report.md`, `Decision_Tree_Update.md`, `Experiment_Report.md`, `Architecture_Report.md`, `EraMatchedGOES_Protocol.md`, `analysis.json`, `reproducibility_manifest.json`, `verification.json`, this summary. Quality gates all PASS (70 tests, V3 + frozen harness integrity CONFIRMED, both dataset manifests verify, determinism identical, AgentOS 100/100).
