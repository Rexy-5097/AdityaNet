<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Sprint 32 Phase 4 — pre-registered statistical analysis, four paired comparisons on the S2 span. -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-12 -->

# Sprint 32 — Statistical Analysis (F3, EraMatchedGOES vs F2 and F0, S2 span)

**The era-matched control resolves the Sprint 31 ambiguity decisively and against the ISRO hypothesis. When the training era is held fixed at Stage-2, the GOES-only model (EraMatchedGOES, True Skill Score 0.4383 ± 0.0055) is the single best arm — better than GOES+Aditya (F2, 0.4022 ± 0.0151), better than late fusion (F3, 0.3952 ± 0.0142), and better than the deployed original-era baseline (F0, 0.4068). Adding the Aditya-L1 channels to era-matched GOES changes True Skill Score by −0.0388 on average (negative in 3 of 3 seeds, at all three block sizes, Cohen's d −10.7), and switching to the late-fusion architecture changes it by a further −0.0070 vs F2 (negative-leaning, 0 of 5 seeds significant). The one thing that helps is the training era itself: EraMatchedGOES exceeds F0 by +0.0315 (positive in 3 of 3 seeds, Cohen's d +5.8). No comparison reaches per-seed 95% significance on this short span, but the pre-registered success test for Aditya value fails 0 of 3 and the point estimate is that Aditya-L1 removes skill.** All rules were locked in commit `28b25b4` before any F3/EMG result existed. Machine-readable: `artifacts/sprint32/analysis.json`.

