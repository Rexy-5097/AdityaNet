<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Sprint 32 Phase 5 — six scientific questions answered from Phase 4 measurements. -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-12 -->

# Sprint 32 — Scientific Conclusion (Phase 5)

Each answer states evidence first (from `artifacts/sprint32/analysis.json` / `Statistical_Analysis.md`), then the labelled answer.

**Q1. Does late fusion outperform single-encoder fusion?**
Evidence: paired ΔTSS(F3−F2) = −0.0070 mean across 5 seeds, 0 of 5 seeds significant, 0 of 5 meeting the +0.02 improvement criterion (per-seed +0.0104/−0.0302/−0.0034/+0.0272/−0.0391); F3 arm mean 0.3952 < F2 0.4022.
**Answer: NOT SUPPORTED.** Keeping the two instruments in separate encoders until after pooling does not improve on F2's single-encoder concatenation; the point estimate is slightly worse.

**Q2. Does Aditya-L1 provide statistically significant incremental information once training-era effects are removed by the era-matched control?**
Evidence: the clean, era-controlled comparison ΔTSS(F2−EraMatchedGOES) = −0.0388 mean, negative in 3 of 3 seeds and at all three block sizes (Cohen's d −10.7), 0 of 3 seeds meeting the pre-registered "≥ +0.02, lower bound > 0" success criterion; EraMatchedGOES (0.4383) exceeds F2 (0.4022) on TSS, ROC-AUC, and PR-AUC.
**Answer: NOT SUPPORTED.** With era held fixed and only the Aditya-L1 channels differing, adding those channels does not add information — the central estimate is that it removes ≈0.039 True Skill Score. (Not *significantly* negative per-seed — the S2 span gives wide intervals — but the test for a significant positive effect fails decisively and the sign is stable.)

**Q3. Does GOES remain sufficient when era effects are properly controlled?**
Evidence: EraMatchedGOES (GOES-only, Stage-2 era) is the best arm on TSS (0.4383), ROC-AUC (0.7826), and PR-AUC (0.4670), beating every arm that includes Aditya-L1 (F2, F3) and the deployed baseline (F0); it also captures pre-onset recall 0.6296 (vs F0's 0.3704) at roughly half F2's false-alarm cost.
**Answer: SUPPORTED BY EVIDENCE.** GOES alone, retrained on the recent era, is not merely sufficient — it is superior to every Aditya-inclusive configuration tested.

**Q4. Is Aditya-L1 scientifically useful for operational solar flare forecasting?**
Evidence: across the fair, physics-engineered, era-controlled test, no Aditya-inclusive arm (F2 single-encoder, F3 late-fusion) beats era-matched GOES-only or the deployed GOES baseline on window True Skill Score; the de-confounded Aditya effect is negative (Q2); Sprint 31's Phase 2 found no SoLEXS flare response at GOES peaks and Sprint 27 measured conditional mutual information 0.0.
**Answer: NOT SUPPORTED** for window-level forecasting skill. (One narrow operational nuance survives — pre-onset episode recall is higher in Aditya arms — but it is not unique to Aditya: era-matched GOES reproduces most of it at half the false-alarm cost, so it is not evidence of Aditya usefulness.)

**Q5. Should Version 4 adopt late fusion as its architecture?**
Evidence: F3 (late fusion) is the worst arm measured (TSS 0.3952), below F2, below era-matched GOES, and below F0 (ΔTSS(F3−F0) = −0.0116, 0/5 significant); the decision tree's Path D condition (F3 > F2) is not met.
**Answer: NOT SUPPORTED.** Version 4 should not adopt late fusion; the measured best configuration is a single-encoder GOES-only model retrained on the recent era.

**Q6. Is the original ISRO hypothesis — that multi-instrument Aditya-L1 data improves operational flare forecasting — SUPPORTED, PARTIALLY SUPPORTED, or NOT SUPPORTED?**
Evidence: the decisive era-controlled comparison (Q2) shows the Aditya-L1 channels do not add measurable window-level value and the point estimate is negative (ΔTSS(F2−EraMatchedGOES) = −0.0388, 0/3 passing); neither the single-encoder (F2) nor the late-fusion (F3) Aditya configuration beats era-matched GOES-only or the deployed baseline; the apparent Sprint 31 gain was training era (ΔTSS(EraMatchedGOES−F0) = +0.0315), not instrument information.
**Answer: NOT SUPPORTED.** After a fair, physics-engineered, era-controlled evaluation, Aditya-L1 does not provide statistically significant incremental predictive value beyond GOES for operational solar flare forecasting; the recent-era retraining that Sprint 31 mistook for an Aditya effect is fully realized by GOES alone.
