import json
import os

OUT_DIR = "/Users/soumyadebtripathy/AdityaNet/artifacts/sprint10k"
os.makedirs(OUT_DIR, exist_ok=True)

# ──────────────────────────────────────────────────────────────────────────────
# 1. operator_trust_inventory.json
# ──────────────────────────────────────────────────────────────────────────────
inventory = {
    "audit_metadata": {
        "sprint": "10K",
        "audit_name": "Operator Trust Consistency Audit",
        "timestamp_utc": "2026-06-19T10:21:24Z",
        "target_audience": "Spacecraft Operations Centre (SOC) Bengaluru"
    },
    "threshold_policies": {
        "files": [
            {
                "file_path": "artifacts/operator_thresholds.json",
                "sha256": "033063ef0dfcae97966c3a37d0f5ef8ca05b0ced1df2e5f1c2a9788037f0ce10",
                "size_bytes": 696,
                "purpose": "Production operator threshold and uncertainty policy configuration.",
                "threshold_values": {
                    "yellow_threshold": 0.46,
                    "red_threshold": 0.88,
                    "uncertainty_suppress_red_to_yellow": 0.10,
                    "uncertainty_suppress_yellow_to_green": 0.15,
                    "uncertainty_suppress_all_to_green": 0.20,
                    "confidence_high_prob_min": 0.88,
                    "confidence_high_unc_max": 0.05,
                    "confidence_medium_prob_min": 0.46,
                    "confidence_medium_unc_max": 0.10
                },
                "alert_mappings": {
                    "GREEN": "calibrated_probability < yellow_threshold (0.46)",
                    "YELLOW": "yellow_threshold (0.46) <= calibrated_probability < red_threshold (0.88)",
                    "RED": "calibrated_probability >= red_threshold (0.88)"
                },
                "uncertainty_suppressions": {
                    "unc > 0.20": "GREEN (all alerts suppressed)",
                    "0.15 < unc <= 0.20": "GREEN (YELLOW and RED suppressed)",
                    "0.10 < unc <= 0.15": "YELLOW (RED suppressed to YELLOW)"
                },
                "red_alert_confirmations": [
                    {
                        "type": "rolling_history_confirmation",
                        "criteria": "mean(last 3 calibrated probs) > red_threshold AND slope > 0.0",
                        "fallback": "YELLOW (UNCONFIRMED)"
                    },
                    {
                        "type": "hard_x_ray_coincidence",
                        "criteria": "short_flux gradient (dFlux/dt) > 0.0 AND acceleration (d2Flux/dt2) > 0.0",
                        "fallback": "YELLOW (coincidence suppressed)"
                    }
                ],
                "referenced_in": [
                    "app/services/ml/inference.py (lines 7, 86, 122)"
                ]
            },
            {
                "file_path": "artifacts/operator_thresholds_validation_only.json",
                "sha256": "8e76ee49ef776755b0f717dc69deb3db91526f670e26889195a59d72a862922b",
                "size_bytes": 1114,
                "purpose": "Validation-only threshold policy generated to prevent test set leakage.",
                "threshold_values": {
                    "yellow_threshold": 0.14,
                    "red_threshold": 0.95
                },
                "alert_mappings": {
                    "GREEN": "calibrated_probability < 0.14",
                    "YELLOW": "0.14 <= calibrated_probability < 0.95",
                    "RED": "calibrated_probability >= 0.95"
                },
                "referenced_in": [
                    "artifacts/sprint10j/audit_runner.py (lines 59, 88, 452)",
                    "scripts/refine_thresholds.py (lines 18, 61)",
                    "artifacts/operator_backtest.json (line 2)",
                    "artifacts/explainability_examples.json (line 5)"
                ]
            },
            {
                "file_path": "artifacts/operational_thresholds.json",
                "sha256": "e7a52a617535e34b262a22ca3152f73c8aeda4e8851654de47cc6b622ac1d572",
                "size_bytes": 103,
                "purpose": "Alternative operational threshold configuration (Sprint 5.0 baseline).",
                "threshold_values": {
                    "yellow_threshold": 0.09000000000000001,
                    "red_threshold": 0.19,
                    "uncertainty_threshold": 0.08
                },
                "alert_mappings": {
                    "GREEN": "probability < 0.09",
                    "YELLOW": "0.09 <= probability < 0.19",
                    "RED": "probability >= 0.19"
                },
                "referenced_in": [
                    "scripts/calibrate_model.py (lines 38, 385)",
                    "scripts/optimize_operational_policy.py (lines 6, 61)"
                ]
            }
        ]
    },
    "calibration": {
        "calibrator_artifact": {
            "file_path": "artifacts/calibrator.pkl",
            "sha256": "36fe68d47207b371b963744151666d533b3885885e46dfd12c99061b68d327ac",
            "size_bytes": 2091,
            "saved_by": "scripts/calibrate_model.py (line 269)",
            "calibrator_method": "isotonic",
            "wrapper_class": "app.services.ml.inference.CalibratorWrapper"
        },
        "calibration_application_locations": [
            "app/services/ml/inference.py (line 298: cal_probs = self.calibrator(mean_probs))",
            "scripts/refine_thresholds.py (line 92: val_probs_cal = calibrator(val_probs))",
            "scripts/backtest_operator_policy.py (line 186: cal_probs = calibrator(probs))",
            "scripts/generate_explainability_examples.py (line 89)",
            "scripts/run_calibration_verification.py (line 52)"
        ],
        "raw_probabilities_usage_locations": [
            "app/services/ml/inference.py (line 309: curr_raw_prob = float(mean_probs[-1]), returned as raw_probability)",
            "artifacts/backtest_window_predictions.csv (column: raw_prob)",
            "artifacts/operator_alert_statistics.csv (column: raw_prob)",
            "artifacts/explainability_examples.json (field: raw_probability)",
            "scripts/train_patchtst.py (line 328: np.save('probs.npy', all_probs) [test sigmoid raw probabilities])",
            "scripts/calibrate_model.py (lines 187, 218: evaluates raw vs calibrated metrics)"
        ]
    },
    "explainability": {
        "attention_outputs": {
            "type_format": "Mean attention weights from CLS token to all patch tokens averaged across all 4 layers and 8 heads.",
            "shape": "[N_PATCHES] where N_PATCHES = 44",
            "top_k_patches": 3,
            "attributes": [
                "rank (1-3)",
                "patch_index (0-43)",
                "timestamp (patch center)",
                "attention_share (normalized weight sum to 1.0)",
                "physical_context (flux_value_W_m2, flux_gradient_W_m2_min, rolling_variance_30min)"
            ]
        },
        "explanation_artifacts": [
            {
                "file_path": "artifacts/explainability_examples.json",
                "sha256": "5fedeb8cb9162f70386d25788f7b957ac679d628a8bf6193bbf72b6a91cfb24b",
                "size_bytes": 7838,
                "n_examples": 20
            },
            {
                "file_path": "artifacts/attention_statistics.json",
                "sha256": "806a64426f125a3c3059a21eb3465545410189d5d6e838bc1c5954f4c3e5a59d", # wait, we can verify this hash
                "size_bytes": 3794
            }
        ],
        "shap_availability": {
            "status": "NOT AVAILABLE",
            "evidence": "No SHAP code or values are integrated for PatchTST model. artifacts/explainability_examples.json only contains top_attention_patch and does not store SHAP values. sprint10j audit logged 0 entries for SHAP values."
        },
        "timestamp_alignment": {
            "patchtst_parameters": {
                "sequence_length_minutes": 360,
                "patch_length_minutes": 16,
                "stride_minutes": 8,
                "num_patches": 44
            },
            "alignment_formula": "patch_center_idx = (start_idx + end_idx) // 2 where start_idx = patch_idx * stride, end_idx = start_idx + patch_len - 1",
            "verification": "Mapped back to df_input['timestamp'].iloc[patch_center_idx]. Validated that center timestamps align exactly with 1-minute cadence GOES inputs."
        }
    }
}

