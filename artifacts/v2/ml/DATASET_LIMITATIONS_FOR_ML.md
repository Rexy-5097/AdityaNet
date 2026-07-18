<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Milestone X — how the frozen dataset constrains modelling, evaluation, and claims. -->
<!-- DATE: 2026-07-18 -->

# Dataset Limitations for ML — `AdityaNet_v2_dataset_r1`

How the frozen dataset constrains **model choice**, **evaluation**, **loss functions**, **validation strategy**, and **achievable scientific claims**. Each limitation is stated with the measurement behind it and the concrete constraint it imposes.

---

## L-1 — The effective sample size is 581, not 564,160

**Measurement.** 564,160 usable minutes contain **581 independent M/X events** (4,065 ≥C; **47** X-class; **179** M/X on combined days).

**Constrains model choice.** Model capacity must be sized to ~581 events, not to half a million rows. A model with thousands of effective parameters will fit event-specific noise. **Recommendation: ≤ ~15 features and a low-capacity learner for the first benchmark**; deep sequence models only if Stage 3 evidence justifies them.

**Constrains evaluation.** Minute-level metrics overstate confidence by roughly 564,160/581 ≈ **970×**. **All metrics must be event-level**, with confidence intervals from a block bootstrap over events. Reporting minute-level AUC as the headline would be a statistical error, not a stylistic choice.

**Constrains claims.** Any subgroup smaller than ~50 events cannot support a quantitative claim. This rules out standalone X-class conclusions (47 events; ~15–20 in a test split, where one event moves recall by ~5 points).

## L-2 — Forecast skill is horizon-flat: it is activity-state persistence, not precursor detection

**Measurement.** Prediction AUC on **quiet minutes only** (in-progress flares excluded): 30 min **0.8119**, 60 min 0.8023, 120 min 0.7951, 360 min **0.7884**. A **12× horizon change costs 0.024 AUC**.

**Constrains claims — severely.** Genuine precursor information must decay with horizon. Near-flat skill across 30 min to 6 h is the signature of a slowly varying activity state that persists for days. **A raw forecasting AUC of ~0.80 must never be reported as flare-prediction skill.** It must be reported as *improvement over a persistence baseline*, with the skill-vs-horizon curve published alongside.

**Constrains validation.** Persistence and climatology baselines are **mandatory**, not optional — without them the number is uninterpretable. This is v1's forecast-vs-persistence finding reproduced on real data, now with the mechanism identified.

**Constrains loss functions.** Optimising a horizon-agnostic loss will find the persistence solution, because that is where the gradient is. If precursor detection is the goal, the objective must explicitly reward *short*-horizon discrimination over long — otherwise the model will correctly learn "the Sun is active" and the result will be misread.

## L-3 — No instrument response: physical severity targets are unconstructible

**Measurement.** No RMF/ARF anywhere in the archive. Channels are ordinal. The light curve is a band-limited integral of the spectrum with LC/Σ(PI) ratio varying **1.76–20.4** (F-1).

**Constrains model choice.** No regression target in physical units (W/m², GOES class as a continuous quantity) can be built or validated. **Calibrated severity regression is excluded** — this is a data limitation no architecture resolves.

**Constrains claims.** Permitted: "the model ranks events by observed intensity," "the model classifies against GOES-defined labels." **Not permitted:** "the model estimates GOES flux," "the model measures plasma temperature," or any statement in keV.

**Constrains features.** No physically-calibrated spectral feature (temperature, emission measure, spectral index) is derivable. Spectral features are ordinal-channel statistics only.

## L-4 — The combined-instrument arm is 171 days

**Measurement.** SoLEXS-only: **424 days, 581 M/X events**. Combined SoLEXS+HEL1OS: **171 days (2025-12-07 → 2026-06-15), 179 M/X events, 13 X-class**.

**Constrains validation.** A chronological split within 171 days leaves a test period of ~2 months — too short for a stable estimate and containing no activity-phase diversity.

**Constrains claims.** Combined-instrument results cannot be generalised beyond a single ~6-month solar-maximum window. **The ISRO brief's combined requirement is best served by an ablation on the shared window**, not by a primary benchmark, since only a matched-window comparison attributes a difference to the instrument rather than the epoch.

## L-5 — Spectral features carry little marginal information; hardness ratios carry none for prediction

**Measurement** (55,710 minutes, 40 days): band sums add **≤ 0.012 AUC** over the total rate (hard 0.8911 vs total 0.8794). Hardness ratios: **−0.030** for nowcast, and **0.5075 — indistinguishable from random — for 60-min prediction**.

**Constrains features.** Elaborate spectral engineering is **not** justified in advance. Hardness-ratio features for prediction are directly refuted. The 340-channel spectrum must earn inclusion through a measured ablation.

**Constrains claims.** Until the Stage-4 ablation runs, **no claim may be made that spectral resolution improves flare detection or prediction**. The univariate evidence points the other way.

*Scope of this limitation:* it establishes that simple band-sums and ratios add little. It does not prove the full 340-dim spectrum is uninformative under a multivariate model — which is exactly why the ablation exists.

