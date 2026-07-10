<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Sprint 26B go/no-go decision on the training-procedure investigation. -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-05 -->

# NO-GO — E2 failed to exceed Baseline; the training-procedure investigation is complete and Sprint 26 should be closed.

E2 (uncapped steps per epoch), the last unscreened experiment, produced a test policy True Skill Score of 0.3770 against the Baseline's 0.3940 — a shortfall of 0.0170 on the primary endpoint (its advantage over persistence, +0.0752, is likewise below Baseline's +0.0923) — so no single-variable change to the training procedure improved on the frozen Version 1 baseline, and there is nothing left to confirm.

## Supporting evidence (all `OBSERVED` this session)

- **E2 is below Baseline on the primary endpoint.** Test policy True Skill Score 0.3770 versus 0.3940 (`artifacts/sprint26b/runs/E2/eval.json`; `artifacts/sprint26a/runs/Baseline/eval.json`). The pre-registered decision rule (`artifacts/sprint25/04_success_criteria.md`; this sprint's brief) is that if E2 does not exceed Baseline, the training-procedure investigation is declared complete.
- **E2 ranks last of seven.** Final ranking by test policy True Skill Score: Baseline 0.3940, E3 0.3940, E6 0.3934, E1 0.3840, E4 0.3798, E5 0.3793, E2 0.3770 (`artifacts/sprint26b/UPDATED_CONFIGURATION_RANKING.md`).
- **The mechanism is understood.** E2 overfit the quiet-sun Solar Cycle 24 training distribution: validation True Skill Score peaked at epoch 2 (0.5718, far below Baseline's 0.6053) and declined every epoch afterward while training loss kept falling (`artifacts/sprint26b/E2_EXECUTION_REPORT.md`). Training on the full imbalanced dataset each epoch made the fit tighter to the training regime, and that did not transfer to the operating regime — the opposite of the hypothesis that full-data epochs would improve the checkpoint.
- **The complete single-variable screen is exhausted.** Across all six other configurations (E1 regime-inclusive data, E3 patience 8, E4 shorter learning-rate horizon, E5 higher Focal-Loss alpha, E6 Platt calibration, plus the reference Baseline), none exceeded Baseline either; E2 was the final candidate and also failed.

## Decision

**Close Sprint 26. Declare the training-procedure investigation complete.** No single-variable training, learning-rate, loss, data-composition, or calibration change tested in Sprints 26A and 26B improved on the frozen Version 1 baseline on the primary endpoint. The five-seed confirmation campaign is not warranted, because there is no challenger configuration that exceeded Baseline to confirm.

## Important scope note (not a reopening of this decision)

This decision is `OBSERVED` on single seeds and closes the *training-procedure* line of investigation as pre-registered. It does not claim that the Version 1 architecture is at its ceiling in any deeper sense — it establishes only that the specific, evidence-motivated single-variable procedure changes enumerated in `artifacts/sprint25/03_experiment_matrix.csv` do not beat the baseline. The natural consequence, per the Sprint 24 decision framework, is that if further forecast-skill improvement is sought, it must come from beyond these training-procedure levers (for example architecture, or the multi-instrument data question) rather than from more of the same — but that is a Version 4 scoping matter, explicitly out of scope here, and no such work is begun.

## What must NOT happen next (per this sprint's constraints)

No additional experiments, no architecture redesign, and no Version 4 work are initiated by this decision. Sprint 26 closes here.
