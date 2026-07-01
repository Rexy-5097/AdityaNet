# Sprint 10G-OD: Signal Localization Audit Report

## 1. Executive Summary Table

| Metric | Measured Value |
| :--- | :---: |
| Total Features Evaluated | 54 |
| Valid Folds | 3 |
| Degenerate Folds | 1 (Fold C - June 11) |
| Best Generalizing Feature | solexs_sdd2_spec_counts_ch36 |
| Best Generalizing Raw Channel | solexs_sdd2_spec_counts_ch36 |
| Peak Memory Usage | 601776.00 MB |
| Total Execution Time | 143.908 seconds |

---

## 2. Task 6A: Raw Channel Leaderboard

Top 10 raw spectral channels ranked by Positive Folds descending, Mean $\Delta$AUC descending, and Variance ascending.

| Rank | Channel Name | Positive Folds | Mean $\Delta$AUC | Variance | Worst $\Delta$AUC | 10G-N Full $\Delta$AUC |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: |
| 1 | `solexs_sdd2_spec_counts_ch36` | 3/3 | 0.032911 | 7.236993e-04 | 0.011470 | 0.004949 |
| 2 | `solexs_sdd2_spec_counts_ch37` | 2/3 | 0.026596 | 7.994714e-04 | -0.004353 | 0.010485 |
| 3 | `solexs_sdd2_spec_counts_ch35` | 2/3 | 0.017298 | 1.166096e-03 | -0.023647 | 0.044172 |
| 4 | `solexs_sdd2_spec_counts_ch34` | 1/3 | -0.007021 | 4.332543e-03 | -0.071553 | 0.027004 |
| 5 | `solexs_sdd2_spec_counts_ch33` | 1/3 | -0.037723 | 9.508574e-03 | -0.117668 | 0.027180 |
| 6 | `solexs_sdd2_spec_counts_ch13` | 1/3 | -0.043479 | 3.784762e-03 | -0.130248 | 0.012942 |
| 7 | `solexs_sdd2_spec_counts_ch31` | 1/3 | -0.063343 | 1.360148e-02 | -0.204737 | 0.014398 |
| 8 | `solexs_sdd2_spec_counts_ch30` | 1/3 | -0.088894 | 7.045946e-03 | -0.198198 | 0.033709 |
| 9 | `solexs_sdd2_spec_counts_ch29` | 1/3 | -0.093555 | 6.614146e-03 | -0.171307 | 0.042151 |
| 10 | `solexs_sdd2_spec_counts_ch32` | 1/3 | -0.094202 | 1.116375e-02 | -0.211437 | 0.024669 |

---

## 3. Task 6: Pure Feature Ranking (Top 15)

Top 15 features across all types (raw, band, compression) ranked.

| Rank | Feature Name | Feature Type | Positive Folds | Mean $\Delta$AUC | Variance | Worst $\Delta$AUC | 10G-N Full $\Delta$AUC |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| 1 | `solexs_sdd2_spec_counts_ch36` | Raw Channel | 3/3 | 0.032911 | 7.236993e-04 | 0.011470 | 0.004949 |
| 2 | `solexs_sdd2_spec_counts_ch37` | Raw Channel | 2/3 | 0.026596 | 7.994714e-04 | -0.004353 | 0.010485 |
| 3 | `solexs_sdd2_spec_counts_ch35` | Raw Channel | 2/3 | 0.017298 | 1.166096e-03 | -0.023647 | 0.044172 |
| 4 | `solexs_sdd2_spec_counts_ch34` | Raw Channel | 1/3 | -0.007021 | 4.332543e-03 | -0.071553 | 0.027004 |
| 5 | `band_D_median` | Physical Band | 1/3 | -0.037174 | 1.093656e-02 | -0.145479 | 0.018186 |
| 6 | `solexs_sdd2_spec_counts_ch33` | Raw Channel | 1/3 | -0.037723 | 9.508574e-03 | -0.117668 | 0.027180 |
| 7 | `solexs_sdd2_spec_counts_ch13` | Raw Channel | 1/3 | -0.043479 | 3.784762e-03 | -0.130248 | 0.012942 |
| 8 | `band_D_zscore_mean` | Physical Band | 1/3 | -0.044078 | 5.638348e-03 | -0.098619 | 0.036141 |
| 9 | `band_D_sum` | Physical Band | 1/3 | -0.047884 | 7.883596e-03 | -0.146830 | 0.023712 |
| 10 | `median_ratio` | Compression | 1/3 | -0.048020 | 4.272347e-03 | -0.140405 | 0.071251 |
| 11 | `band_D_mean` | Physical Band | 1/3 | -0.048645 | 7.352728e-03 | -0.144866 | 0.023391 |
| 12 | `band_D_trimmed_mean` | Physical Band | 1/3 | -0.048645 | 7.352728e-03 | -0.144866 | 0.023391 |
| 13 | `solexs_sdd2_spec_counts_ch31` | Raw Channel | 1/3 | -0.063343 | 1.360148e-02 | -0.204737 | 0.014398 |
| 14 | `hard_soft_ratio` | Compression | 1/3 | -0.073502 | 1.023153e-02 | -0.216462 | 0.071026 |
| 15 | `hard_band_mean` | Compression | 1/3 | -0.075133 | 7.763886e-03 | -0.164735 | 0.034111 |

---

## 4. Task 3B: Sprint 10G-N Protocol Reproduction Comparison

Comparison of Full Overlap $\Delta$AUC (Sprint 10G-N protocol) and LODO Mean $\Delta$AUC for all compression configurations and top ablated features.