## L-6 — Class imbalance and its interaction with event scarcity

**Measurement.** Base rates: M/X nowcast **2.37 %**, M/X ≤60 min **4.58 %**, ≥C nowcast 12.25 %, ≥C ≤60 min 29.93 %.

**Constrains loss functions.** At 2.4 % positives, unweighted accuracy is meaningless and plain cross-entropy under-weights positives. Class weighting or focal loss is appropriate — **but** with 581 events, aggressive re-weighting increases variance on the rare class. **Recommendation: mild class weighting, and select on a threshold-free ranking metric (AUC/AP) rather than on accuracy.**

**Constrains evaluation.** Report the **precision–recall frontier**, not a single operating point. v1's most important operational lesson was that a fixed false-alarm budget can bury a working detector; the frontier makes the trade-off visible instead of pre-judged.

## L-7 — Missingness must be masked, never imputed

**Measurement.** T1 `counts_total` NaN on **4.20 %** of minutes; `rate_total` non-finite on **7.6 %**; every NaN flagged (`q_no_data`, `q_partial`). T3's 75 % NaN is **structural** (long form), not missing data.

**Constrains model choice.** Architectures requiring dense complete input need an explicit **mask channel**; imputation is prohibited by dataset policy and would fabricate observations. If an architecture cannot accept masks, prefer a different architecture rather than imputing.

**Constrains evaluation.** The dropped-window fraction is an experimental parameter and must be reported — dropping differs systematically between quiet and active periods, so silently dropping could bias the base rate.

## L-8 — GTI semantics are not fully characterised

**Measurement.** On **70 of 414 days**, GTI excludes seconds that nevertheless carry finite counts — **266,919 s** total, up to 43,199 s in one day, concentrated (top-10 days = 80.2 %). Mechanism unknown (A-14 / F-2).

**Constrains features.** `live_time_s` and `gti_fraction` are usable as observability covariates but **their exact semantics are open**. Do not build a physical rate normalisation that depends on GTI meaning more than "seconds the archive marks good."

**Constrains claims.** Exposure-normalised quantities carry an unquantified systematic on those 70 days. Any result sensitive to exposure normalisation should be checked with and without them.

## L-9 — Labels are exogenous and instrument-mismatched

**Measurement.** All labels come from the GOES catalogue, defined on **GOES 1–8 Å flux**. SoLEXS has no cross-calibration to that scale. v1 measured C-class detection at 0.244 recall versus 0.909 for M — i.e. many catalogued C flares are below SoLEXS's effective sensitivity.

**Constrains claims.** A "missed" flare may be a **genuinely unobservable** one, not a model failure. Recall against the GOES catalogue conflates model performance with instrument sensitivity. **Report per-class recall with event counts always attached**, and treat ≥C results as sensitivity-limited.

**Constrains loss functions.** Training on ≥C labels injects label noise concentrated in the positive class — the most damaging kind. **Recommendation: train the primary benchmark on M/X labels** (0.954 vs 0.800 univariate AUC quantifies the difference) and use ≥C as a robustness check.

## L-10 — Single detector, single solar-cycle phase

**Measurement.** SoLEXS science is **SDD2 only** (SDD1 F-12 inactive across 426 GTI files). The span sits near solar maximum; M/X events per quarter range from **3** (2025Q2) to **181** (2024Q2).

**Constrains validation.** No detector-redundancy check is possible for SoLEXS. The 60× quarterly variation means a naive chronological split can produce train/test periods with wildly different base rates — the split must be chosen with event counts in view (hence the recommended 2024Q1–2025Q4 / 2026Q1–Q2 split, ~423 / ~155 events).

**Constrains claims.** **No cross-cycle generalisation claim is supportable.** Results apply to a solar-maximum regime observed by one detector.

---

## Summary — what can and cannot be claimed

**Supportable with this dataset**
- M/X flare **nowcast/detection** performance, event-level, with CIs — the signal is strong and verified (AUC 0.954 from one raw column).
- **Improvement over persistence** for short-horizon prediction, *if* demonstrated against the mandatory baselines.
- **Ablation results**: does spectral resolution help? does HEL1OS help? — as measured deltas with CIs.
- **Operational characterisation**: recall, false-alarm attribution, latency, the full frontier.

**Not supportable**
- Calibrated flux or severity regression (**no RMF**).
- Raw forecasting AUC presented as precursor skill (**horizon-flat**).
- Standalone X-class conclusions (**47 events**).
- Cross-cycle or multi-detector generalisation (**one phase, one detector**).
- Any claim in keV or physical spectral units (**ordinal channels only**).

**The through-line:** this dataset's strength is *detection*, and its strength there is genuine and large. Its forecasting signal is real but is an activity-state effect, and its severity axis is physically unavailable. A programme that leads with detection, controls forecasting against persistence, and treats spectra and HEL1OS as measured ablations will produce defensible results. One that leads with forecasting AUC or severity regression will produce claims this dataset cannot support.
