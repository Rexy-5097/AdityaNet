import json
import os

OUT_DIR = "/Users/soumyadebtripathy/AdityaNet/artifacts/sprint11a"
os.makedirs(OUT_DIR, exist_ok=True)

# ──────────────────────────────────────────────────────────────────────────────
# 1. model_bottlenecks.json
# ──────────────────────────────────────────────────────────────────────────────
bottlenecks = {
    "bottlenecks": [
        {
            "category": "architecture_limitations",
            "name": "Single-scale Patching and Fixed Resolution",
            "repository_location": "app/services/ml/model.py (lines 33-46)",
            "measurable_evidence": "PatchTST uses fixed PATCH_LEN=16 and STRIDE=8, mapping 360 inputs into 44 tokens. Embedded dimension is hardcoded at 128.",
            "impact_on_performance": "Limits model's capacity to represent multi-scale features (e.g. fast solar spikes vs slow background decay). The model has only 822,401 parameters, underutilizing capacity relative to 5.1M training rows.",
            "additional_data_required": False,
            "architectural_changes_required": True
        },
        {
            "category": "optimization_limitations",
            "name": "Under-converged Training",
            "repository_location": "artifacts/training_history.json (lines 1-50)",
            "measurable_evidence": "Training history contains only 3 epochs. Training loss dropped from 0.0699 to 0.0539, and validation loss dropped from 0.0757 to 0.0725. Both curves show active downward slopes without plateauing.",
            "impact_on_performance": "The model has not reached convergence, indicating that the baseline model is under-trained and likely sub-optimal.",
            "additional_data_required": False,
            "architectural_changes_required": False
        },
        {
            "category": "feature_limitations",
            "name": "Omission of Multi-Instrument Inputs",
            "repository_location": "app/services/ml/features.py (compute_features())",
            "measurable_evidence": "Feature columns are restricted to 14 GOES-only features. Processed Aditya-L1 telemetry (SoLEXS and HEL1OS) parquets containing rate and counts are present on disk but never loaded or merged.",
            "impact_on_performance": "The model is blind to soft and hard X-ray measurements from the Aditya-L1 observatory, which provide vital spatial and spectral constraints on flaring regions.",
            "additional_data_required": True,
            "architectural_changes_required": True
        },
        {
            "category": "data_limitations",
            "name": "Split Class Imbalance Shift",
            "repository_location": "artifacts/sprint10l/dataset_fingerprint.json",
            "measurable_evidence": "Positive target rate in train split is 0.62% (31,993 / 5,160,952), validation split is 4.07% (63,849 / 1,568,399), and test split is 23.20% (419,150 / 1,806,313).",
            "impact_on_performance": "Forces the model to operate under severe non-stationarity and class distribution shift, causing validation-tuned thresholds to mismatch test-set label densities.",
            "additional_data_required": False,
            "architectural_changes_required": False
        },
        {
            "category": "calibration_limitations",
            "name": "Non-Parametric Step Mapping",
            "repository_location": "artifacts/calibrator.pkl",
            "measurable_evidence": "Isotonic Regression calibrator maps continuous raw probabilities to a discrete step function (e.g., mapping multiple distinct raw probabilities to exactly 0.06027905 or 1.0).",
            "impact_on_performance": "Reduces resolution of forecast probability outputs and prevents fine-grained operator risk differentiation.",
            "additional_data_required": False,
            "architectural_changes_required": False
        },
        {
            "category": "uncertainty_limitations",
            "name": "Slow Monte Carlo Dropout Inference",
            "repository_location": "app/services/ml/model.py (lines 330-365)",
            "measurable_evidence": "Epistemic uncertainty requires n_dropout_samples=50 forward passes on the model at every time-step during inference.",
            "impact_on_performance": "High computational overhead for real-time nowcasting. Also, the model lack aleatoric uncertainty prediction.",
            "additional_data_required": False,
            "architectural_changes_required": True
        }
    ]
}
with open(os.path.join(OUT_DIR, "model_bottlenecks.json"), "w") as f:
    json.dump(bottlenecks, f, indent=2)

