"""
tests/test_features_v4_goes_physics.py

Sprint 29 Phase 3 — physical-constraint tests for the three GOES physics
features, WRITTEN BEFORE THE IMPLEMENTATION.

Sprint 28 references: 02_FEATURE_PIPELINE_V4.md NEW rows 1-3 (goes_T_iso,
goes_EM, goes_dT_iso_15m) and their named validation tests: T monotonic in the
channel ratio over the valid domain; EM positive and finite; derivative zero on
constant input and positive under synthetic heating. Plus the Sprint 29 brief's
checks: no future information (causality) and determinism.
"""

import os
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.ml.features_v4.framework import FeatureSet
from app.services.ml.features_v4.goes_physics import (
    GoesTIso,
    GoesEM,
    GoesDTIso15m,
    RATIO_VALID_MIN,
    RATIO_VALID_MAX,
    t_iso_from_ratio,
)


def _frame(short, long):
    n = len(short)
    return pd.DataFrame({
        "timestamp": pd.date_range("2024-01-01", periods=n, freq="min"),
        "short_flux": np.asarray(short, dtype=float),
        "long_flux": np.asarray(long, dtype=float),
    })


# ── goes_T_iso ────────────────────────────────────────────────────────────────

def test_T_monotonic_in_ratio_over_valid_domain():
    r = np.linspace(RATIO_VALID_MIN, RATIO_VALID_MAX, 500)
    t = t_iso_from_ratio(r)
    assert np.all(np.diff(t) > 0), "T must be strictly increasing in R on the valid domain"
    assert np.isfinite(t).all()


def test_T_clipped_outside_valid_domain():
    t_low = t_iso_from_ratio(np.array([1e-6]))
    t_hi = t_iso_from_ratio(np.array([5.0]))
    assert np.isclose(t_low[0], t_iso_from_ratio(np.array([RATIO_VALID_MIN]))[0])
    assert np.isclose(t_hi[0], t_iso_from_ratio(np.array([RATIO_VALID_MAX]))[0])


def test_T_feature_through_framework():
    long = np.full(100, 1e-6)
    short = np.linspace(0.03, 0.3, 100) * long   # rising ratio → rising T
    out, _ = FeatureSet([GoesTIso()]).compute_all(_frame(short, long))
    t = out["goes_T_iso"].values
    assert np.all(np.diff(t) > 0)


# ── goes_EM ───────────────────────────────────────────────────────────────────

def test_EM_finite_positive_in_sanity_band():
    long = np.full(50, 1e-6)                     # ~M1-class long flux
    short = 0.1 * long
    out, _ = FeatureSet([GoesEM()]).compute_all(_frame(short, long))
    log_em = out["goes_EM"].values
    assert np.isfinite(log_em).all()
    assert (log_em > 40).all() and (log_em < 60).all(), \
        "log10 EM proxy outside sanity band (absolute calibration is a proxy; see flag)"


def test_EM_decreases_with_temperature_at_fixed_flux():
    # hotter plasma needs LESS emission measure for the same long-channel flux
    long = np.full(50, 1e-6)
    short_cool = np.full(50, 0.03e-6)
    short_hot = np.full(50, 0.30e-6)
    em_cool, _ = FeatureSet([GoesEM()]).compute_all(_frame(short_cool, long))
    em_hot, _ = FeatureSet([GoesEM()]).compute_all(_frame(short_hot, long))
    assert em_hot["goes_EM"].iloc[0] < em_cool["goes_EM"].iloc[0]


# ── goes_dT_iso_15m ───────────────────────────────────────────────────────────

def test_dT_zero_on_constant_input():
    long = np.full(60, 1e-6); short = np.full(60, 0.1e-6)
    out, _ = FeatureSet([GoesDTIso15m()]).compute_all(_frame(short, long))
    assert np.allclose(out["goes_dT_iso_15m"].values[15:], 0.0)


def test_dT_positive_under_synthetic_heating():
    long = np.full(120, 1e-6)
    short = np.linspace(0.03, 0.3, 120) * long   # monotone heating
    out, _ = FeatureSet([GoesDTIso15m()]).compute_all(_frame(short, long))
    assert (out["goes_dT_iso_15m"].values[15:] > 0).all()


# ── causality (no future information) — all three features ───────────────────

@pytest.mark.parametrize("feat", [GoesTIso(), GoesEM(), GoesDTIso15m()])
def test_no_future_information(feat):
    rng = np.random.default_rng(3)
    long = rng.uniform(5e-7, 5e-6, 200)
    short = long * rng.uniform(0.03, 0.4, 200)
    df = _frame(short, long)
    base, _ = FeatureSet([feat]).compute_all(df)
    df2 = df.copy()
    df2.loc[150:, ["short_flux", "long_flux"]] = 9e-4   # perturb the FUTURE
    pert, _ = FeatureSet([feat]).compute_all(df2)
    np.testing.assert_array_equal(
        base[feat.name].values[:150], pert[feat.name].values[:150],
        err_msg=f"{feat.name} leaked future information into past outputs",
    )


# ── determinism ───────────────────────────────────────────────────────────────

def test_determinism_all_three():
    rng = np.random.default_rng(11)
    long = rng.uniform(5e-7, 5e-6, 300)
    short = long * rng.uniform(0.03, 0.4, 300)
    fs = FeatureSet([GoesTIso(), GoesEM(), GoesDTIso15m()])
    out1, _ = fs.compute_all(_frame(short, long))
    out2, _ = fs.compute_all(_frame(short, long))
    assert (out1.values == out2.values).all()


# ── scope guard: exactly three features exist in the module ──────────────────

def test_exactly_three_goes_physics_features():
    import app.services.ml.features_v4.goes_physics as gp
    from app.services.ml.features_v4.framework import Feature
    feats = [v for v in vars(gp).values()
             if isinstance(v, type) and issubclass(v, Feature) and v is not Feature]
    assert len(feats) == 3, f"Sprint 29 scope is exactly three features, found {len(feats)}"
