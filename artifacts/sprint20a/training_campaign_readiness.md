# Sprint 20A: Training Campaign Readiness Audit — Summary Report

## Audit Overview
This report summarizes the training campaign readiness audit performed on the frozen SuryaNet Version 3 repository.

All reported values are directly computed and verified from the current repository files.

## Deliverables Generated
The following factual audit deliverables have been written to `artifacts/sprint20a/`:

1. **[training_configuration.csv](file:///Users/soumyadebtripathy/AdityaNet/artifacts/sprint20a/training_configuration.csv)**: Detailed training hyperparameters and configurations.
2. **[training_convergence.csv](file:///Users/soumyadebtripathy/AdityaNet/artifacts/sprint20a/training_convergence.csv)**: Checkpoint validation metric values and training epoch convergence histories.
3. **[dataset_balance.csv](file:///Users/soumyadebtripathy/AdityaNet/artifacts/sprint20a/dataset_balance.csv)**: Sample distributions and class imbalance ratios for the 6 Parquet splits.
4. **[feature_usage.csv](file:///Users/soumyadebtripathy/AdityaNet/artifacts/sprint20a/feature_usage.csv)**: Mappings of feature names to instrument categories.
5. **[loss_configuration.csv](file:///Users/soumyadebtripathy/AdityaNet/artifacts/sprint20a/loss_configuration.csv)**: Loss function parameters and code line ranges.
6. **[training_scripts.csv](file:///Users/soumyadebtripathy/AdityaNet/artifacts/sprint20a/training_scripts.csv)**: Directory locations and file details for training pipelines.
7. **[experiment_inventory.csv](file:///Users/soumyadebtripathy/AdityaNet/artifacts/sprint20a/experiment_inventory.csv)**: Model parameter counts and key validation metrics.
8. **[reproducibility_audit.csv](file:///Users/soumyadebtripathy/AdityaNet/artifacts/sprint20a/reproducibility_audit.csv)**: Seed values, framework versions, and file hashes.
9. **[compute_inventory.csv](file:///Users/soumyadebtripathy/AdityaNet/artifacts/sprint20a/compute_inventory.csv)**: Checkpoint sizes, dataset sizes, and memory usage.
10. **[scientific_inventory.csv](file:///Users/soumyadebtripathy/AdityaNet/artifacts/sprint20a/scientific_inventory.csv)**: Validation coverage dimensions.
11. **[experiment_lineage.csv](file:///Users/soumyadebtripathy/AdityaNet/artifacts/sprint20a/experiment_lineage.csv)**: populated traceability from data splits to final test metrics.
12. **[data_leakage_audit.csv](file:///Users/soumyadebtripathy/AdityaNet/artifacts/sprint20a/data_leakage_audit.csv)**: Results of timestamp duplicate checks and window overlaps.
13. **[label_audit.csv](file:///Users/soumyadebtripathy/AdityaNet/artifacts/sprint20a/label_audit.csv)**: Horizon settings and flare class frequency details.
14. **[feature_availability_audit.csv](file:///Users/soumyadebtripathy/AdityaNet/artifacts/sprint20a/feature_availability_audit.csv)**: Operational ingestion delay status and missing data frequencies.
15. **[checkpoint_genealogy.csv](file:///Users/soumyadebtripathy/AdityaNet/artifacts/sprint20a/checkpoint_genealogy.csv)**: Relationship paths between checkpoints.
16. **[production_parity.csv](file:///Users/soumyadebtripathy/AdityaNet/artifacts/sprint20a/production_parity.csv)**: Discrepancy analysis between training and inference preprocessing.
17. **[training_campaign_specification.csv](file:///Users/soumyadebtripathy/AdityaNet/artifacts/sprint20a/training_campaign_specification.csv)**: Standardized protocol definitions for upcoming retraining phases.

## Standardized Retraining Protocol
The standardized training campaign specification has been established as follows:
- **Target Metric**: TSS
- **Primary Metric**: TSS
- **Secondary Metrics**: HSS, MCC, PR-AUC, ROC-AUC, Brier Score, ECE
- **Checkpoint Selection**: Validation TSS
- **Maximum Epochs**: 10
- **Early Stopping**: patience=3 epochs, min_delta=1e-4, mode=max
- **Seed Count**: 5 (Seeds: 42, 123, 3407, 2026, 9999)
- **Evaluation Split**: Chronological sliding-window test split
- **Acceptance Threshold**: Test set TSS > 0.40 and ECE < 0.05
