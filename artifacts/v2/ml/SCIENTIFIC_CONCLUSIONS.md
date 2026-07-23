<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Milestone XI scientific conclusions. Evidence -> Interpretation -> Recommendation. -->
<!-- DATE: 2026-07-18 -->

# Scientific Conclusions — Milestone XI

**Central question:** does machine learning provide measurable operational value beyond strong classical baselines, for M/X flare nowcast and 30-minute prediction on `AdityaNet_v2_dataset_r1`?

**Answer, stated plainly: No — not for these tasks on this dataset. A simple threshold on the SoLEXS count rate is operationally the strongest non-trivial detector, and the gradient-boosted and forest models do not beat it in any way that matters.** This is a negative result, and per the milestone's own success criteria it is a *successful* outcome: an honest, reproducible, statistically defensible benchmark that future work can build on.

Each conclusion below follows the required structure.

---

## Conclusion 1 — ML does not add operational value to M/X nowcast

**Evidence.** Threshold detector: ROC-AUC 0.954, event recall 0.927 [0.875, 0.976], **15 false runs**. Best learned model (Random Forest): AUC 0.966, recall 0.976 [0.930, 1.00], **61 false runs**. Paired ROC-AUC difference LightGBM − Threshold = +0.0076 [+0.0032, +0.0123]. Event-recall CIs overlap. Learned models carry 4–15× the threshold's false-alarm count.

**Interpretation.** The learned models win a statistically-real but operationally-negligible fraction of an AUC point, and pay for it with several-fold more false alarms. On the metric that matters operationally — event recall — they are statistically indistinguishable from the threshold. The feature-importance analysis explains why: the models concentrate on the count-rate level and its recent variability, which is exactly what the one-dimensional threshold already uses.

**Recommendation.** **Adopt the threshold detector as the reference M/X nowcast model.** It is free, interpretable, has the fewest false alarms, and is statistically indistinguishable from the best learned model on event recall. Reserve LightGBM as a calibrated-probability alternative only where a probability output is specifically required.

## Conclusion 2 — ML does not improve 30-minute prediction; it is at best equal, at worst worse

**Evidence.** Threshold: AUC 0.792 [0.708, 0.856], event recall 0.439. Random Forest 0.784; Logistic 0.780; LightGBM 0.768. Paired LightGBM − Threshold = **−0.0229 [−0.0445, −0.0004]** — significantly *negative*. Every learned model's CI overlaps the threshold's on both metrics.

**Interpretation.** There is no evidence any learned model improves prediction, and the one significant paired result is a learned model performing *worse*. The task itself saturates near 44 % event recall.

**Recommendation.** **Use the threshold detector for 30-minute prediction as well.** Do not deploy a learned model here — it adds cost and, in the LightGBM case, measurably degrades ranking.

## Conclusion 3 — The forecasting signal is activity-state persistence, not flare precursor information

**Evidence.** Persistence baseline: AUC 0.983, event recall 1.000, 0 false runs — dominating every model on prediction. From Milestone X: prediction AUC is horizon-flat (0.812 at 30 min → 0.788 at 6 h; a 12× horizon change costs 0.024). The learned models' top features are `roll_mean_60`, `roll_std_60`, `bg_excess` — the background activity level.

**Interpretation.** Persistence dominating, combined with horizon-flat skill, is the unambiguous signature of a slowly-varying *activity state*: the useful information is "the Sun is currently in an active period," which persists for days and is therefore almost equally predictive at 30 minutes and 6 hours. This is **not** flare-specific precursor detection. It reproduces v1's forecast-vs-persistence conclusion — now on real Aditya-L1 data, with the mechanism identified rather than inferred.

**Recommendation.** **Report all future prediction results as improvement over persistence, never as raw AUC.** Frame the prediction task honestly as activity-state nowcasting. If genuine precursor detection is the goal, it requires a signal that decays with horizon — and this dataset does not visibly contain one.

## Conclusion 4 — Spectral resolution does not improve flare detection (v2's founding premise is not supported)

**Evidence.** Adding T2 spectral band-sums to the T1 model changes nowcast AUC by **+0.0033** [within the ~±0.012 bootstrap CI]; hardness ratio +0.0013. Milestone X's univariate analysis predicted this (≤0.012; hardness at random for prediction).

**Interpretation.** v2 was premised on the idea that 340 real spectral channels (versus v1's 9 synthetic ones) would unlock performance v1 could not reach. **For flare detection, they do not.** The spectrum is scientifically real and valuable for characterisation, but it carries no measurable marginal signal for detecting or predicting M/X flares at 1-minute resolution beyond the total rate.

**Recommendation.** **Exclude spectral features from the operational detector.** This is not a failure of the dataset — it is a clean, useful finding that redirects effort: spectral resolution should be applied to flare *characterisation* (e.g. ordinal severity ranking, once an instrument response file is acquired), not to detection.

## Conclusion 5 — The operationally important open problem is onset latency, not steady-state recall

**Evidence.** Persistence achieves perfect steady-state nowcast recall (1.000) trivially, because a flare in progress stays in progress. It cannot detect onset — it requires the flare to already be flagged.

**Interpretation.** Steady-state recall is the wrong headline metric: it is saturated by a trivial baseline. The scientifically and operationally meaningful quantity is **how quickly a detector catches the flare onset** — the moment persistence cannot help with and where a rate-based detector's threshold placement genuinely matters.

**Recommendation.** **Make detection latency at onset the primary metric of any future nowcast work.** The threshold detector already provides a strong, free baseline for it; that is where a learned model would have to demonstrate value.

---

## Overall verdict

| Question | Evidence-based answer |
|---|---|
| Does ML beat classical baselines for M/X nowcast? | **No** — indistinguishable from a threshold on event recall; +0.008 AUC at 4–15× the false alarms |
| Does ML beat classical baselines for 30-min prediction? | **No** — equal at best, significantly worse at worst |
| Is a threshold detector nearly optimal? | **Yes** — recommend it for both tasks |
| Does spectral (T2) resolution help detection? | **No** — +0.003 AUC, confirmed null |
| Do housekeeping (T4) features help? | Not added — leakage + confounded; excluded as features |
| Is the forecasting signal real precursor information? | **No** — it is activity-state persistence |

**This milestone establishes the reference performance the brief asked for: a threshold on the SoLEXS count rate is the honest, reproducible, near-optimal baseline for M/X flare nowcast; learned models add no operational value; spectral features add none; and 30-minute "prediction" is activity-state persistence.** Future research should target onset-latency reduction and — only with an acquired instrument response — spectral severity characterisation. Nothing here recommends complexity that the evidence does not support.
