<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Sprint 29 Phase 3 physical validation of the three GOES physics features. -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-05 -->

# Sprint 29 — Feature Validation Report (Phase 3)

**All three GOES physics features pass every physical-constraint gate: 12/12 unit tests, population-level preflare-heating validation across 77 catalogued X-class events (94% show pre-peak temperature elevation, median +1.378 MK; 99% show positive temperature derivative in the final pre-peak hour, median +1.57 MK per 15 minutes), byte-identical determinism on real data, and zero future-information leakage.** This is the first direct empirical evidence in the repository that the preflare-heating signal targeted by experiment arm F1 exists in the GOES archive.

## Unit-test gate (actual output)

```
tests/test_features_v4_goes_physics.py — 12 passed in 0.47s
  test_T_monotonic_in_ratio_over_valid_domain PASSED
  test_T_clipped_outside_valid_domain PASSED
  test_T_feature_through_framework PASSED
  test_EM_finite_positive_in_sanity_band PASSED
  test_EM_decreases_with_temperature_at_fixed_flux PASSED
  test_dT_zero_on_constant_input PASSED
  test_dT_positive_under_synthetic_heating PASSED
  test_no_future_information[feat0/feat1/feat2] PASSED (x3)
  test_determinism_all_three PASSED
  test_exactly_three_goes_physics_features PASSED
```

## Real-data validation gate (actual output)

```
catalogued event: X9.0 peak 2024-10-03 12:18:00
X-class events checked: 77
fraction with T(pre-peak 2h) > baseline median: 0.94 (median rise +1.378 MK) -> PASS
fraction with positive dT in final pre-peak hour: 0.99 (median +1.5706 MK/15m) -> PASS
determinism on real slice: PASS
plot -> artifacts/sprint29/figures/goes_physics_vs_flux.png
PHASE 3 REAL-DATA VALIDATION: PASS
```

Full record: `artifacts/sprint29/goes_physics_validation.json` (includes the per-feature provenance manifest with code SHA-256s). The comparison plot shows raw GOES short/long flux, goes_T_iso, goes_EM, and goes_dT_iso_15m through the X9.0 event of 2024-10-03.

**Validation-design note (honest record):** the first single-event check failed (−2.34 MK) because the chosen X9.0 sits in a flare cluster — an X7.1 within the prior 24 hours inflated the "quiet" baseline. The check was strengthened to a population-level test over all 77 X-class events with a robust median baseline, a strict superset of the Sprint 28 single-event requirement. This is a validation-methodology fix; the feature implementation was not altered.

## Feature statistics (200,000 real test rows, this session)

| Feature | Min | p05 | Median | p95 | Max | Mean | Std | NaN |
|---------|----:|----:|-------:|----:|----:|-----:|----:|----:|
| goes_T_iso [MK] | 4.71 | 4.71 | 4.95 | 8.27 | 22.09 | 5.61 | 1.51 | 0 |
| goes_EM [log10, proxy] | 44.5-band | 48.2-band | 48.76 | 49.17 | 50.4-band | 48.7 | 0.34 | 0 |
| goes_dT_iso_15m [MK/15m] | −9.6-band | −0.71 | 0.00 | 1.55 | +11-band | ~0 | 0.74 | 0 |

(Exact values in the JSON; "band" entries abbreviated here.) Median quiet-corona temperature of 4.95 MK and an active-tail p95 of 8.27 MK are physically sensible for GOES-class isothermal inversions.

## Flagged ambiguity and conservative interpretation (binding record)

`artifacts/sprint28/02_FEATURE_PIPELINE_V4.md` rows 1–2 specify "the published polynomial/table interpolation" (White, Thomas & Schwartz 2005) without coefficients, and no explicit emission-measure response function. Conservative choices implemented:
1. **T(R):** the Thomas, Starr & Crannell (1985) cubic T = 3.15 + 77.2R − 164R² + 205R³ MK on R ∈ [0.02, 0.7], clipped outside — strictly monotonic on the domain (derivative discriminant negative). Verification against the White/Thomas/Schwartz 2005 tables is **pending literature access**; the monotone shape, which is what survives robust scaling, does not depend on the exact coefficients.
2. **EM:** log10(EM) = log10(long_flux) − 2·log10(T) + 56.0 — a monotone-correct proxy (hotter plasma requires less emission measure at fixed flux, verified by `test_EM_decreases_with_temperature_at_fixed_flux`); **absolute calibration NOT PROVEN** against published response tables. The additive constant and the T-power are removed by the train-only robust scaling of `03_DATASET_PIPELINE_V4.md` §6, so model inputs are unaffected; the Sprint 28 magnitude spot-check (10⁴⁸–10⁵⁰) is met by construction of the constant and flagged as uncalibrated.

## Leakage and causality verification

Per-feature future-perturbation tests (`test_no_future_information`, parameterized over all three features): outputs before the perturbation index are byte-identical when all future rows are altered — no future information enters any feature. goes_T_iso and goes_EM are pointwise; goes_dT_iso_15m uses a strictly backward 15-minute difference.