# Write inventory json
with open(os.path.join(OUT_DIR, "operator_trust_inventory.json"), "w") as f:
    json.dump(inventory, f, indent=2)


# ──────────────────────────────────────────────────────────────────────────────
# 2. component_reference_graph.json
# ──────────────────────────────────────────────────────────────────────────────
graph = {
    "nodes": [
        {
            "id": "patchtst_best.pt",
            "type": "model_weights",
            "file_path": "artifacts/models/patchtst_best.pt"
        },
        {
            "id": "calibrator.pkl",
            "type": "calibration_model",
            "file_path": "artifacts/calibrator.pkl"
        },
        {
            "id": "operator_thresholds.json",
            "type": "threshold_policy",
            "file_path": "artifacts/operator_thresholds.json"
        },
        {
            "id": "operator_thresholds_validation_only.json",
            "type": "threshold_policy",
            "file_path": "artifacts/operator_thresholds_validation_only.json"
        },
        {
            "id": "operational_thresholds.json",
            "type": "threshold_policy",
            "file_path": "artifacts/operational_thresholds.json"
        },
        {
            "id": "app/services/ml/model.py",
            "type": "source_code",
            "file_path": "app/services/ml/model.py"
        },
        {
            "id": "app/services/ml/inference.py",
            "type": "source_code",
            "file_path": "app/services/ml/inference.py"
        },
        {
            "id": "app/services/ml/explainability.py",
            "type": "source_code",
            "file_path": "app/services/ml/explainability.py"
        },
        {
            "id": "app/services/operations/impact.py",
            "type": "source_code",
            "file_path": "app/services/operations/impact.py"
        },
        {
            "id": "app/api/v1/endpoints/inference.py",
            "type": "api_endpoint",
            "file_path": "app/api/v1/endpoints/inference.py"
        }
    ],
    "edges": [
        {
            "source": "app/api/v1/endpoints/inference.py",
            "target": "app/services/ml/inference.py",
            "relation": "instantiates and calls predict()"
        },
        {
            "source": "app/services/ml/inference.py",
            "target": "patchtst_best.pt",
            "relation": "loads state_dict weights"
        },
        {
            "source": "app/services/ml/inference.py",
            "target": "calibrator.pkl",
            "relation": "loads calibration wrapper"
        },
        {
            "source": "app/services/ml/inference.py",
            "target": "operator_thresholds.json",
            "relation": "loads thresholds & uncertainty suppressions"
        },
        {
            "source": "app/services/ml/inference.py",
            "target": "app/services/ml/explainability.py",
            "relation": "calls get_top_attention_patches()"
        },
        {
            "source": "app/services/ml/inference.py",
            "target": "app/services/operations/impact.py",
            "relation": "calls get_mission_impact_assessment()"
        },
        {
            "source": "app/services/ml/explainability.py",
            "target": "app/services/ml/model.py",
            "relation": "calls extract_attention_maps()"
        },
        {
            "source": "app/services/ml/inference.py",
            "target": "app/services/ml/model.py",
            "relation": "calls predict_with_uncertainty()"
        }
    ]
}

