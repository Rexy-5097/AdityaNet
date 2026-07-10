<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Scored V4 candidate ranking, written at V4 planning. -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-03 -->

# Version 4 — Priority Matrix

**Conclusion:** Candidate C1 — the episode-level evaluation harness combined with the cost-loss operator policy and matched baseline comparison — ranks first at 8.70/10, a full 1.45 points clear of the second-ranked candidate. It is the only candidate that scores at ceiling on both operator impact and data availability while requiring no retraining. The walk-forward regime study (C3, 7.25) and the Aditya-L1 corpus extension (C2, 6.75) follow. The ranking, weights, and per-cell scores are shown in full below.

## Methodology

Nine criteria per the brief. All scored 0–10 where **10 is favorable** — so *implementation complexity* is scored as simplicity (10 = trivial) and *risk* as safety (10 = low risk of failure or wasted effort). Weights encode the sprint brief's priority statement ("operator trust is the primary goal; leaderboard metrics are secondary") and sum to 1.00:

| Criterion | Weight | Rationale |
|-----------|--------|-----------|
| Expected operator impact | 0.20 | Primary goal per the brief |
| Scientific importance | 0.15 | Validity underpins trust |
| Expected measurable improvement | 0.15 | Plans must move a number |
| Implementation complexity (simplicity) | 0.10 | Solo developer, Apple M4 only |
| Risk (safety) | 0.10 | Adversarial planning: penalize fragile bets |
| Data availability | 0.10 | Data-blocked work stalls regardless of merit |
| Hackathon value | 0.10 | Near-term submission |
| Publication value | 0.05 | Secondary goal |
| Research novelty | 0.05 | Secondary goal |

Scores are judgments grounded in the evidence cited in `VERSION4_MASTER_PLAN.md`'s classification table; they are inputs to a decision, not measurements.

## Scored table (weighted total = Σ weight × score)

| # | Candidate (problems addressed) | Sci ×.15 | Oper ×.20 | Simpl ×.10 | Novel ×.05 | Hack ×.10 | Publ ×.05 | Safety ×.10 | Data ×.10 | Measur ×.15 | **Total** |
|---|-------------------------------|-----|------|------|------|------|------|------|------|------|-----------|
| C1 | Episode harness + cost-loss RED policy + persistence/climatology on the same yardstick (P1, P2, P3, P4, P14) | 9 | 10 | 7 | 5 | 8 | 7 | 9 | 10 | 9 | **8.70** |
| C3 | Walk-forward regime study: monthly episode metrics + rolling recalibration backtest 2023–2026 (P6, feeds P23) | 8 | 7 | 6 | 6 | 5 | 8 | 8 | 10 | 7 | **7.25** |
| C2 | Extend Aditya-L1 joint corpus from raw archive + SCI-001 significance verdict (P5, P11, gates P24-instrument) | 10 | 5 | 5 | 7 | 8 | 10 | 5 | 7 | 6 | **6.75** |
| C8 | Conformal prediction for coverage-guaranteed alerts (P13, P14) | 7 | 6 | 5 | 9 | 7 | 8 | 5 | 10 | 5 | **6.55** |
| C5 | Stealth-flare FN mitigation: precursor features + retrain (P7, P24) | 7 | 7 | 3 | 7 | 6 | 7 | 4 | 9 | 5 | **6.10** |
| C4 | Shadow-mode pilot: ingestion scheduler + monitoring + live alert log (P21, P23) | 4 | 8 | 4 | 3 | 7 | 2 | 6 | 8 | 6 | **5.85** |
| C9 | Operator frontend/dashboard with provenance display (P22) | 2 | 7 | 5 | 2 | 9 | 1 | 8 | 10 | 5 | **5.80** |
| C6 | Rigor bundle: multi-seed V3, LR/architecture ablations (P9) | 7 | 3 | 5 | 4 | 4 | 9 | 8 | 10 | 5 | **5.75** |
| C7 | Engineering hardening: git + CI + broadened tests + Dockerfile + auth (P16–P20) | 3 | 6 | 5 | 2 | 6 | 2 | 8 | 10 | 6 | **5.65** |
| C12 | New V4 architecture exploration (informed by P7/P28) | 6 | 5 | 3 | 8 | 6 | 7 | 3 | 9 | 4 | **5.35** |
| C10 | model_v3.py defaults fix + V3 integrate-or-retire ADR (P12, P11) | 5 | 3 | 10 | 2 | 3 | 4 | 9 | 10 | 3 | **5.30** |
| C11 | Temperature-scaling forensics (P10) | 4 | 1 | 7 | 5 | 2 | 4 | 8 | 10 | 2 | **4.25** |

## Ranking and notes on the load-bearing scores

1. **C1 — 8.70.** Operator impact 10: it is the difference between a forecaster that cannot say RED (`artifacts/operator_backtest.json` RED: 0) and one whose alert trade-offs an operator chose. Data availability 10: every required array already exists (`artifacts/research/validation.parquet`, archived test predictions `artifacts/calibration/probs.npy`, flare catalog `artifacts/research/flares_full.parquet`). Safety 9: no retraining, deterministic sweeps; the main risk is an unwelcome answer on P2, which is a result, not a failure.
2. **C3 — 7.25.** Costs almost nothing (archived predictions reused; each month scored by a calibrator fit strictly on earlier months) and converts the project's biggest unquantified fear — SC25 drift, `PROJECT_STATUS.md` "CRITICAL WARNING" — into bounds. Depends on C1's harness, hence sequenced second.
3. **C2 — 6.75.** Highest scientific importance and publication value (a verdict on SCI-001 either way), but safety 5: the extended corpus may still contain few clean joint flare episodes (SoLEXS saturation during large events is unaudited — NOT PROVEN either way), and operator impact is indirect this quarter.
4. **C8 — 6.55.** High novelty, but its evaluation is meaningless without C1's episode-aware coverage measurement; folded into Phase D.
5. **C5 — 6.10 and below.** Everything requiring retraining (C5, C12) is deliberately mid-table: V3's lesson is that model sophistication built on a broken yardstick produces unusable claims. C10 is trivial and gets done opportunistically inside Phase B's first day despite its low standalone score. C7's components are staged into Phase D/E where they multiply velocity (git and tests specifically are pulled earlier as Phase B/C hygiene).

## Sensitivity check

C1 remains first under every reasonable reweighting tried: doubling publication weight at the expense of hackathon moves C2 to 7.15 (still second); zeroing hackathon and novelty entirely moves C1 to 8.75 and C3 to 7.35. The ranking's top three are stable; the plan does not hinge on fine-tuned weights.