| Feature Name | 10G-N Full Overlap $\Delta$AUC | LODO Mean $\Delta$AUC | Difference (LODO - 10G-N) |
| :--- | :---: | :---: | :---: |
| `soft_band_mean` | 0.037814 | -0.156824 | -0.194638 |
| `hard_band_mean` | 0.034111 | -0.075133 | -0.109244 |
| `hard_soft_ratio` | 0.071026 | -0.073502 | -0.144528 |
| `pc1_projection` | 0.042804 | -0.133050 | -0.175854 |
| `pc2_projection` | 0.046946 | -0.118874 | -0.165819 |
| `robust_soft_mean` | 0.038392 | -0.155788 | -0.194180 |
| `robust_hard_mean` | 0.034111 | -0.075133 | -0.109244 |
| `winsorized_ratio` | 0.070081 | -0.085029 | -0.155110 |
| `median_ratio` | 0.071251 | -0.048020 | -0.119270 |

---

## 5. Task 5C: Spread & Daily Sign Matrix

Detailing best fold, worst fold, spread ($\Delta\text{AUC}_{\text{best}} - \Delta\text{AUC}_{\text{worst}}$), and daily fold signs for standard compression features, robust alternatives, and top bands.

| Feature Name | Best Fold | Worst Fold | Spread | Fold A Sign | Fold B Sign | Fold D Sign |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `soft_band_mean` | Fold D (0.0155) | Fold A (-0.4203) | 0.435789 | - | - | + |
| `hard_band_mean` | Fold D (0.0447) | Fold B (-0.1647) | 0.209399 | - | - | + |
| `hard_soft_ratio` | Fold D (0.0023) | Fold A (-0.2165) | 0.218804 | - | - | + |
| `pc1_projection` | Fold D (0.0153) | Fold A (-0.3426) | 0.357890 | - | - | + |
| `pc2_projection` | Fold D (-0.0012) | Fold A (-0.3086) | 0.307405 | - | - | - |
| `robust_soft_mean` | Fold D (0.0142) | Fold A (-0.4172) | 0.431413 | - | - | + |
| `robust_hard_mean` | Fold D (0.0447) | Fold B (-0.1647) | 0.209399 | - | - | + |
| `winsorized_ratio` | Fold D (0.0021) | Fold A (-0.2420) | 0.244084 | - | - | + |
| `median_ratio` | Fold D (0.0009) | Fold A (-0.1404) | 0.141257 | - | - | + |
| `band_A_mean` | Fold D (0.0181) | Fold A (-0.4272) | 0.445212 | - | - | + |
| `band_B_mean` | Fold D (0.0160) | Fold A (-0.4099) | 0.425866 | - | - | + |
| `band_C_mean` | Fold D (0.0105) | Fold A (-0.3281) | 0.338608 | - | - | + |
| `band_D_mean` | Fold D (0.0634) | Fold B (-0.1449) | 0.208247 | - | - | + |

---

## 6. Detailed Folds Registry (Folds A, B, & D)

Detailing actual test day $\Delta$AUC and 95% bootstrap confidence intervals for all compression features and robust alternatives.

| Fold | Feature Name | Actual $\Delta$AUC | 95% Bootstrap CI |
| :--- | :--- | :---: | :---: |
| `Fold A` | `soft_band_mean` | -0.420258 | [-0.451488, -0.388465] |
| `Fold A` | `hard_band_mean` | -0.105328 | [-0.143648, -0.068036] |
| `Fold A` | `hard_soft_ratio` | -0.216462 | [-0.259533, -0.172461] |
| `Fold A` | `pc1_projection` | -0.342605 | [-0.376304, -0.304945] |
| `Fold A` | `pc2_projection` | -0.308595 | [-0.339737, -0.280913] |
| `Fold A` | `robust_soft_mean` | -0.417208 | [-0.449227, -0.383854] |
| `Fold A` | `robust_hard_mean` | -0.105328 | [-0.146373, -0.065323] |
| `Fold A` | `winsorized_ratio` | -0.242002 | [-0.283398, -0.197874] |
| `Fold A` | `median_ratio` | -0.140405 | [-0.181725, -0.098125] |
| `Fold B` | `soft_band_mean` | -0.065744 | [-0.088147, -0.043299] |
| `Fold B` | `hard_band_mean` | -0.164735 | [-0.198581, -0.129697] |
| `Fold B` | `hard_soft_ratio` | -0.006386 | [-0.048100, 0.031410] |
| `Fold B` | `pc1_projection` | -0.071829 | [-0.097116, -0.048613] |
| `Fold B` | `pc2_projection` | -0.046837 | [-0.066511, -0.026596] |
| `Fold B` | `robust_soft_mean` | -0.064360 | [-0.085848, -0.043540] |
| `Fold B` | `robust_hard_mean` | -0.164735 | [-0.199984, -0.127977] |
| `Fold B` | `winsorized_ratio` | -0.015168 | [-0.054616, 0.024831] |
| `Fold B` | `median_ratio` | -0.004506 | [-0.039863, 0.031641] |
| `Fold D` | `soft_band_mean` | 0.015531 | [0.011845, 0.019682] |
| `Fold D` | `hard_band_mean` | 0.044665 | [0.037307, 0.052688] |
| `Fold D` | `hard_soft_ratio` | 0.002342 | [0.001555, 0.003157] |
| `Fold D` | `pc1_projection` | 0.015285 | [0.011734, 0.019257] |
| `Fold D` | `pc2_projection` | -0.001189 | [-0.002864, 0.000403] |
| `Fold D` | `robust_soft_mean` | 0.014205 | [0.010984, 0.018097] |
| `Fold D` | `robust_hard_mean` | 0.044665 | [0.036674, 0.052451] |
| `Fold D` | `winsorized_ratio` | 0.002082 | [0.001291, 0.002914] |
| `Fold D` | `median_ratio` | 0.000852 | [0.000391, 0.001318] |
