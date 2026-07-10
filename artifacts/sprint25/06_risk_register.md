<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Sprint 25 per-intervention risk register. -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-04 -->

# Sprint 25 — Risk Register

**Conclusion:** The highest-value intervention (E1, regime-inclusive training) is also the highest-risk, because re-drawing the training/validation split to include the Solar Cycle 25 ramp creates a leakage surface that must be controlled by strict chronological ordering — its failure mode is silent test contamination, and its rollback is total (revert to the frozen Solar Cycle 24-only split). Every other intervention is low-risk and independently revertible because each changes exactly one configuration value against the B0 baseline. Nothing in this campaign modifies a frozen Version 3 artifact; all outputs are new files.

Interventions reference `03_experiment_matrix.csv`; each row below is one pre-registered experiment.

## E1 — Regime-inclusive training data

- **Expected benefit:** Remove the operating-point transfer failure measured in Method D (validation True Skill Score 0.5689 collapsing to test True Skill Score 0.2150).
- **Scientific rationale:** Distribution shift is the only `SUPPORTED` data-level cause (`01_root_cause_analysis.md` H1); training on data representative of the Solar Cycle 25 operating regime is the direct test.
- **Risk:** Chronological leakage — if the re-drawn validation split overlaps or post-dates any training window, threshold and calibration selection become contaminated and every metric is invalid.
- **Failure mode:** Silent test contamination that inflates results without an obvious error; or the opposite, catastrophic forgetting of the quiet Solar Cycle 24 regime.
- **Rollback:** Revert to the frozen Solar Cycle 24-only training split (2010–2019) and 2020–2022 validation; E1 writes only new split-index files, never overwriting `artifacts/research/*.parquet`. Immediate-termination trigger (c) in `04_success_criteria.md` halts on any test read.

## E2 — Uncapped steps per epoch

- **Expected benefit:** Stabilize learning by training on the full set per epoch rather than ~6% (5,000 of 80,646 batches).
- **Scientific rationale:** `H8`/`H11` PARTIALLY SUPPORTED; the frozen run's 4.6-second epochs (`artifacts/training_history.json`) reflect heavy subsampling.
- **Risk:** Overfitting on the majority-negative distribution despite the sampler; 16× longer per-epoch time inflating the compute budget.
- **Failure mode:** Validation True Skill Score peaks early then degrades; or out-of-memory from longer runs.
- **Rollback:** Restore steps_per_epoch=5000; single-value revert.

## E3 — Early-stopping patience 8

- **Expected benefit:** Avoid premature stopping on the noisy 3-epoch validation True Skill Score trajectory (0.5667 → 0.4998 → 0.5936).
- **Scientific rationale:** `H11` PARTIALLY SUPPORTED (`artifacts/training_history.json`).
- **Risk:** Later checkpoints overfit; wasted epochs.
- **Failure mode:** Best validation True Skill Score occurs late but generalizes worse to test.
- **Rollback:** Restore patience=3; single-value revert.

## E4 — Cosine annealing horizon aligned to realized epochs

- **Expected benefit:** Let the learning-rate schedule complete its decay over the actual training length instead of being configured for 20 epochs while 3 run.
- **Scientific rationale:** `H8` PARTIALLY SUPPORTED (`app/services/ml/trainer.py:161-162`; `artifacts/training_history.json` shows lr barely decayed).
- **Risk:** Faster decay may starve later learning; interacts with early stopping.
- **Failure mode:** Under-training if the learning rate decays to near zero before convergence.
- **Rollback:** Restore T_max=max_epochs; single-value revert.

## E5 — Focal Loss alpha 0.50

- **Expected benefit:** Raise positive-class weight to improve recall/skill.
- **Scientific rationale:** `H2` PARTIALLY SUPPORTED; the trainer docstring documents alpha sensitivity (`app/services/ml/trainer.py:8-11,57-59`).
- **Risk:** All-positive prediction collapse (the exact failure the clamp was added to prevent).
- **Failure mode:** Immediate-termination trigger (a) — prediction collapse; the run is logged failed and **not** tuned to rescue it.
- **Rollback:** Restore alpha=0.25; single-value revert.

## E6 — Platt scaling calibration

- **Expected benefit:** Test whether the calibration family changes the persistence-clearing margin or the Expected Calibration Error.
- **Scientific rationale:** `H4` PARTIALLY SUPPORTED; both calibrators are already implemented (`scripts/calibrate_model.py:191-202`) and temperature scaling collapsed to True Skill Score 0.000 in Version 3 (`scientific_validation_report.md` §2), motivating a family comparison.
- **Risk:** Platt scaling's sigmoid assumption may fit the isotonic-favored distribution worse, degrading calibration.
- **Failure mode:** Higher Expected Calibration Error than the isotonic baseline B0.
- **Rollback:** Restore isotonic; single-value revert; the frozen `artifacts/calibrator.pkl` is never touched (E6 writes a new calibrator file).

## Cross-cutting risks

- **Single-machine, no-git bus factor** (`MIGRATION_REPORT.md`, `artifacts/sprint23_5/VERSION4_RISK_REGISTER.md` R6): initialize git before the campaign so every run is revertible; store checkpoints and prediction arrays under `artifacts/sprint25/` only.
- **Metal Performance Shaders cross-platform non-determinism** (±9.76e-4, `scientific_validation_report.md` §3): pin all runs to the same device; treat archived per-run prediction arrays as canonical; reproducibility failure beyond tolerance is immediate-termination trigger (d).
- **Frozen Version 3 integrity:** verified byte-identical at the start and end of the campaign (this document's sibling validation step); trigger (e) halts on any modification.
