"""
app/services/ml/features_v4/aditya.py

Sprint 31 Phase 1 — the Aditya-L1 features of
artifacts/sprint28/02_FEATURE_PIPELINE_V4.md: NEW rows 4-17 plus the single
MODIFY output log_hel1os_band0. No additions, no omissions.

Input contract: features receive the GAP-POLICY-FILLED physical series
(03_DATASET_PIPELINE_V4.md §2 applied by the dataset builder BEFORE feature
computation: masked minutes are NaN, gaps <= 15 min forward-filled). NaN in ->
NaN out for affected timesteps; those values are neutral-imputed in normalized
space after train-only scaling (§6 step 4), with the per-timestep availability
and staleness channels disclosing missingness to the model (§3).

Rolling constructs use trailing (causal) windows with min_periods=1 so masked
minutes are EXCLUDED from the aggregate rather than poisoning it (the row-14
"masked minutes excluded" rule, applied uniformly).

Stateless-by-construction (ADR-0001): the two activity features (rows 12-13)
require the train-split 95th percentile of log_solexs_soft; that value is
computed by the DATASET layer on the training split only and passed here as a
frozen constructor parameter, recorded in params for provenance.
"""

import numpy as np
import pandas as pd

from app.services.ml.features_v4.framework import Feature

_EPS = 1e-12
_DT_SECONDS = 60.0          # 1-minute grid; fluence integrates rate x dt [s]
_ACTIVE_CAP_MIN = 10080     # 7-day cap, mirror of GOES minutes_since_last_flare
_SOLEXS_LOW = ("solexs_rate_ch1", "solexs_rate_ch2", "solexs_rate_ch3")
_SOLEXS_MID = ("solexs_rate_ch4", "solexs_rate_ch5", "solexs_rate_ch6")
_SOLEXS_HIGH = ("solexs_rate_ch7", "solexs_rate_ch8", "solexs_rate_ch9")
_SOLEXS_ALL = _SOLEXS_LOW + _SOLEXS_MID + _SOLEXS_HIGH


def _band_sum(df: pd.DataFrame, cols) -> pd.Series:
    return df[list(cols)].sum(axis=1, min_count=1)   # NaN if the whole band is masked


def _log_soft(df: pd.DataFrame) -> pd.Series:
    return np.log1p(_band_sum(df, _SOLEXS_ALL).clip(lower=0.0))


class SolexsHRHighLow(Feature):
    """Row 4 — thermal-bremsstrahlung spectral hardening (high/low band ratio)."""
    name = "solexs_HR_high_low"
    instrument = "solexs"
    requires = _SOLEXS_ALL
    params = {"numerator": "ch7..ch9", "denominator": "ch1..ch3", "eps": _EPS}

    def compute(self, df):
        return _band_sum(df, _SOLEXS_HIGH) / (_band_sum(df, _SOLEXS_LOW).clip(lower=_EPS))


class SolexsHRMidLow(Feature):
    """Row 5 — same principle, mid band."""
    name = "solexs_HR_mid_low"
    instrument = "solexs"
    requires = _SOLEXS_ALL
    params = {"numerator": "ch4..ch6", "denominator": "ch1..ch3", "eps": _EPS}

    def compute(self, df):
        return _band_sum(df, _SOLEXS_MID) / (_band_sum(df, _SOLEXS_LOW).clip(lower=_EPS))


class SolexsDHR15m(Feature):
    """Row 6 — soft-hard-soft spectral evolution: 15-min backward difference of HR_high_low."""
    name = "solexs_dHR_15m"
    instrument = "solexs"
    requires = _SOLEXS_ALL
    params = {"minutes": 15, "scheme": "backward-difference"}

    def compute(self, df):
        hr = _band_sum(df, _SOLEXS_HIGH) / (_band_sum(df, _SOLEXS_LOW).clip(lower=_EPS))
        return hr.diff(15)


class SolexsHRPeak60m(Feature):
    """Row 7 — impulsive-phase memory: trailing 60-min max of HR_high_low."""
    name = "solexs_HR_peak_60m"
    instrument = "solexs"
    requires = _SOLEXS_ALL
    params = {"window_min": 60}

    def compute(self, df):
        hr = _band_sum(df, _SOLEXS_HIGH) / (_band_sum(df, _SOLEXS_LOW).clip(lower=_EPS))
        return hr.rolling(60, min_periods=1).max()


class LogSolexsSoft(Feature):
    """Row 8 — log-domain soft-band aggregate."""
    name = "log_solexs_soft"
    instrument = "solexs"
    requires = _SOLEXS_ALL
    params = {"transform": "log1p(sum ch1..ch9)"}

    def compute(self, df):
        return _log_soft(df)


class SolexsVariance15m(Feature):
    """Row 9 — preflare intermittency: trailing 15-min variance of log_solexs_soft."""
    name = "solexs_variance_15m"
    instrument = "solexs"
    requires = _SOLEXS_ALL
    params = {"window_min": 15}

    def compute(self, df):
        return _log_soft(df).rolling(15, min_periods=1).var()


class SolexsVariance60m(Feature):
    """Row 10 — same, 60-min window."""
    name = "solexs_variance_60m"
    instrument = "solexs"
    requires = _SOLEXS_ALL
    params = {"window_min": 60}

    def compute(self, df):
        return _log_soft(df).rolling(60, min_periods=1).var()


