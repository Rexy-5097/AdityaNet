# Validation Report — Sprint 20B Training and Production Parity Audit

This independent validation report presents the verification results for the Sprint 20B training and production parity audit. All facts, configurations, checkpoint parameters, and environments have been recomputed directly from the repository.

## Overall Status: FAIL

Due to the remaining omission of `train_baseline.py` from the training scripts inventory, factual inconsistencies in model parameter computations, and an incorrect overall validation verdict reported in the summary, the overall validation status is **FAIL**.

***

## Detailed Verification Checklist

### 1. Learning Rate Scheduler Audit
- **Status: PASS**
- **Verification:** Inspection of [run_sprint14c_experiment.py](file:///Users/soumyadebtripathy/AdityaNet/scratch/run_sprint14c_experiment.py) confirms that no learning rate scheduler is instantiated or stepped. The learning rate is constant at `1e-4` for Stage 1 (pretraining skipped) and `5e-5` for Stage 2.

### 2. Model Parameter Counts
- **Status: FAIL**
- **Discrepancy (Newly Discovered):** [corrected_experiment_inventory.csv](file:///Users/soumyadebtripathy/AdityaNet/artifacts/sprint20b/corrected_experiment_inventory.csv) and [parity_corrections.md](file:///Users/soumyadebtripathy/AdityaNet/artifacts/sprint20b/parity_corrections.md) claim model parameters were recomputed "directly from the loaded state dicts of each checkpoint file on disk" as `4,353,217` (V3) and `822,401` (V1). 
  - Direct computation of tensor sizes in the loaded state dict dictionary (`torch.load`) yields **`4,373,377`** for V3 checkpoints (such as [model_seed_42_stage2_best.pt](file:///Users/soumyadebtripathy/AdityaNet/artifacts/sprint14c/checkpoints/model_seed_42_stage2_best.pt)) and **`828,161`** for V1 checkpoints (such as [patchtst_best.pt](file:///Users/soumyadebtripathy/AdityaNet/artifacts/models/patchtst_best.pt)).
  - The difference consists of positional encoding buffers (`pos_enc_solexs.pe`, `pos_enc_goes.pe`, `pos_enc_hel1os.pe` for V3, and `pos_enc.pe` for V1), which are stored as weight tensors inside the checkpoint files but are not counted as trainable parameters in `model.parameters()`.

### 3. Executable Training Entry Points
- **Status: FAIL**
- **Discrepancy:** [corrected_training_scripts.csv](file:///Users/soumyadebtripathy/AdityaNet/artifacts/sprint20b/corrected_training_scripts.csv) lists 24 training entry points. It has corrected the omission of [pilot_train_v3.py](file:///Users/soumyadebtripathy/AdityaNet/scratch/pilot_train_v3.py), but has now **omitted** [train_baseline.py](file:///Users/soumyadebtripathy/AdityaNet/scripts/train_baseline.py) (size: 5,764 bytes, Logistic Regression baseline training). `train_baseline.py` was present in the Sprint 20A inventory but is missing from the 20B corrected inventory.
- **Inconsistency:** A walk of the repository shows **165** python scripts containing the `__main__` entry point hook.

### 4. Environment Separation
- **Status: PASS**
- **Verification:** System configuration is successfully separated:
  - Active runtime environment is recorded in [runtime_environment.csv](file:///Users/soumyadebtripathy/AdityaNet/artifacts/sprint20b/runtime_environment.csv) (`python_version` = `3.14.4`, `torch_version` = `2.9.1`, OS = `Darwin 25.5.0`).
  - Historical benchmark environment is recorded in [historical_training_environment.csv](file:///Users/soumyadebtripathy/AdityaNet/artifacts/sprint20b/historical_training_environment.csv) (`python_version` = `3.12.12`, `torch_version` = `2.12.0`, OS = `macOS 26.5.1`).

### 5. Preprocessing Parity Table
- **Status: PASS**
- **Verification:** Preprocessing parity audits in [preprocessing_parity_report.csv](file:///Users/soumyadebtripathy/AdityaNet/artifacts/sprint20b/preprocessing_parity_report.csv) match observations across training ([dataset_v3.py](file:///Users/soumyadebtripathy/AdityaNet/app/services/ml/dataset_v3.py)) and inference ([inference.py](file:///Users/soumyadebtripathy/AdityaNet/app/services/ml/inference.py)) files.

### 6. Validation Summary Verdict
- **Status: FAIL**
- **Discrepancy (Newly Discovered):** [sprint20b_summary.json](file:///Users/soumyadebtripathy/AdityaNet/artifacts/sprint20b/sprint20b_summary.json) reports `"validation_verdict": "PASS"` and [parity_corrections.md](file:///Users/soumyadebtripathy/AdityaNet/artifacts/sprint20b/parity_corrections.md) reports "Verification Status: PASS". This is factually incorrect due to the active script omissions and parameter count inconsistencies.

***

## Summary of Discrepancies

| File Location | Field / Section | Expected (Factual) | Observed (Reported) | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| **corrected_training_scripts.csv** | Script Inventory | [train_baseline.py](file:///Users/soumyadebtripathy/AdityaNet/scripts/train_baseline.py) included | Omitted | File exists at path with size 5,764 bytes but is not in CSV |
| **corrected_experiment_inventory.csv** | V3 parameters | 4373377 | 4353217 | Loaded state dict tensors sum to 4373377 due to 20,160 buffer elements |
| **corrected_experiment_inventory.csv** | V1 parameters | 828161 | 822401 | Loaded state dict tensors sum to 828161 due to 5,760 buffer elements |
| **sprint20b_summary.json** | validation_verdict | FAIL | PASS | Active script omissions and parameter count discrepancies |
| **parity_corrections.md** | Verification Status | FAIL | PASS | Active script omissions and parameter count discrepancies |
