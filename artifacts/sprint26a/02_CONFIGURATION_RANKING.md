<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Sprint 26A configuration ranking (exploratory, single seed). -->
<!-- SUPERSEDED BY: Sprint 26B confirmation campaign (not yet run) -->
<!-- DATE: 2026-07-04 -->

# Sprint 26A — Configuration Ranking (Exploratory)

> Exploratory result only. Requires confirmation in Sprint 26B.

**Conclusion:** Ranked by the primary endpoint of `artifacts/sprint25/04_success_criteria.md` — the test True Skill Score advantage over causal persistence (persistence fixed at approximately 0.3018, so ranking by test policy True Skill Score is equivalent) — the retrained Baseline (0.3940) and E3 (0.3940, an identical checkpoint) tie at the top, E6 (0.3934) is essentially level, and E1, E4, and E5 fall below Baseline. E2 is unranked because it was not completed (`NOT PROVEN`). No completed ablation exceeded Baseline on the primary endpoint. This is a single-seed screening; all statements are practical, not inferential.

## Ranking table (primary endpoint: test True Skill Score, persistence-relative)

| Rank | Configuration | Test True Skill Score | Delta from Baseline | ROC-AUC | PR-AUC | Expected Calibration Error | Pre-onset Recall | False Episodes/Month | Warrants confirmation? |
|------|---------------|----------------------:|--------------------:|--------:|-------:|---------------------------:|-----------------:|---------------------:|------------------------|
| 1 | Baseline | 0.3940 | 0.0000 | 0.7521 | 0.4680 | 0.0685 | 0.6192 | 3.163 | Yes — reference configuration |
| 2 | E3 (patience 8) | 0.3940 | +0.0000 | 0.7521 | 0.4680 | 0.0685 | 0.6192 | 3.163 | No — identical checkpoint to Baseline; nothing new to confirm |
| 3 | E6 (Platt calibration) | 0.3934 | −0.0006 | 0.7559 | 0.4907 | 0.0900 | 0.6479 | 2.873 | Yes — level on True Skill Score, higher ROC-AUC/PR-AUC, lower false-episode rate; calibration trade-off worth confirming |
| 4 | E1 (regime-inclusive data) | 0.3840 | −0.0100 | 0.7514 | 0.4792 | 0.0827 | 0.6055 | 3.380 | Weak — below Baseline; did not remove the transfer gap it targeted |
| 5 | E4 (T_max = 10) | 0.3798 | −0.0142 | 0.7504 | 0.4780 | 0.0734 | 0.6466 | 3.042 | No — below Baseline on the primary endpoint |
| 6 | E5 (alpha 0.50) | 0.3793 | −0.0147 | 0.7506 | 0.4674 | 0.0804 | 0.6466 | 3.525 | No — below Baseline; also from interrupted training (partial) |
| — | E2 (uncapped steps) | `NOT PROVEN` | `NOT PROVEN` | — | — | — | — | — | Undetermined — not screened |

## Task 1 — Top 2 configurations (highest primary metric, at or meaningfully close to Baseline)

**Baseline (0.3940) and E6 (0.3934).** These are the two distinct configurations at the top of the primary endpoint. E3, although numerically tied with Baseline, is not a distinct configuration — patience 8 selected the identical epoch-8 checkpoint, so it carries no independent information and is excluded in favour of E6, which is a genuinely different configuration (Platt versus isotonic calibration on the same model) that matches Baseline on True Skill Score while showing a higher ROC-AUC (0.7559 versus 0.7521), a higher PR-AUC (0.4907 versus 0.4680), and a lower false-episode rate (2.873 versus 3.163 per month), at the cost of worse calibration (Expected Calibration Error 0.0900 versus 0.0685).

## Task 2 — Configurations not worth confirming (practical reasoning, single sentence each)

- **E4 (T_max = 10), test True Skill Score 0.3798:** it sits about 0.014 below Baseline on the primary endpoint while offering no primary-metric advantage, so on practical grounds it is not a promising direction to spend five-seed confirmation compute on.
- **E5 (alpha 0.50), test True Skill Score 0.3793:** it is the lowest completed configuration on the primary endpoint and its training was interrupted, so it is doubly unsuitable for confirmation without first re-running it to natural completion.
- **E1 (regime-inclusive data), test True Skill Score 0.3840:** it is below Baseline and, notably, did not reduce the operating-point transfer gap it was designed to address, so on practical grounds it does not currently warrant confirmation — though this is the one negative result most worth revisiting conceptually, because a single seed on one particular chronological split cut is thin evidence against a mechanism the root-cause analysis rated SUPPORTED.
- **E3 (patience 8):** not worth confirming because it is byte-equivalent to Baseline in checkpoint selection and would duplicate the Baseline confirmation.

> Exploratory result only. Requires confirmation in Sprint 26B.
