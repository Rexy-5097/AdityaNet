<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Sprint 31 Phase 5 — pre-registered statistical analysis of F2 vs F1 and F2 vs F0 on the S2 span. -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-12 -->

# Sprint 31 — Statistical Analysis (F2 vs F1 and F2 vs F0, Stage-2 test span)

**Two results, both pre-registered, pointing in different directions. (1) The primary endpoint PASSES: paired ΔTrue Skill Score of F2 over F1-on-S2 is ≥ +0.02 in 5 of 5 seeds (mean +0.0844 ± 0.0352, Cohen's d 2.40) with a positive lower 95% bound in 3 of 5 seeds (bootstrap p 0.018 / 0.008 / 0.004) — the pre-registered "Aditya value CONFIRMED" criterion is met. (2) The same pre-committed analysis shows F2 does NOT exceed the GOES-only frozen baseline F0 on the identical span: per-seed paired ΔTSS −0.0195 to +0.0185, significant in 0 of 5 seeds (bootstrap p 0.56–0.91, mean −0.0046) — and the F1 comparator collapsed on this span (significantly below F0 in 4 of 5 seeds, several seeds at or below the persistence floor). Both facts go to the verdict; neither erases the other.** All rules were locked in commit `30d4f23` before any result existed. Machine-readable record: `artifacts/sprint31/analysis.json`.

Plan applied: `artifacts/sprint25/07_preregistered_analysis_plan.md` + `artifacts/sprint28/04_FAIR_ADITYA_EXPERIMENT.md` statistics section. (The brief's cited path `artifacts/sprint28/07_preregistered_analysis_plan.md` does not exist; the Sprint 25 plan is the plan of record, as in Sprint 30.)

## Primary endpoint (OBSERVED — paired moving-block bootstrap, policy operating point, same-span S2)

Per-seed paired ΔTSS, F2 seed minus F1 same-seed-on-S2, identical resample indices:

| Seed | ΔTSS (F2−F1) | 95% CI | p_boot | ≥ +0.02 | Lower > 0 | Pre-onset degraded | Seed passes |
|------|--------------|--------|--------|---------|-----------|---------------------|-------------|
| 42 | +0.0551 | [−0.0181, +0.1257] | 0.180 | yes | no | no | no |
| 43 | +0.0914 | [+0.0134, +0.1653] | 0.018 | yes | yes | no | **yes** |
| 44 | +0.1083 | [+0.0291, +0.1856] | 0.008 | yes | yes | no | **yes** |
| 45 | +0.0419 | [−0.0423, +0.1229] | 0.296 | yes | no | no | no |
| 46 | +0.1251 | [+0.0363, +0.2101] | 0.004 | yes | yes | no | **yes** |

Criterion (pre-registered; 5-seed majority form after automatic escalation): ΔTSS ≥ +0.02 with lower 95% bound > 0 in ≥ 3 of 5 seeds, pre-onset recall not significantly degraded → **3 of 5 pass → PRIMARY ENDPOINT MET** (DERIVED, mechanical). Effect size: one-sample Cohen's d = +0.0844/0.0352 = **+2.40**. Seeds 42 and 45 are borderline — positive point estimates above the minimum effect but intervals spanning zero — and are reported as borderline, per instruction.

## The pre-registered context comparisons (OBSERVED)

**F2 vs F0 (GOES-14 frozen baseline, same span, paired):** ΔTSS per seed −0.0134 / +0.0020 / −0.0106 / −0.0195 / +0.0185; p_boot 0.788 / 0.908 / 0.818 / 0.690 / 0.564; **0 of 5 significant**; mean −0.0046; Cohen's d −0.30. F2's window-level skill is statistically indistinguishable from the 16-year GOES-only model. Its pre-onset episode recall, however, exceeds F0's in **5 of 5 seeds, all significant** (+0.3889 to +0.4630).

**F1 vs F0 on S2 (the comparator's health check):** ΔTSS −0.0684 / −0.0894 / −0.1189 / −0.0614 / −0.1066, significant in 4 of 5. F1-on-S2 TSS 0.2879–0.3455 sits at or below the recomputed S2 persistence floor (0.3368); F0 = 0.4068 clears it. **Interpretation constraint (DERIVED):** the F2−F1 gap of +0.084 decomposes as F2−F0 (−0.005) plus F0−F1 (+0.089): nearly all of the primary-endpoint margin comes from the comparator's collapse under span transfer, not from F2 exceeding GOES-only skill. The pre-registered design ties training era to arm (F1 trains on 2010–2019, F2 on 2023–2025), so Aditya features and training-regime match are confounded in the primary comparison — a design property flagged in `Scientific_Conclusion.md` Q1/Q5 with the control arm that would resolve it.

## Per-seed / per-arm metric table (OBSERVED, policy operating point, S2 span)

| Arm | TSS | ROC-AUC | PR-AUC | ECE | Ep. recall | Pre-onset | FE/mo | Yellow duty | Red duty | Utility V_max |
|-----|-----|---------|--------|-----|-----------|-----------|-------|-------------|----------|----------------|
| F0_s2 | 0.4068 | 0.7368 | 0.3899 | 0.0234 | 0.5370 | 0.3704 | 3.68 | 0.2183 | 0.0002 | 0.4068 |
| F1 (5-seed mean) | 0.3179 | 0.7269 | 0.4038 | 0.0354 | 0.5926 | 0.4852 | 19.33 | 0.2346 | 0.0000 | 0.3179 |
| F2_s42 | 0.3935 | 0.7617 | 0.4273 | 0.0237 | 0.8704 | 0.8333 | 39.86 | 0.3447 | 0.0023 | 0.3935 |
| F2_s43 | 0.4088 | 0.7692 | 0.4522 | 0.0311 | 0.8333 | 0.7963 | 36.35 | 0.3095 | 0.0013 | 0.4088 |
| F2_s44 | 0.3962 | 0.7758 | 0.4513 | 0.0244 | 0.8519 | 0.8333 | 38.52 | 0.3045 | 0.0000 | 0.3962 |
| F2_s45 | 0.3873 | 0.7653 | 0.4324 | 0.0288 | 0.8519 | 0.8333 | 35.17 | 0.3475 | 0.0000 | 0.3873 |
| F2_s46 | 0.4254 | 0.7703 | 0.4432 | 0.0204 | 0.7778 | 0.7593 | 36.01 | 0.2892 | 0.0015 | 0.4254 |
| **F2 mean ± std** | **0.4022 ± 0.0151** | 0.7685 | 0.4413 | 0.0257 | 0.8370 | 0.8111 | 37.18 | 0.3191 | 0.0010 | 0.4022 |

Operator Utility is the pre-declared parameter-free definition (Richardson 2000 maximum cost-loss relative value, V_max = TSS; locked in commit `30d4f23` before results because no other utility definition exists in the repository). Median lead time: F0 865 min; F2 569–737 min. Floors on S2 (recomputed through the identical frozen class, pre-registered): persistence TSS 0.3368, climatology TSS 0.0.

## Secondary endpoints (F2 − F1 means; individual arm CIs in the sealed eval.json records; none promoted)

ΔROC-AUC +0.0416; ΔPR-AUC +0.0375; ΔECE −0.0098 (F2 better calibrated); Δepisode recall +0.2444 (significant 4/5 paired); Δpre-onset recall +0.3259 (significant 4/5); Δfalse episodes/month +17.85 (worse); Δyellow duty +0.0845; Δred duty +0.0010. Against F0: F2's ROC-AUC is higher in all seeds (0.762–0.776 vs 0.737, point estimates) — a ranking-skill hint that does not survive to the thresholded primary metric and remains secondary.

## Block size and robustness (OBSERVED)

Authoritative block: 2,880 windows (2 days = 8 × the 360-min label horizon; IID tests and McNemar invalid under 359/360-minute window overlap — `artifacts/sprint24/06_statistical_tests.md`). The S2 span yields 261,095 windows ≈ 90 blocks; 1,000 confusion replicates, seed 20260704. Sensitivity: per-seed ΔTSS point estimates and ALL significance classifications are identical at block lengths 1,440 / 2,880 / 5,760 (runtime constant override; frozen file untouched — Sprint 24 precedent). Nothing depends on the block choice.

## Availability stratification (pre-registered; OBSERVED as degenerate)

Per-window SoLEXS quality on the S2 test span: p01 = 0.697, median 0.752, p99 = 0.805 — no window reaches the 0.9 stratum boundary and no window falls below 0.5 availability. Stratum populations: quality ≥ 0.9: **0**; quality < 0.9: 261,095; Aditya present (≥ 0.5): 261,095; absent: **0**. As pre-declared in `Missing_Data_Report.md`, the availability-dependence question is unanswerable on this span because availability has no variance — reported as the measured fact, not silently dropped.

## Seed variance summary

F2 TSS range 0.0380 (escalation correctly triggered at the 3-seed stage: range 0.0153 > 0.015 — the narrowest trigger margin yet); full analysis in `Seed_Variance_Report.md`.
