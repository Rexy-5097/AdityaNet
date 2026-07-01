# SuryaNet V3 Scientific Evaluation & Ablation Protocol

## 1. Dataset Splits
*   **Validation Split**: Chronological validation parquet (`artifacts/sprint14c/s2_val.parquet`, 262,120 windows). Used for early stopping and threshold search.
*   **Chronological Test Split**: Chronological test parquet (`artifacts/sprint14c/s2_test.parquet`, 261,095 windows). Used only for final evaluation.

## 2. Target Metrics
Models will be evaluated against:
*   **Primary Metric**: TSS (Total Skill Score)
*   **Secondary Metrics**: HSS, MCC, PR-AUC, ROC-AUC, Brier Score, ECE

## 3. Operator-Specific Metrics
To align performance with satellite operations, the final evaluation must compute:
*   **Recall for X-class Flares**: Fraction of X-class flares correctly warned.
*   **Recall for M-class Flares**: Fraction of M-class flares correctly warned.
*   **False Alarms Per Day**: Count of false alarms scaled to a 24-hour period.
*   **Average & Median Warning Lead Time**: Time between alert trigger and peak flare time.
*   **Probability Stability**: Flip rate of probabilities under +5% input noise.
*   **Time Between Repeated Alerts**: Re-trigger interval to prevent alarm fatigue.
*   **Miss Rate During Telemetry Outages**: Model error rate when SoLEXS or HEL1OS is missing.

## 4. Calibration & Threshold Search
*   **Calibration**: Isotonic Regression wrapper loaded from `evaluator_v3.py`.
*   **Threshold Search**: Exhaustive sweep over validation set probabilities to find the threshold maximizing TSS.
*   **Bootstrap**: 10,000 bootstrap iterations on the test set to compute 95% confidence intervals for all metrics.

## 5. Uncertainty Protocol
*   **Uncertainty Limits**: Acceptable epistemic uncertainty (MC Dropout std) must be < 0.10.
*   **Confidence Levels**: Mapped to HIGH (prob \ge threshold, unc < 0.05), MEDIUM (unc < 0.10), and LOW (unc \ge 0.10).
*   **Abstention Policy**: Alerts with low confidence (unc \ge 0.10) must downgrade to YELLOW or GREEN to suppress false alarms.

## 6. Instrument Ablation Plan
To isolate the predictive utility of Aditya-L1 instruments:
1.  **GOES Only**: Mask SoLEXS and HEL1OS entirely.
2.  **GOES + SoLEXS**: Mask HEL1OS entirely.
3.  **GOES + HEL1OS**: Mask SoLEXS entirely.
4.  **GOES + SoLEXS + HEL1OS**: Full multi-instrument configuration.
5.  **Remove Uncertainty**: Evaluate without MC Dropout (sampling variance ignored).
6.  **Remove Flare History**: Mask `minutes_since_last_flare` to test pure telemetry dependence.
