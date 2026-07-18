<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Milestone X feature engineering strategy. Opinionated, evidence-backed. -->
<!-- DATE: 2026-07-18 -->

# Feature Engineering Plan — `AdityaNet_v2_dataset_r1`

**Recommendations, not an inventory.** Each table and feature family is either recommended, deferred, or rejected, with the measurement that decides it.

**Headline**

| Table | Verdict | Basis |
|---|---|---|
| **T1** `solexs_lc_1min` | **USE — primary signal carrier** | AUC **0.9536** nowcast from one raw column |
| **T2** `solexs_spec_1min` | **USE, but as a controlled question — not on faith** | band sums add ≤ **0.012** AUC over total |
| **T3** `hel1os_lc_1min` | **DEFER to the ablation phase** | 171-day span, 179 events |
| **T4** `hel1os_hk_1min` | **EXCLUDE as features; USE as quality filter** | instrument state, not solar signal |
| **T5** `hel1os_spec_1min` | **DEFER** | 171 days; three incommensurable channel spaces |
| **T6** `gti_intervals` | **USE as exposure/validity, never as a feature** | defines observability |
| **T7** `provenance_manifest` | **EXCLUDE — leakage risk** | build metadata, not measurement |

---

## 1. T1 — the primary signal carrier

**Evidence.** `rate_total`, raw and unengineered, achieves **AUC 0.9536** for M/X nowcast and **0.79–0.80** for 30–360 min prediction across 564,160 minutes. No other single quantity in the dataset comes close.

**Reasoning.** A feature set should start from the thing that demonstrably carries the signal. T1 is minute-resolution, complete over 424 days, 92.4 % usable, and its physical meaning is unambiguous (band-limited counts and rate with matched live time). It is also the *cheapest* table by two orders of magnitude — 610,560 scalar rows versus 340-element arrays.

**Recommendation. Build the entire first benchmark on T1 alone.** Recommended families, in priority order:

1. **Instantaneous level** — `rate_total`, `log1p(rate_total)`. The log form because flare amplitudes span decades; the AUC 0.9536 is driven by level.
2. **Short-window temporal context** — rolling mean/max/std over 5, 15, 30, 60 min. Rise-rate is the physically motivated precursor quantity and the one genuinely new thing a model can exploit beyond a threshold.
3. **Background-relative excess** — `rate_total` minus a trailing quiet-level percentile (e.g. rolling 6 h 10th percentile). **This is the highest-value engineered feature for the prediction task**, because the horizon-flat AUC (0.812 → 0.788 over 12×) identifies the *background activity level* as the source of forecast skill. Making it explicit lets a model use it directly and lets the analysis separate it from precursor effects.
4. **Observability context** — `gti_fraction`, `n_seconds_present`, `q_partial` as *covariates*, so the model can distinguish "low rate" from "poorly observed."

**Explicitly do not** engineer more than this before the baseline is measured. The single-column AUC is 0.954; the burden is on any added feature to demonstrate improvement.

## 2. T2 — use it, but as a hypothesis under test, not an assumption

**Evidence** (40-day sample, 55,710 minutes, 1,218 M/X-positive):

| Feature | Nowcast AUC | Δ vs total | Predict ≤60 min AUC |
|---|---|---|---|
| total rate | 0.8794 | — | 0.7166 |
| soft (ch 0–59) | 0.8772 | −0.002 | — |
| mid (ch 60–119) | 0.8885 | +0.009 | — |
| hard (ch 120–339) | 0.8911 | **+0.012** | 0.6755 |
| **hardness hard/soft** | 0.8493 | **−0.030** | **0.5075** |
| hardness mid/soft | 0.8641 | −0.015 | — |

**Reasoning.** This is the most important negative result for feature design, and it contradicts the intuition that motivated v2's spectral emphasis.

The 340-channel spectrum, reduced to band sums, adds **at most 0.012 AUC** over the plain total — within sampling noise of the univariate estimates. Worse, **hardness ratios are actively harmful**: −0.030 AUC for nowcast, and **0.5075 — indistinguishable from random — for 60-minute prediction.** The physically appealing idea that spectral hardening precedes flares is **not supported by this dataset** at 1-minute resolution.

I want to be careful about what this does and does not establish. It shows that *simple univariate band-sums and ratios* add little. It does not prove the full 340-dimensional spectrum is uninformative — a multivariate model could exploit structure that no single ratio captures. But it does mean elaborate spectral feature engineering **cannot be justified in advance by evidence**, and building it on faith is exactly the error that produced v1's wasted effort.

**Recommendation. Include T2 as a *controlled ablation*, never as a default.** Specifically: run the primary benchmark with T1 alone, then with T1 + coarse spectral bands, and report the difference with confidence intervals. **Do not build hardness-ratio features for the prediction task** — measured AUC 0.5075 is a direct refutation. If spectral value exists, it must be demonstrated by that ablation, not presumed.

**Practical note:** T2 is 340 floats × 610,560 rows. Load it only for the ablation arm; the primary arm does not need it.

## 3. T3 / T5 — HEL1OS, deferred to the ablation phase

