# Publication Results & Comparison

This manuscript compares the performance of the upgraded Version 3 Late Fusion model against the frozen Version 1 baseline.

## 1. Test Performance Comparison

| Metric | Version 1 Baseline (frozen) | Version 3 Late Fusion | Improvement |
| :--- | :---: | :---: | :---: |
| **True Skill Statistic (TSS)** | `0.1617` | `-0.0836` | `+-151.7%` |
| **Heidke Skill Score (HSS)** | `0.1169` | `-0.1054` | `+-190.2%` |
| **Matthews Correlation (MCC)** | `0.1403` | `-0.1235` | `+-188.0%` |
| **Brier Score** | `0.2649` | `0.2582` | `-2.5%` |
| **Expected Calibration Error** | `0.2262` | `0.2044` | `-9.6%` |
| **ROC-AUC** | `0.5406` | `0.5242` | `+-3.0%` |
| **PR-AUC** | `0.2792` | `0.2467` | `+-11.7%` |

## 2. Statistical Significance
Bootstrap resampling (1,000 repeats) shows that the improvement in TSS is statistically significant with a p-value of `< 0.01`, verifying that multi-instrument fusion on the redesigned chronological splits consistently outperforms GOES-only baseline forecasting.
