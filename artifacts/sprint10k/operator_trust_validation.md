# Sprint 10K-V — Independent Operator Trust Verification Report

**Audit Sprint:** 10K-V  
**Audit Timestamp:** 2026-06-19T10:27:53Z  
**Verification Status:** FAIL  

---

## 1. Executive Summary

This report contains the findings of an independent verification audit on the operator trust pipeline, artifacts, and consistency chains of Sprint 10K. 

> [!NOTE]
> This audit has been performed in strict adherence to verification principles:
> 1. No repository code or artifacts have been modified.
> 2. No training processes have been executed.
> 3. No recommendations or fixes are proposed.
> 4. Factual compliance and existence of all components are reported directly.

---

## 2. Verification Checklist

The compliance status of all required artifacts and components is tabulated below.

### A. Operator-Facing Artifacts
| Path | Status | HASH | Size (bytes) |
|---|---|---|---|
| `artifacts/operator_thresholds.json` | FOUND | `033063ef0dfcae97` | 696 |
| `artifacts/operator_thresholds_validation_only.json` | FOUND | `8e76ee49ef776755` | 1,114 |
| `artifacts/operational_thresholds.json` | FOUND | `e7a52a617535e34b` | 103 |
| `artifacts/calibrator.pkl` | FOUND | `36fe68d47207b371` | 2,091 |
| `artifacts/explainability_examples.json` | FOUND | `5fedeb8cb9162f70` | 7,838 |
| `artifacts/attention_statistics.json` | FOUND | `2e8795cbb4e6cb25` | 3,794 |
| `artifacts/operator_alert_statistics.csv` | FOUND | `055f576164768e42` | 3,266,675 |
| `artifacts/backtest_window_predictions.csv` | FOUND | `7b55b5a1a70474d3` | 3,713,184 |
| `artifacts/operator_backtest.json` | FOUND | `dc21faa3c251f4b9` | 908 |
| `artifacts/operator_readiness_report.json` | FOUND | `b3697d0d8ce4a10f` | 1,095 |
| `artifacts/operator_trust_audit.json` | FOUND | `fa7322eefc1cb862` | 12,464 |
| `artifacts/operator_trust_projection.json` | FOUND | `7abcb1eaf9cb33fc` | 974 |
| `artifacts/aditya_l1_trust_gate_audit.md` | FOUND | `2443d5e551348693` | 10,086 |
| `artifacts/sprint10k/operator_trust_inventory.json` | FOUND | `89206f8ef712cd63` | 6,960 |
| `artifacts/sprint10k/operator_trust_inventory.md` | FOUND | `0709a1b2a779d207` | 10,876 |
| `artifacts/sprint10k/component_reference_graph.json` | FOUND | `7f56a299eca56a24` | 2,739 |
| `artifacts/sprint10k/frontend_backend_mapping.json` | FOUND | `a2c104f011ccf6e3` | 4,057 |
| `artifacts/sprint10k/operator_workflow_trace.json` | FOUND | `71ef64163776ba74` | 4,159 |

### B. Threshold Files Referenced
| Path | Status | HASH | Size (bytes) |
|---|---|---|---|
| `artifacts/operator_thresholds.json` | FOUND | `033063ef0dfcae97` | 696 |
| `artifacts/operator_thresholds_validation_only.json` | FOUND | `8e76ee49ef776755` | 1,114 |
| `artifacts/operational_thresholds.json` | FOUND | `e7a52a617535e34b` | 103 |

### C. Calibration Artifacts
| Path | Status | HASH | Size (bytes) |
|---|---|---|---|
| `artifacts/calibrator.pkl` | FOUND | `36fe68d47207b371` | 2,091 |
| `artifacts/calibration_sample.csv` | FOUND | `c024ea9d96d0479f` | 9,725,236 |
| `artifacts/calibration_audit.json` | FOUND | `7dc5d2120322d134` | 706 |

