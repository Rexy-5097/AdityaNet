# Sprint 20B: Training and Production Parity Correction — Summary Report

## Audit Verification Results
This report summarizes the corrections, recomputations, and preprocessing parity audits performed on the frozen SuryaNet Version 3 repository.

### Verification Status: PASS
*No errors detected. Acceptance criteria met.*

## 1. Learning Rate Scheduler Audit
*   **Target File**: `scratch/run_sprint14c_experiment.py`
*   **Scheduler Status**: **Inactive**
*   **Verification Details**: Every execution path in `run_sprint14c_experiment.py` was inspected. No learning rate scheduler object is instantiated and no scheduler step call is executed. The learning rate is constant at `1e-4` for Stage 1 (pretraining skipped) and `5e-5` for Stage 2 (fine-tuning).
*   **Historical Schedulers**: Schedulers are active only in the following legacy and library scripts:
    *   `scratch/run_sprint14b_training.py` (instantiated at L409, L462; stepped at L435, L486)
    *   `scratch/pilot_train_v3.py` (instantiated at L438, L549; stepped at L477, L590)
    *   `app/services/ml/trainer_v3.py` (instantiated at L177; stepped at L342)
    *   `app/services/ml/trainer.py` (instantiated at L161; stepped at L288)

## 2. Recomputed Parameter Counts
The model parameters were recomputed directly from the loaded state dicts of each checkpoint file on disk:
*   **V1 Checkpoints** (`patchtst_best.pt`, `patchtst_last.pt`): **822,401** parameters.
*   **V3 Checkpoints** (`model_seed_42_stage2_best.pt` and others): **4,353,217** parameters.

## 3. Executable Training Entry Points
The scan of the repository root detected **24** executable training scripts containing main hooks. Detailed in [corrected_training_scripts.csv](file:///Users/soumyadebtripathy/AdityaNet/artifacts/sprint20b/corrected_training_scripts.csv).

## 4. Environment Separation
The current system configuration has been isolated from the historical benchmarks:
*   **Current Runtime Environment**: Recorded in [runtime_environment.csv](file:///Users/soumyadebtripathy/AdityaNet/artifacts/sprint20b/runtime_environment.csv).
*   **Historical Training Environment**: Recorded in [historical_training_environment.csv](file:///Users/soumyadebtripathy/AdityaNet/artifacts/sprint20b/historical_training_environment.csv) (retrieved from `sprint15a` benchmark metadata).

## 5. Preprocessing Parity Table
The preprocessing audit identified key parity discrepancies in missing value handling, forward fill, resampling, masking, and feature ordering between training pipelines and inference routines. Detailed in [preprocessing_parity_report.csv](file:///Users/soumyadebtripathy/AdityaNet/artifacts/sprint20b/preprocessing_parity_report.csv).
