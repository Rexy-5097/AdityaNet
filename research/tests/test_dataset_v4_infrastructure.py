"""
tests/test_dataset_v4_infrastructure.py

Sprint 29 Phase 4 — contract tests for the Version 4 dataset infrastructure,
WRITTEN BEFORE THE IMPLEMENTATION. Synthetic data only (no production dataset
is read or altered).

Sprint 28 references: 03_DATASET_PIPELINE_V4.md §2 (missing-data rules:
forward-fill gaps ≤ 15 min; > 15 min masked and neutral-imputed post-scaling),
§3 (per-timestep availability + staleness/60 channels), §5 (quality score),
§6 (robust median/IQR scaling FIT ON TRAIN ONLY), §7 (provenance manifest with
policy.py-style field discipline and self-hash).
"""

import os
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.ml.dataset_v4.scaling import RobustScaler, TrainOnlyViolation
from app.services.ml.dataset_v4.masks import build_availability, apply_gap_policy, quality_score
from app.services.ml.dataset_v4.manifest import build_manifest, verify_manifest, ManifestError


# ── robust scaling (§6) ───────────────────────────────────────────────────────

def test_scaler_fit_transform_median_iqr():
    rng = np.random.default_rng(0)
    df = pd.DataFrame({"a": rng.normal(10, 3, 5000), "b": rng.exponential(50, 5000)})
    sc = RobustScaler()
    sc.fit(df, split_name="train")
    out = sc.transform(df)
    assert abs(out["a"].median()) < 0.05 and abs(out["b"].median()) < 0.05
    assert 0.5 < out["a"].quantile(0.75) - out["a"].quantile(0.25) < 1.5


def test_scaler_refuses_non_train_fit():
    df = pd.DataFrame({"a": [1.0, 2.0, 3.0]})
    for bad in ("validation", "test", "s2_test"):
        with pytest.raises(TrainOnlyViolation):
            RobustScaler().fit(df, split_name=bad)


def test_scaler_roundtrip_through_params():
    df = pd.DataFrame({"a": np.linspace(0, 100, 1000)})
    sc = RobustScaler(); sc.fit(df, split_name="train")
    sc2 = RobustScaler.from_params(sc.to_params())
    assert (sc.transform(df).values == sc2.transform(df).values).all()
    assert sc.to_params()["fitted_on_split"] == "train"


def test_scaler_transform_before_fit_raises():
    with pytest.raises(RuntimeError):
        RobustScaler().transform(pd.DataFrame({"a": [1.0]}))


# ── availability masks + staleness (§1-§3) ───────────────────────────────────

def test_availability_from_observed_values():
    s = pd.Series([1.0, np.nan, np.nan, 4.0, np.nan, 6.0])
    mask = build_availability(s)
    assert mask.tolist() == [1, 0, 0, 1, 0, 1]


def test_gap_policy_short_gap_forward_filled_with_staleness():
    # 10-minute gap (≤ 15) → forward-filled values, staleness ramps, mask stays 0
    vals = [5.0] + [np.nan] * 10 + [7.0]
    s = pd.Series(vals)
    filled, mask, staleness = apply_gap_policy(s, max_ffill=15, staleness_cap=60)
    assert mask.tolist() == [1] + [0] * 10 + [1]
    assert filled.iloc[1:11].tolist() == [5.0] * 10          # forward-filled
    assert staleness.tolist()[:4] == [0, 1, 2, 3]            # ramping
    assert staleness.iloc[11] == 0                            # fresh again


def test_gap_policy_long_gap_left_nan_for_neutral_imputation():
    # 20-minute gap (> 15) → beyond 15 filled minutes the values stay NaN,
    # to be neutral-imputed in scaled space downstream (§2/§6 step 4)
    vals = [5.0] + [np.nan] * 20 + [7.0]
    filled, mask, staleness = apply_gap_policy(pd.Series(vals), max_ffill=15, staleness_cap=60)
    assert filled.iloc[1:16].notna().all()                    # first 15 min filled
    assert filled.iloc[16:21].isna().all()                    # remainder left NaN
    assert (staleness <= 60).all()


def test_staleness_capped():
    vals = [1.0] + [np.nan] * 100
    _, _, staleness = apply_gap_policy(pd.Series(vals), max_ffill=15, staleness_cap=60)
    assert staleness.max() == 60


def test_quality_score_definition():
    # §5: quality = availability_fraction × (1 − mean(staleness)/cap)
    mask = pd.Series([1, 1, 0, 0], dtype=float)
    staleness = pd.Series([0, 0, 30, 30], dtype=float)
    q = quality_score(mask, staleness, staleness_cap=60)
    assert q == pytest.approx(0.5 * (1 - 15 / 60))


# ── provenance manifest (§7) ──────────────────────────────────────────────────

def _tmp_source(tmp_path):
    p = tmp_path / "src.parquet"
    pd.DataFrame({"x": [1, 2, 3]}).to_parquet(p)
    return str(p)


def test_manifest_build_and_verify(tmp_path):
    src = _tmp_source(tmp_path)
    m = build_manifest(
        dataset_version="dataset_v4.0.0",
        generator_script=__file__,
        source_files=[src],
        split_counts={"train": {"rows": 3, "positives": 1}},
        scaler_params={"fitted_on_split": "train", "columns": {}},
        feature_list=["a", "b"],
    )
    for field in ("dataset_version", "creation_timestamp", "generator_script",
                  "generator_commit", "source_files", "split_counts",
                  "scaler_params", "feature_list_sha256", "sha256"):
        assert field in m, f"manifest missing {field}"
    verify_manifest(m)                                        # self-hash + source hashes


def test_manifest_detects_tamper(tmp_path):
    src = _tmp_source(tmp_path)
    m = build_manifest("dataset_v4.0.0", __file__, [src],
                       {"train": {"rows": 3, "positives": 1}},
                       {"fitted_on_split": "train", "columns": {}}, ["a"])
    m["split_counts"]["train"]["rows"] = 999                  # tamper post-signing
    with pytest.raises(ManifestError, match="self-hash"):
        verify_manifest(m)


def test_manifest_detects_source_change(tmp_path):
    src = _tmp_source(tmp_path)
    m = build_manifest("dataset_v4.0.0", __file__, [src],
                       {"train": {"rows": 3, "positives": 1}},
                       {"fitted_on_split": "train", "columns": {}}, ["a"])
    pd.DataFrame({"x": [9, 9, 9]}).to_parquet(src)            # mutate source file
    with pytest.raises(ManifestError, match="source"):
        verify_manifest(m)


def test_manifest_rejects_non_train_scaler(tmp_path):
    src = _tmp_source(tmp_path)
    with pytest.raises(ManifestError, match="train"):
        build_manifest("dataset_v4.0.0", __file__, [src],
                       {"train": {"rows": 3, "positives": 1}},
                       {"fitted_on_split": "validation", "columns": {}}, ["a"])
