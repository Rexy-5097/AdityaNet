<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Sprint 26B updated ranking with E2 inserted. -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-05 -->

# Sprint 26B — Updated Configuration Ranking (with E2)

> Exploratory result only. Sprint 26B confirmation required before scientific conclusions.

**Conclusion:** With E2 now measured, all seven configurations are ranked. E2 lands in **last place (Rank 7)** on the primary endpoint with a test policy True Skill Score of 0.3770, below every other configuration including the retrained Baseline (0.3940). The Sprint 26A exploratory finding — that no single-variable ablation improves on Baseline — is unchanged and now complete.

## Complete ranking (primary endpoint: test policy True Skill Score, persistence-relative)

| Rank | Configuration | Test True Skill Score | Delta from Baseline | ROC-AUC | PR-AUC | Expected Calibration Error | Pre-onset Recall | Duty Cycle |
|------|---------------|----------------------:|--------------------:|--------:|-------:|---------------------------:|-----------------:|-----------:|
| 1 | Baseline | 0.3940 | 0.0000 | 0.7521 | 0.4680 | 0.0685 | 0.6192 | 0.4210 |
| 2 | E3 (patience 8) | 0.3940 | +0.0000 | 0.7521 | 0.4680 | 0.0685 | 0.6192 | 0.4210 |
| 3 | E6 (Platt calibration) | 0.3934 | −0.0006 | 0.7559 | 0.4907 | 0.0900 | 0.6479 | 0.4449 |
| 4 | E1 (regime-inclusive data) | 0.3840 | −0.0100 | 0.7514 | 0.4792 | 0.0827 | 0.6055 | 0.4142 |
| 5 | E4 (T_max = 10) | 0.3798 | −0.0142 | 0.7504 | 0.4780 | 0.0734 | 0.6466 | 0.4307 |
| 6 | E5 (alpha 0.50, interrupted) | 0.3793 | −0.0147 | 0.7506 | 0.4674 | 0.0804 | 0.6466 | 0.4254 |
| 7 | **E2 (uncapped steps)** | **0.3770** | **−0.0170** | 0.7493 | 0.4791 | 0.0643 | 0.7000 | 0.4514 |

E2 metrics are `OBSERVED` this session (`artifacts/sprint26b/runs/E2/eval.json`); the other six rows are carried unchanged from `artifacts/sprint26a/02_CONFIGURATION_RANKING.md`.

## The four questions

1. **How does E2 compare against Baseline on the primary metric?** E2's test policy True Skill Score of 0.3770 is lower than Baseline's 0.3940 by 0.0170 (its advantage over persistence, +0.0752, is likewise below Baseline's +0.0923), so E2 is worse than Baseline on the primary endpoint (`OBSERVED`).
2. **Where does E2 rank among all seven configurations?** E2 ranks seventh, last, on the primary endpoint (`OBSERVED`).
3. **Does E2 become Rank 1?** No — E2 is Rank 7, not Rank 1 (`OBSERVED`).
4. **Does the Sprint 26A exploratory conclusion change?** No — the conclusion that no single-variable ablation improves on Baseline stands and is now complete, because the one previously unscreened lever, E2, also failed to beat Baseline (`OBSERVED`).

## One nuance worth recording

E2 was not uniformly worse: it produced the highest Pre-onset Episode Recall (0.7000 versus Baseline 0.6192) and the highest Episode Recall (0.7562) of all seven configurations, and a marginally better Expected Calibration Error (0.0643) and Brier score (0.1541). But it reached that higher recall by alerting more (Yellow Duty Cycle 0.4514, the highest of any configuration), which raised its false-positive rate and pulled its True Skill Score — the primary endpoint — below Baseline. This is an exploratory, single-seed observation and is not a basis for any scientific conclusion.

> Exploratory result only. Sprint 26B confirmation required before scientific conclusions.
