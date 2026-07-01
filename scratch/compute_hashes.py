import hashlib
import os
import json

REPO_ROOT = "/Users/soumyadebtripathy/AdityaNet"

files = [
    "artifacts/operator_thresholds.json",
    "artifacts/operator_thresholds_validation_only.json",
    "artifacts/operational_thresholds.json",
    "artifacts/calibrator.pkl",
    "artifacts/models/patchtst_best.pt",
    "artifacts/explainability_examples.json",
    "artifacts/feature_columns.json",
    "artifacts/training_history.json",
    "app/services/ml/inference.py",
    "app/services/ml/explainability.py",
    "app/services/operations/impact.py",
    "app/api/v1/endpoints/inference.py",
]

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

results = {}
for rel in files:
    abs_path = os.path.join(REPO_ROOT, rel)
    if os.path.exists(abs_path):
        results[rel] = {
            "sha256": sha256(abs_path),
            "size_bytes": os.path.getsize(abs_path)
        }
    else:
        results[rel] = "NOT FOUND"

print(json.dumps(results, indent=2))
