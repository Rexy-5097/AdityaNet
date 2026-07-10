<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Sprint 27 physics-derived feature recommendations, each tied to a named solar physics principle. -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-05 -->

# Sprint 27 — Solar Physics Feature Recommendations (Q4)

**Total: 18 recommended new features in 7 physics groups — 3 requiring only GOES, 9 requiring SoLEXS, 4 requiring HEL1OS (2 jointly with a soft-X-ray reference), and 2 requiring either instrument's processed stream.** The highest-priority group overall (G1) needs no Aditya-L1 data at all and can be validated on the full 16-year GOES archive; the highest-priority Aditya-specific group is G2 (SoLEXS spectral hardness dynamics). Every recommendation names its motivating principle; none duplicates an existing construct in `artifacts/feature_columns_v3.json`.

## Physical meaning of the current features (baseline for "not already captured")

GOES: two broadband soft-X-ray irradiances (0.05–0.4 nm, 0.1–0.8 nm) plus log, rolling means/variances (15/60 min), peaks (30/60 min), first and second time derivatives (5/15 min), and flare-history recency — i.e., *amplitude, trend, and memory of integrated thermal coronal emission*, with **no spectral information** (the two-channel ratio is never formed) and **no temperature/emission-measure physics**. SoLEXS: nine instantaneous soft-X-ray channel rates plus nine count duplicates — *spectral amplitude with no dynamics, no ratios*. HEL1OS: two hard-X-ray band rates plus duplicates — *amplitude only*. (`artifacts/feature_columns_v3.json`; `app/services/ml/features.py`.)

## Recommended features

### G1 — Isothermal temperature and emission measure from the GOES channel ratio (3 features; GOES only) — HIGHEST PRIORITY
`T_iso(t)`, `EM(t)`, `dT_iso/dt` (15-minute derivative). **Principle:** under the isothermal assumption, the ratio of the GOES 0.05–0.4 nm to 0.1–0.8 nm channels is a monotonic function of plasma temperature, and the absolute fluxes then yield emission measure — the standard GOES T/EM inversion (White, Thomas & Schwartz 2005, *Solar Physics* 227, 231; earlier Garcia 1994). Preflare coronal heating manifests as rising T before the impulsive phase (preflare/precursor phase in the standard flare picture — Benz 2017, *Living Reviews in Solar Physics* 14, 2). The repository has both channels in every window and has never formed their ratio — the cheapest untested physics in the project, testable on all 16 years with the existing V1 pipeline.

### G2 — SoLEXS spectral hardness dynamics (4 features; SoLEXS) — HIGHEST-PRIORITY ADITYA-SPECIFIC
`HR_solexs(t)` = (sum of upper-third channel rates)/(sum of lower-third channel rates); `dHR/dt` (15 min); `HR_peak_60m`; a second ratio splitting mid/low bands. **Principle:** thermal bremsstrahlung spectral shape hardens with temperature, so multi-channel hardness ratios are temperature proxies at finer resolution than the GOES 2-band ratio; the soft–hard–soft spectral evolution of flares (Grigis & Benz 2004, *Astronomy & Astrophysics* 426, 1093) makes hardness *dynamics* an eruption-phase indicator. Replaces nine redundant raw channels (adjacent-channel r=0.95–0.99, `artifacts/aditya_l1/solexs_channel_redundancy.json`) with the quantity a physicist would actually read off the spectrum. The audits' own compressions (`hard_soft_ratio` in `artifacts/aditya_l1/compression_generalization.json`) prototype this but never entered the model feature set.

### G3 — Neupert-effect fluence features (2 features; HEL1OS) 
`HXR_fluence_30m`, `HXR_fluence_60m` — trailing time-integrals of the HEL1OS hard-X-ray band rate. **Principle:** the Neupert effect (Neupert 1968, *Astrophysical Journal Letters* 153, L59): soft X-ray flux rises approximately as the time integral of the hard X-ray burst, because non-thermal electrons deposit energy that drives chromospheric evaporation (Fisher, Canfield & McClymont 1985). Accumulated HXR fluence is therefore a physically grounded proxy for energy already deposited — a *leading* quantity for the thermal response, which the instantaneous `hel1os_rate_band0` cannot represent.

### G4 — Non-thermal/thermal ratio (2 features; HEL1OS + soft-X-ray reference)
`NT_ratio(t)` = HEL1OS band rate / GOES long-channel flux; `d(NT_ratio)/dt`. **Principle:** thermal versus non-thermal emission separation — emission above ~20 keV in the impulsive phase is dominated by non-thermal thick-target bremsstrahlung while GOES XRS (~1.5–12 keV) is thermal (Benz 2017 review); a rising non-thermal fraction flags particle acceleration onset before the thermal peak. GOES alone cannot form this ratio; it is the sharpest statement of what HEL1OS could uniquely contribute.

### G5 — Multi-timescale variability of SoLEXS soft channels (3 features; SoLEXS)
`solexs_variance_15m`, `solexs_variance_60m`, `solexs_peak_30m` on the summed soft-band rate. **Principle:** preflare small-scale energy release — elevated intermittent brightening/microflaring preceding major flares reflects the intermittency of magnetic energy release, consistent with avalanche/self-organized-criticality flare statistics (power-law flare energy distribution — Crosby, Aschwanden & Dennis 1993, *Solar Physics* 143, 275). These mirror exactly the GOES engineered class that `artifacts/information_gap_report.json` proved dominant, applied to the instrument stream that never received it.

### G6 — Aditya activity-memory features (2 features; SoLEXS or HEL1OS)
`minutes_since_solexs_active` (time since soft-band rate exceeded a validation-calibrated activity percentile) and trailing `active_fraction_6h`. **Principle:** flare waiting-time statistics and activity clustering — flares cluster in time following (piecewise) Poisson statistics with slowly varying rate (Wheatland 2000, *Astrophysical Journal* 536, L109), which is why `minutes_since_last_flare` dominates the GOES set; an instrument-native analogue provides the same memory without depending on the external GOES flare catalog.

### G7 — Log-domain rescaling of all Aditya amplitude features (2 features counted: `log_solexs_soft`, `log_hel1os_band`; plus preprocessing of the rest)
**Principle:** flare energies and X-ray fluxes are distributed over decades following power laws (Crosby, Aschwanden & Dennis 1993), so the natural feature scale is logarithmic — the GOES set already encodes this (`log_long_flux`); the Aditya set does not (raw ranges 150–134,030 measured this session with no transform anywhere in the pipeline, `01_ADITYA_FEATURE_AUDIT.md` §4).

## Explicitly not recommended

Magnetic energy storage proxies (free magnetic energy, shear, polarity-inversion-line gradients — the strongest known flare precursors, e.g. Schrijver 2007, *Astrophysical Journal* 655, L117) **cannot be built**: no magnetogram data source exists in this repository (`PROJECT_STATUS.md` instruments inventory — GOES XRS, SoLEXS, HEL1OS only). Recorded so V4 scoping knows the ceiling of X-ray-only forecasting is a data limitation, `NOT PROVEN` addressable with current instruments.

## Priority order for the campaign (feeds Q6)

1. **G1** (GOES T/EM) — zero Aditya dependency, full 16-year archive, existing V1 pipeline, answers "feature engineering vs instrument addition" directly.
2. **G2 + G7 + deduplication** (SoLEXS hardness dynamics on logged, deduplicated inputs) — the fair test of SoLEXS that has never been run.
3. **G3 + G4** (HEL1OS Neupert fluence and non-thermal ratio) — the fair test of HEL1OS.
4. **G5, G6** — second wave, after 1–3 report.
