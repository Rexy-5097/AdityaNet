<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Sprint 26A summary for the go/no-go decision on Sprint 26B. -->
<!-- SUPERSEDED BY: Sprint 26B (not yet run) -->
<!-- DATE: 2026-07-04 -->

# Sprint 26A — Summary

> Exploratory result only. Requires confirmation in Sprint 26B.

## Complete ranking table (single seed, exploratory)

| Rank | Configuration | Test True Skill Score | Delta from Baseline | ROC-AUC | PR-AUC | Expected Calibration Error | Pre-onset Recall | False Episodes/Month | Duty Cycle |
|------|---------------|----------------------:|--------------------:|--------:|-------:|---------------------------:|-----------------:|---------------------:|-----------:|
| 1 | Baseline | 0.3940 | 0.0000 | 0.7521 | 0.4680 | 0.0685 | 0.6192 | 3.163 | 0.4210 |
| 2 | E3 (patience 8) | 0.3940 | +0.0000 | 0.7521 | 0.4680 | 0.0685 | 0.6192 | 3.163 | 0.4210 |
| 3 | E6 (Platt calibration) | 0.3934 | −0.0006 | 0.7559 | 0.4907 | 0.0900 | 0.6479 | 2.873 | 0.4449 |
| 4 | E1 (regime-inclusive data) | 0.3840 | −0.0100 | 0.7514 | 0.4792 | 0.0827 | 0.6055 | 3.380 | 0.4142 |
| 5 | E4 (T_max = 10) | 0.3798 | −0.0142 | 0.7504 | 0.4780 | 0.0734 | 0.6466 | 3.042 | 0.4307 |
| 6 | E5 (alpha 0.50, interrupted) | 0.3793 | −0.0147 | 0.7506 | 0.4674 | 0.0804 | 0.6466 | 3.525 | 0.4254 |
| — | E2 (uncapped steps) | `NOT PROVEN` | — | — | — | — | — | — | — |

## What this means, in plain terms

A reader deciding whether to fund Sprint 26B should understand three things. First, this is a single-seed screening and every number above is exploratory; nothing here establishes that any configuration is genuinely better or worse than another, because seed-to-seed variation has not been measured. Second, among the six configurations that completed, none of the single-variable ablations improved on the retrained Baseline's test True Skill Score of 0.3940: the patience change (E3) reproduced the Baseline checkpoint exactly, the alternative calibration (E6) matched it on True Skill Score while trading better ranking metrics for worse calibration, and the regime-inclusive data (E1), the shorter learning-rate horizon (E4), and the higher Focal-Loss alpha (E5) all landed below Baseline. Third, and most importantly, the one experiment that could not be completed — E2, training on the full dataset each epoch rather than six percent of it — is precisely the intervention whose effect is unknown, so the screening is genuinely incomplete and its central question is unresolved.

Notably, the regime-inclusive data experiment (E1) did not reduce the operating-point transfer problem it was designed to address, which is a scientifically interesting negative signal given that distribution shift was the one root cause rated SUPPORTED; but a single seed on one particular chronological split is thin evidence, and this should be read as a prompt to re-examine the mechanism, not as a refutation of it.

## Sprint 26B recommendation

Confirm **Baseline** and **E6 (Platt calibration)** across five seeds each through the frozen Sprint 24 evaluation, primarily to establish the Baseline's missing seed-variance distribution and to test whether E6's ranking-metric advantage survives, and **resolve E2 at single seed first** because it is the only untested lever and targets a real limitation (the model currently sees only six percent of the training data per epoch). Exact verbatim hyperparameters are in `03_RECOMMENDED_CONFIRMATION.md`. Nothing else should be confirmed; E1, E3, E4, and E5 do not warrant five-seed compute on the practical grounds recorded in `02_CONFIGURATION_RANKING.md`.

## Compute projection

On Apple M4 Metal Performance Shaders, measured this session: the Baseline-plus-E6 five-seed confirmation is approximately six to eight hours, and adding the single-seed E2 resolution adds approximately five to eight hours, for a full recommended Sprint 26B of roughly eleven to sixteen hours. Sprint 26 established by direct measurement that the bottleneck is compute rather than storage, so a CUDA GPU would meaningfully shorten this — most consequentially for the uncapped E2 run, which is the campaign's limiting factor on Metal Performance Shaders. Details in `04_COMPUTE_REPORT.md`.

> Exploratory result only. Requires confirmation in Sprint 26B.
