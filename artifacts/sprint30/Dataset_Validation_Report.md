<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Sprint 30 Phase 1 — dataset_v4.0.0 build and validation record. -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-11 -->

# Sprint 30 — Dataset Validation Report (dataset_v4.0.0)

**All 15 validation checks PASS (OBSERVED).** The Version 4 dataset at `artifacts/research_v4/dataset_v4.0.0/` carries the exact frozen split timestamps and targets, 17 features processed in the Sprint 28 order (physics on raw physical units → robust scaling fit on train only → normalized-space neutral imputation), per-timestep availability and staleness metadata, and a tamper-detecting provenance manifest. Builder: `scripts/sprint30/build_dataset_v4.py`; full machine-readable record: `artifacts/research_v4/dataset_v4.0.0/build_report.json`.

## Dataset statistics (OBSERVED)

| Split | Rows | Positives | Boundaries | Availability | Neutral-imputed |
|-------|------|-----------|------------|--------------|-----------------|
| train | 5,161,312 | 31,993 | 2010-01-02 00:30 .. 2019-12-31 23:59 | 1.000000 | 0 |
| validation | 1,568,759 | 63,849 | 2020-01-01 00:00 .. 2022-12-31 23:59 | 1.000000 | 0 |
| test | 1,806,673 | 419,150 | 2023-01-01 00:00 .. 2026-06-14 23:51 | 1.000000 | 0 |

Row and positive counts are byte-identical to the frozen `artifacts/research/*.parquet` splits (checks `*_timestamps_identical`, `*_targets_identical` below). The frozen source parquets contain zero NaN values (GOES gaps were handled at the original V1 build, kept unchanged per `03_DATASET_PIPELINE_V4.md` §2), so availability is 1.0 everywhere, all staleness values are 0, per-split quality score (§5 formula) is 1.0, and the neutral-imputation path processed 0 values.

## Validation check output (OBSERVED — builder exit gate)

```
  PASS  train_only_guard                       (TrainOnlyViolation raised on non-train fit)
  PASS  train_timestamps_identical
  PASS  train_targets_identical
  PASS  validation_timestamps_identical
  PASS  validation_targets_identical
  PASS  test_timestamps_identical
  PASS  test_targets_identical
  PASS  chronological_no_overlap               (train < validation < test, no boundary overlap)
  PASS  train_post_scale_median_zero
  PASS  train_post_scale_iqr_one_nondegenerate
  PASS  physics_T_in_inversion_range           (observed [4.630, 47.145] MK = analytic clipped-cubic range)
  PASS  physics_EM_finite
  PASS  physics_determinism_validation_split   (two independent computations, identical frame hash)
  PASS  manifest_verify_roundtrip
  PASS  manifest_tamper_detected               (mutated copy rejected with ManifestError)
```

Two checks were re-calibrated during the build after their first run flagged them; **the pipeline, scaler, and feature code were not modified** — only the assertion bounds:
1. `physics_T_in_inversion_range` originally asserted T ≤ 25 MK from a stale recollection; the Thomas-Starr-Crannell cubic's analytic range on the clipped domain is T(0.02) = 4.630 to T(0.7) = 47.145 MK, which the data exactly attains (DERIVED from the frozen coefficient set).
2. `train_post_scale_iqr_one` originally asserted post-scale IQR = 1 for all 17 features; two features have degenerate raw IQR = 0 on 2010–2019 train, for which the frozen Sprint 29 `RobustScaler` substitutes divisor 1.0 by specification (see Scaling report).

## Scaling report (OBSERVED)

Scaler: per-feature `(x − train_median) / train_IQR`, fit on the train split only (`app/services/ml/dataset_v4/scaling.py`; fitting on any other split raises `TrainOnlyViolation` — negative-control check passed). Full parameters frozen in `manifest.json:scaler_params`. Physics-feature parameters: `goes_T_iso` median 4.63004 MK / IQR 5.19797; `goes_EM` median 48.06808 (log10) / IQR 1.79362; `goes_dT_iso_15m` median 0.0 / degenerate IQR → divisor 1.0.

**Degenerate-IQR features (2 of 17, OBSERVED):** `minutes_since_last_flare` (raw median at its 10,080-minute cap with IQR 0 — the 2010–2019 train decade is quiet-sun-heavy) and `goes_dT_iso_15m` (exactly 0 whenever the channel ratio sits at the quiet-sun clip floor, which covers > 75% of train minutes). Both pass through center-shifted but magnitude-unscaled, the pre-registered `RobustScaler` fallback (Sprint 29, `tests/test_dataset_v4_infrastructure.py`). Their post-scale ranges are [−10,080, 0] and [−42.51, +42.51] respectively.

**Heavy tails (OBSERVED, expected):** robust scaling normalizes the bulk, not the extremes — post-scale maxima reach 3.7×10⁸ (`variance_15m`) and 5.4×10⁴ (`short_flux`) during flares. This is a property of flare statistics under the pre-registered pipeline, is representable in float32, and matches how the raw V1 pipeline also carried extreme dynamic range (raw fluxes spanned 10⁻⁹..10⁻³). No clipping or winsorization is applied — none is specified.

Post-scale train statistics (all 17 features): median ≈ 0 (< 10⁻⁶) for all; IQR = 1.000 for the 15 non-degenerate features. Full table in `build_report.json:train_post_scale_stats`.

## Feature statistics — physics features in physical units (OBSERVED, train split)

| Feature | Min | Max | Notes |
|---------|-----|-----|-------|
| `goes_T_iso` | 4.630 MK | 47.145 MK | both extremes are the clipped-domain analytic edges |
| `goes_EM` (log10) | 43.653 | 50.544 | finite on all rows; absolute calibration NOT PROVEN (proxy constant, flagged Sprint 29) — scaling-invariant for F1 |
| `goes_dT_iso_15m` | −42.51 MK | +42.51 MK | causal 15-minute backward difference |

## Missing-value report (OBSERVED)

Pre-scaling NaN count: 0 in every feature of every split. Post-scaling NaN count: 0. Neutral-imputation invocations: 0. The §2 gap policy (forward-fill ≤ 15 min, mask + neutral imputation beyond) is implemented and unit-tested but exercised zero times on this GOES-only dataset because the frozen sources are gap-free at grid level.

## Provenance report (OBSERVED)

`manifest.json` (canonical self-hash `5d9d0814ba0e41e6…`) pins: generator script hash; SHA-256 of all 7 source files (3 frozen parquets, `goes_physics.py`, `framework.py`, `scaling.py`, `feature_columns.json`); per-split row/positive counts; the full scaler parameter set with `fitted_on_split: "train"` (enforced — `build_manifest` rejects anything else); the 17-name feature list and its hash (`22b011c278ac460f…`). `verify_manifest` round-trip passed; a tamper test (mutating `fitted_on_split` in a copy) was correctly rejected. Per-feature code SHA-256 provenance from the features_v4 framework: `features_provenance.json`.

## Traceability

Split boundaries → `03_DATASET_PIPELINE_V4.md` §8; processing order → §6 steps 1–4; masks/staleness as metadata (not model inputs for the 17-feature F1 arm) → §1–§3 with §2's "GOES gaps keep the existing V1 handling unchanged"; quality score → §5; manifest → §7; feature definitions → `02_FEATURE_PIPELINE_V4.md` rows 1–3 (`goes_EM` stored as log10 per its row-2 definition); feature isolation/label exclusion → ADR-0001.
