"""
app/services/ml/features_v4/framework.py

Sprint 29 Phase 2 — Version 4 feature-generation framework.

Sprint 28 references: 02_FEATURE_PIPELINE_V4.md (feature definitions and
per-feature validation tests), 03_DATASET_PIPELINE_V4.md §6 (processing order:
physical-domain feature engineering happens BEFORE scaling; scaling — the only
fitted transform — lives in dataset_v4, never here).

Contract (defined by tests/test_features_v4_framework.py, written first):
  modular            — each Feature independently importable; input frame never
                       modified
  deterministic      — identical output for identical input
  provenance-aware   — compute_all returns a manifest recording, per feature:
                       instrument, required columns, parameters, and a SHA-256
                       of the compute source
  train-only fitting — features are STATELESS by construction (no fit method);
                       the framework rejects any feature exposing one
  inference-safe     — features declare `requires`; compute receives ONLY those
                       columns, and label columns are forbidden in `requires`
"""

import hashlib
import inspect

import pandas as pd

# Labels may never enter feature computation (inference-safety;
# 03_DATASET_PIPELINE_V4.md §6 leakage discipline).
FORBIDDEN_COLUMNS = ("target_6hr_binary", "target_6hr_class")


class Feature:
    """Base class. Subclasses define: name, instrument, requires, params, compute."""

    name: str = ""
    instrument: str = ""
    requires: tuple = ()
    params: dict = {}

    def compute(self, df: pd.DataFrame) -> pd.Series:
        raise NotImplementedError

    def provenance(self) -> dict:
        src = inspect.getsource(type(self))
        return {
            "instrument": self.instrument,
            "requires": list(self.requires),
            "params": dict(self.params),
            "code_sha256": hashlib.sha256(src.encode("utf-8")).hexdigest(),
        }


class FeatureSet:
    """Validated collection of features computed against one input frame."""

    def __init__(self, features: list):
        names = [f.name for f in features]
        if len(set(names)) != len(names):
            raise ValueError(f"duplicate feature names: {names}")
        for f in features:
            forbidden = set(f.requires) & set(FORBIDDEN_COLUMNS)
            if forbidden:
                raise ValueError(
                    f"feature {f.name!r} declares forbidden label column(s) "
                    f"{sorted(forbidden)} in requires"
                )
            if hasattr(f, "fit"):
                raise ValueError(
                    f"feature {f.name!r} exposes a fit method; features must be "
                    "stateless (fitting belongs to dataset_v4 scaling only)"
                )
        self.features = list(features)

    def compute_all(self, df: pd.DataFrame):
        """Compute every feature. Returns (DataFrame of outputs, provenance manifest)."""
        outputs = {}
        manifest = {"framework": "features_v4", "features": {}}
        for f in self.features:
            missing = [c for c in f.requires if c not in df.columns]
            if missing:
                raise ValueError(
                    f"feature {f.name!r}: input frame missing required column(s) {missing}"
                )
            # Inference-safety: the feature sees ONLY its declared columns.
            view = df.loc[:, list(f.requires)].copy()
            series = f.compute(view)
            if len(series) != len(df):
                raise ValueError(
                    f"feature {f.name!r} returned length {len(series)} != input {len(df)}"
                )
            outputs[f.name] = series.reset_index(drop=True)
            manifest["features"][f.name] = f.provenance()
        return pd.DataFrame(outputs), manifest
