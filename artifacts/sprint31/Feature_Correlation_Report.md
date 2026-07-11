<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Sprint 31 Phase 1 — correlation structure of the 32 Version 4 features. -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-11 -->

# Sprint 31 — Feature Correlation Report (dataset_v4.1.0-s2, train split)

**Two findings, both OBSERVED on a 200,000-row train sample (full matrix: `artifacts/sprint31/feature_correlation_matrix.csv`): (1) exactly one new feature is a near-duplicate of GOES information — `nonthermal_thermal_ratio` at r = −0.940 with `log_long_flux`; (2) every other Aditya-L1 feature is nearly orthogonal to the entire GOES-17 set (maximum |r| ≤ 0.045). The Sprint 27 duplicate-channel pathology (12 of 22 raw inputs at r = 0.85–0.99 with GOES) is eliminated by the engineering — the new feature set is either genuinely complementary information or uncorrelated noise, and only the sealed F2 evaluation can distinguish the two.**

## Pairs with |r| > 0.90 (the deduplication check)

| Pair | r | Reading |
|------|---|---------|
| `log_long_flux` ~ `nonthermal_thermal_ratio` | −0.940 | HEL1OS band0 is nearly constant, so log1p(band0/long_flux) ≈ const − log(long_flux): the ratio's variance is carried almost entirely by its GOES denominator. The feature is retained — it is pre-registered (row 16) and the governing rules forbid post-hoc omission — but its incremental content is structurally limited. OBSERVED. |
| `short_flux` ~ `long_flux` | +0.937 | Pre-existing GOES pair, present since V1; unchanged. OBSERVED. |

No SoLEXS-internal pair exceeds 0.90: the hardness ratios, variability, activity-memory, and log-soft aggregate separate cleanly (the raw nine channels' 0.95–0.99 adjacent-channel redundancy documented in Sprint 27 does not propagate into the engineered constructs).

## Cross-instrument orthogonality (maximum |r| of each Aditya feature against all 17 GOES features)

| Feature | max \|r\| | vs | | Feature | max \|r\| | vs |
|---------|-----------|-----|-|---------|-----------|-----|
| solexs_HR_high_low | 0.005 | mean_60m | | solexs_peak_30m | 0.017 | log_long_flux |
| solexs_HR_mid_low | 0.003 | goes_dT_iso_15m | | minutes_since_solexs_active | 0.006 | minutes_since_last_flare |
| solexs_dHR_15m | 0.004 | flux_acceleration_15m | | solexs_active_fraction_6h | 0.045 | mean_60m |
| solexs_HR_peak_60m | 0.020 | goes_EM | | hel1os_fluence_30m | 0.010 | log_long_flux |
| log_solexs_soft | 0.011 | log_long_flux | | hel1os_fluence_60m | 0.010 | mean_60m |
| solexs_variance_15m | 0.006 | log_long_flux | | nonthermal_thermal_ratio | **0.940** | log_long_flux |
| solexs_variance_60m | 0.016 | short_flux | | d_ntr_15m | 0.458 | goes_dT_iso_15m |
| | | | | log_hel1os_band0 | 0.011 | goes_EM |

**Interpretation discipline (labeled):** OBSERVED — the SoLEXS engineered features share essentially zero linear structure with GOES. DERIVED — this is a necessary condition for incremental value but nowhere near sufficient: if the SoLEXS signal were solar, it should correlate at least weakly with GOES soft X-ray activity (both instruments watch the same Sun), and the Phase 2 flare-response finding (no SoLEXS hardening/brightening at the two strongest GOES peaks in s2_val) points the same troubling direction as Sprint 27's conditional-mutual-information-zero audit. NOT PROVEN either way at this stage — this is precisely what the sealed F2-vs-F1 comparison measures.
