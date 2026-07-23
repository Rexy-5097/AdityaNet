<!-- VERSION STATUS: FROZEN before any model was fit -->
<!-- REASON: Milestone XI evaluation protocol. Every choice justified by measurement. -->
<!-- DATE: 2026-07-18 -->

# Evaluation Protocol — Milestone XI

**Frozen before any model was fit.** Every design choice below is justified by a measurement on the frozen dataset, not by convention.

---

## 1. Train / validation / test split

**Choice.** Chronological. **Train** 2024-02-01 → 2025-12-31; **Validation** = last 20 % of the pre-test period by time; **Test** = 2026-01-01 → 2026-06-15. Test opened once.

**Evidence.** Autocorrelation of `log1p(rate_total)`: **0.997 @ 1 min, 0.804 @ 60 min, 0.643 @ 480 min**. A random or k-fold split over minutes would place near-identical neighbours in both train and test, leaking the answer. The decorrelation time exceeds 8 hours, so only a *temporal* split with a gap at day granularity avoids leakage.

**Why this boundary.** M/X events by quarter: 2024Q1 96, 2024Q2 181, 2024Q4 6, 2025Q1 7, 2025Q2 3, 2025Q3 46, 2025Q4 87, **2026Q1 94, 2026Q2 61**. The 2026-01-01 cut yields **~423 training events and ~155 test events** — a substantial, contiguous, unseen test period spanning two quarters of genuine activity. Earlier cuts would test on the sparse 2025 tail (3–7 events/quarter); later cuts would leave too little test data.

## 2. Temporal split strategy

**Choice.** Single forward-chaining split (train → val → test in time), no shuffling, no random folds.

**Evidence.** Same autocorrelation result. Additionally, flare occurrence is non-stationary across the solar cycle; a forward split is the only one that measures *generalisation to a future period*, which is the operational question. Cross-validation over time would either leak (random folds) or waste the scarce events (blocked k-fold on 581 events leaves too few per fold for stable estimates).

## 3. Event grouping

**Choice.** Contiguous runs of positive-label minutes = one **event**. Metrics are computed at both the minute and the event level; the event level is primary.

**Evidence.** The dataset contains **564,160 usable minutes but only 581 independent M/X events** (Milestone X). Treating minutes as independent samples overstates the effective sample size by ~970×. An event is the unit at which the label is actually independent.

**Event-level definitions.**
- **Event recall** = fraction of true events with ≥ 1 predicted-positive minute.
- **False event runs** = predicted-positive minute-runs not overlapping any true event (the operational false-alarm unit).

## 4. Handling of autocorrelation

**Choice.** Confidence intervals by **day-block bootstrap**: resample whole UTC days with replacement (1,000 replicates), recompute event recall and minute ROC-AUC on each.

**Evidence.** With minute-level autocorrelation of 0.64 even at 8 h, an IID bootstrap over minutes would produce absurdly narrow intervals. The day (1,440 min) is the practical independent block — it exceeds the strong-correlation window and matches the natural observing unit. This is the same moving-block principle the frozen v1 harness uses, adapted to day granularity.

## 5. Confidence intervals

**Choice.** 95 % CIs from the day-block bootstrap percentiles (2.5 / 97.5) for every reported metric on every model.

**Evidence.** 155 test events is small; point estimates without intervals would invite over-reading. The block bootstrap over days is the honest uncertainty given the autocorrelation structure measured in §4.

## 6. Statistical significance testing

**Choice.** For the headline comparison (best model vs threshold detector), a **paired day-block bootstrap** of the metric *difference*: resample days, compute Δ(event recall) and Δ(ROC-AUC) per replicate, and report the CI of the difference. If that CI contains zero, the two are declared **statistically indistinguishable**.

**Evidence.** Paired testing controls for day-to-day difficulty variation (some test days have large flares, some none). An unpaired comparison would be dominated by which days each bootstrap sample happened to draw. The paired difference isolates the model contribution.

## 7. Metrics reported

Minute-level and event-level, for every model: ROC-AUC, PR-AUC, precision, recall, F1, balanced accuracy, MCC, Brier score (calibration), confusion matrix, false-alarm rate, miss rate, and inference latency (µs/sample).

**Operating-point rule.** Every thresholded metric uses a threshold selected on **train/validation only** — the threshold detector's cut maximises F1 on train; each model's cut maximises F1 on validation. The test set never informs any threshold. Threshold-free metrics (ROC-AUC, PR-AUC) are reported alongside to separate ranking quality from operating-point choice.

## 8. No imputation

**Choice.** Minutes with non-finite `rate_total` are **dropped** (masked) from training and evaluation; never imputed.

**Evidence.** Dataset policy (Milestones I–IX): NaN is the missing-data sentinel, never filled. 7.6 % of minutes are non-finite rate (`live_time_s == 0`). The dropped fraction is reported as an experimental parameter.

## 9. What would falsify a positive ML claim

Pre-committed, so the conclusion cannot be rationalised after the fact:
- If the best model's event-recall CI **overlaps** the threshold detector's, the models are **not** shown to add operational value → recommend the threshold.
- If ROC-AUC differences are within the paired-bootstrap CI of zero, the models are **statistically indistinguishable** from the threshold.
- If T2 spectral features do not move validation metrics beyond their CI, T2 is declared **non-contributory** (Milestone X predicted this; the ablation tests it).
- If T4 housekeeping features improve validation but degrade test, they are declared a **generalisation hazard** and excluded.
