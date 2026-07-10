"""
app/services/ml/features_v4/goes_physics.py

Sprint 29 Phase 3 — the three GOES physics features of
artifacts/sprint28/02_FEATURE_PIPELINE_V4.md (NEW rows 1-3). No others.

Physics: isothermal temperature and emission measure from the GOES two-channel
ratio (White, Thomas & Schwartz 2005, Solar Physics 227, 231); preflare heating
as precursor (Benz 2017, Living Reviews in Solar Physics 14, 2).

FLAGGED AMBIGUITY (per the Sprint 29 brief's conservative-interpretation rule):
Sprint 28 names "the published polynomial/table interpolation" for T(R) without
supplying coefficients, and no explicit long-channel response function for EM.
Conservative choices, recorded here and in Feature_Validation_Report.md:
  * T(R): the Thomas, Starr & Crannell (1985) cubic
        T[MK] = 3.15 + 77.2 R - 164 R^2 + 205 R^3,  R = short/long,
    valid domain R in [0.02, 0.7] (clipped outside). Strictly monotonic on the
    domain (its derivative 77.2 - 328R + 615R^2 has negative discriminant, so
    it is positive everywhere). Verification against the White/Thomas/Schwartz
    2005 tables is pending literature access — the monotone SHAPE, which is
    what survives the pipeline's robust scaling, does not depend on it.
  * EM: log10(EM) = log10(long_flux) - 2 log10(T[MK]) + C with C = 56.0 — a
    monotone-correct PROXY (hotter plasma needs less emission measure for the
    same long-channel flux); absolute calibration NOT PROVEN against published
    response tables. The additive constant and power are removed by the
    train-only robust scaling of 03_DATASET_PIPELINE_V4.md section 6, so model
    inputs are unaffected by the uncalibrated constant.
"""

import numpy as np
import pandas as pd

from app.services.ml.features_v4.framework import Feature

RATIO_VALID_MIN = 0.02
RATIO_VALID_MAX = 0.70
_EPS = 1e-12
_EM_LOG_CONST = 56.0
_DERIV_MINUTES = 15


def _ratio(df: pd.DataFrame) -> np.ndarray:
    short = df["short_flux"].to_numpy(dtype=float)
    long = df["long_flux"].to_numpy(dtype=float)
    r = short / np.clip(long, _EPS, None)
    return np.clip(r, RATIO_VALID_MIN, RATIO_VALID_MAX)


def t_iso_from_ratio(r: np.ndarray) -> np.ndarray:
    """Thomas, Starr & Crannell (1985) cubic; input clipped to the valid domain."""
    r = np.clip(np.asarray(r, dtype=float), RATIO_VALID_MIN, RATIO_VALID_MAX)
    return 3.15 + 77.2 * r - 164.0 * r**2 + 205.0 * r**3


class GoesTIso(Feature):
    """Isothermal temperature [MK] from the GOES channel ratio (row 1)."""
    name = "goes_T_iso"
    instrument = "goes"
    requires = ("short_flux", "long_flux")
    params = {"ratio_valid_domain": [RATIO_VALID_MIN, RATIO_VALID_MAX],
              "inversion": "Thomas-Starr-Crannell-1985-cubic"}

    def compute(self, df: pd.DataFrame) -> pd.Series:
        return pd.Series(t_iso_from_ratio(_ratio(df)), index=df.index)


class GoesEM(Feature):
    """log10 emission-measure proxy at the inverted temperature (row 2)."""
    name = "goes_EM"
    instrument = "goes"
    requires = ("short_flux", "long_flux")
    params = {"response_proxy": "T^2", "log_const": _EM_LOG_CONST,
              "calibration": "proxy — absolute scale NOT PROVEN (flagged)"}

    def compute(self, df: pd.DataFrame) -> pd.Series:
        t = t_iso_from_ratio(_ratio(df))
        long = np.clip(df["long_flux"].to_numpy(dtype=float), _EPS, None)
        log_em = np.log10(long) - 2.0 * np.log10(t) + _EM_LOG_CONST
        return pd.Series(log_em, index=df.index)


class GoesDTIso15m(Feature):
    """15-minute backward difference of goes_T_iso — causal by construction (row 3)."""
    name = "goes_dT_iso_15m"
    instrument = "goes"
    requires = ("short_flux", "long_flux")
    params = {"minutes": _DERIV_MINUTES, "scheme": "backward-difference"}

    def compute(self, df: pd.DataFrame) -> pd.Series:
        t = pd.Series(t_iso_from_ratio(_ratio(df)), index=df.index)
        return t.diff(_DERIV_MINUTES).fillna(0.0)
