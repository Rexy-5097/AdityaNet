# Localization Validation Report - Sprint 10G-OD

## Final Verdict
**PASS** (Zero discrepancies found between the recomputed measurements and the audit outputs)

## 1. Fold Reconstruction Validation
All leave-one-day-out folds were rebuilt directly from timestamps. The training rows, test rows, and day assignments match the expected reconstruction logic exactly.

| Fold ID | Day Assignment (Test Day) | Day Assignments (Train Days) | Recomputed Train Rows | Audit Train Rows | Absolute Difference | Status |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: |
| **Fold A** | `["2026-06-13"]` | `["2026-06-10", "2026-06-11", "2026-06-12"]` | 4260 | 4260 | 0 | PASS |
| **Fold B** | `["2026-06-12"]` | `["2026-06-10", "2026-06-11", "2026-06-13"]` | 4200 | 4200 | 0 | PASS |
| **Fold C** | `["2026-06-11"]` | `["2026-06-10", "2026-06-12", "2026-06-13"]` | 4200 | 4200 | 0 | PASS (Degenerate) |
| **Fold D** | `["2026-06-10"]` | `["2026-06-11", "2026-06-12", "2026-06-13"]` | 4260 | 4260 | 0 | PASS |

---

## 2. Raw Channel Recalculation (Channels 13 to 37)
Recomputed baseline AUC, augmented AUC, and delta AUC for all 25 raw channels across all valid folds match the audit values exactly (within $10^{-6}$ tolerance).

A representative sample of channels (first and last channels) is reported below:

| Feature / Fold | Metric | Audit Value | Recomputed Value | Absolute Difference | Status |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **solexs_sdd2_spec_counts_ch13 (Fold A)** | Baseline AUC | 0.432216 | 0.432216 | 0.000000e+00 | PASS |
| **solexs_sdd2_spec_counts_ch13 (Fold A)** | Augmented AUC | 0.301968 | 0.301968 | 0.000000e+00 | PASS |
| | Delta AUC | -0.130248 | -0.130248 | 0.000000e+00 | PASS |
| **solexs_sdd2_spec_counts_ch13 (Fold B)** | Baseline AUC | 0.509731 | 0.509731 | 0.000000e+00 | PASS |
| **solexs_sdd2_spec_counts_ch13 (Fold B)** | Augmented AUC | 0.504112 | 0.504112 | 0.000000e+00 | PASS |
| | Delta AUC | -0.005619 | -0.005619 | 0.000000e+00 | PASS |
| **solexs_sdd2_spec_counts_ch13 (Fold D)** | Baseline AUC | 0.226227 | 0.226227 | 0.000000e+00 | PASS |
| **solexs_sdd2_spec_counts_ch13 (Fold D)** | Augmented AUC | 0.231657 | 0.231657 | 0.000000e+00 | PASS |
| | Delta AUC | 0.005430 | 0.005430 | 0.000000e+00 | PASS |
| **solexs_sdd2_spec_counts_ch37 (Fold A)** | Baseline AUC | 0.432216 | 0.432216 | 0.000000e+00 | PASS |
| **solexs_sdd2_spec_counts_ch37 (Fold A)** | Augmented AUC | 0.427863 | 0.427863 | 0.000000e+00 | PASS |
| | Delta AUC | -0.004353 | -0.004353 | 0.000000e+00 | PASS |
| **solexs_sdd2_spec_counts_ch37 (Fold B)** | Baseline AUC | 0.509731 | 0.509731 | 0.000000e+00 | PASS |
| **solexs_sdd2_spec_counts_ch37 (Fold B)** | Augmented AUC | 0.573729 | 0.573729 | 0.000000e+00 | PASS |
| | Delta AUC | 0.063998 | 0.063998 | 0.000000e+00 | PASS |
| **solexs_sdd2_spec_counts_ch37 (Fold D)** | Baseline AUC | 0.226227 | 0.226227 | 0.000000e+00 | PASS |
| **solexs_sdd2_spec_counts_ch37 (Fold D)** | Augmented AUC | 0.246370 | 0.246370 | 0.000000e+00 | PASS |
| | Delta AUC | 0.020143 | 0.020143 | 0.000000e+00 | PASS |

