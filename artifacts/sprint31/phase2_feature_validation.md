# Sprint 31 Phase 2 — Feature Validation (features_v4/aditya.py on s2_val)

Generated 2026-07-11T23:31:34.782307 | rows 262480 | train_p95(log_solexs_soft) = 7.599854

**Overall: FAIL**

## 1. Formula conformance — PASS
Independent pandas/numpy recompute vs module output (tol 1e-9, identical NaN placement).

| Feature | Result | max abs diff | NaN match |
|---|---|---|---|
| solexs_HR_high_low | PASS | 0.00e+00 | True |
| solexs_HR_mid_low | PASS | 0.00e+00 | True |
| solexs_dHR_15m | PASS | 0.00e+00 | True |
| solexs_HR_peak_60m | PASS | 0.00e+00 | True |
| log_solexs_soft | PASS | 0.00e+00 | True |
| solexs_variance_15m | PASS | 0.00e+00 | True |
| solexs_variance_60m | PASS | 0.00e+00 | True |
| solexs_peak_30m | PASS | 0.00e+00 | True |
| minutes_since_solexs_active | PASS | 0.00e+00 | True |
| solexs_active_fraction_6h | PASS | 0.00e+00 | True |
| hel1os_fluence_30m | PASS | 0.00e+00 | True |
| hel1os_fluence_60m | PASS | 0.00e+00 | True |
| nonthermal_thermal_ratio | PASS | 0.00e+00 | True |
| d_ntr_15m | PASS | 0.00e+00 | True |
| log_hel1os_band0 | PASS | 0.00e+00 | True |

## 2. Causality (no future leakage) — PASS
First 100,000 outputs identical between full-frame and truncated-frame computation; max abs diff across all 15 features = 0.0e+00.

## 3. No label access — PASS
No feature's `requires` includes target_6hr_binary or target_6hr_class; FeatureSet construction succeeded.

## 4. Determinism — PASS
Two compute_all runs on identical input produce identical pandas row hashes.

## 5. Physical ranges on observed minutes — FAIL

| Feature | Result | min | median | max | flags |
|---|---|---|---|---|---|
| solexs_HR_high_low | FAIL | 0 | 0.91 | 27.19 | nonpositive ratio on 1832 observed minutes (0.9232%) — numerator band sums to exactly 0 in the raw data |
| solexs_HR_mid_low | FAIL | 0 | 0.9104 | 28.24 | nonpositive ratio on 1822 observed minutes (0.9182%) — numerator band sums to exactly 0 in the raw data |
| solexs_dHR_15m | PASS | -21.5 | -0.0005727 | 26.75 | - |
| solexs_HR_peak_60m | PASS | 0.3767 | 3.04 | 27.19 | - |
| log_solexs_soft | PASS | 6.45 | 7.36 | 11.05 | - |
| solexs_variance_15m | PASS | 0.00111 | 0.02097 | 4.15 | - |
| solexs_variance_60m | PASS | 0.006712 | 0.02315 | 4.15 | - |
| solexs_peak_30m | PASS | 6.986 | 7.605 | 11.05 | - |
| minutes_since_solexs_active | PASS | 0 | 26 | 1.008e+04 | - |
| solexs_active_fraction_6h | PASS | 0 | 0.03611 | 0.3083 | - |
| hel1os_fluence_30m | PASS | 6.375 | 9.8 | 13.44 | - |
| hel1os_fluence_60m | PASS | 6.375 | 10.49 | 13.51 | - |
| nonthermal_thermal_ratio | PASS | 9.777 | 15.87 | 27.41 | - |
| d_ntr_15m | PASS | -10.32 | 0.01298 | 12.1 | - |
| log_hel1os_band0 | PASS | 1.792 | 2.401 | 6.87 | - |

## 6. Train-only threshold — PASS
Both activity features record train_p95 = 7.599854 with provenance 'train-split-only (dataset layer)'.

## 7. Flare response — FAIL
Top-20 long_flux observed minutes (two events, peak ~5.2e-4 W/m^2): 30% exceed split-median HR_high_low (0.9104); 40% exceed split-median log_solexs_soft (7.361). Expected both > 50%. SoLEXS shows no spectral hardening or brightening co-temporal with the GOES flare peaks in s2_val — a data/physics finding, not a formula error (check 1 passed).
