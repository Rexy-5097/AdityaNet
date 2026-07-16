<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Layer 3 — statistical record: bootstrap intervals, seed variance, escalation. -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-16 -->

# Layer 3 — Statistical Analysis

**The five-seed primary endpoint fails decisively and the failure is not a statistical artifact: every seed's entire 95% block-bootstrap confidence interval for false episodes per month sits far above the 5.0 budget (the lowest lower bound across all seeds is 18.09, seed 44), the across-seed mean is 35.94 ± 11.17, and the verdict is invariant to seed selection — 0 of 5 pass where 3 of 5 were required.**

## Statistical procedure (frozen; applied unchanged)

Episode metrics computed through the frozen Sprint-24 `UnifiedEvaluator` instantiated on the nowcast rise-phase label array; 95% confidence intervals from the moving-block bootstrap with block length 2,880 windows (2 days = 8× the 360-minute window span; the stride-1 windows overlap 359 of 360 minutes, so IID resampling remains invalid), 1,000 confusion replicates, RNG seed 20260704. The false-episodes-per-month interval bootstraps per-block false-episode counts on the harness's own pre-registered resample indices; its point-consistency with the harness's authoritative count was verified exactly (304/237/134 for seeds 42/43/44 at Component 2). Episode-recall intervals use the harness's episode-block bootstrap.

## Per-seed intervals (OBSERVED, sealed)

| Seed | FE/month [95% CI] | Episode recall [95% CI] |
|------|--------------------|--------------------------|
| 42 | 50.92 [43.21, 59.13] | 0.9279 [0.856, 0.983] |
| 43 | 39.69 [32.82, 47.06] | 0.9189 [0.829, 0.983] |
| 44 | 22.44 [18.09, 27.13] | 0.9009 [0.820, 0.968] |
| 45 | 27.64 [22.11, 33.33] | 0.9099 [0.823, 0.975] |
| 46 | 39.02 [31.99, 46.40] | 0.9099 [0.823, 0.975] |

`DERIVED`: no seed's interval approaches the 5.0 budget — the gap between the best seed's lower bound (18.09) and the budget is 3.6×, so the REJECTED verdict is robust to both within-run bootstrap uncertainty and across-seed variance, and the two uncertainty sources are reported separately per the project's standing rule (never pooled).

## Seed variance and the escalation record

The pre-registered escalation clause fired mechanically after seeds 42–44 (observed false-episodes-per-month range 28.47 > the 1.0 trigger; decision taken by the frozen rule in `analysis.json`, values sealed at the time), seeds 45 and 46 were trained and sealed-evaluated under the identical protocol, and the five-seed rule (majority 3 of 5) was then applied: 0 of 5 pass → REJECTED; the escalation flag correctly extinguishes at five seeds. The escalation seeds landed inside the original envelope (27.64 and 39.02 vs the 22.44–50.92 range), so the verdict was, as anticipated, mathematically locked — the escalation's contribution is the improved characterization of the anomalously large false-episode variance: FE/month std 11.17 (31% of the mean) against an episode-recall std of just 0.0103 (1.1% of the mean). `DERIVED`: recall is a stable property of the detector while false-episode production is strongly seed-dependent at matched recall — the single most actionable statistical fact for any future policy design (for example cross-seed ensembling), and an input to the registered follow-up Experiment A.

## Sensitivity to the label definition (pre-registered secondary analyses)

Full table in `Sensitivity_Labels.md`; statistically, the whole-event label reproduces the failure at nearly identical values (false episodes per month 22.44–50.92, recall 0.897–0.925 — alerts overlapping rise phases almost always overlap the containing whole event), while the onset-only label degrades recall drastically (0.377–0.518) at even higher false-episode rates, confirming the rise-phase label was the most favorable of the three pre-registered formulations. No label choice changes the verdict.
