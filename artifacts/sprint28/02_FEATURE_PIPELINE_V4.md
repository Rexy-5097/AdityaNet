<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Sprint 28 Version 4 feature pipeline specification. -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-05 -->

# Sprint 28 — Version 4 Feature Pipeline Specification (Task 2)

**Dispositions: KEEP 14 · MODIFY 10 · REMOVE 12 · NEW 17. Net feature space: 36 current model inputs → 32 Version 4 model inputs (minus 4 columns), while the number of physically distinct quantities rises from roughly 5 (two GOES fluxes plus their derived family, one effective SoLEXS amplitude, one effective HEL1OS amplitude, flare recency) to roughly 15.** Every disposition traces to `artifacts/sprint27/02_FEATURE_VALUE_ANALYSIS.md` classifications and every NEW feature to a named physics group in `artifacts/sprint27/04_SOLAR_PHYSICS_RECOMMENDATIONS.md`; constructs Sprint 27 did not support (for example magnetogram-based proxies) are absent.

## Current-feature dispositions

### GOES (14 features) — KEEP ×14
`short_flux, long_flux, log_long_flux, mean_15m, variance_15m, mean_60m, variance_60m, peak_30m, peak_60m, flux_gradient_5m, flux_gradient_15m, flux_acceleration_5m, flux_acceleration_15m, minutes_since_last_flare` — all KEEP unchanged. Evidence: this is the proven skill-carrying set (`artifacts/information_gap_report.json`: removing engineered/history features collapses True Skill Score to 0.0), and Version 4 comparability to the Sprint 24 frozen baselines requires it intact.

### SoLEXS (18 features) — MODIFY ×9, REMOVE ×9
- `solexs_rate_ch1 … solexs_rate_ch9` — **MODIFY ×9**: no longer direct model inputs; retained upstream solely as the raw inputs from which the NEW derived constructs below are computed (soft-band aggregate, hardness ratios, variability, activity-memory). Modification stated precisely: the nine columns are consumed by the feature builder and do not appear in the model feature list. Evidence: UNKNOWN classification with conditional information 0.0 (`artifacts/sprint27/02_FEATURE_VALUE_ANALYSIS.md`); adjacent-channel redundancy 0.95–0.99 (`artifacts/aditya_l1/solexs_channel_redundancy.json`).
- `solexs_counts_ch1 … solexs_counts_ch9` — **REMOVE ×9**: r = 0.847–0.867 with their rate twins; residual variance is exposure bookkeeping (`02_FEATURE_VALUE_ANALYSIS.md`, computed on `artifacts/sprint14c/s2_val.parquet`).

### HEL1OS (4 features) — MODIFY ×1, REMOVE ×3
- `hel1os_rate_band0` — **MODIFY**: replaced as input by `log_hel1os_band0 = log1p(hel1os_rate_band0)`; the raw column remains upstream input to fluence and ratio constructs. Evidence: no transform exists anywhere in the pipeline (Sprint 27 grep) against a physics expectation of log-domain scale (Crosby, Aschwanden & Dennis 1993 power-law flare statistics; `04_SOLAR_PHYSICS_RECOMMENDATIONS.md` G7).
- `hel1os_rate_band1` — **REMOVE**: r = 0.9911 with band0 (computed in Sprint 27).
- `hel1os_counts_band0`, `hel1os_counts_band1` — **REMOVE ×2**: REDUNDANT classification (r ≈ 0.955 with rate twins).

## NEW features (17)