# ──────────────────────────────────────────────────────────────────────────────
# 2. unused_data_inventory.json
# ──────────────────────────────────────────────────────────────────────────────
unused_data = {
    "unused_scientific_signals": [
        {
            "signal_source": "SoLEXS Instrument Telemetry",
            "location": "data/aditya_l1/processed/solexs/",
            "availability": "Processed Parquet files on disk (5-second cadence)",
            "temporal_coverage": "2023-12-13 to 2026-06-14",
            "current_usage_status": "UNUSED",
            "whether_discarded": True,
            "whether_reaches_model": False,
            "channels_fields": ["rate", "counts", "channel"]
        },
        {
            "signal_source": "HEL1OS Instrument Telemetry",
            "location": "data/aditya_l1/processed/hel1os/",
            "availability": "Processed Parquet files on disk (5-second cadence)",
            "temporal_coverage": "2023-10-29 to 2026-06-14",
            "current_usage_status": "UNUSED",
            "whether_discarded": True,
            "whether_reaches_model": False,
            "energy_bands_fields": ["rate", "counts", "energy_band"]
        },
        {
            "signal_source": "GOES Telemetry Metadata",
            "location": "artifacts/research/goes_full.parquet (columns: satellite, quality_flag, processing_version)",
            "availability": "Parquet columns and goesxrs database columns",
            "temporal_coverage": "2010-01-02 to 2026-06-14",
            "current_usage_status": "UNUSED",
            "whether_discarded": True,
            "whether_reaches_model": False
        },
        {
            "signal_source": "Flare Catalogue Attributes",
            "location": "artifacts/research/flares_full.parquet (columns: peak_time, end_time, region_number, location, importance)",
            "availability": "Parquet columns and flareevent database columns",
            "temporal_coverage": "2010 to 2026",
            "current_usage_status": "MOSTLY UNUSED (Only start_time used to calculate minutes_since_last_flare)",
            "whether_discarded": True,
            "whether_reaches_model": False
        }
    ]
}
with open(os.path.join(OUT_DIR, "unused_data_inventory.json"), "w") as f:
    json.dump(unused_data, f, indent=2)

# ──────────────────────────────────────────────────────────────────────────────
# 3. architecture_ceiling_v2.json
# ──────────────────────────────────────────────────────────────────────────────
ceiling = {
    "architecture_ceiling_analysis": {
        "model_parameters": {
            "current_parameters": 822401,
            "maximum_allowed_parameters": 10000000,
            "capacity_utilization_ratio": 0.08224
        },
        "convergence_evidence": {
            "training_history_epochs": 3,
            "training_loss_evolution": "Epoch 1: 0.069929 -> Epoch 2: 0.055849 -> Epoch 3: 0.053917 (decreasing)",
            "validation_loss_evolution": "Epoch 1: 0.075791 -> Epoch 2: 0.074228 -> Epoch 3: 0.072590 (decreasing)",
            "validation_tss_evolution": "Epoch 1: 0.5667 -> Epoch 2: 0.4998 -> Epoch 3: 0.5936 (increasing)",
            "has_converged": False,
            "model_can_still_improve": True
        },
        "attention_specialization": {
            "current_usage": "Averaged CLS attention weights across all 4 layers and 8 heads.",
            "limitations": "Washes out individual layer and head specializations.",
            "model_can_still_improve": True
        }
    }
}
with open(os.path.join(OUT_DIR, "architecture_ceiling_v2.json"), "w") as f:
    json.dump(ceiling, f, indent=2)

# ──────────────────────────────────────────────────────────────────────────────
# 4. retraining_readiness.json
# ──────────────────────────────────────────────────────────────────────────────
readiness = {
    "retraining_readiness_checklist": {
        "frozen_datasets": {
            "status": "PASS",
            "evidence_location": "artifacts/sprint10l/dataset_fingerprint.json"
        },
        "immutable_hashes": {
            "status": "PASS",
            "evidence_location": "artifacts/sprint10l/repository_fingerprint_v1.json"
        },
        "reproducibility": {
            "status": "PASS",
            "evidence_location": "artifacts/sprint10j/prediction_certificate.json"
        },
        "deterministic_evaluation": {
            "status": "PASS",
            "evidence_location": "artifacts/sprint10j/execution_manifest.json"
        },
        "baseline_metrics": {
            "status": "PASS",
            "evidence_location": "artifacts/sprint10l/production_metrics_snapshot.json"
        },
        "calibration_freeze": {
            "status": "PASS",
            "evidence_location": "artifacts/calibrator.pkl"
        },
        "operator_evidence": {
            "status": "PASS",
            "evidence_location": "artifacts/sprint10j/prediction_evidence.json"
        },
        "validation_protocol": {
            "status": "PASS",
            "evidence_location": "app/services/ml/dataset.py (SolarFlareWindowDataset)"
        }
    },
    "final_readiness_verdict": "PASS"
}
with open(os.path.join(OUT_DIR, "retraining_readiness.json"), "w") as f:
    json.dump(readiness, f, indent=2)