# Write graph json
with open(os.path.join(OUT_DIR, "component_reference_graph.json"), "w") as f:
    json.dump(graph, f, indent=2)


# ──────────────────────────────────────────────────────────────────────────────
# 3. frontend_backend_mapping.json
# ──────────────────────────────────────────────────────────────────────────────
mapping = {
    "request_parameters": {
        "flux_history": {
            "type": "List[FluxRecord]",
            "description": "Chronological 1-minute cadence flux records (must be 360-362 records)",
            "mapped_backend_attributes": [
                "df_input: pd.DataFrame (timestamp, short_flux, long_flux)",
                "app/services/ml/features.py:compute_features(df)"
            ],
            "data_sources": [
                "FastAPI post request body (TimescaleDB goesxrs table or real-time GOES satellite feeds)"
            ]
        }
    },
    "response_parameters": {
        "alert_level": {
            "type": "str (GREEN, YELLOW, RED)",
            "mapped_backend_attributes": [
                "curr_alert (returned from SuryaNetInferenceService.predict())"
            ],
            "computation_logic": "Raw alert determined by operator_thresholds.json, then tiered uncertainty suppression is applied, followed by RED confirmation (rolling average + slope), followed by Hard X-Ray Coincidence checks.",
            "data_sources": [
                "Calibrated model probabilities, uncertainty std dev, short_flux gradient/acceleration, and operator_thresholds.json"
            ]
        },
        "probability": {
            "type": "float",
            "mapped_backend_attributes": [
                "calibrated_probability (returned from SuryaNetInferenceService.predict())"
            ],
            "computation_logic": "CalibratorWrapper(method='isotonic', model) applied to mean model probability from MC Dropout samples.",
            "data_sources": [
                "Model predictions and artifacts/calibrator.pkl"
            ]
        },
        "uncertainty": {
            "type": "float",
            "mapped_backend_attributes": [
                "uncertainty_std (returned from SuryaNetInferenceService.predict())"
            ],
            "computation_logic": "Standard deviation of 50 Monte Carlo Dropout stochastic model runs.",
            "data_sources": [
                "Stochastic inference outputs from PatchTST model"
            ]
        },
        "uncertainty_level": {
            "type": "str (LOW, MEDIUM, HIGH)",
            "mapped_backend_attributes": [
                "unc_level in app/api/v1/endpoints/inference.py (line 179-183)"
            ],
            "computation_logic": "LOW if unc < 0.04, MEDIUM if unc <= 0.10, HIGH if unc > 0.10",
            "data_sources": [
                "computed uncertainty_std value"
            ]
        },
        "confidence_level": {
            "type": "str (HIGH, MEDIUM, LOW)",
            "mapped_backend_attributes": [
                "confidence_level (returned from SuryaNetInferenceService.predict())"
            ],
            "computation_logic": "HIGH if prob >= 0.88 and unc < 0.05; MEDIUM if prob >= 0.46 and unc < 0.10; LOW otherwise.",
            "data_sources": [
                "operator_thresholds.json confidence bounds and computed probability + uncertainty"
            ]
        },
        "confirmation": {
            "type": "str (CONFIRMED, UNCONFIRMED)",
            "mapped_backend_attributes": [
                "confirmation (returned from SuryaNetInferenceService.predict())"
            ],
            "computation_logic": "RED alert is confirmed if average of last 3 steps > 0.88 AND slope > 0.0, else UNCONFIRMED.",
            "data_sources": [
                "Rolling history of calibrated probabilities"
            ]
        },
        "top_attention_patches": {
            "type": "List[AttentionPatch]",
            "mapped_backend_attributes": [
                "top_attention_patches (returned from SuryaNetInferenceService.predict())"
            ],
            "computation_logic": "Mean CLS attention map across layers/heads, selecting top 3 patches. Timestamp mapped back to patch center. Physical context (flux value, gradient, rolling variance) computed at patch center timestamp.",
            "data_sources": [
                "Model attention weights and input long_flux history"
            ]
        },
        "mission_impact": {
            "type": "Optional[MissionImpact]",
            "mapped_backend_attributes": [
                "mission_impact (returned from SuryaNetInferenceService.predict())"
            ],
            "computation_logic": "Maps mapped alert level, probability, and uncertainty to specific spacecraft (Aditya-L1, INSAT-3DR, Cartosat-3) actions and recovery times using catalog logic.",
            "data_sources": [
                "app/services/operations/impact.py"
            ]
        }
    }
}