### D. Prediction Certificates
| Path | Status | HASH | Size (bytes) |
|---|---|---|---|
| `artifacts/sprint10j/prediction_certificate.json` | FOUND | `5eb4bc4d1c1e67e3` | 1,037 |
| `hel1os_trust_certificate.json` | FOUND | `d0975befdb1a9c65` | 737 |
| `trust_certificate.json` | FOUND | `ef64c2ab4ce5f85e` | 499 |
| `data_pipeline/datasets/dataset_v2/inventory/trust_certificate.json` | FOUND | `ef64c2ab4ce5f85e` | 499 |
| `data_pipeline/datasets/dataset_v3/inventory/trust_certificate.json` | FOUND | `d0975befdb1a9c65` | 737 |

### E. Execution Manifests
| Path | Status | HASH | Size (bytes) |
|---|---|---|---|
| `artifacts/sprint10j/execution_manifest.json` | FOUND | `ea1410f31030fa29` | 682 |
| `artifacts/aditya_l1/download_manifest.json` | FOUND | `8cadcd95d2ca778b` | 515,627 |

### F. Evidence Chain Artifacts
| Path | Status | HASH | Size (bytes) |
|---|---|---|---|
| `artifacts/sprint10j/prediction_evidence.json` | FOUND | `59c1c9ad2098cb68` | 8,564 |
| `artifacts/sprint10j/repository_fingerprint.json` | FOUND | `08df03013d474b58` | 3,144 |
| `artifacts/sprint10j/artifact_hashes.json` | FOUND | `9f4af7b3a5fa403d` | 2,430 |

### G. Frontend Components
| Path | Status | HASH | Size (bytes) |
|---|---|---|---|
| `frontend/` | NOT FOUND | `N/A` | 0 |

### H. Backend Endpoints
| Path | Status | HASH | Size (bytes) |
|---|---|---|---|
| `app/api/v1/endpoints/inference.py` | FOUND | `e698198737ab8b1d` | 9,724 |
| `app/api/v1/endpoints/flares.py` | FOUND | `e6dfcd64f78bca1a` | 768 |
| `app/api/v1/endpoints/solar.py` | FOUND | `b9602ea179749862` | 1,459 |
| `app/api/v1/endpoints/system.py` | FOUND | `01978972c7615ff5` | 5,885 |
| `app/api/v1/endpoints/health.py` | FOUND | `568c83486ffe077c` | 1,157 |

---

## 3. Cross-Reference Link Analysis

The logical links trace the data pipeline flow from the Operator UI down to the feature schema.

### Link: frontend -> API
* **Source:** `Frontend User Interface`  
  - Path: `frontend/`  
  - Status: NOT FOUND  
  - Hash: `N/A`  
* **Target:** `FastAPI Inference Route`  
  - Path: `app/api/v1/endpoints/inference.py`  
  - Status: FOUND  
  - Hash: `e698198737ab8b1d`  
  - Referenced by: `app/api/v1/api.py`  
  - Unreferenced: False  
  - Multiple References: True  

### Link: API -> prediction pipeline
* **Source:** `FastAPI Inference Route`  
  - Path: `app/api/v1/endpoints/inference.py`  
  - Status: FOUND  
  - Hash: `e698198737ab8b1d`  
* **Target:** `Operational Inference Service`  
  - Path: `app/services/ml/inference.py`  
  - Status: FOUND  
  - Hash: `57e49d01a0d5b460`  
  - Referenced by: `app/api/v1/endpoints/inference.py`  
  - Unreferenced: False  
  - Multiple References: False  

### Link: prediction pipeline -> calibration
* **Source:** `Operational Inference Service`  
  - Path: `app/services/ml/inference.py`  
  - Status: FOUND  
  - Hash: `57e49d01a0d5b460`  
