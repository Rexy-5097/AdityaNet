<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Sprint 24 episode-level metrics, all numbers computed this session. -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-04 -->

# Sprint 24 — Episode-Level Metrics

**Conclusion:** At the episode level — the operator-relevant view — the V1 model with the clean policy (Method C) detects 526 of 730 flare episodes (episode recall 0.7205) versus persistence's 407 (0.5575), and detects **before flare onset** on 60.4% of episodes versus persistence's 30.8% — nearly double, and the single most operationally meaningful result of the sprint. But this comes with long, heavy alerting: Method C's alert episodes average 33.5 hours and cover 41.5% of all time. Persistence, by contrast, alerts in tight 6-hour blocks tied to flares that already happened, so its "lead time" is largely retrospective.

All numbers computed this session (`artifacts/sprint24/results_abc.json`, `results_d.json`) via `scripts/sprint24/eval_framework.py`. Episode construction: maximal positive-label runs merged across gaps ≤ 60 minutes; first flare onset = episode start + 360 minutes; "pre-onset detected" = alerting began before the first flare onset. 730 label episodes over 41.42 months (17.6 flare episodes/month).

## Episode metrics (identical framework)

| Metric | A persistence | B climatology | C V1 + clean policy | D V1 + val-swept θ |
|--------|-------------:|--------------:|--------------------:|-------------------:|
| Episodes detected (of 730) | 407 | 0 | 526 | 687 |
| Episodes missed | 323 | 730 | 204 | 43 |
| Episode recall | 0.5575 | 0.0000 | **0.7205** | 0.9411 |
| Episode recall 95% CI | [0.5151, 0.6028] | [0, 0] | [0.6767, 0.7685] | — |
| Pre-onset episode recall | 0.3082 | 0.0000 | **0.6041** | 0.9151 |
| Pre-onset recall 95% CI | [0.2671, 0.3507] | [0, 0] | [0.5575, 0.6548] | — |
| Episode precision | 0.5562 | 0.0000 | 0.6223 | 0.8553 |
| Number of alert episodes | 730 | 0 | 376 | 76 |
| False alert episodes / month | 7.823 | 0.000 | 3.429 | 0.266 |
| Mean lead time (min) | 481.3 | — | 2026.4 | 24593.9 |
| Median lead time (min) | 455.0 | — | 1262.5 | 14735.0 |
| Positive-lead fraction | 0.5528 | 0.0000 | 0.8384 | 0.9723 |
| Mean alert duration (min) | 579.9 | 0.0 | 2010.7 | 18583.0 |
| Median alert duration (min) | 360.0 | 0.0 | 1132.5 | 11184.5 |

## Reading the table

- **Pre-onset recall is the headline.** Episode recall counts any alert that overlaps a flare episode, including alerts that fire only after the flare has begun — of limited protective value. Pre-onset recall counts only episodes where the alert preceded the first flare. Method C achieves 0.6041 versus persistence 0.3082, a +0.2959 difference (significant, `06_statistical_tests.md`). This is where the model earns its keep: persistence, by construction, mostly "detects" a flare episode only once a flare in it has already fired (its pre-onset recall of 0.31 comes only from clustered episodes where an earlier flare precedes a later one). The model genuinely anticipates.

- **The lead-time numbers must be read with care.** Method C's mean lead time of 2026 minutes and Method D's of 24,594 minutes are inflated by long, merged alert episodes: when the model sits in an alert state for many hours or days, the "earliest overlapping alert" can precede onset by a large margin, some of which is really just a high duty cycle rather than precise anticipation. The positive-lead fraction (C: 0.84, D: 0.97) is more trustworthy than the mean. Persistence's lead of ~455 minutes is near the 360-minute horizon because its alerts are mechanically tied to flares within the trailing window.

- **Method D's episode dominance is a duty-cycle artifact.** D detects 687/730 episodes and misses only 43, with just 0.27 false episodes/month — superficially excellent. But it achieves this by alerting 77.7% of the time in 76 enormous alert episodes averaging 18,583 minutes (~13 days) each. A forecaster that is almost always on trivially covers almost every flare; this is not skill, it is the degenerate high-recall corner, and it is why episode recall alone cannot decide the verdict.

- **Method C's operating point is heavy but structured.** 376 alert episodes, mean duration 33.5 hours, 3.43 false episodes/month, covering 41.5% of time. Better than D's near-constant alerting, but still a high burden — quantified for the operator in `05_operator_analysis.md`.
