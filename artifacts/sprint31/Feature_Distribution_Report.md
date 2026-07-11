<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Sprint 31 Phase 1 — post-scaling distribution audit of the 32 Version 4 features. -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-11 -->

# Sprint 31 — Feature Distribution Report (dataset_v4.1.0-s2, train split)

**All 15 new Aditya-L1 features scale correctly (median 0, IQR 1 post-scaling — OBSERVED) and none is constant or degenerate. Two structural findings matter downstream: (1) the HEL1OS-derived features ride on a nearly constant instrument channel, giving them extreme post-scale tails; (2) the SoLEXS activity features behave sensibly against their train-only threshold. Full numbers: `artifacts/sprint31/feature_distribution_stats.json`.**

Post-scale train statistics for the 15 new features (OBSERVED; median/IQR exact by construction for non-degenerate columns):

| Feature | p01 | p99 | min | max | Note |
|---------|-----|-----|-----|-----|------|
| solexs_HR_high_low | −1.22 | +4.16 | −1.60 | +40.9 | 0 on 0.92% of observed minutes (zero hard-band counts, valid) |
| solexs_HR_mid_low | −1.22 | +4.16 | −1.60 | +61.9 | |
| solexs_dHR_15m | −2.89 | +2.89 | −28.2 | +25.3 | symmetric, as a difference feature should be |
| solexs_HR_peak_60m | −1.25 | +1.60 | −1.62 | +19.2 | |
| log_solexs_soft | −1.96 | +9.26 | −5.80 | +17.6 | quiet-floor median log1p(9×150)≈7.2 confirmed by subagent |
| solexs_variance_15m | −1.10 | +46.6 | −1.42 | +229.5 | heavy tail — flare-time variance bursts |
| solexs_variance_60m | −1.27 | +178.1 | −2.03 | +279.7 | heaviest tail of the SoLEXS set |
| solexs_peak_30m | −1.47 | +34.7 | −4.63 | +42.0 | |
| minutes_since_solexs_active | −0.59 | +3.57 | −0.59 | +218.5 | cap 10,080 honored; 1.2% exactly at "just active" |
| solexs_active_fraction_6h | −0.91 | +4.82 | −1.18 | +8.82 | raw ∈ [0, 0.308] — activity is rare, as expected for a 95th-percentile trigger |
| hel1os_fluence_30m | −1.73 | +82.2 | **−103.0** | +112.0 | near-constant channel → tiny IQR → extreme scaled tails |
| hel1os_fluence_60m | −1.70 | +104.5 | **−171.8** | +140.1 | same mechanism |
| nonthermal_thermal_ratio | −2.69 | +4.33 | −6.19 | +12.0 | see Correlation Report: r = −0.94 with log_long_flux |
| d_ntr_15m | −5.92 | +7.45 | −32.1 | +29.0 | |
| log_hel1os_band0 | −2.04 | +14.9 | −3.96 | +29.1 | |

**Interpretive notes (labeled):**
- OBSERVED: the HEL1OS band0 rate is nearly constant in quiet conditions (median 10, minimum 5 — `Dataset_Report.md` source characterization), so fluence integrals have a minuscule train IQR; under the pre-registered robust scaler their rare excursions map to post-scale magnitudes of ±100–170. This is representable in float32 and analogous to the V1-era raw-flux dynamic range; per the governing rules it is documented, not clipped.
- OBSERVED: the SoLEXS variance features carry the largest right tails of the new set (p99 up to +178) — flare-time intermittency bursts, exactly the avalanche-statistics signal row 9–10 target.
- DERIVED: no new feature is constant (all IQRs nonzero pre-scaling), so none enters the degenerate-IQR fallback that two GOES features hit in Sprint 30 (`minutes_since_last_flare` and `goes_dT_iso_15m` remain the only degenerate columns on THIS split family's GOES side — recorded in `build_report.json:degenerate_iqr_features` = [] for the 32-set on s2_train, where solar-max activity gives even the GOES quiet-features nonzero IQR; OBSERVED value in the build report).
- NOT PROVEN: whether any of these distributions carries flare-predictive signal — that is exactly the F2 experiment's question and is answered only by the sealed evaluation.