---

## 3. Physical Band Recalculation
Recomputed band aggregations (`mean`, `median`, `trimmed_mean`, `sum`, `zscore_mean`) for all 4 bands (`band_A` ... `band_D`) and all valid folds match the audit values exactly (within $10^{-6}$ tolerance).

A representative sample of band features is reported below:

| Band Feature / Fold | Metric | Audit Value | Recomputed Value | Absolute Difference | Status |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **band_A_mean (Fold A)** | Baseline AUC | 0.432216 | 0.432216 | 0.000000e+00 | PASS |
| **band_A_mean (Fold A)** | Augmented AUC | 0.005063 | 0.005063 | 0.000000e+00 | PASS |
| | Delta AUC | -0.427153 | -0.427153 | 0.000000e+00 | PASS |
| **band_A_mean (Fold B)** | Baseline AUC | 0.509731 | 0.509731 | 0.000000e+00 | PASS |
| **band_A_mean (Fold B)** | Augmented AUC | 0.441151 | 0.441151 | 0.000000e+00 | PASS |
| | Delta AUC | -0.068580 | -0.068580 | 0.000000e+00 | PASS |
| **band_A_mean (Fold D)** | Baseline AUC | 0.226227 | 0.226227 | 0.000000e+00 | PASS |
| **band_A_mean (Fold D)** | Augmented AUC | 0.244286 | 0.244286 | 0.000000e+00 | PASS |
| | Delta AUC | 0.018059 | 0.018059 | 0.000000e+00 | PASS |
| **band_B_trimmed_mean (Fold A)** | Baseline AUC | 0.432216 | 0.432216 | 0.000000e+00 | PASS |
| **band_B_trimmed_mean (Fold A)** | Augmented AUC | 0.022347 | 0.022347 | 0.000000e+00 | PASS |
| | Delta AUC | -0.409870 | -0.409870 | 0.000000e+00 | PASS |
| **band_B_trimmed_mean (Fold B)** | Baseline AUC | 0.509731 | 0.509731 | 0.000000e+00 | PASS |
| **band_B_trimmed_mean (Fold B)** | Augmented AUC | 0.444455 | 0.444455 | 0.000000e+00 | PASS |
| | Delta AUC | -0.065275 | -0.065275 | 0.000000e+00 | PASS |
| **band_B_trimmed_mean (Fold D)** | Baseline AUC | 0.226227 | 0.226227 | 0.000000e+00 | PASS |
| **band_B_trimmed_mean (Fold D)** | Augmented AUC | 0.242224 | 0.242224 | 0.000000e+00 | PASS |
| | Delta AUC | 0.015996 | 0.015996 | 0.000000e+00 | PASS |
| **band_C_sum (Fold A)** | Baseline AUC | 0.432216 | 0.432216 | 0.000000e+00 | PASS |
| **band_C_sum (Fold A)** | Augmented AUC | 0.105628 | 0.105628 | 0.000000e+00 | PASS |
| | Delta AUC | -0.326588 | -0.326588 | 0.000000e+00 | PASS |
| **band_C_sum (Fold B)** | Baseline AUC | 0.509731 | 0.509731 | 0.000000e+00 | PASS |
| **band_C_sum (Fold B)** | Augmented AUC | 0.416720 | 0.416720 | 0.000000e+00 | PASS |
| | Delta AUC | -0.093011 | -0.093011 | 0.000000e+00 | PASS |
| **band_C_sum (Fold D)** | Baseline AUC | 0.226227 | 0.226227 | 0.000000e+00 | PASS |
| **band_C_sum (Fold D)** | Augmented AUC | 0.236630 | 0.236630 | 0.000000e+00 | PASS |
| | Delta AUC | 0.010402 | 0.010402 | 0.000000e+00 | PASS |
| **band_D_zscore_mean (Fold A)** | Baseline AUC | 0.432216 | 0.432216 | 0.000000e+00 | PASS |
| **band_D_zscore_mean (Fold A)** | Augmented AUC | 0.336500 | 0.336500 | 0.000000e+00 | PASS |
| | Delta AUC | -0.095716 | -0.095716 | 0.000000e+00 | PASS |
| **band_D_zscore_mean (Fold B)** | Baseline AUC | 0.509731 | 0.509731 | 0.000000e+00 | PASS |
| **band_D_zscore_mean (Fold B)** | Augmented AUC | 0.411112 | 0.411112 | 0.000000e+00 | PASS |
| | Delta AUC | -0.098619 | -0.098619 | 0.000000e+00 | PASS |
| **band_D_zscore_mean (Fold D)** | Baseline AUC | 0.226227 | 0.226227 | 0.000000e+00 | PASS |
| **band_D_zscore_mean (Fold D)** | Augmented AUC | 0.288328 | 0.288328 | 0.000000e+00 | PASS |
| | Delta AUC | 0.062100 | 0.062100 | 0.000000e+00 | PASS |

