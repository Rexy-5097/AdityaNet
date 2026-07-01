import os
import hashlib
import json

REPO_ROOT = "/Users/soumyadebtripathy/AdityaNet"

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

files = {
    "prediction_certificate": "artifacts/sprint10j/prediction_certificate.json",
    "execution_manifest": "artifacts/sprint10j/execution_manifest.json",
    "repository_fingerprint": "artifacts/sprint10j/repository_fingerprint.json",
    "artifact_hashes": "artifacts/sprint10j/artifact_hashes.json",
    "operator_workflow_trace": "artifacts/sprint10k/operator_workflow_trace.json",
    "component_reference_graph": "artifacts/sprint10k/component_reference_graph.json",
}

for name, rel in files.items():
    abs_path = os.path.join(REPO_ROOT, rel)
    print(f"{name} hash: {sha256(abs_path)}")
