<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Sprint 30 Phase 5 — pre-registered statistical analysis of F1 vs F0. -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-11 -->

# Sprint 30 — Statistical Analysis (F1 vs F0)

**Primary endpoint: FAILED. The pre-registered minimum effect of interest — paired ΔTrue Skill Score ≥ +0.02 with lower 95% bound > 0 — is met by 0 of 5 seeds (majority of 3 required after escalation). Mean paired ΔTSS = −0.0311 ± 0.0276 (DERIVED); the delta is significantly NEGATIVE in 3 of 5 seeds and not significantly different from zero in the other 2. The result is invariant across all three block lengths tested. This is a definitive negative on the pre-registered question.**

Plan applied: `artifacts/sprint25/07_preregistered_analysis_plan.md` plus the statistics section of `artifacts/sprint28/04_FAIR_ADITYA_EXPERIMENT.md` and the criteria in `artifacts/sprint29/experiments/F1.json`. (The Sprint 30 brief cited the path `artifacts/sprint28/07_preregistered_analysis_plan.md`, which does not exist; the Sprint 25 document is the pre-registered analysis plan of record and is what the Sprint 28 specification itself cites.) Analysis code: `scripts/sprint30/analyze.py`, committed with every interpretive rule pre-declared **before results existed** (commits `3bf2ee8` and `89a688d`). Machine-readable record: `artifacts/sprint30/analysis.json`.

## Primary endpoint (OBSERVED — paired moving-block bootstrap, policy operating point)

Per-seed paired ΔTSS (F1 seed minus F0, identical resample indices through the frozen harness's `paired_window`):

| Seed | ΔTSS | 95% CI | Significant | ≥ +0.02 | Lower bound > 0 | Seed passes |
|------|------|--------|-------------|---------|------------------|-------------|
| 42 | −0.0089 | [−0.0311, +0.0139] | no | no | no | **no** |
| 43 | −0.0397 | [−0.0647, −0.0152] | yes (negative) | no | no | **no** |
| 44 | −0.0514 | [−0.0761, −0.0272] | yes (negative) | no | no | **no** |
| 45 | +0.0043 | [−0.0197, +0.0281] | no | no | no | **no** |
| 46 | −0.0597 | [−0.0845, −0.0345] | yes (negative) | no | no | **no** |

Success criterion (pre-registered, post-escalation majority form): ΔTSS ≥ +0.02 with lower 95% bound > 0 in ≥ 3 of 5 seeds, pre-onset recall not significantly degraded → **0 of 5 pass → FAILURE** (`F1.json:failure_criterion`: "criterion unmet … → negative verdict; no post-hoc substitution permitted"). Even the best seed (45, +0.0043) sits below the minimum effect of interest with an interval spanning zero — under the pre-registration, an effect below +0.02 "will not be claimed as a positive finding regardless of interval position."

Effect size (DERIVED): one-sample Cohen's d of the per-seed deltas against zero = mean/std = −0.0311 / 0.0276 = **−1.13** (the pre-declared form; F0 is a fixed reference with no seed distribution).

## Block size and its justification

Block length 2,880 windows (2 days) is the frozen Sprint 24 constant: 8 × the 360-minute label horizon, so at most one block boundary in eight severs a label-dependence span; stride-1 windows overlap 359/360 minutes, making IID tests and McNemar invalid (autocorrelation — `artifacts/sprint24/06_statistical_tests.md`), hence the moving-block bootstrap with 1,000 confusion replicates, 200 ranking replicates, episode blocks of 10, RNG seed 20260704. Robustness (pre-registered check, OBSERVED): the per-seed ΔTSS point estimates are IDENTICAL at block lengths 1,440 / 2,880 / 5,760 (point estimates do not depend on resampling), and the significance classification of every seed is unchanged at all three lengths (seeds 43/44/46 significantly negative, seeds 42/45 not significant, at every block size). The 2,880 result is authoritative; nothing hinges on the choice.

## Secondary endpoints (OBSERVED per-arm values; deltas DERIVED; none may be promoted to the headline)

| Endpoint | F0 | F1 (5-seed mean) | Δ (mean) | Reading |
|----------|-----|------------------|----------|---------|
| ROC-AUC | 0.7521 | 0.7481 | −0.0040 | no ranking-skill change |
| PR-AUC | 0.4680 | 0.4839 | +0.0160 | small gain |
| Episode recall | 0.7301 | 0.8120 | +0.0819 | improved, significant in 5/5 seeds (paired) |
| Pre-onset episode recall | 0.6192 | 0.7589 | +0.1397 | improved, **significant in 5/5 seeds** (paired: +0.1014, +0.1315, +0.0973, +0.2068, +0.1616) |
| Expected Calibration Error | 0.0685 | 0.0781 | +0.0096 | slightly worse |
| False episodes/month | 3.16 | 16.94 | +13.78 | **5.4× worse** |
| Yellow duty cycle | 0.4210 | 0.4137 | −0.0073 | unchanged |
| Median lead time | 1,451 min | 705 min | −746 min | halved |

The coherent picture: F1's alerting is *fragmented* — it catches more distinct flare episodes and far more of them before onset (the physics features do appear to carry pre-onset information), but it emits ~17 false episodes per month against F0's 3.2 at similar total alert time, and its window-level recall is lower (0.68–0.73 vs 0.7236), which is what the primary TSS metric penalizes. Under the pre-registered multiple-comparisons stance, the pre-onset recall gain is a secondary observation and cannot alter the FAILURE verdict; it is recorded as hypothesis-generating for the episode-level operator-policy program (decision tree Path C's parallel track).

## Validation-to-test transfer note (OBSERVED)

Every F1 seed beat F0 on validation TSS (0.6044–0.6199 vs 0.6053, best-epoch values) yet 4 of 5 lost on test — repeating the Sprint 24 Method D lesson that the 2020–2022 validation regime rewards different behavior than the 2023–2026 test regime. The pre-registration anticipated exactly this failure mode by putting the verdict on the sealed test evaluation through the frozen harness, not on validation numbers.

## Sources

Every number above traces to `artifacts/sprint30/analysis.json` (generated by `scripts/sprint30/analyze.py` from the sealed `artifacts/sprint30/runs/*/eval.json` records and archived calibrated probability arrays) — all produced in this session. No value is carried from any pre-session source except F0's pre-registered reference 0.3940, which this session's re-evaluation reproduced exactly (0.3940129618, `Sprint30_F0_Report.md`).
