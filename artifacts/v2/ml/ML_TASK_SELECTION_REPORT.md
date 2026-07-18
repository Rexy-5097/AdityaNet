<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Milestone X task selection. Opinionated, evidence-backed recommendations. -->
<!-- DATE: 2026-07-18 -->

# ML Task Selection Report — `AdityaNet_v2_dataset_r1`

**Role note:** this document is deliberately opinionated. Every recommendation cites measurements taken on the frozen dataset. Where evidence is insufficient, I say so and do not recommend.

**Headline recommendations**

| | Task | Why |
|---|---|---|
| **PRIMARY** | **M/X flare nowcast (detection) from SoLEXS** | AUC **0.9536** from a single raw column; 581 independent events; 564,160 windows |
| **SECONDARY** | **M/X 30–60 min prediction, with mandatory persistence controls** | Real signal (AUC 0.80) but **horizon-flat** — must be controlled or it will be misread as precursor skill |
| **FUTURE** | X-class, combined multimodal, self-supervised pretraining | 47 / 13 events; 171 days — statistically insufficient for a first benchmark |
| **EXCLUDED** | Calibrated severity/flux regression | **Impossible** — no RMF exists in the archive |

---

## 1. Measurements underlying every recommendation

All measured on the frozen dataset (T1 `rate_total`, 564,160 usable minutes) against the authenticated GOES catalogue.

**Window and label counts**

| Task | Windows | Positives | Base rate | **Independent events** |
|---|---|---|---|---|
| Nowcast M/X (in progress) | 564,160 | 13,377 | 2.37 % | **581** |
| Nowcast ≥C (in progress) | 564,160 | 69,109 | 12.25 % | **4,065** |
| Predict M/X ≤ 30 min | 564,160 | 13,755 | 2.44 % | 581 |
| Predict M/X ≤ 60 min | 564,160 | 25,866 | 4.58 % | 581 |
| Predict M/X ≤ 360 min | 564,160 | 109,831 | 19.47 % | 581 |
| Predict ≥C ≤ 60 min | 564,160 | 168,839 | 29.93 % | 4,065 |
| Predict X ≤ 60 min | 564,160 | 2,558 | 0.45 % | **47** |
| **Combined** M/X ≤ 60 min | 222,301 | 5,840 | 2.63 % | **179** (X: **13**) |

**Signal presence — univariate AUC of the raw, unengineered T1 rate**

| Task | AUC |
|---|---|
| **Nowcast M/X** | **0.9536** |
| Nowcast ≥C | 0.8000 |
| Predict M/X ≤ 30 min | 0.8021 |
| Predict M/X ≤ 60 min | 0.7936 |
| Predict M/X ≤ 120 min | 0.7862 |
| Predict M/X ≤ 360 min | 0.7838 |

**The decisive control** — same prediction task with all flare-in-progress minutes removed (491,399 quiet minutes):

| Horizon | AUC (all) | **AUC (quiet only)** |
|---|---|---|
| 30 min | 0.8021 | **0.8119** |
| 60 min | 0.7936 | **0.8023** |
| 120 min | 0.7862 | 0.7951 |
| 360 min | 0.7838 | 0.7884 |

**Spectral value (T2, 40-day sample, 55,710 minutes)**

| Feature | Nowcast M/X AUC | Predict ≤60 min AUC |
|---|---|---|
| total rate | 0.8794 | 0.7166 |
| soft (ch 0–59) | 0.8772 | — |
| mid (ch 60–119) | 0.8885 | — |
| hard (ch 120–339) | 0.8911 | 0.6755 |
| hardness ratio hard/soft | 0.8493 | **0.5075** |

---

## 2. PRIMARY RECOMMENDATION — M/X nowcast (detection) from SoLEXS

**Evidence.** 564,160 usable windows; 13,377 positive minutes; **581 independent M/X events**; base rate 2.37 %. A **single raw column** (`rate_total`, no feature engineering) achieves **AUC 0.9536**. Labels derive from the authenticated GOES catalogue, and the pipeline's solar sensitivity is independently corroborated (T1 peak 16:49 UTC vs GOES X8.7 at 16:51, finding F-7).

**Reasoning.** This is the only candidate where the signal is unambiguous, large, and verified. AUC 0.95 from an unengineered column means the physics is present in the data, not something a model must manufacture — which is precisely what a *first* benchmark should establish. 581 independent events is enough for stable evaluation with confidence intervals; the 2.37 % base rate is imbalanced but well within standard practice. It also satisfies the ISRO problem statement directly, which asks to "detect (nowcast) **or** predict."