**Evidence.** HEL1OS covers **171 days** jointly with SoLEXS (2025-12-07 → 2026-06-15), containing **179 M/X events** versus 581 on the SoLEXS-only arm. T5 spans **three incommensurable channel spaces** (SoLEXS PI 340, CZT PHA 341, CdTe PHA 511) with no response matrix relating them.

**Reasoning.** The ISRO brief asks for combined data, so these tables must be used eventually — but using them in the *primary* benchmark would cut the event count by 3.2× and the span to under six months. That trades the project's strongest evidence for its weakest.

**Recommendation. Defer T3/T5 to a dedicated ablation on the shared 171-day window**, comparing SoLEXS-only against SoLEXS+HEL1OS *on identical days*. That is the only design that attributes a difference to the instrument rather than to the time span. Within T3, prefer the **broad-band columns** (`czt1_18_160_rate`, `cdte1_1p8_90_rate`) as the primary HEL1OS signal and treat the four narrow bands as the ablation's second tier. **Never concatenate spectra across detector families** (F-4 / F-11).

## 4. T4 — exclude as features; use as a quality filter

**Evidence.** T4 contains detector temperatures, HV monitors, pile-up and saturation counters, hot-pixel counts, and `suninfov`. These are **instrument-state** telemetry. Separately, its `mjd` series is telemetry-ordered with inversions in 112/389 orbits (F-3).

**Reasoning.** Using instrument housekeeping as model features invites a specific and severe failure: the model learns instrument-state correlations that happen to track solar activity in this sample — detector temperature tracks orbital and seasonal cycles, which track observing conditions — and those correlations will not generalise. This is a well-known trap in instrument-derived ML, and with only 581 events there is ample room to fit it.

There is one legitimate use. **`suninfov` determines whether the instrument was even pointed at the Sun**, and pile-up/saturation counters indicate when a measurement may be compromised. These are **validity conditions**, not predictors.

**Recommendation. Exclude all T4 columns from the feature set.** Use `suninfov` and the saturation/pile-up counters **only** to filter or flag samples, and document that filter as part of the experimental protocol. If someone later wants to test instrument-state features, that must be a separate, explicitly-labelled experiment with its own generalisation check.

## 5. T6 / T7 — exposure and provenance, never features

**Evidence.** T6 defines good-time intervals; its `live_time_s` already propagates into T1. T7 contains `src_file`, `src_sha256`, `parsed_at_utc`, `creator`, `parser_version`.

**Reasoning.** T6 belongs in the *validity* layer: it determines which minutes are observable at all, and T1 already carries the derived quantities (`live_time_s`, `gti_fraction`). Using raw GTI structure as a feature would be circular.

T7 is worse — it is a **leakage vector**. `src_file` and `obs_date` encode the calendar date directly; a model given them can memorise which days had flares. `parsed_at_utc` encodes build order. None are measurements of the Sun.

**Recommendation. T6 → validity/exposure layer only. T7 → provenance and audit only; never joined into a feature matrix.** I recommend enforcing this structurally: the feature-assembly function should accept an explicit column allowlist and reject any provenance column by name, rather than relying on discipline.

## 6. Features I recommend *against* building

| Feature family | Why not |
|---|---|
| Hardness ratios for prediction | **Measured AUC 0.5075** — no signal. Direct refutation. |
| Full 340-dim spectra in the first model | ≤ 0.012 AUC gain as bands; 340× cost; overfitting risk with 581 events |
| Instrument-state features (T4) | Non-generalising instrument correlations |
| Calendar/date features | Leakage — memorises active periods |
| Cross-instrument channel concatenation | Three incommensurable spaces (F-4), no response matrix |
| Long-horizon (> 6 h) aggregates | Horizon-flat AUC shows no additional information at long lags |
| Imputed/interpolated gap fills | Dataset policy is explicit NaN; imputation would fabricate observations |

## 7. Handling missingness — a design decision, not a default

**Evidence.** T1 `counts_total` is NaN on 4.20 % of minutes; `rate_total` on 7.6 % (where `live_time_s == 0`). Every NaN is flagged (`q_no_data`, `q_partial`). The dataset never imputes.

**Reasoning.** Imputing would manufacture observations the instrument did not make — the precise failure this project spent Milestones I–IX eliminating. But models need a defined behaviour.

**Recommendation.** Use **masking, not imputation**: drop windows whose target minute is unobserved, and for context windows pass an explicit validity mask alongside the values. Report the fraction of windows dropped as an experimental parameter. If a model architecture cannot accept masks, that is a reason to reconsider the architecture — not a reason to impute.

## 8. Recommended first feature set (concrete)

For the primary benchmark, from **T1 only**:

```
log1p(rate_total)                     level
rolling mean/max/std @ 5,15,30,60 min temporal context
rate_total − rolling_p10(6 h)         background-relative excess  ← highest value for prediction
d(rate_total)/dt @ 5,15 min           rise rate
gti_fraction, n_seconds_present       observability covariates
q_partial                             quality flag
```

≈ 15 features. **Deliberately small**: with 581 independent events, a large feature space invites overfitting that event-level evaluation would then have to detect rather than prevent. Every addition beyond this set should be justified by a measured ablation, not by physical intuition — the hardness-ratio result (0.5075) is the cautionary case.
