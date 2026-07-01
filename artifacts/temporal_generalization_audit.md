# Sprint 10G-OC: Temporal Generalization Audit Report

## 1. Executive Summary Table

| Metric | Measured Value |
| :--- | :---: |
| Non-Degenerate Folds | 3 |
| Degenerate Folds | 1 (Fold C - June 11) |
| Best Generalizing Feature | pc1_projection |
| Peak Memory Usage | 499024.00 MB |
| Total Execution Time | 16.752 seconds |

---

## 2. Degenerate Folds Registry

On **2026-06-11** (Fold C Test set), the target `target_6hr_binary_c` was constant (all 1s). As a result, Fold C is registered as **DEGENERATE** and completely excluded from all downstream statistical summaries, significance tests, confidence intervals, and operator ranking to prevent mathematical distortion.

---

## 3. Task 1: Leave-One-Day-Out evaluation

Metrics computed at forecast lead horizon $h = 60$ minutes.

### Fold A (Test Days: ['2026-06-13'])

| Configuration | AUC | PR-AUC | Brier Score | Max TSS | Delta AUC |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `Baseline History` | 0.432399 | 0.453031 | 0.283731 | 0.019664 | - |
| `History + hard_soft_ratio` | 0.215716 | 0.352476 | 0.334200 | 0.000000 | -0.216683 |
| `History + soft_band_mean` | 0.011313 | 0.313443 | 0.303656 | 0.000000 | -0.421086 |
| `History + pc1_projection` | 0.090204 | 0.322365 | 0.302585 | 0.000000 | -0.342195 |
| `History + pc2_projection` | 0.123849 | 0.331265 | 0.313472 | 0.000000 | -0.308550 |

### Fold B (Test Days: ['2026-06-12'])

| Configuration | AUC | PR-AUC | Brier Score | Max TSS | Delta AUC |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `Baseline History` | 0.509934 | 0.497485 | 0.281434 | 0.152182 | - |
| `History + hard_soft_ratio` | 0.503337 | 0.463170 | 0.356375 | 0.122806 | -0.006598 |
| `History + soft_band_mean` | 0.443997 | 0.451128 | 0.304688 | 0.263540 | -0.065937 |
| `History + pc1_projection` | 0.437899 | 0.447366 | 0.304172 | 0.158410 | -0.072035 |
| `History + pc2_projection` | 0.462795 | 0.452088 | 0.299120 | 0.108470 | -0.047140 |

### Fold C (Test Days: ['2026-06-11'])

*DEGENERATE FOLD (No classes present in test set)*

### Fold D (Test Days: ['2026-06-10'])

| Configuration | AUC | PR-AUC | Brier Score | Max TSS | Delta AUC |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `Baseline History` | 0.225990 | 0.410128 | 0.425348 | 0.000000 | - |
| `History + hard_soft_ratio` | 0.227948 | 0.410495 | 0.426367 | 0.000000 | 0.001958 |
| `History + soft_band_mean` | 0.239201 | 0.413388 | 0.425809 | 0.000000 | 0.013210 |
| `History + pc1_projection` | 0.238897 | 0.413300 | 0.425755 | 0.000000 | 0.012907 |
| `History + pc2_projection` | 0.225040 | 0.409814 | 0.424975 | 0.000000 | -0.000950 |

---

## 4. Fold Stability & Significance Audit (Tasks 2, 3, & 4B)

Summary statistics and permutation p-values over all non-degenerate folds.
Significant folds are defined as folds with empirical permutation p-value $p \le 0.05$ (1000 shuffles).

| Feature Name | Mean $\Delta$AUC | Std $\Delta$AUC | Positive Folds | Significant Folds | Consistency Class |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `hard_soft_ratio` | -0.073774 | 0.101112 | 1/3 | 0/3 | `mixed_sign` |
| `soft_band_mean` | -0.157938 | 0.188859 | 1/3 | 1/3 | `mixed_sign` |
| `pc1_projection` | -0.133774 | 0.151401 | 1/3 | 1/3 | `mixed_sign` |
| `pc2_projection` | -0.118880 | 0.135436 | 0/3 | 0/3 | `always_negative` |

---

## 5. Confidence Intervals & Permutation Significance Registry (Tasks 4 & 4B)

Detailing 95% Confidence Intervals (obtained via 1000 bootstrap draws) and empirical p-values (obtained via 1000 shuffles) for each feature and fold.

| Fold | Feature Name | Actual $\Delta$AUC | 95% Bootstrap CI | Permutation p-value | Significant ($p \le 0.05$) |
| :--- | :--- | :---: | :---: | :---: | :---: |
| `Fold A` | `hard_soft_ratio` | -0.216683 | [-0.258162, -0.172230] | 1.0000 | False |
| `Fold A` | `soft_band_mean` | -0.421086 | [-0.453603, -0.390525] | 1.0000 | False |
| `Fold A` | `pc1_projection` | -0.342195 | [-0.381575, -0.306178] | 1.0000 | False |
| `Fold A` | `pc2_projection` | -0.308550 | [-0.337339, -0.280899] | 1.0000 | False |
| `Fold B` | `hard_soft_ratio` | -0.006598 | [-0.045705, 0.030333] | 0.1860 | False |
| `Fold B` | `soft_band_mean` | -0.065937 | [-0.088903, -0.043883] | 0.9990 | False |
| `Fold B` | `pc1_projection` | -0.072035 | [-0.096527, -0.049768] | 1.0000 | False |
| `Fold B` | `pc2_projection` | -0.047140 | [-0.066848, -0.026824] | 0.9600 | False |
| `Fold D` | `hard_soft_ratio` | 0.001958 | [0.001232, 0.002648] | 0.9890 | False |
| `Fold D` | `soft_band_mean` | 0.013210 | [0.009861, 0.016705] | 0.0000 | True |
| `Fold D` | `pc1_projection` | 0.012907 | [0.010034, 0.016411] | 0.0000 | True |
| `Fold D` | `pc2_projection` | -0.000950 | [-0.002694, 0.000922] | 0.9660 | False |

---

## 6. Worst Day Audit (Task 5B)

Detailing best, worst, and absolute spread of $\Delta$AUC across non-degenerate folds.

| Feature Name | Best Fold $\Delta$AUC | Worst Fold $\Delta$AUC | Spread (Best - Worst) |
| :--- | :---: | :---: | :---: |
| `hard_soft_ratio` | 0.001958 | -0.216683 | 0.218641 |
| `soft_band_mean` | 0.013210 | -0.421086 | 0.434296 |
| `pc1_projection` | 0.012907 | -0.342195 | 0.355102 |
| `pc2_projection` | -0.000950 | -0.308550 | 0.307600 |

---

## 7. Task 5: Operator Robustness Table

Features ranked hierarchically by:
1. `positive_fold_count` (descending)
2. `significant_fold_count` (descending)
3. `minimum_delta_auc` (descending, rewarding worst-case performance)
4. `mean_delta_auc` (descending)
5. `variance` (ascending)

| Rank | Feature Name | Positive Folds | Significant Folds | Worst-Case $\Delta$AUC | Mean $\Delta$AUC | Variance |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: |
| 1 | `pc1_projection` | 1/3 | 1/3 | -0.342195 | -0.133774 | 2.292215e-02 |
| 2 | `soft_band_mean` | 1/3 | 1/3 | -0.421086 | -0.157938 | 3.566759e-02 |
| 3 | `hard_soft_ratio` | 1/3 | 0/3 | -0.216683 | -0.073774 | 1.022363e-02 |
| 4 | `pc2_projection` | 0/3 | 0/3 | -0.308550 | -0.118880 | 1.834300e-02 |