class SolexsPeak30m(Feature):
    """Row 11 — recent maximum brightening: trailing 30-min max of log_solexs_soft."""
    name = "solexs_peak_30m"
    instrument = "solexs"
    requires = _SOLEXS_ALL
    params = {"window_min": 30}

    def compute(self, df):
        return _log_soft(df).rolling(30, min_periods=1).max()


class MinutesSinceSolexsActive(Feature):
    """Row 12 — flare waiting-time clustering: minutes since log_solexs_soft
    last exceeded its TRAIN-SPLIT 95th percentile (frozen parameter), cap 10080."""
    name = "minutes_since_solexs_active"
    instrument = "solexs"
    requires = _SOLEXS_ALL

    def __init__(self, train_p95: float):
        self.params = {"train_p95_log_solexs_soft": float(train_p95),
                       "cap_min": _ACTIVE_CAP_MIN,
                       "threshold_provenance": "train-split-only (dataset layer)"}
        self._thr = float(train_p95)

    def compute(self, df):
        soft = _log_soft(df)
        active = (soft > self._thr).to_numpy()          # NaN -> False (not active)
        idx = np.arange(len(soft), dtype=float)
        last = pd.Series(np.where(active, idx, np.nan)).ffill().to_numpy()
        minutes = np.where(np.isnan(last), _ACTIVE_CAP_MIN, idx - last)
        return pd.Series(np.minimum(minutes, _ACTIVE_CAP_MIN), index=df.index)


class SolexsActiveFraction6h(Feature):
    """Row 13 — fraction of the trailing 360 min above the same train percentile."""
    name = "solexs_active_fraction_6h"
    instrument = "solexs"
    requires = _SOLEXS_ALL

    def __init__(self, train_p95: float):
        self.params = {"train_p95_log_solexs_soft": float(train_p95),
                       "window_min": 360,
                       "threshold_provenance": "train-split-only (dataset layer)"}
        self._thr = float(train_p95)

    def compute(self, df):
        active = (_log_soft(df) > self._thr).astype(float)   # NaN -> 0 (not active)
        return active.rolling(360, min_periods=1).sum() / 360.0


class Hel1osFluence30m(Feature):
    """Row 14 — Neupert effect: trailing 30-min integral of band0 rate, masked
    minutes excluded, log1p-stored."""
    name = "hel1os_fluence_30m"
    instrument = "hel1os"
    requires = ("hel1os_rate_band0",)
    params = {"window_min": 30, "dt_seconds": _DT_SECONDS, "store": "log1p"}

    def compute(self, df):
        s = df["hel1os_rate_band0"].rolling(30, min_periods=1).sum() * _DT_SECONDS
        return np.log1p(s.clip(lower=0.0))


class Hel1osFluence60m(Feature):
    """Row 15 — same, 60-min integral."""
    name = "hel1os_fluence_60m"
    instrument = "hel1os"
    requires = ("hel1os_rate_band0",)
    params = {"window_min": 60, "dt_seconds": _DT_SECONDS, "store": "log1p"}

    def compute(self, df):
        s = df["hel1os_rate_band0"].rolling(60, min_periods=1).sum() * _DT_SECONDS
        return np.log1p(s.clip(lower=0.0))


class NonthermalThermalRatio(Feature):
    """Row 16 — thermal vs non-thermal separation: band0 / GOES long flux,
    eps-guarded, log1p-stored."""
    name = "nonthermal_thermal_ratio"
    instrument = "hel1os+goes"
    requires = ("hel1os_rate_band0", "long_flux")
    params = {"eps": _EPS, "store": "log1p"}

    def compute(self, df):
        r = df["hel1os_rate_band0"].clip(lower=0.0) / df["long_flux"].clip(lower=_EPS)
        return np.log1p(r)


class DNtr15m(Feature):
    """Row 17 — particle-acceleration onset timing: 15-min backward difference of row 16."""
    name = "d_ntr_15m"
    instrument = "hel1os+goes"
    requires = ("hel1os_rate_band0", "long_flux")
    params = {"minutes": 15, "scheme": "backward-difference"}

    def compute(self, df):
        r = df["hel1os_rate_band0"].clip(lower=0.0) / df["long_flux"].clip(lower=_EPS)
        return np.log1p(r).diff(15)


class LogHel1osBand0(Feature):
    """MODIFY output — log1p(hel1os_rate_band0) replaces the raw column as input."""
    name = "log_hel1os_band0"
    instrument = "hel1os"
    requires = ("hel1os_rate_band0",)
    params = {"transform": "log1p"}

    def compute(self, df):
        return np.log1p(df["hel1os_rate_band0"].clip(lower=0.0))


def aditya_features(train_p95_log_solexs_soft: float):
    """The complete Aditya-L1 feature list (rows 4-17 + the MODIFY output), in
    the 02_FEATURE_PIPELINE_V4.md model-input order: SoLEXS 10, HEL1OS 5."""
    return [
        SolexsHRHighLow(), SolexsHRMidLow(), SolexsDHR15m(), SolexsHRPeak60m(),
        LogSolexsSoft(), SolexsVariance15m(), SolexsVariance60m(), SolexsPeak30m(),
        MinutesSinceSolexsActive(train_p95_log_solexs_soft),
        SolexsActiveFraction6h(train_p95_log_solexs_soft),
        Hel1osFluence30m(), Hel1osFluence60m(),
        NonthermalThermalRatio(), DNtr15m(), LogHel1osBand0(),
    ]
