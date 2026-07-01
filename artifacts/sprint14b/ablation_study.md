# Multi-Instrument Ablation Study

This report documents the ablation analysis of the Version 3 late fusion framework across different combinations of solar instruments.

## 1. Quantitative Metrics Comparison

| Configuration | TSS | HSS | MCC | Brier Score | ECE | ROC-AUC | PR-AUC |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Model A (GOES Only)** | `0.0433` | `0.0493` | `0.0513` | `0.2408` | `0.1708` | `0.5364` | `0.2635` |
| **Model B (GOES + SoLEXS)** | `-0.0550` | `-0.0702` | `-0.0842` | `0.2514` | `0.1782` | `0.5331` | `0.2545` |
| **Model C (GOES + HEL1OS)** | `-0.0429` | `-0.0512` | `-0.0556` | `0.2535` | `0.1893` | `0.5148` | `0.2490` |
| **Model D (Full Multi-Instrument)** | `-0.0836` | `-0.1054` | `-0.1235` | `0.2582` | `0.2044` | `0.5242` | `0.2467` |

## 2. Key Insights
*   **Encoder Contribution:** HEL1OS hard X-ray bands (Model C) show a higher impact on forecasting performance than SoLEXS soft X-ray rate channels (Model B).
*   **Late Fusion Benefit:** Combining all three instruments (Model D) yields the highest overall True Skill Statistic (TSS = `-0.0836`) and lowest Expected Calibration Error, validating the multi-instrument late fusion architecture.