---

## 4. Compression Recalculation
Recomputed metrics for all 9 compression features (`soft_band_mean`, `hard_band_mean`, `hard_soft_ratio`, `pc1_projection`, `pc2_projection`, `robust_soft_mean`, `robust_hard_mean`, `winsorized_ratio`, `median_ratio`) match the audit values exactly (within $10^{-6}$ tolerance).

| Compression Feature / Fold | Metric | Audit Value | Recomputed Value | Absolute Difference | Status |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **soft_band_mean (Fold A)** | Baseline AUC | 0.432216 | 0.432216 | 0.000000e+00 | PASS |
| **soft_band_mean (Fold A)** | Augmented AUC | 0.011958 | 0.011958 | 0.000000e+00 | PASS |
| | Delta AUC | -0.420258 | -0.420258 | 0.000000e+00 | PASS |
| **soft_band_mean (Fold B)** | Baseline AUC | 0.509731 | 0.509731 | 0.000000e+00 | PASS |
| **soft_band_mean (Fold B)** | Augmented AUC | 0.443987 | 0.443987 | 0.000000e+00 | PASS |
| | Delta AUC | -0.065744 | -0.065744 | 0.000000e+00 | PASS |
| **soft_band_mean (Fold D)** | Baseline AUC | 0.226227 | 0.226227 | 0.000000e+00 | PASS |
| **soft_band_mean (Fold D)** | Augmented AUC | 0.241758 | 0.241758 | 0.000000e+00 | PASS |
| | Delta AUC | 0.015531 | 0.015531 | 0.000000e+00 | PASS |
| **hard_soft_ratio (Fold A)** | Baseline AUC | 0.432216 | 0.432216 | 0.000000e+00 | PASS |
| **hard_soft_ratio (Fold A)** | Augmented AUC | 0.215754 | 0.215754 | 0.000000e+00 | PASS |
| | Delta AUC | -0.216462 | -0.216462 | 0.000000e+00 | PASS |
| **hard_soft_ratio (Fold B)** | Baseline AUC | 0.509731 | 0.509731 | 0.000000e+00 | PASS |
| **hard_soft_ratio (Fold B)** | Augmented AUC | 0.503345 | 0.503345 | 0.000000e+00 | PASS |
| | Delta AUC | -0.006386 | -0.006386 | 0.000000e+00 | PASS |
| **hard_soft_ratio (Fold D)** | Baseline AUC | 0.226227 | 0.226227 | 0.000000e+00 | PASS |
| **hard_soft_ratio (Fold D)** | Augmented AUC | 0.228570 | 0.228570 | 0.000000e+00 | PASS |
| | Delta AUC | 0.002342 | 0.002342 | 0.000000e+00 | PASS |
| **pc1_projection (Fold A)** | Baseline AUC | 0.432216 | 0.432216 | 0.000000e+00 | PASS |
| **pc1_projection (Fold A)** | Augmented AUC | 0.089611 | 0.089611 | 0.000000e+00 | PASS |
| | Delta AUC | -0.342605 | -0.342605 | 0.000000e+00 | PASS |
| **pc1_projection (Fold B)** | Baseline AUC | 0.509731 | 0.509731 | 0.000000e+00 | PASS |
| **pc1_projection (Fold B)** | Augmented AUC | 0.437902 | 0.437902 | 0.000000e+00 | PASS |
| | Delta AUC | -0.071829 | -0.071829 | 0.000000e+00 | PASS |
| **pc1_projection (Fold D)** | Baseline AUC | 0.226227 | 0.226227 | 0.000000e+00 | PASS |
| **pc1_projection (Fold D)** | Augmented AUC | 0.241513 | 0.241513 | 0.000000e+00 | PASS |
| | Delta AUC | 0.015285 | 0.015285 | 0.000000e+00 | PASS |
| **winsorized_ratio (Fold A)** | Baseline AUC | 0.432216 | 0.432216 | 0.000000e+00 | PASS |
| **winsorized_ratio (Fold A)** | Augmented AUC | 0.190214 | 0.190214 | 0.000000e+00 | PASS |
| | Delta AUC | -0.242002 | -0.242002 | 0.000000e+00 | PASS |
| **winsorized_ratio (Fold B)** | Baseline AUC | 0.509731 | 0.509731 | 0.000000e+00 | PASS |
| **winsorized_ratio (Fold B)** | Augmented AUC | 0.494563 | 0.494563 | 0.000000e+00 | PASS |
| | Delta AUC | -0.015168 | -0.015168 | 0.000000e+00 | PASS |
| **winsorized_ratio (Fold D)** | Baseline AUC | 0.226227 | 0.226227 | 0.000000e+00 | PASS |
| **winsorized_ratio (Fold D)** | Augmented AUC | 0.228309 | 0.228309 | 0.000000e+00 | PASS |
| | Delta AUC | 0.002082 | 0.002082 | 0.000000e+00 | PASS |

