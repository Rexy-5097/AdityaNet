<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Sprint 31 Phase 1 — dataset_v4.1.0-s2 build and validation record. -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-11 -->

# Sprint 31 — Dataset Report (dataset_v4.1.0-s2)

**All 18 builder validation checks PASS and all 7 code-level Phase 2 verification categories completed (5 PASS; 2 flagged items are data findings, not pipeline defects — detailed below). The F2 dataset at `artifacts/research_v4/dataset_v4.1.0-s2/` carries the exact frozen Stage-2 split timestamps and targets, the complete 32-feature Version 4 input set (GOES 17 + SoLEXS 10 + HEL1OS 5 per `02_FEATURE_PIPELINE_V4.md` — no additions, no omissions), four per-timestep availability/staleness disclosure channels, train-only robust scaling, and a tamper-detecting provenance manifest.** Builder: `scripts/sprint31/build_dataset_v4_s2.py`; machine-readable: `build_report.json`; independent code verification: `phase2_feature_validation.{json,md}` (subagent, parallel with the build).

## Splits (OBSERVED — identical to frozen `artifacts/sprint14c/s2_*.parquet`)

| Split | Rows | Positives (rate) | Boundaries |
|-------|------|------------------|------------|
| train | 786,298 | 246,514 (31.35%) | 2023-12-13 00:00 .. 2025-06-14 23:59 |
| validation | 262,480 | 43,703 (16.65%) | 2025-06-15 00:00 .. 2025-12-14 23:59 |
| test | 261,455 | 31,113 (11.90%) | 2025-12-15 00:00 .. 2026-06-14 23:51 |

Timestamps and both target columns verified byte-identical to the frozen sources; chronological non-overlap verified. The test span matches the pre-registered S2 pairing span exactly (`F0.json:spans.test_s2_pairing`: 2025-12-15..2026-06-14; 261,095 windows).

## Builder validation output (OBSERVED)

```
PASS train_only_guard (TrainOnlyViolation raised)     PASS hr_ratios_positive
PASS train_timestamps_identical                       PASS active_fraction_in_01
PASS train_targets_identical                          PASS minutes_since_active_in_cap
PASS validation_timestamps_identical                  PASS fluences_nonnegative
PASS validation_targets_identical                     PASS disclosure_channels_in_01
PASS test_timestamps_identical                        PASS aditya_features_deterministic
PASS test_targets_identical                           PASS manifest_verify_roundtrip
PASS chronological_no_overlap                         PASS manifest_tamper_detected
PASS train_post_scale_median_zero_low_imputation_cols
PASS train_post_scale_iqr_one_nondegenerate_low_imputation
```

## Phase 2 independent verification (subagent; OBSERVED)

| Check | Result |
|-------|--------|
| Formula conformance, all 15 Aditya features vs spec (independent reimplementation) | PASS — max abs diff 0.0, NaN placement identical |
| Causality (truncation invariance over first 100,000 rows) | PASS — all features identical; nothing looks forward |
| No label access (`requires` audit + framework guard) | PASS |
| Determinism (two full computations) | PASS |
| Train-only activity threshold provenance (p95 = 7.599854, train observed minutes only) | PASS |
| Physical ranges | FLAGGED: `solexs_HR_high_low`/`_mid_low` equal exactly 0 on 0.92% of observed minutes (the high/mid bands record zero counts in quiet sun). The ε-guarded spec formula yields 0 when the numerator is 0 — a valid physical value ("no hard emission"), so the check's "strictly positive" expectation was stricter than the spec. No pipeline change. All other ranges nominal (HR max 28.2 ≤ 100; fractions ∈ [0, 0.308]; caps honored). |
| Flare response | FLAGGED DATA FINDING: at the 20 highest GOES long-flux observed minutes (two ~M5 events), only 30%/40% exceed the split-median `solexs_HR_high_low`/`log_solexs_soft` — SoLEXS shows no co-temporal hardening/brightening at GOES flare peaks. Formula conformance is exact, so this is an instrument-data property, consistent with Sprint 27's conditional-information-zero audit. Carried to `Scientific_Conclusion.md`. |

## Missing-data handling and the §2 gap policy (OBSERVED — full detail in `Missing_Data_Report.md`)

The Sprint 27 defect is confirmed in the raw sources and fixed here: masked minutes are zero-filled in `s2_*.parquet` (SoLEXS rates read 0.0 where `mask_solexs`=0 while real rates never fall below 150). The V4 build NaN-s those minutes, forward-fills ≤ 15 minutes, and discloses via channels. Measured structure: SoLEXS unavailability (24.37% of train minutes) consists of 145,006 micro-gaps — median run 1 minute, p99 = 4, maximum 9 — so 100% of masked minutes fall inside the ≤15-minute fill regime; post-fill availability 99.9997%, mean staleness 0.32 min. HEL1OS: 191 isolated 1-minute gaps (99.98% available). Neutral imputation therefore processed only 48/32/40 cells (train/validation/test) — leading-edge derivative NaNs. Consequence flagged for Phase 5: per-window availability is nearly homogeneous, so availability stratification may be degenerate; it will be reported as measured.

## Model input construction (32 + 4 = 36 channels; flagged interpretation)

The 32 scaled features are the `02_FEATURE_PIPELINE_V4.md` model-input list. Per `03_DATASET_PIPELINE_V4.md` §3 ("per instrument, two per-timestep channels appended to the model input") the SoLEXS and HEL1OS `available_t` (binary) and `staleness_t/60` channels are appended as model inputs — carrying §3's own normalization, not robust-scaled. GOES receives no disclosure channels per §2's "GOES gaps … keep the existing V1 handling unchanged." F2 model width: 36. This resolves the 32-vs-§3 surface tension conservatively in favor of §3's motivating finding (Sprint 27: masks were created and discarded; zero-fill indistinguishable from data) — excluding the channels would rebuild the exact defect Version 4 exists to fix.

## Scaling and provenance (OBSERVED)

RobustScaler fit on s2_train only (guard verified); scaler parameters, source SHA-256 list (3 frozen parquets + 5 code files + feature list), split counts, and canonical self-hash in `manifest.json` (verify + tamper-detection both pass). Per-feature code SHA-256 and the frozen p95 threshold in `features_provenance.json`. Post-scale train stats: median ≈ 0 and IQR = 1 for all low-imputation, non-degenerate columns; near-constant channels (HEL1OS-derived) show extreme post-scale tails (documented in `Feature_Distribution_Report.md`) — a data property under the pre-registered scaler, not adjusted.
