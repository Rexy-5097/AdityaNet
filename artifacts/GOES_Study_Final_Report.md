<!-- VERSION STATUS: FROZEN -->
<!-- REASON: Capstone of the completed GOES benchmark & incremental-value study (Sprints 22-32). Frozen at git tag v4-goes-final. No further experiments. -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-12 -->

# GOES Study — Final Report (Study A, FROZEN)

**Status: COMPLETE. Frozen at git tag `v4-goes-final`. This study answered one research question — "does adding SoLEXS+HEL1OS improve a state-of-the-art GOES flare-forecasting system?" — rigorously and in the negative. It is preserved as a scientific benchmark and comparison. No further experiments run against it; only bug fixes. All new engineering effort moves to the Aditya-only program (Study B).**

## The research question this study closed

> Under fair, physics-engineered, era-controlled, multi-seed evaluation, do the Aditya-L1 X-ray payloads (SoLEXS + HEL1OS) provide statistically significant incremental predictive value **beyond GOES** for operational solar-flare forecasting?

**Answer: NOT SUPPORTED** (`artifacts/sprint32/FINAL_VERDICT.md`).

## Benchmark numbers (OBSERVED, frozen Sprint 24 harness)

| Arm | Configuration | Span | TSS |
|-----|---------------|------|-----|
| Persistence floor | causal trailing-6h | V1 | 0.3018 |
| V1 + clean policy (deployed) | 14 GOES features | V1 | 0.3811 |
| EraMatchedGOES | GOES-17, recent (S2) era | S2 | **0.4383 ± 0.0055** (best) |
| F0 | GOES-14, original era (frozen V1) | S2 | 0.4068 |
| F2 | GOES-17 + 15 Aditya + 4 masks | S2 | 0.4022 ± 0.0151 |
| F3 | same, late fusion | S2 | 0.3952 ± 0.0142 |
| S2 persistence floor | — | S2 | 0.3368 |

Key de-confounded deltas (S2 span, paired): Aditya effect ΔTSS(F2−EraMatchedGOES) = **−0.0388** (0/3 passing, negative 3/3); late-fusion ΔTSS(F3−F2) = **−0.0070** (0/5); era effect ΔTSS(EraMatchedGOES−F0) = **+0.0315** (positive 3/3).

## What the study established (each a completed result)

1. **Leakage discovery & remediation** (Sprints 22.5–23): the deployed operator thresholds had been swept on test-set predictions; a versioned, provenance-gated policy system replaced them (`app/services/ml/policy.py`, 9 startup checks).
2. **Honest baseline** (Sprint 24): V1+policy beats causal persistence on TSS (paired Δ+0.0794, p≈0.001) through a frozen episode-level block-bootstrap harness.
3. **Training-procedure levers exhausted** (Sprints 26/26A/26B): no ablation beat the baseline.
4. **GOES physics features fail** (Sprint 30): F1 (T_iso/EM/dT) did not beat F0, 0/5 seeds. Path A foreclosed.
5. **Aditya incremental value fails** (Sprint 31→32): F2 beat F1 but the era-matched control proved that margin was training era, not features; F2 does not beat era-matched GOES. PARTIALLY→NOT SUPPORTED.
6. **Late fusion fails** (Sprint 32): F3 is the worst arm; Path D foreclosed.
7. **The one positive lever: data recency.** Retraining GOES-only on the recent era (+0.0315 TSS over F0) is the only change that improved on the deployed baseline — consistent across seeds, not instrument- or feature-driven.

## Frozen assets (immutable; enforced by fingerprints/manifests)

Frozen inputs: V3 checkpoints, frozen datasets (`artifacts/research/*.parquet`, `artifacts/sprint14c/s2_*.parquet`), the Sprint 24 harness (`scripts/sprint24/eval_framework.py`, SHA-pinned). Sealed results: all Sprint 24/26/30/31/32 `runs/*/eval.json` + analysis.json. Provenance: `benchmark_manifest.json`, `artifacts/sprint26/phase1_fingerprints.json`, both dataset_v4 manifests. These were already fingerprint-guarded; the tag `v4-goes-final` records the completion point.

## Shared infrastructure that stays LIVE (reused by Study B — NOT frozen)

`app/services/ml/model.py`, `features_v4/` framework, `dataset_v4/` (scaling, masks, manifest), the frozen harness (used, not modified), calibration, bootstrap, provenance system, CI, unit tests, the pre-registration/sealed-evaluation discipline. Study B swaps **only the input features** (GOES → SoLEXS+HEL1OS); everything else transfers unchanged.

## Handoff to Study B

The completed question was "does Aditya improve GOES." The open question — and the one the ISRO challenge actually asks — is "can a pipeline built on SoLEXS+HEL1OS forecast/nowcast flares on its own." That has never been tested (every arm here contained GOES). Study B begins with a measure-only feasibility gate (`artifacts/sprint33/00_FEASIBILITY_PREREGISTRATION.md`) before any multi-sprint commitment.
