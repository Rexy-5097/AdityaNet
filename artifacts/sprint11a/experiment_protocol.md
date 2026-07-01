# Version 2 Experiment Specification: SuryaNet Model Upgrade

This document outlines the formal experimental protocol for the SuryaNet Version 2 model upgrade. It defines the hypotheses, variables, evaluation and comparison processes, success criteria, and rollback triggers. All tests must be executed under strict reproducibility constraints.

---

## 1. Hypotheses

*   **Hypothesis 1 (H1 - Data Integration):**
    Integrating processed Aditya-L1 SoLEXS and HEL1OS telemetry alongside GOES flux features improves M/X-class solar flare forecasting True Skill Statistic (TSS) on the test split compared to the GOES-only baseline.
*   **Hypothesis 2 (H2 - Capacity Utilization):**
    Increasing the PatchTST parameter capacity (from 822,401 parameters up to 5,000,000 parameters) under the 10,000,000 parameter constraint allows the model to capture multi-scale temporal dynamics more effectively, thereby reducing validation loss.
*   **Hypothesis 3 (H3 - Optimization Convergence):**
    Training the PatchTST model to full convergence (plateauing validation loss) will decrease the Brier Score and Expected Calibration Error (ECE) compared to the 3-epoch under-converged baseline.

---

## 2. Experimental Variables

### Fixed Variables (No Changes Permitted)

| Variable | Baseline Value / Definition | Exact Reference |
| :--- | :--- | :--- |
| **Train Dataset Split** | `2010-01-02 00:30:00` to `2019-12-31 23:59:00` | [dataset_fingerprint.json](file:///Users/soumyadebtripathy/AdityaNet/artifacts/sprint10l/dataset_fingerprint.json) |
| **Validation Split** | `2020-01-01 00:00:00` to `2022-12-31 23:59:00` | [dataset_fingerprint.json](file:///Users/soumyadebtripathy/AdityaNet/artifacts/sprint10l/dataset_fingerprint.json) |
| **Test Dataset Split** | `2023-01-01 00:00:00` to `2026-06-14 23:51:00` | [dataset_fingerprint.json](file:///Users/soumyadebtripathy/AdityaNet/artifacts/sprint10l/dataset_fingerprint.json) |
| **Forecast Task** | Binary nowcast: M/X flare risk within next 6 hours | [model_fingerprint.json](file:///Users/soumyadebtripathy/AdityaNet/artifacts/sprint10l/model_fingerprint.json) |
| **Sequence Window** | 360 minutes (6 hours) | [model_fingerprint.json](file:///Users/soumyadebtripathy/AdityaNet/artifacts/sprint10l/model_fingerprint.json) |
| **Random Seed** | 42 | [model.py](file:///Users/soumyadebtripathy/AdityaNet/app/services/ml/model.py) |

### Allowed to Change (V2 Experimental Targets)

| Variable | Baseline Value | Proposed Experimental Bounds |
| :--- | :--- | :--- |
| **Input Features** | 14 GOES-only features | Include processed SoLEXS rates/channels and HEL1OS rates/bands |
| **Model Capacity** | 822,401 parameters (`EMBED_DIM=128`, `N_HEADS=8`, `N_LAYERS=4`, `FF_DIM=512`) | Up to 10,000,000 parameters (`EMBED_DIM=256`, `N_HEADS=16`, `N_LAYERS=6`, `FF_DIM=1024`) |
| **Training Epochs** | 3 epochs | Max 20 epochs; Early Stopping patience increased from 3 to 5 |
| **Calibration Layer** | Isotonic Regression | Platt scaling vs. Isotonic Regression vs. Temperature Scaling on Val Set |

---

## 3. Evaluation Protocol

1.  **Data Ingestion:**
    Load train, validation, and test splits. Align processed SoLEXS (`rate`, `counts`, `channel`) and HEL1OS (`rate`, `counts`, `energy_band`) telemetry data with GOES telemetry data chronologically based on matching timestamps.
2.  **Model Initialization:**
    Initialize the modified PatchTST architecture using seed `42`. Ensure the parameter budget does not exceed `10,000,000` parameters.
3.  **Training:**
    Train the model on the training split. Compute the training loss and validation loss at the end of each epoch.
4.  **Weights Selection:**
    Monitor True Skill Statistic (TSS) on the validation split. Save the model checkpoint corresponding to the epoch with the highest validation TSS.
5.  **Calibration Fit:**
    Evaluate calibration candidates (Platt scaling, Isotonic Regression, Temperature Scaling) on the validation raw predictions. Select the method resulting in the lowest validation Brier Score.
6.  **Threshold Tuning:**
    Determine operational thresholds (yellow and red alerts) on validation calibrated predictions. Ensure zero leakage of test set metrics or labels during this step.
7.  **Inference and Test Set Evaluation:**
    Execute stateless inference on the test split using the selected model, calibrator, and validation-tuned thresholds.

---

## 4. Comparison Protocol

Directly compare the test split performance metrics of the Version 2 model against the frozen baseline test set metrics snapshot:

*   **TSS:** Baseline = `0.2298`
*   **ROC-AUC:** Baseline = `0.7485`
*   **PR-AUC:** Baseline = `0.4950`
*   **Brier Score:** Baseline = `0.2365` (raw) / `0.1594` (calibrated)
*   **ECE:** Baseline = `0.2722` (raw) / `0.0876` (calibrated)
*   **Precision:** Baseline = `0.2865`
*   **Recall:** Baseline = `0.9286`
*   **False Alarm Ratio (FAR):** Baseline = `0.7135`

---

## 5. Success Criteria

*   **TSS Increase:** An absolute increase of $\ge 0.05$ on the test split compared to the baseline (`TSS >= 0.2798`).
*   **Calibration Quality:** Calibrated Expected Calibration Error (ECE) on the test split must remain $\le 0.10$.
*   **Data Leakage Constraint:** Zero test set leakage during feature engineering, model training, calibrator fitting, and threshold tuning.

---

## 6. Rollback Criteria

The experiment will be aborted, and the production system will roll back to the frozen baseline (Version 1) if any of the following occur:

1.  **Performance Degradation:**
    The test split TSS drops below the baseline of `0.2298`.
2.  **Overfitting:**
    Validation loss increases for $\ge 5$ consecutive epochs while training loss continues to decrease.
3.  **Latency Constraints:**
    The average real-time nowcast inference latency exceeds `1.0` second per sequence window.
