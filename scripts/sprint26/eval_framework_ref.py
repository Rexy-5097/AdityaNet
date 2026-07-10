"""
scripts/sprint26/eval_framework_ref.py

Shared fixtures for Sprint 26 evaluation: the frozen Sprint 24 UnifiedEvaluator
built on the test split, and the FIXED persistence and climatology baselines
(identical to Sprint 24). Every checkpoint is scored against these same objects.
"""
import numpy as np
import pandas as pd
from scripts.sprint24.eval_framework import UnifiedEvaluator

SEQ = 360
_TEST = "artifacts/research/test.parquet"
_VAL = "artifacts/research/validation.parquet"


def _test_frame():
    return pd.read_parquet(_TEST, columns=["timestamp", "target_6hr_binary"])


def get_evaluator():
    tdf = _test_frame()
    target = tdf["target_6hr_binary"].values.astype(np.int8)
    ts = tdf["timestamp"].values[SEQ:]
    labels = target[SEQ:]
    return UnifiedEvaluator(ts, labels)


def persistence_alerts():
    """Causal persistence (Method A of Sprint 24): trailing-window flare indicator
    = target at row i (fully observable at decision time)."""
    tdf = _test_frame()
    target = tdf["target_6hr_binary"].values.astype(np.int8)
    n = len(tdf) - SEQ
    return target[:n].astype(np.int8)


def climatology_prob():
    """Validation-era positive window rate (Method B of Sprint 24)."""
    vdf = pd.read_parquet(_VAL, columns=["target_6hr_binary"])
    return float(vdf["target_6hr_binary"].values[SEQ:].mean())
