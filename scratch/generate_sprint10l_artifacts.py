import json
import os
import hashlib

REPO_ROOT = "/Users/soumyadebtripathy/AdityaNet"
OUT_DIR = os.path.join(REPO_ROOT, "artifacts/sprint10l")
os.makedirs(OUT_DIR, exist_ok=True)

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def fstat(path):
    s = os.stat(path)
    return {
        "relative_path": os.path.relpath(path, REPO_ROOT),
        "sha256": sha256(path),
        "file_size_bytes": s.st_size
    }

# ──────────────────────────────────────────────────────────────────────────────
# 1. Dataset Fingerprint
# ──────────────────────────────────────────────────────────────────────────────
dataset_fp = {
    "version": "1.0.0",
    "status": "FROZEN",
    "production_datasets": {
        "train.parquet": {
            "relative_path": "artifacts/research/train.parquet",
            "version": "1.0.0",
            "date_range": "2010-01-02 00:30:00 to 2019-12-31 23:59:00",
            "number_of_rows": 5161312,
            "number_of_windows": 5160952,
            "number_of_positive_labels": 31993,
            "number_of_negative_labels": 5128959,
            "sha256": "e31493d60255e9cc27a944e30ea19c67cb580376dc638f545962687e9fb8f518",
            "size_bytes": 422678025
        },
        "validation.parquet": {
            "relative_path": "artifacts/research/validation.parquet",
            "version": "1.0.0",
            "date_range": "2020-01-01 00:00:00 to 2022-12-31 23:59:00",
            "number_of_rows": 1568759,
            "number_of_windows": 1568399,
            "number_of_positive_labels": 63849,
            "number_of_negative_labels": 1504550,
            "sha256": "9c1b770f22684abc0a21fb5ba3233cf80a5768619fe868763c0af0b73acff8d4",
            "size_bytes": 138691501
        },
        "test.parquet": {
            "relative_path": "artifacts/research/test.parquet",
            "version": "1.0.0",
            "date_range": "2023-01-01 00:00:00 to 2026-06-14 23:51:00",
            "number_of_rows": 1806673,
            "number_of_windows": 1806313,
            "number_of_positive_labels": 419150,
            "number_of_negative_labels": 1387163,
            "sha256": "3f2b270f98a2480b37637f7e5461e5cc02ac8392d8af2ca9243cb3ad5edc5441",
            "size_bytes": 163280890
        },
        "goes_full.parquet": {
            "relative_path": "artifacts/research/goes_full.parquet",
            "version": "raw",
            "date_range": "2010-01-02 00:00:00 to 2026-06-14 23:59:00",
            "number_of_rows": 8631360,
            "number_of_windows": 8631360,
            "number_of_positive_labels": "N/A",
            "number_of_negative_labels": "N/A",
            "sha256": "65d85524c7ba955e835534ad120fadbff877b4fbbff50f824a79189f9c45b616",
            "size_bytes": 155043819
        },
        "flares_full.parquet": {
            "relative_path": "artifacts/research/flares_full.parquet",
            "version": "raw",
            "date_range": "N/A",
            "number_of_rows": 21945,
            "number_of_windows": 21945,
            "number_of_positive_labels": "N/A",
            "number_of_negative_labels": "N/A",
            "sha256": "536842648c3891e59b7fb68e86b1dd720fe59c36749d5636c24b61e90bae499a",
            "size_bytes": 936034
        }
    }
}
with open(os.path.join(OUT_DIR, "dataset_fingerprint.json"), "w") as f:
    json.dump(dataset_fp, f, indent=2)

# ──────────────────────────────────────────────────────────────────────────────
# 2. Model Fingerprint
# ──────────────────────────────────────────────────────────────────────────────
model_fp = {
    "architecture": "PatchTST (CLS-token variant, multivariate-patch)",
    "number_of_parameters": 822401,
    "trainable_parameters": 822401,
    "checkpoint_hash": "010dc798b2a4625365d1551c2f7710ba3eb23d5eaada2145cb9bcf947ca21484",
    "checkpoint_size_bytes": 9957975,
    "checkpoint_file_path": "artifacts/models/patchtst_best.pt",
    "training_epochs": 3,
    "optimizer": "AdamW (lr=1e-4, weight_decay=1e-4, clip_norm=1.0)",
    "scheduler": "CosineAnnealingLR (T_max=20)",
    "loss_function": "Focal Loss (gamma=2.0, alpha=0.25)",
    "dropout": 0.2,
    "window_length_minutes": 360,
    "feature_count": 14,
    "input_tensor_shape": "[batch, seq_len=360, n_features=14]",
    "output_definition": "Single raw logit [batch, 1] representing M/X flare risk within 6 hours"
}
with open(os.path.join(OUT_DIR, "model_fingerprint.json"), "w") as f:
    json.dump(model_fp, f, indent=2)