# ──────────────────────────────────────────────────────────────────────────────
# 5. experiment_protocol.json
# ──────────────────────────────────────────────────────────────────────────────
protocol = {
    "experiment_metadata": {
        "experiment_name": "SuryaNet Version 2 Model Upgrade",
        "target_version": "v2.0.0-alpha",
        "timestamp_utc": "2026-06-19T10:52:54Z"
    },
    "hypotheses": [
        {
            "id": "H1",
            "statement": "Integrating processed Aditya-L1 SoLEXS and HEL1OS telemetry alongside GOES flux features improves M/X-class solar flare forecasting TSS on the test split compared to the GOES-only baseline."
        },
        {
            "id": "H2",
            "statement": "Increasing PatchTST parameter capacity (e.g. from 822K to 5M parameters) under the 10M constraint enables the model to utilize the training split more effectively and reduces validation loss."
        },
        {
            "id": "H3",
            "statement": "Training the PatchTST model to full convergence (plateauing validation loss) will decrease the baseline Brier Score and ECE."
        }
    ],
    "variables": {
        "fixed_variables": {
            "train_dataset_split": "artifacts/research/train.parquet (2010-01-02 to 2019-12-31)",
            "validation_dataset_split": "artifacts/research/validation.parquet (2020-01-01 to 2022-12-31)",
            "test_dataset_split": "artifacts/research/test.parquet (2023-01-01 to 2026-06-14)",
            "forecast_task": "Binary nowcast: predict M/X-class flare risk within the next 6 hours",
            "sequence_window_minutes": 360,
            "random_seed": 42
        },
        "allowed_to_change_variables": {
            "input_features": "Include processed SoLEXS rates/channels and HEL1OS rates/bands.",
            "model_capacity": "Hyperparameters: EMBED_DIM (128 -> 256), N_HEADS (8 -> 16), N_LAYERS (4 -> 6), FF_DIM (512 -> 1024). Limit total params < 10,000,000.",
            "training_epochs": "Increase max_epochs from 3 (or early stopped 3) to 20; increase early stopping patience from 3 to 5.",
            "calibration_layer": "Optionally evaluate Platt scaling vs Isotonic Regression vs temperature scaling on the validation set."
        }
    },
    "protocols": {
        "evaluation_protocol": [
            "1. Ingest train, val, and test splits with both GOES and Aditya-L1 features aligned chronologically.",
            "2. Initialize model architecture using seed 42.",
            "3. Train model on training split. At the end of each epoch, evaluate loss and TSS on the validation split.",
            "4. Save model weights corresponding to the epoch with the highest validation TSS.",
            "5. Apply calibrator candidate models to validation raw predictions; select the candidate with the lowest validation Brier Score.",
            "6. Tune yellow and red alert thresholds on validation calibrated predictions using the trust score formula.",
            "7. Run inference on test split statelessly using the selected model, calibrator, and validation-tuned thresholds."
        ],
        "comparison_protocol": "Compare Version 2 test set performance metrics directly against the frozen baseline test set metrics snapshot (ROC-AUC, PR-AUC, TSS, Precision, Recall, F1, FAR, Brier Score, and ECE).",
        "success_criteria": {
            "test_tss_increase_absolute": 0.05,
            "test_ece_upper_bound": 0.10,
            "leakage_constraint": "Zero test set leakage during threshold tuning or calibration fitting."
        },
        "rollback_criteria": [
            "1. Version 2 test set TSS is lower than the Version 1 baseline TSS (0.2298).",
            "2. Validation loss increases while training loss continues to decrease (overfitting).",
            "3. Real-time inference latency exceeds 1.0 second per window."
        ]
    }
}
with open(os.path.join(OUT_DIR, "experiment_protocol.json"), "w") as f:
    json.dump(protocol, f, indent=2)

print("Generated all json deliverables in artifacts/sprint11a/")