Plan applied: `artifacts/sprint25/07_preregistered_analysis_plan.md` + Sprint 31 methodology. (The brief's cited `sprint28/07_preregistered_analysis_plan.md` does not exist; the Sprint 25 plan is the plan of record, as in Sprints 30–31.)

## Arm True Skill Scores (OBSERVED, policy operating point, S2 test span 261,095 windows)

| Arm | Description | Seeds | TSS mean ± std | Per-seed TSS |
|-----|-------------|-------|----------------|--------------|
| **EraMatchedGOES** | GOES-17, Stage-2 era, single encoder | 42,43,44 | **0.4383 ± 0.0055** | 0.4328 / 0.4438 / 0.4384 |
| F0 | GOES-14, original era, frozen V1 | — (ref) | 0.4068 | (single) |
| F2 | GOES-17 + 15 Aditya + 4 masks, Stage-2, single encoder | 42–46 | 0.4022 ± 0.0151 | 0.3935 / 0.4088 / 0.3962 / 0.3873 / 0.4254 |
| F3 | same 36 channels, late-fusion (two encoders) | 42–46 | 0.3952 ± 0.0142 | 0.4038 / 0.3786 / 0.3928 / 0.4145 / 0.3863 |

S2 floors (recomputed through the frozen class): persistence TSS 0.3368, climatology TSS 0.0. Every arm clears persistence.

## The four pre-registered paired comparisons (OBSERVED, 2880-window blocks, same resample indices)

### 1. F3 vs F2 — does late fusion improve single-encoder fusion?
Per-seed ΔTSS (F3−F2): +0.0104 / −0.0302 / −0.0034 / +0.0272 / −0.0391; p_boot 0.71 / 0.27 / 0.92 / 0.40 / 0.20; **0 of 5 significant**; mean −0.0070, Cohen's d −0.25. **Late fusion does not improve on single-encoder fusion** — the pre-registered improvement criterion (≥ +0.02, lower bound > 0, majority) is met 0 of 5. Path D is NOT triggered.

### 2. F3 vs F0 — does late fusion beat the original GOES baseline?
Per-seed ΔTSS (F3−F0): −0.0030 / −0.0282 / −0.0140 / +0.0077 / −0.0206; **0 of 5 significant**; mean −0.0116, Cohen's d −0.82. **Late fusion does not beat the deployed GOES-only baseline** (leans below it).

### 3. F2 vs EraMatchedGOES — the ADITYA EFFECT, era controlled (PRIMARY ISRO ENDPOINT)
Per-seed ΔTSS (F2−EMG): −0.0394 / −0.0349 / −0.0421; 95% CIs [−0.0923,+0.0275] / [−0.0771,+0.0148] / [−0.0873,+0.0035]; p_boot 0.230 / 0.154 / 0.074; **0 of 3 significant, but negative in 3 of 3**; mean −0.0388, Cohen's d −10.7 (huge because between-seed variance is tiny). **Once the training era is held fixed, adding the Aditya-L1 channels does not add value — the point estimate is that it removes ≈0.039 True Skill Score.** The pre-registered "Aditya value SUPPORTED" criterion (dTSS ≥ +0.02 with lower bound > 0 in a majority) is met 0 of 3; the effect is the wrong sign and its magnitude exceeds the +0.02 minimum effect of interest. This is the decisive de-confounded measurement of the ISRO hypothesis.

### 4. EraMatchedGOES vs F0 — the ERA EFFECT
Per-seed ΔTSS (EMG−F0): +0.0260 / +0.0369 / +0.0315; p_boot 0.386 / 0.248 / 0.378; **0 of 3 per-seed significant, but positive in 3 of 3**; mean +0.0315, Cohen's d +5.8. **Training GOES-only on the recent Stage-2 era is worth ≈+0.03 True Skill Score over the deployed 16-year-original-era model** — the only positive signal in the sprint. (Caveat, per protocol §5: this comparison also differs in 14 vs 17 GOES features, so it mixes era with a minor feature difference; the Aditya comparison #3 is the clean one.)

## Block-size sensitivity (OBSERVED — 2880 authoritative)

The Aditya-effect per-seed point estimates are **identical at block lengths 1440 / 2880 / 5760** (−0.0394 / −0.0349 / −0.0421 in every case), and the significance classification is unchanged (0 of 3 significant at every block size). Point estimates do not depend on resampling; only interval widths change. Nothing about any conclusion depends on the block choice. Full table in `analysis.json:block_sensitivity`.

## All-metric summary (OBSERVED, arm means, policy operating point)

| Metric | F0 | EraMatchedGOES | F2 | F3 |
|--------|-----|----------------|-----|-----|
| True Skill Score | 0.4068 | **0.4383** | 0.4022 | 0.3952 |
| ROC-AUC | 0.7368 | **0.7826** | 0.7685 | 0.7658 |
| PR-AUC | 0.3899 | **0.4670** | 0.4413 | 0.4403 |
| Expected Calibration Error | 0.0234 | 0.0271 | 0.0257 | 0.0266 |
| Episode recall | 0.5370 | 0.6667 | 0.8370 | 0.7996 |
| Pre-onset recall | 0.3704 | 0.6296 | 0.8111 | 0.7846 |
| False episodes / month | 3.68 | 21.05 | 37.18 | 32.83 |
| Yellow duty cycle | 0.2183 | 0.2306 | 0.3191 | 0.2624 |
| RED duty cycle | 0.0002 | 0.0000 | 0.0010 | 0.0047 |
| Median lead time (min) | 865 | 943 | 682 | 606 |

Operator Utility (V_max = TSS, Richardson 2000, pre-declared) tracks the TSS row exactly; EraMatchedGOES has the highest peak cost-loss value of any arm. Note that EraMatchedGOES also carries the best ROC-AUC and PR-AUC and captures much of the pre-onset-recall gain (0.630 vs F0's 0.370) at roughly HALF the false-alarm cost of F2 (21 vs 37 per month) — the pre-onset improvement Sprint 31 attributed to Aditya is substantially reproduced by era-matched GOES alone.

## Seed variance

F3 range 0.0359 (escalated to 5 seeds, as F2 did); EraMatchedGOES range 0.0109 (< 0.015, no escalation — the tightest arm yet). Full variance analysis in `Seed_Variance_Report.md`... (see `Experiment_Report.md` for the consolidated seed table).

## Interpretation discipline

No comparison reaches per-seed 95% significance — the S2 span yields ~90 bootstrap blocks and therefore wide single-run intervals (a span limitation, not a model property, carried since Sprint 31). The verdict does not rest on a significant *negative*; it rests on the pre-registered test for a significant *positive* Aditya effect failing 0 of 3 with a consistently negative point estimate. Direction, block-size invariance, and the enormous Cohen's d (tiny seed variance) make the sign reliable even where the per-run interval is wide. Secondary endpoints are reported for completeness and none is promoted to rescue the primary (plan §3 multiple-comparisons stance).