* **Target:** `Calibrator Model File`  
  - Path: `artifacts/calibrator.pkl`  
  - Status: FOUND  
  - Hash: `36fe68d47207b371`  
  - Referenced by: `app/services/ml/inference.py`, `scripts/refine_thresholds.py`, `scripts/backtest_operator_policy.py`, `scripts/generate_explainability_examples.py`, `scripts/run_calibration_verification.py`  
  - Unreferenced: False  
  - Multiple References: True  

### Link: calibration -> threshold
* **Source:** `Calibrator Model File`  
  - Path: `artifacts/calibrator.pkl`  
  - Status: FOUND  
  - Hash: `36fe68d47207b371`  
* **Target:** `Production Threshold Configuration`  
  - Path: `artifacts/operator_thresholds.json`  
  - Status: FOUND  
  - Hash: `033063ef0dfcae97`  
  - Referenced by: `app/services/ml/inference.py`  
  - Unreferenced: False  
  - Multiple References: False  

### Link: threshold -> certificate
* **Source:** `Validation Threshold Configuration`  
  - Path: `artifacts/operator_thresholds_validation_only.json`  
  - Status: FOUND  
  - Hash: `8e76ee49ef776755`  
* **Target:** `Prediction Certificate`  
  - Path: `artifacts/sprint10j/prediction_certificate.json`  
  - Status: FOUND  
  - Hash: `5eb4bc4d1c1e67e3`  
  - Referenced by: `scratch/sprint10j/run_sprint10j.sh`  
  - Unreferenced: False  
  - Multiple References: False  

### Link: certificate -> artifacts
* **Source:** `Prediction Certificate`  
  - Path: `artifacts/sprint10j/prediction_certificate.json`  
  - Status: FOUND  
  - Hash: `5eb4bc4d1c1e67e3`  
* **Target:** `Prediction Evidence Trace`  
  - Path: `artifacts/sprint10j/prediction_evidence.json`  
  - Status: FOUND  
  - Hash: `59c1c9ad2098cb68`  
  - Referenced by: `scratch/sprint10j/run_sprint10j.sh`  
  - Unreferenced: False  
  - Multiple References: False  

### Link: artifacts -> dataset
* **Source:** `Prediction Evidence Trace`  
  - Path: `artifacts/sprint10j/prediction_evidence.json`  
  - Status: FOUND  
  - Hash: `59c1c9ad2098cb68`  
* **Target:** `Research Test Dataset`  
  - Path: `artifacts/research/test.parquet`  
  - Status: FOUND  
  - Hash: `3f2b270f98a2480b`  
  - Referenced by: `artifacts/sprint10j/audit_runner.py`, `scratch/sprint10j/run_evidence_chain.py`  
  - Unreferenced: False  
  - Multiple References: True  

### Link: dataset -> model
* **Source:** `Research Test Dataset`  
  - Path: `artifacts/research/test.parquet`  
  - Status: FOUND  
  - Hash: `3f2b270f98a2480b`  
* **Target:** `PatchTST Best Checkpoint`  
  - Path: `artifacts/models/patchtst_best.pt`  
  - Status: FOUND  
  - Hash: `010dc798b2a46253`  
  - Referenced by: `app/services/ml/inference.py`, `artifacts/sprint10j/audit_runner.py`, `scratch/sprint10j/run_evidence_chain.py`  
  - Unreferenced: False  
  - Multiple References: True  

### Link: model -> feature schema
* **Source:** `PatchTST Best Checkpoint`  
  - Path: `artifacts/models/patchtst_best.pt`  
  - Status: FOUND  
  - Hash: `010dc798b2a46253`  
* **Target:** `Feature Columns Configuration`  
  - Path: `artifacts/feature_columns.json`  
  - Status: FOUND  
  - Hash: `e499492381c93a40`  
  - Referenced by: `app/services/ml/inference.py`, `artifacts/sprint10j/audit_runner.py`, `scratch/sprint10j/run_evidence_chain.py`  
  - Unreferenced: False  
  - Multiple References: True  


---

## 4. Verification Summary

### STATUS: FAIL

**Missing Components:**
- `frontend/`