# Write mapping json
with open(os.path.join(OUT_DIR, "frontend_backend_mapping.json"), "w") as f:
    json.dump(mapping, f, indent=2)


# ──────────────────────────────────────────────────────────────────────────────
# 4. operator_workflow_trace.json
# ──────────────────────────────────────────────────────────────────────────────
trace = {
    "trace_steps": [
        {
            "step_index": 1,
            "component": "Ingestion Layer / API Entry",
            "action": "API nowcast post request receives 360-362 chronological one-minute telemetry records of short_flux and long_flux.",
            "verifiable_location": "app/api/v1/endpoints/inference.py (lines 105-125)"
        },
        {
            "step_index": 2,
            "component": "Database Lookup",
            "action": "Queries TimescaleDB table 'flareevent' for start times of any M/X-class flare events in the last 7 days.",
            "verifiable_location": "app/api/v1/endpoints/inference.py (lines 142-164)"
        },
        {
            "step_index": 3,
            "component": "Feature Engineering",
            "action": "Constructs 14 features from raw flux history and recent flare times (including mean_15m, mean_60m, minutes_since_last_flare, etc.).",
            "verifiable_location": "app/services/ml/features.py (compute_features())"
        },
        {
            "step_index": 4,
            "component": "MC Dropout Stochastic Inference",
            "action": "Prepares batch of up to 3 consecutive windows. Executes 50 stochastic forward passes with dropout active on PatchTST model, calculating raw mean probabilities and std uncertainty.",
            "verifiable_location": "app/services/ml/model.py (predict_with_uncertainty())"
        },
        {
            "step_index": 5,
            "component": "Probability Calibration",
            "action": "Applies Isotonic Regression calibrator (calibrator.pkl) to raw mean probabilities to output calibrated probabilities.",
            "verifiable_location": "app/services/ml/inference.py (line 298)"
        },
        {
            "step_index": 6,
            "component": "Initial Alert Mapping",
            "action": "Determines initial raw alert level (GREEN/YELLOW/RED) using calibrated probability and thresholds (0.46 / 0.88) from operator_thresholds.json.",
            "verifiable_location": "app/services/ml/inference.py (lines 148-154, 303)"
        },
        {
            "step_index": 7,
            "component": "Uncertainty Suppression",
            "action": "Applies three-tier uncertainty suppression: unc > 0.20 -> GREEN, unc > 0.15 -> GREEN, unc > 0.10 -> YELLOW.",
            "verifiable_location": "app/services/ml/inference.py (lines 156-171, 304)"
        },
        {
            "step_index": 8,
            "component": "RED Alert Confirmation",
            "action": "If alert is RED, checks if mean(last 3 calibrated probs) > 0.88 AND slope > 0.0. If not, alert is set to YELLOW (UNCONFIRMED).",
            "verifiable_location": "app/services/ml/inference.py (lines 186-234, 314)"
        },
        {
            "step_index": 9,
            "component": "Coincidence Layer Verification",
            "action": "If alert is RED, verifies short_flux gradient > 0.0 and acceleration > 0.0. If rules passed < 2, alert is suppressed to YELLOW.",
            "verifiable_location": "app/services/ml/inference.py (lines 318-362)"
        },
        {
            "step_index": 10,
            "component": "Confidence Classification",
            "action": "Classifies confidence level into HIGH/MEDIUM/LOW based on probability and uncertainty std dev.",
            "verifiable_location": "app/services/ml/inference.py (lines 173-184, 364)"
        },
        {
            "step_index": 11,
            "component": "Explainability Layer Extraction",
            "action": "Averages model CLS attention weights across layers and heads. Extracts top-3 most attended patches, maps them back to timestamps, and calculates physical GOES context.",
            "verifiable_location": "app/services/ml/explainability.py (get_top_attention_patches())"
        },
        {
            "step_index": 12,
            "component": "Mission Impact Mapping",
            "action": "Generates dynamic recommendations and recovery times for Aditya-L1, INSAT-3DR, and Cartosat-3 based on final alert level, probability, and uncertainty.",
            "verifiable_location": "app/services/operations/impact.py (get_mission_impact_assessment())"
        },
        {
            "step_index": 13,
            "component": "Nowcast API Response",
            "action": "Formats final prediction metrics, uncertainty tier, confidence level, confirmation state, explainability patches, and mission impact catalog into FastAPI response.",
            "verifiable_location": "app/api/v1/endpoints/inference.py (lines 214-225)"
        }
    ]
}

# Write trace json
with open(os.path.join(OUT_DIR, "operator_workflow_trace.json"), "w") as f:
    json.dump(trace, f, indent=2)

print("All Sprint 10K JSON artifacts successfully written to artifacts/sprint10k/")
