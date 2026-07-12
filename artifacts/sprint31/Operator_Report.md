<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Sprint 31 — operator-facing implications of the F2 measurements. -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-12 -->

# Sprint 31 — Operator Report

**Bottom line for operations: no deployment change is justified by these measurements. The deployed configuration (V1 + the Sprint 23 clean policy — arm F0) remains statistically unbeaten on overall alert quality for the current solar regime: F2's True Skill Score (0.4022 ± 0.0151 across 5 seeds) is indistinguishable from F0's 0.4068 (paired difference not significant in any seed), and Operator Utility — the maximum cost-loss relative value, V_max = TSS (Richardson 2000, the pre-declared parameter-free definition) — is therefore also a tie. What F2 DOES change, dramatically and consistently, is the alert profile: it catches far more flare episodes before onset at the price of roughly ten times the false-episode load. Whether that trade is worth making is an operator cost-ratio question this pre-registration cannot answer.**

## The measured trade (OBSERVED, S2 span 2025-12-15..2026-06-14, policy thresholds 0.14/0.95)

| Quantity | F0 (deployed config) | F2 (5-seed mean) | Change |
|----------|----------------------|-------------------|--------|
| True Skill Score / Operator Utility V_max | 0.4068 | 0.4022 ± 0.0151 | none (n.s. in 5/5 seeds) |
| Episode recall | 0.5370 | 0.8370 | **+0.30** (significant) |
| Pre-onset episode recall | 0.3704 | 0.8111 | **+0.44** (significant in 5/5 seeds, +0.389..+0.463) |
| False episodes per month | 3.68 | 37.18 | **10.1× worse** |
| Yellow duty cycle | 0.2183 | 0.3191 | +0.10 (alerts ~32% of the time) |
| RED duty cycle | 0.0002 | 0.0010 | both effectively dormant |
| Median lead time (min) | 865 | 682 | −183 min |
| Expected Calibration Error | 0.0234 | 0.0257 | comparable |

Reading: under F2, a satellite operator would receive advance warning before 81% of M/X flare episodes instead of 37% — but would also field roughly 37 false alarm episodes per month instead of 3.7. In cost-loss terms the two profiles have equal peak value; they sit at different points on the same ROC surface (F2's ranking skill, ROC-AUC 0.7685 vs 0.7368, is actually higher — the policy threshold, frozen at 0.14/0.95 from the V1-era validation, does not exploit it).

## What would make this actionable (labeled recommendations, not actions)

1. **Episode-level cost-loss policy analysis under a NEW pre-registration** — the recurring finding of Sprints 30 and 31 (physics/instrument arms improve pre-onset recall at heavy false-alarm cost) is exactly the trade a cost-loss operator policy with an explicit C/L ratio adjudicates. This is decision-tree Path C's parallel operator track and does not depend on further model-skill gains. NOT PROVEN: whether any real operator's C/L ratio favors F2's profile.
2. **Threshold refit is NOT licensed:** the 0.14/0.95 policy thresholds are validation-derived for the V1 pipeline; refitting them for F2 on any test data is barred by the Sprint 23 rules, and refitting on S2 validation would constitute a new arm requiring pre-registration.
3. RED tier remains effectively dormant in every arm (duty ≤ 0.23% everywhere) — the Sprint 22 B2 bottleneck is untouched by feature or instrument work, consistent with its classification as a decision-layer problem.