The obvious objection — *a threshold nearly solves it, so where is the ML contribution?* — is exactly why it is the right first benchmark. The scientific contribution is **not** "ML beats a threshold." It is quantifying the **operational trade-off**: at what false-alarm rate can a given recall be sustained, and does a learned model improve that frontier over a calibrated threshold. That is a publishable, falsifiable claim with a strong, honest baseline. A benchmark whose baseline is weak invites overclaiming; this one does not.

**Recommendation. Adopt M/X nowcast from SoLEXS as the primary benchmark.** Evaluate at the **event level** (581 events), not the minute level — minute windows are heavily autocorrelated and minute-level metrics will overstate confidence by roughly the ratio 564,160 / 581 ≈ 970×. Report episode recall, false episodes per unit time, and detection latency. The single-column threshold at AUC 0.9536 is the **mandatory baseline**; any model must beat it explicitly.

## 3. SECONDARY RECOMMENDATION — M/X 30–60 min prediction, with mandatory controls

**Evidence.** 25,866 positive minutes at 60 min (4.58 %), 581 events, AUC 0.7936. Crucially, removing every flare-in-progress minute **does not** destroy the signal — AUC *rises* slightly to 0.8023 on 491,399 quiet minutes. But skill is **nearly flat across a 12× horizon change**: 0.8119 (30 min) → 0.7884 (360 min), a decay of only **0.024 AUC**.

**Reasoning.** Two conclusions follow, and they point in opposite directions.

First, the signal is **real**: it survives removal of ongoing flares, so it is not the trivial artifact of detecting a flare already underway. Something in the quiescent SoLEXS background genuinely carries information about future flaring.

Second, the signal is **not a precursor**. Genuine precursor information must decay with horizon — knowing a flare is 30 minutes away should be far easier than knowing it is 6 hours away. A 12× horizon increase costing 0.024 AUC is the unmistakable signature of a *slowly varying activity-state* effect: an elevated background means "this is an active period," which persists for days and is therefore almost equally predictive at 30 minutes and 6 hours.

This matters enormously for how results are reported. An uncontrolled AUC of 0.80 would be presented as flare forecasting skill; the horizon-flatness proves most of it is activity-state persistence. **This reproduces v1's forecast-vs-persistence finding — but now on real data, with the mechanism identified.**

**Recommendation. Adopt 30–60 min M/X prediction as the secondary benchmark, but only with three controls made mandatory and pre-registered:** (1) a **persistence baseline** (current activity state predicts future state); (2) a **climatology baseline** (base rate by period); (3) the **skill-vs-horizon curve** from 30 min to 6 h, reported always. Any claimed forecasting skill must be stated as *improvement over persistence*, never as raw AUC. Prefer **30–60 min** over 6 h: the horizon curve shows the marginal information is concentrated at short horizons, and shorter horizons are operationally more useful.

## 4. Ranked evaluation of all candidate tasks

| Rank | Task | Windows | Events | Signal | Verdict |
|---|---|---|---|---|---|
| **1** | **M/X nowcast (SoLEXS)** | 564,160 | **581** | **AUC 0.954** | **PRIMARY** |
| **2** | **M/X 30–60 min prediction** | 564,160 | 581 | AUC 0.80 (horizon-flat) | **SECONDARY, controlled** |
| 3 | ≥C nowcast | 564,160 | **4,065** | AUC 0.800 | Strong alternative — see §5 |
| 4 | ≥C 60 min prediction | 564,160 | 4,065 | — | Viable; balance 29.9 % |
| 5 | Combined multimodal M/X | 222,301 | 179 | not measured | **FUTURE** — §6 |
| 6 | Flare probability calibration | as above | 581 | — | Add-on to 1–2, not standalone |
| 7 | Self-supervised pretraining | 564,160 | n/a | — | **FUTURE** — no labelled scarcity yet justifies it |
| 8 | Time-to-next-flare regression | 564,160 | 581 | — | Censoring makes it harder for no gain over ranked tasks |
| 9 | Anomaly detection | 564,160 | n/a | — | Unfalsifiable without agreed anomaly labels |
| 10 | HEL1OS-only forecasting | ~1.03 M rows | 179 | not measured | **FUTURE** — 171-day span |
| 11 | Multi-class (B/C/M/X) | 564,160 | 4,065 | — | Class boundaries are GOES-defined; see §7 |
| 12 | **X-class prediction** | 564,160 | **47** (13 combined) | — | **FUTURE RESEARCH — not a benchmark** |
| — | **Severity / GOES-flux regression** | — | — | — | **EXCLUDED — impossible** |

## 5. On ≥C nowcast — the strongest alternative, and why I still rank it second

**Evidence.** 69,109 positives (12.25 %, far better balance) and **4,065 independent events — 7× the M/X count**. But univariate AUC is **0.800 vs 0.954** for M/X, and the detector's own per-class behaviour in v1 showed C-class detection at 0.244 recall versus 0.909 for M.

