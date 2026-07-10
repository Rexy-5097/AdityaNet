<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Sprint 24 paired significance tests, computed this session. -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-04 -->

# Sprint 24 — Statistical Tests

**Conclusion:** Method C (V1 + clean policy) significantly beats causal persistence on True Skill Score (+0.0794, p ≈ 0.001), Matthews Correlation Coefficient (+0.0248, p = 0.032), recall (+0.2439), F1 (+0.0438), episode recall (+0.1630), and pre-onset episode recall (+0.2959) — every one with a paired 95% confidence interval excluding zero. On Heidke Skill Score the difference is −0.0029 with a confidence interval [−0.0243, +0.0202] spanning zero (p = 0.82): **on Heidke Skill Score, C beating persistence is NOT PROVEN.** On window precision, persistence is significantly better (C is worse by −0.0681). The validation-swept-threshold model (Method D) is significantly *worse* than persistence on True Skill Score (−0.0868), confirming operating-point transfer failure across the regime shift.

## Test used

Paired moving-block bootstrap. For each of 1,000 replicates the same resampled blocks are drawn for both methods (identical RNG indices), the metric is recomputed for each, and the per-replicate difference is formed. Significance = the 95% percentile interval of the difference excludes zero. Bootstrap two-sided p-value = 2 × min(fraction of differences ≤ 0, fraction ≥ 0), floored at 1/1000. McNemar's test is deliberately **not** used: it assumes independent paired trials, which stride-1 autocorrelated windows violate. Justification and block size in `04_bootstrap_analysis.md`.

## Method C versus Method A (causal persistence)

| Metric | Δ (C − A) | 95% CI of Δ | Bootstrap p | Significant | Interpretation |
|--------|----------:|-------------|------------:|:-----------:|----------------|
| True Skill Score | +0.0794 | [+0.0538, +0.1062] | 0.001 | **Yes** | The model's skill exceeds persistence; robust across block sizes. |
| Heidke Skill Score | −0.0029 | [−0.0243, +0.0202] | 0.820 | No | **NOT PROVEN** — essentially tied; C is fractionally lower. |
| Matthews Corr. Coef. | +0.0248 | [+0.0021, +0.0486] | 0.032 | Yes | Modest but significant correlation advantage. |
| Recall / POD | +0.2439 | [+0.2222, +0.2662] | 0.001 | Yes | The model catches far more flare windows. |
| Precision | −0.0681 | [−0.0829, −0.0508] | 0.001 | Yes (adverse) | Persistence is significantly **more** precise; C trades precision for recall. |
| F1 | +0.0438 | [+0.0272, +0.0617] | 0.001 | Yes | Net of the recall gain and precision loss, C's F1 is higher. |
| Episode recall | +0.1630 | [+0.1342, +0.1945] | 0.001 | Yes | 526 vs 407 of 730 episodes detected. |
| Pre-onset episode recall | +0.2959 | [+0.2575, +0.3384] | 0.001 | Yes | The operationally decisive result: near-doubling of before-onset detection. |

ROC-AUC is compared by interval non-overlap rather than a paired delta: C 0.7482 [0.7309, 0.7669] versus A 0.6509 [0.6328, 0.6685] — non-overlapping, so C's discrimination is significantly better.

## Method C versus Method B (climatology)

Every metric significant in C's favor (climatology emits no alerts): True Skill Score +0.3811 [0.3434, 0.4168], Heidke +0.2989, recall +0.7077, episode recall +0.7205 — all p ≈ 0.001. Beating climatology is necessary but trivial; it is the no-skill floor.

## Method D versus Method A and Method C

| Comparison | ΔTSS | 95% CI | Significant | Interpretation |
|-----------|-----:|--------|:-----------:|----------------|
| D − A (persistence) | −0.0868 | [−0.1296, −0.0451] | **Yes (adverse)** | The validation-swept raw-threshold model is significantly **worse** than persistence on window True Skill Score — the model at that operating point loses to the trivial baseline. |
| D − C (clean policy) | −0.1661 | [−0.2026, −0.1303] | Yes (adverse) | Calibration + the policy threshold (C) is what lifts the model above persistence; the raw validation-optimal threshold (D) does not transfer. |

Note D beats both A and C on *episode* recall (+0.3836 vs A, +0.2205 vs C, both significant), but this is the duty-cycle degeneracy documented in `03_episode_metrics.md` (alerting 77.7% of the time), not genuine skill — which is exactly why window-level True Skill Score, where D fails, is retained as a check on episode-level recall.

## Plain-language summary

The model genuinely outperforms persistence, but the claim must be stated precisely: it wins on True Skill Score, on discrimination (ROC-AUC), and especially on anticipating flares before they begin, all with statistical significance under the correct autocorrelation-aware test. It is a *tie* on Heidke Skill Score (not proven) and it is *less precise* than persistence. It is not a landslide; it is a modest, real, and directional advantage concentrated in recall and early warning.
