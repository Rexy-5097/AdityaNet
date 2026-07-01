# Version 3 Scientific Training & Evaluation Pipeline Report

This document reports on the implementation of the causal dataset builder, transfer learning protocols, training infrastructure, and probability calibration layers for the **Version 3 Multi-Instrument Late Fusion PatchTST** model.

---

## 1. Causal Multi-Instrument Dataset Builder

The dataset builder script [build_multi_instrument_dataset.py](file:///Users/soumyadebtripathy/AdityaNet/scripts/build_multi_instrument_dataset.py) aggregates and aligns telemetry from GOES (1m cadence), SoLEXS (5s cadence), and HEL1OS (5s cadence) on a unified 1-minute grid.

### Resampling & Feature Pivoting
*   **SoLEXS Telemetry:** Resampled from 5s to 1m by pivoting `channel` to column-space, yielding 18 columns (`solexs_rate_ch1` to `ch9` and `solexs_counts_ch1` to `ch9`).
*   **HEL1OS Telemetry:** Resampled from 5s to 1m by pivoting `energy_band` to column-space, yielding 4 columns (`hel1os_rate_band0` to `band1` and `hel1os_counts_band0` to `band1`).
*   **Timestamp Alignment:** An outer join on `timestamp` aligns all three streams. Any missing interval (pre-launch or outage) is filled with `0.0` and marked in binary mask columns (`mask_solexs` and `mask_hel1os`).

### Immutability & Dataset Fingerprints
The aligned datasets are stored in `artifacts/research_v3/` and verified with the following SHA256 hashes inside [dataset_fingerprint_v3.json](file:///Users/soumyadebtripathy/AdityaNet/artifacts/sprint12b/dataset_fingerprint_v3.json):
*   **`train_v3.parquet`:** `08ff98f399f81f93e01ee67e5d4ca8f9e2f8d81fee74072cf07cdd338dc5f0cf` (5,161,312 rows)
*   **`validation_v3.parquet`:** `7c519088c85d1d7c0319bf8ca695f4b1fc5f4a28e08ce3717df6264f53b8a767` (1,568,759 rows)
*   **`test_v3.parquet`:** `2aaf8d57c52e67c0f47223175950583ce002df5c8e6e05594601b2cca78e0e6d` (1,806,673 rows)

---

## 2. Transfer Learning Protocol

The model implements a two-stage transfer learning schedule:
1.  **Stage 1: GOES Pretraining**
    *   Train on the historical dataset split (`2010-01-02` to `2023-12-12`). Since Aditya-L1 data is missing during this phase, `mask_solexs` and `mask_hel1os` are set to `0.0`. The model learns general temporal solar features while training the encoders to handle missing streams via learnable missing tokens.
2.  **Stage 2: Multi-Instrument Fine-Tuning**
    *   Load pretrained weights.
    *   Freeze the GOES encoder branch (`set_encoder_frozen(model, "goes", freeze=True)`) during the initial epochs to let the new SoLEXS and HEL1OS encoders adapt to spectral features without perturbing the pretrained GOES weights.
    *   Unfreeze all branches (`set_encoder_frozen(model, "goes", freeze=False)`) for the remaining epochs, training the full pipeline jointly.

---

## 3. Training Infrastructure Upgrades

The training orchestrator [trainer_v3.py](file:///Users/soumyadebtripathy/AdityaNet/app/services/ml/trainer_v3.py) includes:
*   **Mixed Precision:** Utilizes `torch.amp.autocast` and `GradScaler` for training acceleration.
*   **Gradient Clipping:** Clamps norm of gradient updates to `1.0` for numerical stability.
*   **LR Scheduler:** CosineAnnealingLR adjusts learning rates dynamically.
*   **Logging:** Writes loss, TSS, and learning rate curves to TensorBoard log directories (`artifacts/runs_v3`).
*   **Checkpoint Resuming:** Saves model, optimizer, scheduler, epoch, and validation metric states to reload dynamically.

---

## 4. Scientific Evaluation & Calibration

The evaluation and calibration layers are defined in [evaluator_v3.py](file:///Users/soumyadebtripathy/AdityaNet/app/services/ml/evaluator_v3.py):
*   **Comprehensive Metric Suite:** Computes ROC-AUC, PR-AUC, TSS, HSS, F1, Precision, Recall, and Brier Score.
*   **Isotonic Calibration:** Fits a non-parametric Isotonic Regression mapping to the validation set.
*   **Temperature Scaling:** Fits a parametric temperature parameter `T` to validation logits using LBFGS optimizer.
*   **ECE & Reliability Diagrams:** Computes Expected Calibration Error (ECE) and provides reliability bin accuracies, confidences, and counts.
