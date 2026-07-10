"""
app/services/ml/dataset_v4/scaling.py

Sprint 29 Phase 4 — robust scaling, train-only by construction.
Sprint 28 reference: 03_DATASET_PIPELINE_V4.md §6 step 3 ("robust
standardization (median/interquartile range) per feature, fit on the training
split only and frozen into the dataset manifest") and the leakage discipline
of artifacts/sprint22_5/FINAL_VERDICT.md.
"""

import numpy as np
import pandas as pd


class TrainOnlyViolation(Exception):
    """Raised when a scaler fit is attempted on anything but the training split."""


class RobustScaler:
    """Per-column (x - median) / IQR scaling. Fit refuses non-train splits."""

    def __init__(self):
        self._params = None

    def fit(self, df: pd.DataFrame, split_name: str):
        if split_name != "train":
            raise TrainOnlyViolation(
                f"RobustScaler.fit called with split_name={split_name!r}; "
                "scaling parameters may only be fit on the training split "
                "(03_DATASET_PIPELINE_V4.md section 6)."
            )
        cols = {}
        for c in df.columns:
            v = df[c].to_numpy(dtype=float)
            med = float(np.nanmedian(v))
            iqr = float(np.nanpercentile(v, 75) - np.nanpercentile(v, 25))
            cols[c] = {"median": med, "iqr": iqr if iqr > 0 else 1.0}
        self._params = {"fitted_on_split": split_name, "columns": cols}
        return self

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        if self._params is None:
            raise RuntimeError("RobustScaler.transform called before fit")
        out = {}
        for c in df.columns:
            p = self._params["columns"][c]
            out[c] = (df[c].to_numpy(dtype=float) - p["median"]) / p["iqr"]
        return pd.DataFrame(out, index=df.index)

    def to_params(self) -> dict:
        if self._params is None:
            raise RuntimeError("scaler not fitted")
        return {"fitted_on_split": self._params["fitted_on_split"],
                "columns": {k: dict(v) for k, v in self._params["columns"].items()}}

    @classmethod
    def from_params(cls, params: dict) -> "RobustScaler":
        sc = cls()
        sc._params = {"fitted_on_split": params["fitted_on_split"],
                      "columns": {k: dict(v) for k, v in params["columns"].items()}}
        return sc
