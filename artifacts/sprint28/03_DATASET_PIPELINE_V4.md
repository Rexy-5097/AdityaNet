<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Sprint 28 Version 4 dataset pipeline specification. -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-05 -->

# Sprint 28 — Version 4 Dataset Pipeline Specification (Task 3)

**The change a reviewer asks about first: Version 4 replaces the label-minute scalar mask and silent zero-fill with per-timestep availability channels plus normalized-space neutral imputation — because Sprint 27 proved the current loader discards the per-minute masks the builder correctly creates (`app/services/ml/dataset_v3.py:110-111` versus `scripts/build_multi_instrument_dataset.py:114,120`) and feeds the model zeros indistinguishable from data for 24.4% of SoLEXS minutes inside "available" windows.** Every choice below cites its motivating finding.

## 1. Temporal alignment protocol — KEPT, one addition
Left-merge of instrument streams onto the 1-minute GOES timestamp grid, rates resampled by mean and counts by sum, exactly as today (`build_multi_instrument_dataset.py:48-50,108`) — Sprint 27 found alignment correct at grid level; the failure was semantic (zero-fill), not temporal. Addition: the merge records a per-minute `staleness` counter per instrument (minutes since the last genuinely observed sample, capped at 60) so downstream consumers can distinguish fresh from forward-filled values.

## 2. Missing-data rules — impute with disclosure, reject at threshold
- Gaps ≤ 15 minutes: forward-fill the physical value; the staleness channel discloses the fill age. Rationale: SoLEXS availability is 75.60% (computed in Sprint 27 on `artifacts/sprint14c/s2_val.parquet`) — outright rejection of any gap would discard a large fraction of windows, and short gaps in slowly varying thermal emission are physically interpolable (the same reasoning behind the existing GOES NaN forward-fill in `app/services/ml/inference.py`).
- Gaps > 15 minutes: timesteps marked mask=0 and imputed with the **normalized-space neutral value 0 (the train-split median after robust scaling)** — never the physical zero that Sprint 27 identified as out-of-manifold (real SoLEXS rates never go below 150; `artifacts/sprint27/01_ADITYA_FEATURE_AUDIT.md` §2).
- Window-level rejection threshold: if an instrument's within-window availability fraction is below **0.5**, that instrument is declared missing for the window and the model's missing-token path is used. The 0.5 value is a pre-registered pipeline constant; its optimality is `NOT PROVEN` and it is subjected to the sensitivity check in `04_FAIR_ADITYA_EXPERIMENT.md`. GOES gaps (0.23% rate, `artifacts/research_dataset_report.json`) keep the existing V1 handling unchanged for baseline comparability.

## 3. Mask and availability-channel construction
Per instrument, two per-timestep channels appended to the model input: binary `available_t` (from the builder's per-minute masks, `build:114,120` — now actually consumed) and `staleness_t/60`. Window-level scalars derived from them: `availability_fraction` (drives the §2 rejection rule and the model missing-token blend, replacing the label-minute scalar of `dataset_v3.py:110-111`). Motivation: Sprint 27 loss points 3–4; `artifacts/sprint27/05_FUSION_LIMITATIONS.md` limitation 3 (mask granularity is a loader defect, not a fusion defect).

## 4. Windowing parameters — unchanged, justified
360-minute input windows, label = `target_6hr_binary` at the window-end row, stride 1 for training sampling: locked to the forecast horizon (`app/services/ml/config.py` FORECAST_HORIZON_MINUTES=360) and to comparability with the frozen Sprint 24 evaluation harness and its episode construction (`artifacts/sprint24/01_evaluation_framework.md`). Changing windowing would invalidate every baseline the fair test depends on.

## 5. Quality score
Per window and instrument: `quality = availability_fraction × (1 − mean(staleness_t)/60)`, stored in dataset metadata (not a model input in Version 4.0) to enable the availability-stratified evaluation required by `04_FAIR_ADITYA_EXPERIMENT.md` §Stratification — the response to the operational-availability concern (SoLEXS down one quarter of the time) recorded in `07_EXTERNAL_REVIEW.md`.

## 6. Processing order (normalization AFTER physics, scaling fit on train only)
1. Physical-domain feature engineering first — ratios, temperature/emission-measure inversion, fluence integrals computed on raw physical units (`artifacts/sprint28/02_FEATURE_PIPELINE_V4.md` formulas require physical values; a ratio of normalized quantities is physically meaningless).
2. Log transforms where the feature spec says so (G7 principle).
3. Robust standardization (median/interquartile range) per feature, **fit on the training split only** and frozen into the dataset manifest — the leakage discipline is non-negotiable given this repository's history (`artifacts/sprint22_5/FINAL_VERDICT.md`; Sprint 23 gates).
4. Masked-timestep imputation with the normalized-space neutral value (§2), guaranteeing imputed values sit at the distribution center rather than the out-of-manifold physical zero (Sprint 27 loss point 3).

## 7. Dataset versioning
`dataset_v4.<major>.<minor>` directories under `artifacts/research_v4/`, each carrying a Sprint 23-style provenance manifest: the 13 mandatory fields of `app/services/ml/policy.py` REQUIRED_PROVENANCE_FIELDS adapted to datasets (generator script hash, source-file SHA-256 list, row/positive counts per split, scaler parameters, feature list hash, self-hash), enforced by the same load-time gate pattern. Motivation: requirement M3 (`artifacts/sprint27/07_VERSION4_REQUIREMENTS.md`); the V3 lesson that unfingerprinted artifacts invite silent corruption (`artifacts/sprint22_5/02_threshold_provenance.md`).

## 8. Split policy
Chronological splits identical in boundaries to the frozen ones — V1-era splits for GOES-only arms (train 2010–2019, validation 2020–2022, test 2023–2026) and Stage-2 boundaries for Aditya arms (`artifacts/sprint14c/s2_*.parquet` dates) — so every Version 4 number remains paired-comparable to the frozen Sprint 24 and sprint14c records. New splits require an ADR plus new leakage audits per the standing rule (`context/workflow.md` Rule 2).
