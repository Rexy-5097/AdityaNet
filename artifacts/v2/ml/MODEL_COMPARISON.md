<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Milestone XI model comparison — performance, uncertainty, significance, interpretability. -->
<!-- DATE: 2026-07-18 -->

# Model Comparison — Milestone XI

Performance, uncertainty, strengths, weaknesses, and statistical significance for every model, both tasks.

---

## 1. Nowcast — head-to-head

| Model | Strength | Weakness | Verdict vs threshold |
|---|---|---|---|
| Persistence | Perfect steady-state tracking (recall 1.0, 0 false) | **No onset detection** — needs the flare already flagged | Dominates, but operationally hollow (§4) |
| **Threshold (rate)** | **Fewest false alarms (15); simplest; free; interpretable** | Slightly lower recall (0.927) and AUC (0.954) | **Baseline — the one to beat** |
| Logistic | Cheap; interpretable coefficients | Worst false-alarm count (228); poorly calibrated (Brier 0.029) | AUC +0.010 but **15× more false runs** |
| Random Forest | Highest AUC (0.966); best learned precision (0.766) | 4× the threshold's false runs (61) | AUC +0.012, recall indistinguishable |
| LightGBM | Highest event recall (0.988); calibrated (Brier 0.016) | 5× the threshold's false runs (79) | AUC +0.007, more false alarms |

**Statistical significance.** LightGBM − Threshold ROC-AUC = **+0.0076 [+0.0032, +0.0123]** — the CI excludes zero, so the difference is *real*, but it is **under one AUC point**. Event-recall CIs **overlap heavily** (threshold [0.875, 0.976] vs LightGBM [0.960, 1.00]), so on the operational metric the models are **statistically indistinguishable** from the threshold. The learned models' only consistent, significant edge is a fraction of an AUC point — bought with 4–15× more false alarms.

## 2. Prediction — head-to-head

| Model | ROC-AUC [95% CI] | Event recall [95% CI] | Verdict |
|---|---|---|---|
| **Threshold (rate)** | **0.792** [0.708, 0.856] | 0.439 [0.250, 0.571] | **Best non-trivial model** |
| Logistic | 0.780 [0.674, 0.850] | 0.463 [0.268, 0.600] | Indistinguishable from threshold |
| Random Forest | 0.784 [0.694, 0.850] | 0.415 [0.220, 0.547] | Indistinguishable from threshold |
| LightGBM | 0.768 [0.680, 0.831] | 0.439 [0.256, 0.565] | **Significantly worse** (paired Δ −0.023 [−0.045, −0.0004]) |

**Every learned model's CI overlaps the threshold's on both metrics**, and the one significant paired result is LightGBM being *worse*. There is **no evidence that any learned model improves 30-min prediction over a threshold on the current rate.**

## 3. What each model learned (interpretability)

**LightGBM feature importance (nowcast, top 8):** `roll_std_60` 0.141, `roll_mean_60` 0.127, `bg_excess` 0.108, `roll_max_15` 0.086, `rise_15` 0.086, `roll_std_15` 0.084, `log_rate` 0.081, `roll_mean_30` 0.080.

**Logistic coefficients (nowcast, top |β|):** `log_rate` **+5.90**, `roll_std_15` −4.70, `roll_mean_15` −3.24, `gti_fraction` +2.30, `roll_max_15` +2.20.

**Interpretation.** Both models concentrate on the **level and recent variability of the count rate**. The dominant logistic coefficient is `log_rate` — literally the quantity the threshold detector thresholds. The tree's top features (`roll_mean_60`, `roll_std_60`, `bg_excess`) are the **background activity level** identified in Milestone X. The models are not discovering a new signal; they are re-expressing "the current and recent rate is elevated," which the threshold captures in one dimension. This is *why* the threshold is competitive: the learned models' feature space collapses onto the rate.

## 4. On persistence — why the strongest number is the least useful

Persistence achieves AUC 0.982 / recall 1.000 / 0 false runs by predicting `y(t) ≈ y(t−1)`. For **nowcast**, this is legitimate (whether a flare was in progress a minute ago is known at time t) but tells you nothing until the flare has *already started* — it cannot detect onset, which is the operationally valuable moment. For **prediction**, persistence exploits that the "flare within 30 min" label barely changes minute to minute; it provides no lead time beyond the label's own smoothness.

**Consequence for evaluation.** Steady-state recall is the wrong headline metric for nowcast — persistence maxes it trivially. The right metric is **detection latency at onset**, which persistence cannot address and which the threshold and learned models can. This should be the focus of any future nowcast work.

## 5. Calibration

Brier scores (lower better): Persistence 0.001, LightGBM 0.016, Random Forest 0.019, Logistic 0.029. The threshold detector is a hard classifier (no calibrated probability). Among learned models, **LightGBM is best calibrated**; logistic is notably worse and should not be used for probability outputs without recalibration.

## 6. Overall recommendation

**Nowcast:** the **threshold detector** is the recommended operational model — 92.7 % event recall at 15 false runs, free, interpretable, and statistically indistinguishable from the learned models on event recall. If a calibrated probability is required, **LightGBM** is the learned alternative, at the cost of ~5× more false alarms for < 1 AUC point.

**Prediction:** the **threshold detector**, because no learned model beats it and one is significantly worse. But note the task ceiling: ~44 % event recall, dominated by activity-state persistence.
