"""
app/services/ml/dataset_v4/masks.py

Sprint 29 Phase 4 — per-timestep availability, gap policy, staleness, quality.
Sprint 28 references: 03_DATASET_PIPELINE_V4.md §1 (staleness counter),
§2 (forward-fill gaps ≤ 15 min; longer gaps left for neutral imputation
post-scaling), §3 (per-timestep availability channel — the fix for the
label-minute scalar collapse at app/services/ml/dataset_v3.py:110-111),
§5 (quality = availability_fraction × (1 − mean staleness / cap)).
"""

import numpy as np
import pandas as pd


def build_availability(values: pd.Series) -> pd.Series:
    """Per-timestep binary availability: 1 where a value was genuinely observed."""
    return values.notna().astype(np.int8)


def apply_gap_policy(values: pd.Series, max_ffill: int = 15, staleness_cap: int = 60):
    """
    Returns (filled_values, availability_mask, staleness_minutes).

    Gaps of length <= max_ffill minutes: forward-filled (values only; the mask
    still records 0 — availability means OBSERVED, not filled). Longer gaps:
    the first max_ffill minutes are filled, the remainder stays NaN for
    downstream neutral imputation in scaled space. Staleness counts minutes
    since the last genuine observation, capped at staleness_cap.
    """
    mask = build_availability(values)
    filled = values.ffill(limit=max_ffill)
    # staleness: minutes since last observed sample (0 where observed)
    idx = np.arange(len(values))
    last_obs = pd.Series(np.where(mask.to_numpy() == 1, idx, np.nan)).ffill()
    staleness = idx - last_obs.to_numpy()
    staleness = np.where(np.isnan(staleness), staleness_cap, staleness)
    staleness = np.minimum(staleness, staleness_cap).astype(np.int32)
    return filled, mask, pd.Series(staleness, index=values.index)


def quality_score(mask: pd.Series, staleness: pd.Series, staleness_cap: int = 60) -> float:
    """Window-level instrument quality per 03_DATASET_PIPELINE_V4.md §5."""
    availability_fraction = float(pd.Series(mask).mean())
    return availability_fraction * (1.0 - float(pd.Series(staleness).mean()) / staleness_cap)
