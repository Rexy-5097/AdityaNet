# Sprint 10L — Production Baseline Freeze & Reproducibility Certificate
**Certificate ID:** `SURYANET-PROD-BASELINE-V1`  
**Freezing Timestamp (UTC):** `2026-06-19T10:38:17Z`  
**Pipeline Version:** `1.5.0-SprintDA03C`  
**Status:** **FROZEN** (Immutable Production Baseline)

---

## Executive Summary

This document certifies the immutable freeze of the SuryaNet PatchTST production model, calibration layer, dataset assets, pipeline configurations, metrics snapshot, and execution environment as Version 1. 

> [!IMPORTANT]
> This is a read-only freezing and evidence collection sprint. No code has been modified, no weights altered, no thresholds adjusted, and no datasets changed. This baseline serves as the ground truth reference point prior to any future model retraining.

---

## 1. Dataset Freeze

The production pipeline utilizes the following frozen data assets. All samples, date ranges, and hashes are recorded exactly as observed in the repository.

| Dataset File | Relative Path | Date Range | Rows | Valid Windows | Positives | Negatives | SHA256 Hash | Size (bytes) |
|---|---|---|---|---|---|---|---|---|
| Train Set | [train.parquet](file:///Users/soumyadebtripathy/AdityaNet/artifacts/research/train.parquet) | 2010-01-02 00:30:00 to 2019-12-31 23:59:00 | 5,161,312 | 5,160,952 | 31,993 | 5,128,959 | `e31493d60255e9cc27a944e30ea19c67cb580376dc638f545962687e9fb8f518` | 422,678,025 |
| Validation Set | [validation.parquet](file:///Users/soumyadebtripathy/AdityaNet/artifacts/research/validation.parquet) | 2020-01-01 00:00:00 to 2022-12-31 23:59:00 | 1,568,759 | 1,568,399 | 63,849 | 1,504,550 | `9c1b770f22684abc0a21fb5ba3233cf80a5768619fe868763c0af0b73acff8d4` | 138,691,501 |
| Test Set | [test.parquet](file:///Users/soumyadebtripathy/AdityaNet/artifacts/research/test.parquet) | 2023-01-01 00:00:00 to 2026-06-14 23:51:00 | 1,806,673 | 1,806,313 | 419,150 | 1,387,163 | `3f2b270f98a2480b37637f7e5461e5cc02ac8392d8af2ca9243cb3ad5edc5441` | 163,280,890 |
| GOES Telemetry | [goes_full.parquet](file:///Users/soumyadebtripathy/AdityaNet/artifacts/research/goes_full.parquet) | 2010-01-02 00:00:00 to 2026-06-14 23:59:00 | 8,631,360 | 8,631,360 | N/A | N/A | `65d85524c7ba955e835534ad120fadbff877b4fbbff50f824a79189f9c45b616` | 155,043,819 |
| Flare Catalog | [flares_full.parquet](file:///Users/soumyadebtripathy/AdityaNet/artifacts/research/flares_full.parquet) | N/A | 21,945 | 21,945 | N/A | N/A | `536842648c3891e59b7fb68e86b1dd720fe59c36749d5636c24b61e90bae499a` | 936,034 |

---

## 2. Model Freeze

The active production neural network is locked with the parameters cataloged below.

### Model Architecture and Parameters
* **Architecture:** PatchTST (CLS-token variant, multivariate-patch)
* **Total Parameters:** `822,401`
* **Trainable Parameters:** `822,401`
* **Model Checkpoint Path:** [patchtst_best.pt](file:///Users/soumyadebtripathy/AdityaNet/artifacts/models/patchtst_best.pt)
* **Checkpoint SHA256 Hash:** `010dc798b2a4625365d1551c2f7710ba3eb23d5eaada2145cb9bcf947ca21484`
* **Checkpoint Size:** 9,957,975 bytes
* **Training Epochs:** 3 (stopped early at best validation TSS epoch)
* **Optimizer Configuration:** `AdamW (lr=1e-4, weight_decay=1e-4, clip_norm=1.0)`
* **Scheduler Configuration:** `CosineAnnealingLR (T_max=20)`
* **Loss Function:** `Focal Loss (gamma=2.0, alpha=0.25)`
* **Dropout Rate:** 0.2
* **Sequence Window Length:** 360 minutes
* **Feature Count:** 14 features (defined in [`feature_columns.json`](file:///Users/soumyadebtripathy/AdityaNet/artifacts/feature_columns.json))
* **Input Tensor Shape:** `[batch, seq_len=360, n_features=14]`
* **Output Definition:** Single raw logit `[batch, 1]` representing M/X solar flare risk within 6 hours.

---

## 3. Calibration Freeze

The calibration layer mappings and configurations are locked as follows:

* **Calibrator Type:** Isotonic Regression
* **Calibrator Artifact Path:** [calibrator.pkl](file:///Users/soumyadebtripathy/AdityaNet/artifacts/calibrator.pkl)
* **Calibrator SHA256 Hash:** `36fe68d47207b371b963744151666d533b3885885e46dfd12c99061b68d327ac`
* **Active Threshold Policy Path:** [operator_thresholds_validation_only.json](file:///Users/soumyadebtripathy/AdityaNet/artifacts/operator_thresholds_validation_only.json) (Validation-only split policy to avoid test leakage)
* **Threshold Policy SHA256 Hash:** `8e76ee49ef776755b0f717dc69deb3db91526f670e26889195a59d72a862922b`
* **Validation Split Used:** [`validation.parquet`](file:///Users/soumyadebtripathy/AdityaNet/artifacts/research/validation.parquet)

---

## 4. Performance Freeze

Existing model metrics are snapshot below. No new metrics were computed for this freeze.

### Baseline Test Metrics (Threshold = 0.3367)
* **ROC-AUC:** `0.7485138191198613`
* **PR-AUC:** `0.49504222148278926`
* **TSS:** `0.22978874475124356`
* **Precision:** `0.2864895500196892`
* **Recall:** `0.928615054276512`
* **F1:** `0.43788577230398845`
* **False Alarm Ratio (FAR):** `0.7135104499803109`
* **Probability of False Detection (POFD):** `0.6988263095252685`
* **Brier Score:** `0.23647454380989075`
* **Confusion Matrix:** 
  - True Positives (TP): `389,229`
  - False Positives (FP): `969,386`
  - False Negatives (FN): `29,921`
  - True Negatives (TN): `417,777`

### Calibration Comparison

| Metric | Raw Baseline | Platt Scaling | Isotonic Regression |
|---|---|---|---|
| Brier Score | `0.236474502226` | `0.170877072332` | `0.159406167414` |
| Expected Calibration Error (ECE) | `0.272192487842` | `0.120272842539` | `0.087619197528` |
| ROC-AUC | `0.748513819120` | `0.748513819194` | `0.748207795017` |
| PR-AUC | `0.495042221483` | `0.495042220195` | `0.474712960989` |

> [!NOTE]
> **Maximum Calibration Error (MCE):** NOT FOUND. The MCE metric is not computed or stored in any repository artifacts and is left as unspecified.

---

## 5. Operator Pipeline Freeze

The following operator-facing and traceability components are fingerprinted for compliance.

| Pipeline Artifact | File Path | SHA256 Hash |
|---|---|---|
| Prediction Certificate | [prediction_certificate.json](file:///Users/soumyadebtripathy/AdityaNet/artifacts/sprint10j/prediction_certificate.json) | `5eb4bc4d1c1e67e366e7c8cab05da22d653bacb70704de4a5e2ef9855a2351b7` |
| Execution Manifest | [execution_manifest.json](file:///Users/soumyadebtripathy/AdityaNet/artifacts/sprint10j/execution_manifest.json) | `ea1410f31030fa29b7c00cc3f62a7db0f3a9e8d89b4d9c7937a89bfd6d419a92` |
| Repository Fingerprint | [repository_fingerprint.json](file:///Users/soumyadebtripathy/AdityaNet/artifacts/sprint10j/repository_fingerprint.json) | `08df03013d474b58c98dd76da43d62080257dc8fe85956cd554d88fdd23ed3d4` |
| Artifact Hashes | [artifact_hashes.json](file:///Users/soumyadebtripathy/AdityaNet/artifacts/sprint10j/artifact_hashes.json) | `9f4af7b3a5fa403d51de4248c6fd74da15eba1035524e0053958e44f0643143e` |
| Operator Workflow Trace | [operator_workflow_trace.json](file:///Users/soumyadebtripathy/AdityaNet/artifacts/sprint10k/operator_workflow_trace.json) | `71ef64163776ba74e023b9f97c58a260c379404cc5d19db0d9ad0cbb9c784851` |
| Dependency Graph | [component_reference_graph.json](file:///Users/soumyadebtripathy/AdityaNet/artifacts/sprint10k/component_reference_graph.json) | `7f56a299eca56a2416ec3ab1e4f5a3fd6a22a6439918f7fcfcf611d22b54f20c` |

---

## 6. Environment Freeze

The software environment and hardware execution configurations are locked as follows.

* **Python Version:** `3.14.4 (main, Apr  7 2026, 13:13:20) [Clang 21.0.0 (clang-2100.0.123.102)]`
* **Torch Version:** `2.9.1`
* **Numpy Version:** `2.3.5`
* **Pandas Version:** `2.3.3`
* **System Platform:** `macOS-26.5.1-arm64-arm-64bit-Mach-O`
* **System Processor:** `arm (Apple Silicon)`
* **MPS Available:** `True` (Metal Performance Shaders accelerated GPU)
* **CUDA Available:** `False`
* **Random Seeds:**
  - `torch_manual_seed`: 42
  - `numpy_random_seed`: `NOT EXPLICITLY SET IN CODE`
  - `python_random_seed`: `NOT EXPLICITLY SET IN CODE`
* **Deterministic Settings:**
  - `torch.use_deterministic_algorithms`: `False`

---

## 7. Deliverables Register

All deliverables are registered under [artifacts/sprint10l/](file:///Users/soumyadebtripathy/AdityaNet/artifacts/sprint10l/):

* [baseline_certificate.json](file:///Users/soumyadebtripathy/AdityaNet/artifacts/sprint10l/baseline_certificate.json)
* [baseline_certificate.md](file:///Users/soumyadebtripathy/AdityaNet/artifacts/sprint10l/baseline_certificate.md)
* [model_fingerprint.json](file:///Users/soumyadebtripathy/AdityaNet/artifacts/sprint10l/model_fingerprint.json)
* [dataset_fingerprint.json](file:///Users/soumyadebtripathy/AdityaNet/artifacts/sprint10l/dataset_fingerprint.json)
* [environment_fingerprint.json](file:///Users/soumyadebtripathy/AdityaNet/artifacts/sprint10l/environment_fingerprint.json)
* [production_metrics_snapshot.json](file:///Users/soumyadebtripathy/AdityaNet/artifacts/sprint10l/production_metrics_snapshot.json)
* [repository_fingerprint_v1.json](file:///Users/soumyadebtripathy/AdityaNet/artifacts/sprint10l/repository_fingerprint_v1.json)
