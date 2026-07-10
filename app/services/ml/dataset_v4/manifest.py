"""
app/services/ml/dataset_v4/manifest.py

Sprint 29 Phase 4 — dataset provenance manifest schema, writer, verifier.
Sprint 28 reference: 03_DATASET_PIPELINE_V4.md §7 ("Sprint 23-style provenance
manifest ... enforced by the same load-time gate pattern"); reuses the
canonical-hash discipline of app/services/ml/policy.py.
"""

import hashlib
import json
import os
from datetime import datetime, timezone


class ManifestError(Exception):
    """Manifest incomplete, tampered, or referencing changed sources."""


def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _canonical_sha256(doc: dict) -> str:
    shadow = dict(doc)
    shadow["sha256"] = ""
    payload = json.dumps(shadow, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def build_manifest(dataset_version: str, generator_script: str, source_files: list,
                   split_counts: dict, scaler_params: dict, feature_list: list) -> dict:
    if scaler_params.get("fitted_on_split") != "train":
        raise ManifestError(
            "scaler_params.fitted_on_split must be 'train' "
            "(03_DATASET_PIPELINE_V4.md section 6 train-only discipline)"
        )
    doc = {
        "dataset_version": dataset_version,
        "creation_timestamp": datetime.now(timezone.utc).isoformat(),
        "generator_script": generator_script,
        "generator_commit": "sha256:" + _sha256_file(generator_script),
        "source_files": [{"path": p, "sha256": _sha256_file(p)} for p in source_files],
        "split_counts": split_counts,
        "scaler_params": scaler_params,
        "feature_list": list(feature_list),
        "feature_list_sha256": hashlib.sha256(
            json.dumps(sorted(feature_list)).encode()).hexdigest(),
    }
    doc["sha256"] = _canonical_sha256(doc)
    return doc


def verify_manifest(doc: dict) -> None:
    """Verify self-hash and that every recorded source file is unchanged."""
    required = ("dataset_version", "creation_timestamp", "generator_script",
                "generator_commit", "source_files", "split_counts",
                "scaler_params", "feature_list", "feature_list_sha256", "sha256")
    missing = [f for f in required if f not in doc]
    if missing:
        raise ManifestError(f"manifest missing fields: {missing}")
    if doc["sha256"] != _canonical_sha256(doc):
        raise ManifestError("manifest self-hash mismatch — content modified after signing")
    for rec in doc["source_files"]:
        if not os.path.exists(rec["path"]):
            raise ManifestError(f"source file missing: {rec['path']}")
        if _sha256_file(rec["path"]) != rec["sha256"]:
            raise ManifestError(f"source file changed since manifest: {rec['path']}")
