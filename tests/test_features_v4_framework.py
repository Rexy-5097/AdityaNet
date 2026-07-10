"""
tests/test_features_v4_framework.py

Sprint 29 Phase 2 — contract tests for the Version 4 feature framework,
WRITTEN BEFORE THE IMPLEMENTATION (tests define the contract).

Sprint 28 references: 02_FEATURE_PIPELINE_V4.md (per-feature validation-test
requirement), 03_DATASET_PIPELINE_V4.md §6 (train-only fitting: features are
stateless; fitting lives only in the dataset scaler), and the Sprint 29 brief's
five framework properties: modular, deterministic, provenance-aware,
train-only-fitting, inference-safe.
"""

import os
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.ml.features_v4.framework import (
    Feature,
    FeatureSet,
    FORBIDDEN_COLUMNS,
)


# ── toy features used by the contract tests ───────────────────────────────────

class DoubleFlux(Feature):
    name = "double_flux"
    instrument = "goes"
    requires = ("long_flux",)
    params = {"factor": 2.0}

    def compute(self, df: pd.DataFrame) -> pd.Series:
        return df["long_flux"] * self.params["factor"]


class SneakyUndeclared(Feature):
    name = "sneaky"
    instrument = "goes"
    requires = ("long_flux",)
    params = {}

    def compute(self, df: pd.DataFrame) -> pd.Series:
        return df["short_flux"] * 1.0  # accesses a column it never declared


class WantsLabels(Feature):
    name = "wants_labels"
    instrument = "goes"
    requires = ("long_flux", "target_6hr_binary")
    params = {}

    def compute(self, df: pd.DataFrame) -> pd.Series:
        return df["long_flux"]


def _frame(n=100, seed=0):
    rng = np.random.default_rng(seed)
    return pd.DataFrame({
        "timestamp": pd.date_range("2024-01-01", periods=n, freq="min"),
        "long_flux": rng.random(n) * 1e-6,
        "short_flux": rng.random(n) * 1e-7,
        "target_6hr_binary": (rng.random(n) < 0.2).astype(int),
    })


# ── modular ───────────────────────────────────────────────────────────────────

def test_feature_computes_and_aligns():
    df = _frame()
    out, manifest = FeatureSet([DoubleFlux()]).compute_all(df)
    assert list(out.columns) == ["double_flux"]
    assert len(out) == len(df)
    np.testing.assert_allclose(out["double_flux"].values, df["long_flux"].values * 2.0)


def test_input_dataframe_not_modified():
    df = _frame()
    before = df.copy(deep=True)
    FeatureSet([DoubleFlux()]).compute_all(df)
    pd.testing.assert_frame_equal(df, before)


# ── inference-safe ────────────────────────────────────────────────────────────

def test_compute_receives_only_declared_columns():
    with pytest.raises(KeyError):
        FeatureSet([SneakyUndeclared()]).compute_all(_frame())


def test_label_columns_forbidden_in_requires():
    assert "target_6hr_binary" in FORBIDDEN_COLUMNS
    with pytest.raises(ValueError, match="forbidden"):
        FeatureSet([WantsLabels()])


def test_missing_required_column_raises():
    df = _frame().drop(columns=["long_flux"])
    with pytest.raises(ValueError, match="missing required"):
        FeatureSet([DoubleFlux()]).compute_all(df)


# ── deterministic ─────────────────────────────────────────────────────────────

def test_determinism_identical_output_across_runs():
    df = _frame(seed=7)
    out1, _ = FeatureSet([DoubleFlux()]).compute_all(df)
    out2, _ = FeatureSet([DoubleFlux()]).compute_all(df)
    assert (out1.values == out2.values).all()


# ── provenance-aware ──────────────────────────────────────────────────────────

def test_provenance_manifest_complete():
    _, manifest = FeatureSet([DoubleFlux()]).compute_all(_frame())
    assert manifest["framework"] == "features_v4"
    rec = manifest["features"]["double_flux"]
    for key in ("instrument", "requires", "params", "code_sha256"):
        assert key in rec, f"provenance missing {key}"
    assert rec["requires"] == ["long_flux"]
    assert rec["params"] == {"factor": 2.0}
    assert len(rec["code_sha256"]) == 64


# ── train-only fitting (structural statelessness) ─────────────────────────────

def test_features_are_stateless_no_fit_interface():
    assert not hasattr(DoubleFlux(), "fit"), (
        "Features must be stateless; fitting belongs exclusively to the "
        "dataset scaler (03_DATASET_PIPELINE_V4.md section 6)"
    )


def test_duplicate_feature_names_rejected():
    with pytest.raises(ValueError, match="duplicate"):
        FeatureSet([DoubleFlux(), DoubleFlux()])
