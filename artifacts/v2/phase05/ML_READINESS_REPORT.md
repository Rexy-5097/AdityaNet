<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Milestone IX engineering readiness review for AdityaNet_v2_dataset_r1. -->
<!-- DATE: 2026-07-18 -->

# ML Readiness Report — `AdityaNet_v2_dataset_r1`

**Engineering readiness review. Not model selection.** No features engineered, no data split, no algorithm chosen. This assesses whether the frozen dataset is *suitable to be consumed* by machine learning, and states its limits plainly.

**Verdict: READY, with two scope limits that must be respected — the combined-instrument arm is 171 days, and severity labels cannot be derived from Aditya data alone.**

---

## 1. Temporal coverage

| Arm | Days | Span | Usable minutes |
|---|---|---|---|
| **SoLEXS-only** | **424** | 2024-02-01 → 2026-06-15 | 564,160 of 610,560 (**92.4 %**) |
| **HEL1OS-only** | 189 | 2025-12-07 → 2026-06-17 | 277,054 HK / 1,027,773 LC rows |
| **COMBINED (both instruments, same day)** | **171** | **2025-12-07 → 2026-06-15** | — |

**The binding constraint:** the ISRO problem statement asks for *combined* SoLEXS + HEL1OS. **HEL1OS coverage begins only 2025-12-07**, so the combined arm spans **171 days (~5.6 months)**, not the 2.4-year SoLEXS span. Any combined-instrument model is limited to that window. The SoLEXS-only arm has 424 days across 28 months at ~50 % duty.

## 2. Label availability

Labels come from the **GOES/NOAA flare catalog** (authenticated real; `goes_full.parquet` verified against the May-2024 X8.7 storm to the minute). The frozen dataset itself carries **no label column** — deliberately, since labelling is a modelling decision.

| Population | Flares | B | C | M | X |
|---|---|---|---|---|---|
| Catalogue over the SoLEXS span | 8,712 | 445 | 6,840 | 1,344 | 83 |
| **On days with SoLEXS data** | **4,385** | 320 | 3,484 | **534** | **47** |
| **On COMBINED days** | **1,963** | 217 | 1,567 | **166** | **13** |

**Assessment.** The SoLEXS-only arm has adequate event counts for M/X-class work (534 M + 47 X). The combined arm is thin at the top of the class scale — **13 X-class events across 171 days** — which constrains what can be estimated about the rarest class regardless of method.

**Label caveat (structural, not fixable by modelling):** flare classes are defined on **GOES 1–8 Å flux**. Aditya-L1 provides no calibrated flux (no RMF/ARF in the archive — F-1), so *severity labels are exogenous*. Using GOES labels for training is legitimate; deriving or predicting a **calibrated GOES flux value** from Aditya channels is not supported by this dataset.

## 3. Target availability

Detection/nowcast targets are constructible from the catalogue and the frozen timestamps (event-overlap, rise-phase, horizon-shifted windows). **No target is materialised in the frozen dataset**, so the labelling rule remains an explicit, auditable modelling choice rather than a baked-in assumption.

## 4. Missingness

| Table | Missing | Nature |
|---|---|---|
| T1 `counts_total` | 25,623 / 610,560 (**4.20 %**) | genuine absence; `q_no_data` marks every one |
| T1 `rate_total` | 7.6 % non-finite | NaN where `live_time_s == 0` — **never imputed** |
| T2 `counts` | per-channel NaN, aligned with T1 | same origin |
| T3 band cells | 75.0 % | **structural, not missing** — long form: each row populates only its own detector's columns |
| T4 / T5 | low | per-orbit coverage |

**Every missing value is explicit NaN with an accompanying quality flag.** There is no silent zero-fill anywhere, verified by AST scan and unit tests. Consumers must handle NaN deliberately — the dataset will not hide it.

## 5. Detector coverage

| Instrument | Detectors with science | Note |
|---|---|---|
| SoLEXS | **SDD2 only** | SDD1 supplies GTI only and is F-12 inactive archive-wide (426 detections) |
| HEL1OS | **CZT1, CZT2, CdTe1, CdTe2** | all four present; **two incommensurable channel spaces** (CZT 341, CdTe 511) |

**Binding rule for feature work:** never concatenate spectra across families or instruments — SoLEXS PI 340, CZT PHA 341, CdTe PHA 511 are three different spaces with no response matrix to relate them (F-4). Filter on `detchans`/`detector` first.

## 6. Provenance completeness

**Complete.** 5,199 provenance rows; **0 orphan rows, 0 duplicate entries, 0 rows missing provenance**, archive-wide. Every canonical row resolves to exactly one archive product with its SHA-256. Per-(minute, detector) ownership for HEL1OS is version-resolved and unique (1,065,572 owned pairs, F-15-guarded).

**Provenance columns are not features** and must not be used as such.

## 7. Archive-quality findings carried in

| Finding | Effect on ML |
|---|---|
| 12 SoLEXS days excluded (F-19 GTI defect) | absent from the dataset; no gap-filling |
| 2 HEL1OS orbits excluded (F-16 duplicate HK time) | as above |
| HK telemetry-order jitter (F-3) | T4 is **not chronologically sorted**; sort explicitly if needed |
| One 1153 s HK time jump | isolated anomaly in `HLS_20260617_121028` |
| GTI-exclusion excess (F-2) | `live_time_s` may exclude time that carries finite counts; mechanism unknown |
| 2023-12-13 lost; HEL1OS pre-2025-12 absent | acquisition gaps, not defects |

## 8. Remaining limitations (state these in any result)

1. **Combined-instrument span is 171 days.** The 2.4-year figure applies to SoLEXS alone.
2. **No energy calibration.** Channels are ordinal; no RMF/ARF exists. No keV claim is derivable, so no physical spectral-index or temperature quantity can be computed from this dataset.
3. **Severity labels are exogenous** (GOES-defined) and cannot be validated against Aditya flux.
4. **The light curve is band-limited**, not the total spectrum (F-1); `counts_total` and Σ(spectrum) are different quantities differing by a factor of 1.76–20.4.
5. **GTI-exclusion excess unexplained** (F-2) — `live_time_s` semantics are not fully characterised.
6. **13 X-class events** on combined days limits rare-class conclusions.
7. **SDD1 contributes nothing**; SoLEXS is effectively single-detector.
8. **Solar-cycle phase:** the span sits near solar maximum; nothing here supports cross-cycle generalisation.

## 9. Readiness verdict

| Criterion | Status |
|---|---|
| Data immutable & versioned | ✅ `AdityaNet_v2_dataset_r1`, hash `43fd0e22…` |
| Reproducible from raw archive | ✅ byte-identical, 12/12 sampled days |
| Provenance complete | ✅ 0 orphans / 0 duplicates / 0 missing |
| Missingness explicit | ✅ NaN + `q_*` flags, never imputed |
| Documented | ✅ every column (`DATA_DICTIONARY.md`) |
| Scientifically validated | ✅ all assumptions discharged (M-VIII) |
| Archive anomalies inventoried | ✅ `ARCHIVE_QUALITY_REPORT.md` |
| Labels available | ✅ external (GOES catalogue), counts §2 |
| Sufficient for combined-instrument ML | ⚠️ **171 days — scope-limited** |
| Sufficient for calibrated severity regression | ❌ **no RMF — not supported** |

**READY for feature engineering (Milestone X)** on both arms, subject to §8. The dataset is immutable, documented, reproducible, and validated; its limits are measured rather than assumed, and each one is traceable to evidence in `SCIENTIFIC_FINDINGS.md`.
