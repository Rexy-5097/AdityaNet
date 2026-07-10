<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Sprint 26A recommendation for the Sprint 26B confirmation campaign. -->
<!-- SUPERSEDED BY: Sprint 26B (not yet run) -->
<!-- DATE: 2026-07-04 -->

# Sprint 26A — Recommended Sprint 26B Confirmation Campaign

> Exploratory result only. Requires confirmation in Sprint 26B.

**Conclusion:** Sprint 26B should confirm the **Baseline** and **E6 (Platt calibration)** configurations, each across five seeds, evaluated only through the frozen Sprint 24 framework — **and must additionally resolve E2 (uncapped steps per epoch), which Sprint 26A did not screen.** Because no completed ablation beat Baseline and E6 only matches it, the confirmation is as much about establishing the Baseline's seed-variance distribution (which still does not exist) as about testing a challenger; E2 remains the one genuinely unknown lever and should be screened at single seed before or alongside the five-seed confirmation.

## Recommended configurations (maximum 2 plus Baseline)

### Baseline — verbatim from `artifacts/sprint25/03_experiment_matrix.csv`
> AdamW 1e-4/wd1e-4, CosineAnnealingLR T_max=max_epochs, FocalLoss gamma2.0 alpha0.25, WeightedRandomSampler ~0.50, steps_per_epoch 5000, max_epochs 20, patience 3, isotonic calibration, 5 seeds

Five seeds: 42, 43, 44, 45, 46. Frozen Sprint 24 evaluation. Rationale: the seed-variance reference distribution for the frozen Version 1 configuration still does not exist (only single-seed points from Sprint 26 and Sprint 26A); it must be established before any challenger can be judged.

### E6 — Platt scaling calibration — verbatim from `artifacts/sprint25/03_experiment_matrix.csv`
> variable_changed: calibration method; new_value: Platt scaling (logistic regression on logits); baseline_value: isotonic regression

Five seeds: 42, 43, 44, 45, 46, each reusing that seed's Baseline-trained checkpoint with Platt calibration substituted for isotonic (training is identical to Baseline; only the calibration family differs). Frozen Sprint 24 evaluation. Rationale: E6 matched Baseline on test True Skill Score (0.3934 versus 0.3940) with a higher ROC-AUC (0.7559 versus 0.7521), a higher PR-AUC (0.4907 versus 0.4680), and a lower false-episode rate (2.873 versus 3.163 per month), at the cost of a worse Expected Calibration Error (0.0900 versus 0.0685); whether that discrimination-versus-calibration trade-off is real or seed noise is exactly what confirmation should resolve. Because E6 requires no separate training, adding it to the Baseline confirmation is nearly free.

## Mandatory addendum — resolve E2 first

E2 (steps_per_epoch = 80646, full-data-per-epoch) was **not screened** in Sprint 26A (`NOT PROVEN`). It is the only configuration whose effect is entirely unknown, and it targets a PARTIALLY SUPPORTED root cause (the model sees only ~6% of the training set per epoch under the cap). Sprint 26B should screen E2 at single seed 42 to completion before committing five-seed compute, and promote it to the five-seed confirmation only if its single-seed test True Skill Score is at or above Baseline.

## Nothing else

Sprint 26B runs only Baseline (5 seeds), E6 (5 seeds, calibration-only), and the E2 single-seed resolution described above. E1, E3, E4, and E5 are not recommended for confirmation on the practical grounds recorded in `02_CONFIGURATION_RANKING.md`. No parameter is changed from `03_experiment_matrix.csv`; the frozen Sprint 24 evaluation and the Sprint 25 success criteria apply unchanged.

> Exploratory result only. Requires confirmation in Sprint 26B.
