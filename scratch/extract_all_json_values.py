import os
import json
import pandas as pd
import numpy as np

aditya_l1_dir = "/Users/soumyadebtripathy/AdityaNet/artifacts/aditya_l1"
artifacts_dir = "/Users/soumyadebtripathy/AdityaNet/artifacts"
scratch_dir = "/Users/soumyadebtripathy/AdityaNet/scratch"

summary = {}

# Let's write a function to safely load json
def load_json(path):
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return "NOT FOUND"

# Load JSONs
jsons = {
    "provenance_audit": load_json(os.path.join(aditya_l1_dir, "provenance_audit.json")),
    "train_test_boundary_audit": load_json(os.path.join(aditya_l1_dir, "train_test_boundary_audit.json")),
    "corpus_completeness_audit": load_json(os.path.join(aditya_l1_dir, "corpus_completeness_audit.json")),
    "overlap_corpus_statistics": load_json(os.path.join(aditya_l1_dir, "overlap_corpus_statistics.json")),
    "trust_gate_audit": load_json(os.path.join(aditya_l1_dir, "trust_gate_audit.json")),
    "trust_gate_validation": load_json(os.path.join(aditya_l1_dir, "trust_gate_validation.json")),
    "window_overlap_audit": load_json(os.path.join(aditya_l1_dir, "window_overlap_audit.json")),
    "file_inventory": load_json(os.path.join(aditya_l1_dir, "file_inventory.json")),
    "archive_inventory": load_json(os.path.join(aditya_l1_dir, "archive_inventory.json")),
    
    # Root artifacts
    "baseline_metrics": load_json(os.path.join(artifacts_dir, "baseline_metrics.json")),
    "test_metrics": load_json(os.path.join(artifacts_dir, "test_metrics.json")),
    "training_history": load_json(os.path.join(artifacts_dir, "training_history.json")),
    "evaluation_audit_report": load_json(os.path.join(artifacts_dir, "evaluation_audit_report.json")),
    "operator_thresholds": load_json(os.path.join(artifacts_dir, "operator_thresholds.json")),
    "operator_thresholds_validation_only": load_json(os.path.join(artifacts_dir, "operator_thresholds_validation_only.json")),
    "operator_readiness_report": load_json(os.path.join(artifacts_dir, "operator_readiness_report.json")),
    "operator_backtest": load_json(os.path.join(artifacts_dir, "operator_backtest.json")),
    "operator_trust_projection": load_json(os.path.join(artifacts_dir, "operator_trust_projection.json")),
    "operator_trust_audit": load_json(os.path.join(artifacts_dir, "operator_trust_audit.json")),
    "calibration_audit": load_json(os.path.join(artifacts_dir, "calibration_audit.json")),
    
    # Diagnostic json files
    "attention_statistics": load_json(os.path.join(artifacts_dir, "attention_statistics.json")),
    "error_by_year": load_json(os.path.join(artifacts_dir, "error_by_year.json")),
    "error_clusters": load_json(os.path.join(artifacts_dir, "error_clusters.json")),
    "fn_statistics": load_json(os.path.join(artifacts_dir, "fn_statistics.json")),
    "fp_statistics": load_json(os.path.join(artifacts_dir, "fp_statistics.json")),
    "fn_root_cause_verification": load_json(os.path.join(artifacts_dir, "fn_root_cause_verification.json")),
    "fp_root_cause_verification": load_json(os.path.join(artifacts_dir, "fp_root_cause_verification.json")),
}

# Write summary to scratch
with open(os.path.join(scratch_dir, "extracted_json_values.json"), "w") as f:
    json.dump(jsons, f, indent=2)

print("Finished extracting all JSON values to scratch/extracted_json_values.json")
