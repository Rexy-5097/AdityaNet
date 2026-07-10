<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Sprint 24 operator workload analysis, all numbers computed this session. -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-04 -->

# Sprint 24 — Operator Analysis

**Conclusion:** For a satellite operator with finite attention, the deployed Method C policy (yellow ≥ 0.14) is **marginally useful at best**: it holds the system in a yellow-alert state 41.5% of the time — roughly 9.9 hours of every day — across 376 alert episodes averaging 33.5 hours each, while still missing 204 of 730 flare episodes (28%) and raising 3.4 false alert episodes per month. That is a heavy, near-continuous alerting load for imperfect coverage. The RED tier does fire in this deterministic evaluation (94 red episodes, 0.93% of time), which is more usable, but Method C's overall duty cycle is the core operability problem. Method D is worse (77.7% alert time). Persistence is lighter (23.2% alert time) but retrospective. No evaluated policy is comfortably operator-grade.

All numbers computed this session (`artifacts/sprint24/results_abc.json`, `results_d.json`). Test span 41.42 months; 730 flare episodes; 17.6 flare episodes/month.

## Operator workload by policy

| Quantity | A persistence | C V1 + clean policy | D V1 + val-swept θ |
|----------|-------------:|--------------------:|-------------------:|
| Fraction of time in alert (yellow) | 0.2320 | 0.4150 | 0.7771 |
| Alert-minutes per day | 332.5 | 594.6 | 1113.4 |
| Alert episodes total | 730 | 376 | 76 |
| Alert episodes per month | 17.63 | 9.08 | 1.83 |
| Mean alert-episode duration | 9.7 h | 33.5 h | 309.7 h (~12.9 d) |
| False alert episodes per month | 7.82 | 3.43 | 0.27 |
| Flare episodes missed (of 730) | 323 | 204 | 43 |
| Pre-onset detections (of 730) | 225 | 441 | 668 |
| RED alert windows | n/a | 16,774 (0.93% of time) | n/a |
| RED alert episodes | n/a | 94 | n/a |
| Mean warning time (positive-lead fraction) | 481 min (0.55) | 2026 min (0.84) | 24,594 min (0.97) |

## Is Method C operationally useful?

**Partially, with a serious workload cost.** The case *for*: 9.08 alert episodes/month and 3.43 false episodes/month is a countable, non-overwhelming number of discrete events; 441 of 730 flare episodes are flagged before onset (60.4%); and unlike the frozen Version 3 backtest (which reported zero RED alerts through the suppression pipeline), the RED tier here issues 94 episodes, so the highest-severity channel is not inert at the threshold level. The case *against*: the system sits in yellow 41.5% of the time — an operator is being told "elevated risk" for the better part of every day, which erodes the signal value of the alert and invites alarm fatigue; alert episodes averaging 33.5 hours mean a single alert dominates an operator's attention for more than a full shift cycle; and 28% of flare episodes are still missed. A useful operational alert must be rarer, sharper, and shorter than this.

**Caveat that softens the burden, not the verdict:** Method C here applies the yellow/red thresholds deterministically and does **not** simulate the MC-Dropout uncertainty suppression or the sequential RED confirmation logic in `app/services/ml/inference.py`. Both mechanisms only ever *remove* alerts, so the true deployed duty cycle is lower than 41.5% and the false-episode rate is lower than 3.43/month — these are upper bounds. The direction of the operability problem (too much yellow, episodes too long) stands regardless, because suppression trims edges rather than restructuring the alert into short, sharp warnings.

## Is Method D useful?

**No.** It misses only 43 episodes but by alerting 77.7% of the time in 12.9-day-average alert episodes — an "almost always on" forecaster provides no actionable timing information. Its low false-episode rate (0.27/month) is a consequence of merging nearly everything into a handful of enormous alert episodes, not of precision.

## Is persistence useful as a reference?

Persistence alerts 23.2% of the time in tight ~9.7-hour blocks, but by construction it only "warns" about flares that have already occurred within the trailing window — its 0.55 positive-lead fraction means nearly half its "detections" come after onset. It is a light but retrospective baseline, not an operational forecaster.

## Operator bottom line

None of the evaluated operating points delivers the "rare, sharp, early" alert profile a finite-attention operator needs. The model has the *discrimination* to support such a profile (ROC-AUC 0.7482, clearly above persistence), but the current threshold-and-policy layer converts that discrimination into a high-duty-cycle, long-episode alert stream. Restructuring the alerting — shorter episodes, cost-calibrated thresholds, event-onset-focused triggering — is an operator-decision-layer problem, addressed in the recommendation (`07_decision_report.md`).
