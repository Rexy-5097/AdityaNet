NOT SUPPORTED

# Final Verdict — Sprint 32 (ISRO hypothesis)

**Question:** After a fair physics-engineered evaluation, does Aditya-L1 provide statistically significant incremental predictive value beyond GOES for operational solar flare forecasting — with the training-era confound removed?

**Era-matched Aditya effect — ΔTSS(F2 − EraMatchedGOES):** point estimate **−0.0388** (negative in all 3 shared seeds; per-seed 95% block-bootstrap CIs [−0.0923, +0.0275], [−0.0771, +0.0148], [−0.0873, +0.0035]; bootstrap p_boot 0.230 / 0.154 / 0.074; **0 of 3 seeds** meet the pre-registered "≥ +0.02, lower bound > 0" success test; Cohen's d −10.7). Equivalently, the era-matched GOES-only control (EraMatchedGOES) exceeds the GOES+Aditya arm (F2) by +0.0388 True Skill Score. Decision tree: **Path D foreclosed** (F3 ≤ F2) and **Path B premise falsified** (F2 ≤ EraMatchedGOES); the Aditya-L1 feature and fusion program is closed (`artifacts/sprint32/Decision_Tree_Update.md`).

Once the training era is held fixed at the recent Stage-2 period, adding the 15 Aditya-L1 features and 4 availability channels does not add measurable window-level skill and the point estimate is that it removes ≈0.039 True Skill Score, failing the pre-registered positive-effect test in 0 of 3 seeds (`artifacts/sprint32/analysis.json`, `Statistical_Analysis.md`). The improvement Sprint 31 attributed to Aditya-L1 is fully explained by training on recent data — EraMatchedGOES, a GOES-only model, is the best arm measured (True Skill Score 0.4383) and beats the deployed baseline F0 by +0.0315 while every Aditya-inclusive arm underperforms it (`artifacts/sprint32/Statistical_Analysis.md`).