# ──────────────────────────────────────────────────────────────────────────────
# 3. Environment Fingerprint
# ──────────────────────────────────────────────────────────────────────────────
env_fp = {
    "python_version": "3.14.4 (main, Apr  7 2026, 13:13:20) [Clang 21.0.0 (clang-2100.0.123.102)]",
    "torch_version": "2.9.1",
    "numpy_version": "2.3.5",
    "pandas_version": "2.3.3",
    "system_platform": "macOS-26.5.1-arm64-arm-64bit-Mach-O",
    "system_processor": "arm",
    "mps_available": True,
    "cuda_available": False,
    "random_seeds": {
        "torch_manual_seed": 42,
        "numpy_random_seed": "NOT EXPLICITLY SET IN CODE",
        "python_random_seed": "NOT EXPLICITLY SET IN CODE"
    },
    "deterministic_settings": {
        "torch_backends_cudnn_deterministic": "N/A",
        "torch_backends_mps_deterministic": "N/A",
        "torch_use_deterministic_algorithms": False
    }
}
with open(os.path.join(OUT_DIR, "environment_fingerprint.json"), "w") as f:
    json.dump(env_fp, f, indent=2)

# ──────────────────────────────────────────────────────────────────────────────
# 4. Production Metrics Snapshot
# ──────────────────────────────────────────────────────────────────────────────
metrics_snapshot = {
    "baseline_test_metrics": {
        "threshold": 0.33666666666666667,
        "roc_auc": 0.7485138191198613,
        "pr_auc": 0.49504222148278926,
        "tss": 0.22978874475124356,
        "precision": 0.2864895500196892,
        "recall": 0.928615054276512,
        "f1": 0.43788577230398845,
        "false_alarm_ratio_far": 0.7135104499803109,
        "probability_of_false_detection_pofd": 0.6988263095252685,
        "brier_score": 0.23647454380989075,
        "confusion_matrix": {
            "tp": 389229,
            "fp": 969386,
            "fn": 29921,
            "tn": 417777
        }
    },
    "calibrator_comparison": {
        "selected_method": "isotonic",
        "raw": {
            "brier": 0.23647450222602825,
            "ece": 0.27219248784172617,
            "roc_auc": 0.7485138191198613,
            "pr_auc": 0.49504222148278926
        },
        "platt": {
            "brier": 0.17087707233155602,
            "ece": 0.12027284253876283,
            "roc_auc": 0.7485138191938172,
            "pr_auc": 0.49504222019454946
        },
        "isotonic": {
            "brier": 0.15940616741357702,
            "ece": 0.08761919752821726,
            "roc_auc": 0.7482077950174735,
            "pr_auc": 0.4747129609890704
        }
    },
    "maximum_calibration_error_mce": "NOT FOUND / NOT COMPUTED IN REPOSITORY"
}
with open(os.path.join(OUT_DIR, "production_metrics_snapshot.json"), "w") as f:
    json.dump(metrics_snapshot, f, indent=2)

