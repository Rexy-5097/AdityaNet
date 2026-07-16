<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Layer 3 — provenance and integrity record for the frozen-contract execution. -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-16 -->

# Layer 3 — Provenance Report

**All frozen artifacts byte-identical throughout; all leakage gates pass; the contract was executed without modifying any pre-registered element.**

## Frozen-artifact fingerprints (verified pre-execution and re-verified at closure; OBSERVED)

| Artifact | Check | Status |
|----------|-------|--------|
| Frozen contract `artifacts/sprint33_nowcast/00_PREREGISTRATION.md` | committed at `d142cf8` before any result; unmodified since | INTACT |
| Version 3 stage-2 checkpoint | SHA-256 == `benchmark_manifest.json` | INTACT |
| Frozen `artifacts/sprint14c/s2_test.parquet` | SHA-256 == `benchmark_manifest.json` | INTACT |
| Sprint-24 harness `scripts/sprint24/eval_framework.py` | SHA-256 == `artifacts/sprint26/phase1_fingerprints.json`; imported, never edited | INTACT |
| Study A tag `v4-goes-final` | present, unmodified | INTACT |

## Leakage discipline (OBSERVED per seed)

For every seed (42–46): the isotonic calibrator was fit on the validation split only and serialized with its SHA-256 recorded in `operating_point.json` **before** any test read; the operating threshold was selected on validation calibrated probabilities only (`calibrator_fitted_on: "validation"`, `threshold_selected_on: "validation"` recorded per seed); the test set was opened exactly once per seed for a single `UnifiedEvaluator.evaluate()` call; no metric was recomputed with different parameters after the sealed pass. The nowcast feature set has empty overlap with the GOES-17 feature list (verified — 15 features, all SoLEXS/HEL1OS-derived); GOES enters only as the label source via the NOAA catalog, per the standing rule in `artifacts/GOES_Study_Final_Report.md`. Post-sealing analyses (trade-off curve, sensitivity labels) post-process the frozen `test_cal_probs.npy` arrays with deterministic ground-truth labels — no model re-inference, frozen operating points unchanged.

## Determinism (OBSERVED)

`eval_episode_nowcast.py` re-run for seed 42 produced identical primary metrics; `analyze.py` re-run produced identical aggregation, decision, signal-versus-policy classification, and sensitivity tables (verified at both the three-seed and five-seed stages). Eval loaders use `num_workers=0`, ordered iteration.

## Deviations log (complete; none scientific)

Two implementation bugs occurred and were fixed without touching any pre-registered element: a verification-script substring bug that falsely flagged four SoLEXS features as GOES columns (corrected to exact-set disjointness, which passes), and a shell command that wrote the Component 1 runner before creating its directory (recreated; no training had run). One wording-discipline correction adopted from external review is applied throughout the deliverables: `SIGNAL-LIMITED` is confined to its pre-registered definition, "minimum observed under the tested configuration" replaces "floor," and the trade-off sweep-range caveat is stated explicitly. No hypothesis, threshold, seed, metric, stopping rule, or statistical procedure was modified after execution began; no run was repeated because its result was disappointing.

## Reproducibility

`scripts/sprint33_nowcast/run.sh` reproduces the full sprint from scratch (five seeds, sealed evals, frozen aggregation). Per-seed artifacts under `artifacts/sprint33_nowcast/runs/s<seed>/`: `calibrator.pkl` (hashed), `operating_point.json`, `val_cal_probs.npy`, `test_cal_probs.npy`, sealed `eval.json`. Checkpoints under `artifacts/sprint33/runs/NC_s<seed>/best.pt` (on disk, referenced by hash-recorded metadata).