---

## 5. Stability Recalculation Validation
Recomputed stability summary statistics across the valid folds match the audit values exactly:

| Feature Name | Metric | Audit Value | Recomputed Value | Absolute Difference | Status |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **hard_soft_ratio** | mean_delta_auc | -0.07350183265862344 | -0.07350183265862344 | 0.000000e+00 | PASS |
| **hard_soft_ratio** | std_delta_auc | 0.1011510101516582 | 0.1011510101516582 | 0.000000e+00 | PASS |
| **hard_soft_ratio** | variance_delta_auc | 0.01023152685470086 | 0.01023152685470086 | 0.000000e+00 | PASS |
| **hard_soft_ratio** | min_delta_auc | -0.21646218487394958 | -0.21646218487394958 | 0.000000e+00 | PASS |
| **hard_soft_ratio** | max_delta_auc | 0.0023422353935894924 | 0.0023422353935894924 | 0.000000e+00 | PASS |
| **hard_soft_ratio** | positive_fold_count | 1 | 1 | 0.000000e+00 | PASS |
| **hard_soft_ratio** | negative_fold_count | 2 | 2 | 0.000000e+00 | PASS |
| **pc1_projection** | mean_delta_auc | -0.13304955978268418 | -0.13304955978268418 | 0.000000e+00 | PASS |
| **pc1_projection** | std_delta_auc | 0.15238625213891271 | 0.15238625213891271 | 0.000000e+00 | PASS |
| **pc1_projection** | variance_delta_auc | 0.02322156984094428 | 0.02322156984094428 | 0.000000e+00 | PASS |
| **pc1_projection** | min_delta_auc | -0.34260504201680675 | -0.34260504201680675 | 0.000000e+00 | PASS |
| **pc1_projection** | max_delta_auc | 0.015285381205749432 | 0.015285381205749432 | 0.000000e+00 | PASS |
| **pc1_projection** | positive_fold_count | 1 | 1 | 0.000000e+00 | PASS |
| **pc1_projection** | negative_fold_count | 2 | 2 | 0.000000e+00 | PASS |
| **winsorized_ratio** | mean_delta_auc | -0.08502937641548818 | -0.08502937641548818 | 0.000000e+00 | PASS |
| **winsorized_ratio** | std_delta_auc | 0.11121964368996577 | 0.11121964368996577 | 0.000000e+00 | PASS |
| **winsorized_ratio** | variance_delta_auc | 0.012369809142522942 | 0.012369809142522942 | 0.000000e+00 | PASS |
| **winsorized_ratio** | min_delta_auc | -0.24200210084033613 | -0.24200210084033613 | 0.000000e+00 | PASS |
| **winsorized_ratio** | max_delta_auc | 0.0020817497800817986 | 0.0020817497800817986 | 0.000000e+00 | PASS |
| **winsorized_ratio** | positive_fold_count | 1 | 1 | 0.000000e+00 | PASS |
| **winsorized_ratio** | negative_fold_count | 2 | 2 | 0.000000e+00 | PASS |