| # | Feature | Instrument | Physics principle (named) | Implementation formula/procedure | Validation test |
|---|---------|-----------|---------------------------|----------------------------------|-----------------|
| 1 | `goes_T_iso` | GOES | Isothermal temperature from the two-channel ratio (White, Thomas & Schwartz 2005, *Solar Physics* 227, 231) | R(t) = short_flux/long_flux, clipped to the inversion's valid domain; T via the published polynomial/table interpolation | Monotonicity of T in R over the valid domain; on a catalogued X-class event in `artifacts/research/flares_full.parquet`, T rises before the GOES peak |
| 2 | `goes_EM` | GOES | Emission measure from long-channel flux at the inverted T (same reference) | EM = long_flux / f(T) with f from the same inversion; stored as log10(EM) | EM positive and finite on all valid rows; spot-check magnitude ~10⁴⁸–10⁵⁰ cm⁻³ during M-class events |
| 3 | `goes_dT_iso_15m` | GOES | Preflare/precursor heating phase (Benz 2017, *Living Reviews in Solar Physics* 14, 2) | Centered-free 15-minute backward difference of goes_T_iso | Zero on constant-T synthetic input; positive during synthetic linear heating |
| 4 | `solexs_HR_high_low` | SoLEXS | Thermal-bremsstrahlung spectral hardening as temperature proxy | Σ(rate_ch7..ch9)/Σ(rate_ch1..ch3), computed on physical rates, ε-guarded | Bounded positive; rises during catalogued flare intervals in the Stage-2 corpus |
| 5 | `solexs_HR_mid_low` | SoLEXS | Same principle, mid-band | Σ(rate_ch4..ch6)/Σ(rate_ch1..ch3) | As #4 |
| 6 | `solexs_dHR_15m` | SoLEXS | Soft-hard-soft spectral evolution (Grigis & Benz 2004, *Astronomy & Astrophysics* 426, 1093) | 15-minute backward difference of solexs_HR_high_low | Zero on constant input |
| 7 | `solexs_HR_peak_60m` | SoLEXS | Same; impulsive-phase memory | Rolling 60-minute max of solexs_HR_high_low | Equals current value on monotone series |
| 8 | `log_solexs_soft` | SoLEXS | Log-domain flux scaling (Crosby, Aschwanden & Dennis 1993) | log1p(Σ rate_ch1..ch9) | Finite on all rows incl. masked zeros |
| 9 | `solexs_variance_15m` | SoLEXS | Preflare small-scale energy-release intermittency (avalanche statistics, same reference) | Rolling 15-min variance of log_solexs_soft | Matches numpy reference on synthetic data |
| 10 | `solexs_variance_60m` | SoLEXS | Same | Rolling 60-min variance | Same |
| 11 | `solexs_peak_30m` | SoLEXS | Same; recent maximum brightening | Rolling 30-min max of log_solexs_soft | Same |
| 12 | `minutes_since_solexs_active` | SoLEXS | Flare waiting-time clustering (Wheatland 2000, *Astrophysical Journal* 536, L109) | Minutes since log_solexs_soft last exceeded its train-split 95th percentile; capped 10,080 (mirror of GOES `minutes_since_last_flare` cap, `app/services/ml/config.py`) | Resets to 0 at synthetic threshold crossing; cap honored |
| 13 | `solexs_active_fraction_6h` | SoLEXS | Same | Fraction of trailing 360 min above the same percentile | ∈[0,1]; 1.0 on always-active synthetic input |
| 14 | `hel1os_fluence_30m` | HEL1OS | Neupert effect — SXR rise tracks time-integrated HXR (Neupert 1968, *ApJL* 153, L59; chromospheric evaporation, Fisher, Canfield & McClymont 1985) | Trailing 30-min sum of hel1os_rate_band0 × Δt, masked minutes excluded, log1p-stored | Equals analytic integral on synthetic boxcar burst |
| 15 | `hel1os_fluence_60m` | HEL1OS | Same | Trailing 60-min integral | Same |
| 16 | `nonthermal_thermal_ratio` | HEL1OS + GOES | Thermal vs non-thermal emission separation (>20 keV thick-target vs XRS thermal band; Benz 2017) | hel1os_rate_band0 / long_flux, ε-guarded, log1p-stored | Spikes on synthetic HXR-burst-with-flat-SXR input |
| 17 | `d_ntr_15m` | HEL1OS + GOES | Particle-acceleration onset precedes thermal peak (same principle + Neupert timing) | 15-minute backward difference of #16 | Zero on constant input |

## Version 4 model input list (32)

GOES 17 = the 14 KEEP + features 1–3. SoLEXS 10 = features 4–13. HEL1OS 5 = features 8-independent set 14–17 plus `log_hel1os_band0` (the MODIFY output). All engineered in physical units first, then log/normalization per the Task 3 ordering (`03_DATASET_PIPELINE_V4.md`).

## Explicitly absent

Magnetic-energy proxies (no magnetogram source exists — `artifacts/sprint27/04_SOLAR_PHYSICS_RECOMMENDATIONS.md` "Explicitly not recommended"); any raw SoLEXS/HEL1OS spectral channel as a direct input (redundancy evidence above); any feature whose only support would be general domain knowledge rather than a Sprint 27-named principle.
