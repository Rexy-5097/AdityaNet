<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Sprint 28 definitive fair Aditya-L1 experiment specification (pre-registered design). -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-05 -->

# Sprint 28 — Fair Aditya-L1 Experiment Specification (Task 4)

**Four arms — F0: GOES-14 baseline (frozen V1 reference); F1: GOES-physics (14 KEEP + goes_T_iso, goes_EM, goes_dT_iso_15m = 17 features); F2: GOES-physics + engineered Aditya features (all 32 Version 4 inputs, single concatenated encoder); F3: same 32 inputs through the per-timestep-mask late-fusion architecture. Primary metric: paired True Skill Score difference on the same-span test set under the frozen Sprint 24 statistical machinery, with pre-onset episode recall as the designated co-secondary.** The design isolates features (F1, F2) from fusion (F3) so a single experiment answers both the instrument question and the fusion question from `artifacts/sprint27/05_FUSION_LIMITATIONS.md`.

## Arms and dataset construction

| Arm | Features | Architecture | Train/val data | Test data |
|-----|----------|--------------|----------------|-----------|
| F0 | 14 GOES (KEEP set) | Frozen V1 PatchTST | Existing (frozen) | Both spans (already measured on V1 span: policy True Skill Score 0.3940, `artifacts/sprint26a/runs/Baseline/eval.json`; re-evaluated on the S2 span for pairing) |
| F1 | 17 GOES-physics | V1 PatchTST, input width 17 | V1-era splits rebuilt through the Version 4 pipeline (`03_DATASET_PIPELINE_V4.md`), 2010–2019 train / 2020–2022 validation | V1 test span AND S2 test span |
| F2 | 32 Version 4 inputs | Single PatchTST encoder on concatenated inputs (no per-instrument branches — avoids the encoder data-starvation defect B7, `artifacts/sprint28/01_ROOT_CAUSE_MATRIX.md`) | Stage-2 boundaries (`artifacts/sprint14c/s2_train/val.parquet` dates) rebuilt through the Version 4 pipeline | S2 test span |
| F3 | 32 Version 4 inputs | Late-fusion V3-style with per-timestep availability channels and window missing-token per `03_DATASET_PIPELINE_V4.md` §3 | Same as F2 | S2 test span |

**Cross-span comparability rule (design revision from adversarial review):** every Aditya-relevant comparison (F2 or F3 versus F1 or F0) is computed **same-span, paired** on the S2 test period; the F1-versus-F0 comparison on the full 16-year-trained V1 span is reported separately. No conclusion may mix spans.

## Evaluation framework

The frozen Sprint 24 `UnifiedEvaluator` (`scripts/sprint24/eval_framework.py`) with its exact constants — episode construction with 60-minute merge gap, onset = episode start + 360 minutes, moving-block bootstrap with 2,880-window blocks, 1,000 confusion replicates, 200 ranking-metric replicates, RNG seed 20260704 — applied unmodified. **One named modification, per the brief's allowance:** for arms F2/F3 the evaluator is instantiated on the Stage-2 test span (261,095 windows, 11.92% positive, `PROJECT_STATUS.md` dataset inventory) instead of the V1 test span, because the documented limitation is that Aditya-L1 data does not exist before December 2023 (`scripts/build_multi_instrument_dataset.py:116,122` zero-fills pre-2023), so the V1 span cannot evaluate instrument arms. Persistence and climatology floors are recomputed on that span through the identical class. Nothing else changes.

## Training procedure

The Sprint 25 frozen protocol baseline (`artifacts/sprint25/02_retraining_protocol.md`): AdamW learning rate 1e-4, weight decay 1e-4, CosineAnnealingLR T_max = max_epochs 20, Focal Loss gamma 2.0 alpha 0.25, WeightedRandomSampler, gradient clip 1.0, patience 3 on validation True Skill Score, steps-per-epoch 5,000, isotonic calibration fit on validation only, thresholds selected on validation only. Justification: Sprint 26 established this procedure's behavior across seven configurations; changing it here would confound the feature/fusion question with a training-procedure question.

## Statistics, seeds, and pre-registration

- **Statistical test:** paired moving-block bootstrap deltas on identical resample indices (the Sprint 24 `paired_window`/`paired_episode` machinery); significance = 95% percentile interval of the difference excluding zero. No IID tests, no McNemar (autocorrelation, `artifacts/sprint24/06_statistical_tests.md`).
- **Minimum seeds: 3 (42, 43, 44) per trained arm.** Justification: single-seed results are pre-classified exploratory by this repository's own standard (`artifacts/sprint26a/01_SCREENING_RESULTS.md`; requirement M2 of `artifacts/sprint27/07_VERSION4_REQUIREMENTS.md`); three seeds is the minimum giving an across-seed range and a majority criterion. Five seeds is the publication tier (below).
- **Minimum effect of interest (pre-registered): paired ΔTrue Skill Score ≥ +0.02.** Anchor: the full-instrument gap ever measured is +0.0085 single-seed (`scientific_validation_report.md` §6); an effect below 0.02 is within the plausible seed-noise band whose width is itself unmeasured (see Unresolved Criticism U1 in `07_EXTERNAL_REVIEW.md`) and will not be claimed as a positive finding regardless of interval position.
- **Success criteria (pre-registered):** Aditya value CONFIRMED only if F2 beats F1-on-S2 with paired ΔTrue Skill Score ≥ +0.02, lower 95% bound > 0, in at least 2 of 3 seeds, with pre-onset episode recall not degraded. Fusion value CONFIRMED only if F3 additionally beats F2 under the same rule.
- **Failure criteria (pre-registered):** if F2-versus-F1 fails the above in at least 2 of 3 seeds, the verdict is "no measurable Aditya-L1 value under fair conditions," closing the question at the feature level (decision tree Paths A/C, `05_VERSION4_DECISION_TREE.md`); no post-hoc arm, threshold, or metric substitution is permitted.
- **Stratified reporting (design revision from adversarial review):** all F2/F3 metrics additionally reported on availability strata (SoLEXS quality ≥ 0.9 versus < 0.9 windows, per `03_DATASET_PIPELINE_V4.md` §5) so operational downtime effects are visible rather than averaged away.
- **Publication-level minimum quality:** 5 seeds on the winning comparison, the extended flare-bearing audit corpus (campaign prerequisite P0, `artifacts/sprint27/06_EXPERIMENT_CAMPAIGN.md`) corroborating at audit level, all Sprint 23 provenance gates green, and the honest-negative contingency wording pre-authorized as in `artifacts/sprint25/07_preregistered_analysis_plan.md` §4.

## Compute (calibrated to `artifacts/sprint26a/04_COMPUTE_REPORT.md` measurements)

| Item | Basis | Estimate |
|------|-------|----------|
| F1 training ×3 seeds | measured V1-scale 38.2 min train + ~10 min eval | ~2.5 h |
| F0/F1 S2-span re-evaluations | measured eval ~10 min each | ~0.7 h |
| F2 training ×3 seeds (S2 splits are ~15% of V1 train size; input width 32 vs 14) | scaled from measured V1 anchors | ~1.5–2.5 h |
| F3 training ×3 seeds (V3-scale, 5.3× parameters) | extrapolated 3–5× V1 — extrapolation, not measurement | ~6–10 h |
| Dataset rebuilds (V4 pipeline, both split families) | input/output-bound, cf. E1 split build measured minutes | ~2–3 h |
| **Total** | | **~13–19 h; feasible in two to three overnight M4 sessions; F3 deferrable to CUDA if constrained (priority order F1 → F2 → F0-S2 → F3)** |
