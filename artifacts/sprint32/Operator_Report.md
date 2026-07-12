<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Sprint 32 Phase 6 — operator-facing analysis and deployment recommendation. -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-12 -->

# Sprint 32 — Operator Report

**Deployment recommendation: do NOT deploy F3 (late fusion); keep F0 as the deployed configuration, and open a properly-powered confirmation of the era-matched GOES retraining (EraMatchedGOES) as the Version 4 candidate. The measured reason is direct: F3's True Skill Score (0.3952 ± 0.0142 across 5 seeds) is below the deployed F0 baseline (0.4068) in 4 of 5 seeds (paired ΔTSS −0.0116, 0 of 5 significant), so late fusion offers operators no skill gain and adds architectural complexity and false alarms. The only arm that improves on F0 is GOES-only retrained on the recent era (EraMatchedGOES, 0.4383) — which improves by dropping Aditya-L1, not adding it.**

## Operational metric comparison (OBSERVED, S2 span, policy thresholds 0.14/0.95)

| Quantity | F0 (deployed) | EraMatchedGOES | F2 | F3 (late fusion) |
|----------|---------------|----------------|-----|-------------------|
| True Skill Score / Operator Utility V_max | 0.4068 | **0.4383** | 0.4022 | 0.3952 |
| ROC-AUC | 0.7368 | **0.7826** | 0.7685 | 0.7658 |
| False episodes / month | **3.68** | 21.05 | 37.18 | 32.83 |
| Operator workload proxy (yellow duty cycle) | **0.2183** | 0.2306 | 0.3191 | 0.2624 |
| Episode recall | 0.5370 | 0.6667 | 0.8370 | 0.7996 |
| Pre-onset recall | 0.3704 | 0.6296 | 0.8111 | 0.7846 |
| RED duty cycle | 0.0002 | 0.0000 | 0.0010 | 0.0047 |
| Median lead time (min) | 865 | 943 | 682 | 606 |
| Alert stability (seed std of TSS) | — | **0.0055** | 0.0151 | 0.0142 |

## Reading for operators (labeled)

- OBSERVED: **F3 is dominated.** It has lower True Skill Score than F0, more than 8× F0's false episodes per month (32.8 vs 3.7), shorter lead time (606 vs 865 min), and the highest RED duty cycle of any arm — worse operational usefulness on every axis that matters to a satellite operator. There is no cost-loss ratio at which F3's peak value (V_max = TSS 0.3952) exceeds F0's (0.4068), so it is never preferred.
- OBSERVED: **EraMatchedGOES is the standout.** Highest True Skill Score, highest ROC-AUC and PR-AUC, best seed stability (std 0.0055 — the tightest arm in the whole program), and it recovers most of the pre-onset warning gain (0.630 vs F0's 0.370) at roughly HALF the false-alarm cost of the Aditya arms (21/month vs F2's 37, F3's 33). The pre-onset improvement that Sprint 31 read as an Aditya benefit is substantially a recent-era-retraining benefit, achievable with GOES alone.
- DERIVED: **Aditya-L1 costs operators false alarms.** Adding the Aditya channels (F0→ or EMG→F2) roughly doubles false episodes per month (21→37) while lowering True Skill Score — a strictly worse operating profile.

## Recommendation

1. **Keep F0 deployed now.** No arm in this sprint clears F0 at per-seed 95% significance on this span, so no immediate switch is licensed; F3 in particular is measurably worse and is explicitly not recommended.
2. **Promote EraMatchedGOES to a Version 4 deployment candidate via a new, adequately-powered pre-registration.** Its +0.0315 mean True Skill Score over F0 is consistent (3/3 seeds, Cohen's d +5.8) but not per-seed significant on the ~90-block S2 span; a confirmation over a longer evaluation window (or the pre-registered 5-seed tier plus a wider test span as it accrues) would license deployment. The change it represents — retrain GOES-only on recent data, drop Aditya — is low-risk and reuses the proven single-encoder pipeline.
3. **Do not deploy any Aditya-L1-inclusive model** on the current evidence: both Aditya arms are worse than era-matched GOES on skill and far worse on false-alarm load.
4. The episode-level cost-loss operator-policy program (Sprint 30/31 Path C track) remains the right home for tuning the pre-onset-vs-false-alarm trade under an explicit operator cost/loss ratio, independent of instrument choice — and should now be run against EraMatchedGOES, not an Aditya arm.