# ──────────────────────────────────────────────────────────────────────────────
# 5. Repository Fingerprint V1
# ──────────────────────────────────────────────────────────────────────────────
repo_fp_v1 = {
    "audit_timestamp_utc": "2026-06-19T10:38:17Z",
    "pipeline_version": "1.5.0-SprintDA03C",
    "fingerprints": {
        "model_weights": fstat(os.path.join(REPO_ROOT, "artifacts/models/patchtst_best.pt")),
        "calibrator_pkl": fstat(os.path.join(REPO_ROOT, "artifacts/calibrator.pkl")),
        "operator_thresholds_json": fstat(os.path.join(REPO_ROOT, "artifacts/operator_thresholds.json")),
        "operator_thresholds_val_only_json": fstat(os.path.join(REPO_ROOT, "artifacts/operator_thresholds_validation_only.json")),
        "operational_thresholds_json": fstat(os.path.join(REPO_ROOT, "artifacts/operational_thresholds.json")),
        "feature_columns_json": fstat(os.path.join(REPO_ROOT, "artifacts/feature_columns.json")),
        "training_history_json": fstat(os.path.join(REPO_ROOT, "artifacts/training_history.json")),
        "explainability_examples_json": fstat(os.path.join(REPO_ROOT, "artifacts/explainability_examples.json")),
        "attention_statistics_json": fstat(os.path.join(REPO_ROOT, "artifacts/attention_statistics.json")),
        "prediction_certificate_json": fstat(os.path.join(REPO_ROOT, "artifacts/sprint10j/prediction_certificate.json")),
        "execution_manifest_json": fstat(os.path.join(REPO_ROOT, "artifacts/sprint10j/execution_manifest.json")),
        "repository_fingerprint_json": fstat(os.path.join(REPO_ROOT, "artifacts/sprint10j/repository_fingerprint.json")),
        "artifact_hashes_json": fstat(os.path.join(REPO_ROOT, "artifacts/sprint10j/artifact_hashes.json")),
        "operator_workflow_trace_json": fstat(os.path.join(REPO_ROOT, "artifacts/sprint10k/operator_workflow_trace.json")),
        "component_reference_graph_json": fstat(os.path.join(REPO_ROOT, "artifacts/sprint10k/component_reference_graph.json")),
        "app_services_ml_inference_py": fstat(os.path.join(REPO_ROOT, "app/services/ml/inference.py")),
        "app_services_ml_model_py": fstat(os.path.join(REPO_ROOT, "app/services/ml/model.py")),
        "app_services_ml_dataset_py": fstat(os.path.join(REPO_ROOT, "app/services/ml/dataset.py")),
        "app_services_ml_explainability_py": fstat(os.path.join(REPO_ROOT, "app/services/ml/explainability.py")),
        "app_services_operations_impact_py": fstat(os.path.join(REPO_ROOT, "app/services/operations/impact.py")),
        "app_api_v1_endpoints_inference_py": fstat(os.path.join(REPO_ROOT, "app/api/v1/endpoints/inference.py"))
    }
}
with open(os.path.join(OUT_DIR, "repository_fingerprint_v1.json"), "w") as f:
    json.dump(repo_fp_v1, f, indent=2)

# ──────────────────────────────────────────────────────────────────────────────
# 6. Baseline Certificate (Master File - Preliminary)
# ──────────────────────────────────────────────────────────────────────────────
baseline_cert = {
    "certificate_id": "SURYANET-PROD-BASELINE-V1",
    "timestamp_utc": "2026-06-19T10:38:17Z",
    "pipeline_version": "1.5.0-SprintDA03C",
    "status": "FROZEN",
    "sha256_digests": {
        "baseline_certificate_md": "CALCULATED_LATER",
        "model_fingerprint_json": sha256(os.path.join(OUT_DIR, "model_fingerprint.json")),
        "dataset_fingerprint_json": sha256(os.path.join(OUT_DIR, "dataset_fingerprint.json")),
        "environment_fingerprint_json": sha256(os.path.join(OUT_DIR, "environment_fingerprint.json")),
        "production_metrics_snapshot_json": sha256(os.path.join(OUT_DIR, "production_metrics_snapshot.json")),
        "repository_fingerprint_v1_json": sha256(os.path.join(OUT_DIR, "repository_fingerprint_v1.json"))
    },
    "operator_pipeline_references": {
        "prediction_certificate": "artifacts/sprint10j/prediction_certificate.json",
        "execution_manifest": "artifacts/sprint10j/execution_manifest.json",
        "repository_fingerprint": "artifacts/sprint10j/repository_fingerprint.json",
        "artifact_hashes": "artifacts/sprint10j/artifact_hashes.json",
        "operator_workflow_trace": "artifacts/sprint10k/operator_workflow_trace.json",
        "dependency_graph": "artifacts/sprint10k/component_reference_graph.json"
    },
    "calibration_references": {
        "calibrator_type": "isotonic",
        "artifact_hash": "36fe68d47207b371b963744151666d533b3885885e46dfd12c99061b68d327ac",
        "threshold_policy_hash": "8e76ee49ef776755b0f717dc69deb3db91526f670e26889195a59d72a862922b",
        "calibration_artifact_path": "artifacts/calibrator.pkl",
        "threshold_artifact_path": "artifacts/operator_thresholds_validation_only.json",
        "validation_split_used": "artifacts/research/validation.parquet"
    }
}
with open(os.path.join(OUT_DIR, "baseline_certificate.json"), "w") as f:
    json.dump(baseline_cert, f, indent=2)

# Write MD file with verified hashes
md_content = f"""# Sprint 10L — Production Baseline Freeze & Reproducibility Certificate
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
"""

md_path = os.path.join(OUT_DIR, "baseline_certificate.md")
with open(md_path, "w") as f:
    f.write(md_content)

# Update baseline_certificate.json with md hash
baseline_cert["sha256_digests"]["baseline_certificate_md"] = sha256(md_path)
with open(os.path.join(OUT_DIR, "baseline_certificate.json"), "w") as f:
    json.dump(baseline_cert, f, indent=2)

print("Updated baseline_certificate.json with final MD hash.")