**Reasoning.** More events and better balance are real statistical advantages. But C-class flares sit near SoLEXS's sensitivity floor, so a substantial fraction are unobservable in this data — the label says "flare" where the instrument shows nothing. That is **label noise concentrated in the positive class**, the most damaging kind. The 0.15 AUC gap quantifies it.

**Recommendation.** Use ≥C nowcast as a **robustness check** on the primary benchmark, not as the headline. If a model's M/X performance holds up under the ≥C label, that is meaningful evidence of generality. Do **not** lead with it — the noisier labels weaken any claim built on it.

## 6. On the combined multimodal task — what the ISRO brief asks for, and why it cannot be first

**Evidence.** The combined arm is **171 days**, 222,301 windows, **179 M/X events**, and only **13 X-class events**. The SoLEXS-only arm has **581 M/X events across 424 days**.

**Reasoning.** The problem statement asks for combined SoLEXS + HEL1OS, so this task must eventually be addressed. But it has **3.2× fewer events** and a **5.6-month** span with no seasonal or activity-phase diversity. Running it first would mean the project's headline result rests on the weakest-powered configuration available. The honest sequence is to establish the benchmark where evidence is strongest, then test whether adding HEL1OS improves it.

**Recommendation.** Treat combined multimodal as a **planned second-phase experiment with an explicit ablation**: SoLEXS-only vs SoLEXS+HEL1OS **on the identical 171-day window**. That design answers the brief's actual question — *does hard X-ray add information?* — and is the only way to attribute any difference to HEL1OS rather than to a different time span. Report it as an ablation, not as the primary benchmark.

## 7. On X-class prediction — explicitly not a benchmark

**Evidence.** **47 X-class events** on SoLEXS days; **13** on combined days. The 2,558 "positive minutes" at 60 min are misleading — they collapse to 47 independent events.

**Reasoning.** With 47 events, a chronological test split leaves roughly 15–20 events for evaluation. A single event's classification shifts recall by ~5 percentage points, and no confidence interval of practical width can be constructed. Any X-class-specific claim from this dataset would be statistically indefensible regardless of method sophistication.

**Recommendation. Classify X-class prediction as a future research objective, not an initial benchmark.** Report X-class results only as a *stratified subgroup* of the M/X benchmark, always with event counts attached, and never as a standalone headline. Revisit only after multi-year acquisition.

## 8. On severity regression — excluded on physical grounds

**Evidence.** No RMF/ARF exists anywhere in the archive (finding F-1). Channels are ordinal indices; the SoLEXS light curve is a band-limited integral whose exact band is unrecoverable; the LC/spectrum ratio varies **1.76–20.4**.

**Reasoning.** GOES flare classes are defined on calibrated 1–8 Å flux. Without a response matrix there is no path from Aditya channel counts to a calibrated flux, so a regression target in physical units cannot be constructed or validated from this dataset. This is a data limitation, not a modelling difficulty — no architecture resolves it.

**Recommendation. Exclude calibrated severity/flux regression entirely** until an instrument response file is acquired. If severity is needed, use **ordinal ranking** against GOES-derived class labels and state explicitly that the output is a rank, not a flux.

## 9. Evaluation design implied by the evidence

**Evidence.** 564,160 minutes reduce to **581 independent M/X events**. M/X events by quarter: 2024Q1 96, 2024Q2 181, 2024Q4 6, 2025Q1 7, 2025Q2 3, 2025Q3 46, 2025Q4 87, 2026Q1 94, 2026Q2 61.

**Reasoning.** Minute-level cross-validation would be catastrophically optimistic — adjacent minutes are nearly identical, so random splits leak. And the quarterly distribution is deeply non-uniform: a naive chronological 80/20 split would put most of 2024's 277 events in train and evaluate on a sparse tail.

**Recommendation.** (1) **Event-level metrics**, always. (2) **Chronological splitting only** — never random, never k-fold over minutes. (3) A defensible split given the quarterly counts: **train 2024Q1–2025Q4 (≈423 events), test 2026Q1–Q2 (≈155 events)**, which keeps a substantial, contiguous, unseen test period. (4) Confidence intervals via **block bootstrap over events**, not minutes — the frozen v1 harness already implements this and should be reused.

## 10. Summary

**Do this first:** M/X nowcast from SoLEXS, event-level evaluation, single-column threshold as the mandatory baseline.
**Do this second:** 30–60 min M/X prediction with persistence and climatology controls and a published skill-vs-horizon curve.
**Then:** the SoLEXS-vs-combined ablation on the shared 171-day window, answering the brief's real question.
**Not yet:** X-class as a standalone task, self-supervised pretraining, anomaly detection.
**Never, with this dataset:** calibrated severity regression.
