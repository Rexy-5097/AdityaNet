<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Study B Phase 0.5 — pre-registered measure-only feasibility gate for the Aditya-only program. Written and committed BEFORE any Aditya-only model is trained. -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-12 -->

# Study B — Aditya-only Feasibility (Phase 0.5, PRE-REGISTERED)

**One question, measured before committing any multi-sprint roadmap: do SoLEXS+HEL1OS ALONE carry enough predictive signal to forecast and/or nowcast solar flares, under the existing Version 4 infrastructure? Every arm to date has contained GOES; this has never been tested. This is a measure-only gate — simplest baseline, no new architecture, no transfer learning, no physics additions, no hyperparameter search. The decision rule below is fixed before results and cannot move after.**

## Design (locked)

- **Inputs:** the 15 engineered Aditya-L1 features only (indices 17–31 of `dataset_v4.1.0-s2`: 10 SoLEXS + 5 HEL1OS). **Zero GOES inputs.** GOES is used only as the label source.
- **Model:** the existing single-encoder `PatchTST(n_features=15)`. No changes.
- **Training:** the existing Sprint 32 driver and frozen protocol, byte-for-byte (AdamW 1e-4, FocalLoss γ2/α0.25, WeightedRandomSampler, patience 3, isotonic calibration on validation). No tuning.
- **Data:** the Stage-2 splits (`dataset_v4.1.0-s2`), Aditya columns subset. Train 786,298 / val 262,480 / test 261,455 rows.

## Two tasks

**Task 1 — Forecast (the risky, gating question).** Label = existing `target_6hr_binary` (M/X flare within 6h). Evaluated through the **frozen Sprint 24 harness on the S2 span** — so the result is directly comparable to the frozen GOES benchmark (F0 0.4068, F2 0.4022, EraMatchedGOES 0.4383, S2 persistence floor 0.3368). Seeds 42/43/44.

**Task 2 — Nowcast (the near-certain question).** Label = M/X flare in its **rise phase** (catalog `start_time`→`peak_time`, median 11 min) covering the window-end minute — a "flare rising now" detector. Window-level metrics only (ROC-AUC, TSS, precision/recall); the forecast-episode harness does not apply to nowcast semantics (formalizing a nowcast episode metric is deferred to the real Sprint 33). Single seed (42) — feasibility only.

## Pre-registered decision rule (FIXED before results)

**Forecast tiers** (Aditya-only, S2 test, policy operating point):
- **STRONG** — TSS ≥ 0.25 OR ROC-AUC ≥ 0.70 → clear standalone forecast signal.
- **WEAK-BUT-REAL** — 0.10 ≤ TSS < 0.25 AND ROC-AUC ≥ 0.60 → learnable but limited.
- **FAIL** — TSS < 0.10 OR ROC-AUC < 0.60 → no usable standalone forecast signal.

**Nowcast:** VIABLE if window-level ROC-AUC ≥ 0.80.

**Overall decision (mechanical):**
- Forecast STRONG or WEAK-BUT-REAL → **PROCEED** with the full Aditya roadmap (Sprints 33–37: nowcaster, forecaster with transfer learning + training fixes, payload ablation, standalone benchmark, operator demo).
- Forecast FAIL **and** Nowcast VIABLE → **PIVOT** to a nowcast-centric submission (explicitly allowed by the problem statement's "detect (nowcast) **or** predict (forecast)").
- Both FAIL → **RECONSIDER** project direction (report the honest negative).

No optimization is permitted in response to whichever tier is hit — the tier only selects the next roadmap, it does not license tuning this experiment.

## What this does and does not decide

Decides: whether standalone Aditya-L1 has learnable flare signal, and which task (forecast vs nowcast) is stronger — before a month of investment. Does not decide: the best achievable Aditya performance (that is the roadmap's job, with transfer learning and the training-regime fixes deliberately withheld here so this baseline stays honest and comparable).

## Reuse / integrity

Reuses unchanged: `dataset_v4` pipeline, `PatchTST`, the frozen Sprint 24 harness, provenance manifests, bootstrap, calibration, CI, tests. Sealed evaluation (no test metric inspected before the analysis step). The feasibility datasets carry their own provenance manifest. GOES `v4-goes-final` frozen artifacts are untouched.
