# Validation Report — Sprint 20A Training Campaign Readiness Audit

This independent validation report presents the verification results for the Sprint 20A training campaign readiness audit. All facts, configurations, dataset counts, checkpoint parameters, and reproducibility versions have been recomputed directly from the repository.

## Overall Status: FAIL

Due to multiple factual discrepancies in hyperparameters, environment library versions, model parameter counts, and script exclusions, the overall verification status is **FAIL**.

***

## Detailed Verification Checklist

### 1. Training Configuration & Hyperparameters
- **Status: FAIL**
- **Discrepancy:** `training_configuration.csv` lists `scheduler` as `CosineAnnealingLR (T_max=max_epochs)`. However, the script `scratch/run_sprint14c_experiment.py` does not instantiate or use any learning rate scheduler.

### 2. Dataset Balance
- **Status: PASS**
- **Verification:** All sample counts, positive/negative splits, and imbalance ratios in `dataset_balance.csv` match the actual parquet files exactly:
  - `train_v3.parquet`: 5,161,312 total, 31,993 positive, 5,129,319 negative (imbalance: 160.33)
  - `validation_v3.parquet`: 1,568,759 total, 63,849 positive, 1,504,910 negative (imbalance: 23.57)
  - `test_v3.parquet`: 1,806,673 total, 419,150 positive, 1,387,523 negative (imbalance: 3.31)
  - `s2_train.parquet`: 786,298 total, 246,518 positive, 539,780 negative (imbalance: 2.19)
  - `s2_val.parquet`: 262,480 total, 43,691 positive, 218,789 negative (imbalance: 5.01)
  - `s2_test.parquet`: 261,455 total, 31,111 positive, 230,344 negative (imbalance: 7.40)

### 3. Feature Inventory
- **Status: PASS**
- **Verification:** The 36 active feature columns and 8 metadata/mask/target columns in `feature_usage.csv` match the dataset schemas and model input configurations exactly (14 GOES, 18 SoLEXS, 4 HEL1OS features).

### 4. Loss Configuration
- **Status: PASS**
- **Verification:** FocalLoss is configured as described in `loss_configuration.csv`, matching the implementation in `app/services/ml/trainer_v3.py` lines 44-60 (including the `[0.25, 0.75]` dynamic alpha clamping and `gamma = 2.0`).

### 5. Training Scripts
- **Status: FAIL**
- **Discrepancy:** `training_scripts.csv` omits the training runner `scratch/pilot_train_v3.py` (44,692 bytes) from its inventory.

### 6. Experiment Inventory
- **Status: FAIL**
- **Discrepancies:**
  - `model_seed_42_stage2_best.pt` parameter count is reported as `4353217`, but the checkpoint actually contains `4373377` parameters.
  - `patchtst_best.pt` parameter count is reported as `828000`, but the checkpoint actually contains `828161` parameters.

### 7. Reproducibility Information
- **Status: FAIL**
- **Discrepancies:** The reported package versions in `reproducibility_audit.csv` do not match the environment:
  - `python_version`: reported `3.12.12`, actual `3.14.4`
  - `numpy_version`: reported `1.26.4`, actual `2.3.5`
  - `pandas_version`: reported `2.2.1`, actual `2.3.3`
  - `pytorch_version`: reported `2.12.0`, actual `2.9.1`
  - `scikit_learn_version`: reported `1.4.1`, actual `1.7.2`
  - `scipy_version`: reported `1.12.0`, actual `1.16.3`

### 8. Compute Inventory
- **Status: PASS**
- **Verification:** Measured execution stats (Peak RSS: 0.774 GB, Peak Swap: 0.591 GB, Epoch Time: 304.26s) and dataset file sizes are accurately recorded in `compute_inventory.csv`.

### 9. Scientific Inventory
- **Status: PASS**
- **Verification:** All listed scientific verification dimensions (multiple seeds, chronological generalization, production evaluation, telemetry, ablation, uncertainty) exist at the specified paths.

***

## Summary of Discrepancies

| Reported File | Field / Metric | Expected (Factual) | Observed (Reported) |
| :--- | :--- | :--- | :--- |
| **training_configuration.csv** | scheduler | None | CosineAnnealingLR (T_max=max_epochs) |
| **training_scripts.csv** | Script Inventory | `scratch/pilot_train_v3.py` included | Omitted |
| **experiment_inventory.csv** | model_seed_42_stage2_best.pt parameters | 4373377 | 4353217 |
| **experiment_inventory.csv** | patchtst_best.pt parameters | 828161 | 828000 |
| **reproducibility_audit.csv** | python_version | 3.14.4 | 3.12.12 |
| **reproducibility_audit.csv** | numpy_version | 2.3.5 | 1.26.4 |
| **reproducibility_audit.csv** | pandas_version | 2.3.3 | 2.2.1 |
| **reproducibility_audit.csv** | pytorch_version | 2.9.1 | 2.12.0 |
| **reproducibility_audit.csv** | scikit_learn_version | 1.7.2 | 1.4.1 |
| **reproducibility_audit.csv** | scipy_version | 1.16.3 | 1.12.0 |