---

## 6. Bootstrap Validation (Tolerance: 1e-4)
Recomputed 95% Confidence Intervals for Delta AUC match the audited bounds exactly (within $10^{-4}$ tolerance).

| Fold | Feature Name | Audit 95% CI | Recomputed 95% CI | Lower Difference | Upper Difference | Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **Fold A** | `hard_soft_ratio` | [-0.259533, -0.172461] | [-0.259533, -0.172461] | 0.000000e+00 | 0.000000e+00 | PASS |
| **Fold A** | `pc1_projection` | [-0.376304, -0.304945] | [-0.376304, -0.304945] | 0.000000e+00 | 0.000000e+00 | PASS |
| **Fold A** | `winsorized_ratio` | [-0.283398, -0.197874] | [-0.283398, -0.197874] | 0.000000e+00 | 0.000000e+00 | PASS |
| **Fold B** | `hard_soft_ratio` | [-0.048100, 0.031410] | [-0.048100, 0.031410] | 0.000000e+00 | 0.000000e+00 | PASS |
| **Fold B** | `pc1_projection` | [-0.097116, -0.048613] | [-0.097116, -0.048613] | 0.000000e+00 | 0.000000e+00 | PASS |
| **Fold B** | `winsorized_ratio` | [-0.054616, 0.024831] | [-0.054616, 0.024831] | 0.000000e+00 | 0.000000e+00 | PASS |
| **Fold D** | `hard_soft_ratio` | [0.001555, 0.003157] | [0.001555, 0.003157] | 0.000000e+00 | 0.000000e+00 | PASS |
| **Fold D** | `pc1_projection` | [0.011734, 0.019257] | [0.011734, 0.019257] | 0.000000e+00 | 0.000000e+00 | PASS |
| **Fold D** | `winsorized_ratio` | [0.001291, 0.002914] | [0.001291, 0.002914] | 0.000000e+00 | 0.000000e+00 | PASS |

---

## 7. Ranking Validation
Rebuilt ranking table from raw metrics matches the audit rankings exactly:

| Rank | Feature Name | Audit Positive Folds | Recomputed Positive Folds | Audit Mean $\Delta$AUC | Recomputed Mean $\Delta$AUC | Status |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: |
| **1** | `solexs_sdd2_spec_counts_ch36` | 3/3 | 3/3 | 0.032911 | 0.032911 | PASS |
| **2** | `solexs_sdd2_spec_counts_ch37` | 2/3 | 2/3 | 0.026596 | 0.026596 | PASS |
| **3** | `solexs_sdd2_spec_counts_ch35` | 2/3 | 2/3 | 0.017298 | 0.017298 | PASS |
| **4** | `solexs_sdd2_spec_counts_ch34` | 1/3 | 1/3 | -0.007021 | -0.007021 | PASS |
| **5** | `band_D_median` | 1/3 | 1/3 | -0.037174 | -0.037174 | PASS |
| **6** | `solexs_sdd2_spec_counts_ch33` | 1/3 | 1/3 | -0.037723 | -0.037723 | PASS |
| **7** | `solexs_sdd2_spec_counts_ch13` | 1/3 | 1/3 | -0.043479 | -0.043479 | PASS |
| **8** | `band_D_zscore_mean` | 1/3 | 1/3 | -0.044078 | -0.044078 | PASS |
| **9** | `band_D_sum` | 1/3 | 1/3 | -0.047884 | -0.047884 | PASS |
| **10** | `median_ratio` | 1/3 | 1/3 | -0.048020 | -0.048020 | PASS |
