"""
tests/test_eval_framework.py

Sprint 24 — unit tests for the unified evaluation framework on synthetic data
with hand-computable ground truth.
"""

import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.sprint24.eval_framework import (
    UnifiedEvaluator, _runs, _merge_runs, _confusion, _metrics_from_confusion,
)


def _ts(n, start="2023-01-01"):
    return np.datetime64(start) + np.arange(n) * np.timedelta64(1, "m")


def test_runs_basic():
    m = np.array([0, 1, 1, 0, 0, 1, 0, 1, 1, 1], dtype=bool)
    r = _runs(m)
    assert r.tolist() == [[1, 2], [5, 5], [7, 9]]


def test_merge_runs_gap_tolerance():
    ts = _ts(200)
    runs = np.array([[10, 20], [50, 60], [150, 160]])  # gaps 30 min and 90 min
    merged = _merge_runs(runs, ts, gap_min=60)
    assert merged.tolist() == [[10, 60], [150, 160]]


def test_confusion_and_perfect_metrics():
    labels = np.array([1, 1, 0, 0, 1, 0], dtype=np.int8)
    alerts = labels.copy()
    tp, fp, fn, tn = _confusion(labels, alerts)
    assert (tp, fp, fn, tn) == (3, 0, 3 - 3, 3)
    m = _metrics_from_confusion(tp, fp, fn, tn)
    assert m["TSS"] == 1.0 and m["HSS"] == 1.0 and m["MCC"] == 1.0


def test_random_alerts_near_zero_tss():
    rng = np.random.default_rng(0)
    labels = (rng.random(50000) < 0.2).astype(np.int8)
    alerts = (rng.random(50000) < 0.5).astype(np.int8)
    tp, fp, fn, tn = _confusion(labels, alerts)
    assert abs(_metrics_from_confusion(tp, fp, fn, tn)["TSS"]) < 0.02


def test_episode_detection_and_lead_time():
    n = 5000
    labels = np.zeros(n, np.int8)
    labels[1000:1500] = 1          # one label episode; onset = start + 360 min
    alerts = np.zeros(n, np.int8)
    alerts[1100:1200] = 1          # alerting starts 100 min into episode → pre-onset
    ev = UnifiedEvaluator(_ts(n), labels)
    res = ev.evaluate("t", alerts.astype(float), alerts)
    e = res["episode"]
    assert e["n_label_episodes"] == 1
    assert e["episodes_detected"] == 1 and e["episodes_missed"] == 0
    assert e["pre_onset_recall"] == 1.0            # alert at +100 < onset at +360
    assert e["lead_time_min_mean"] == pytest.approx(260.0)  # 360 - 100
    assert e["false_alert_episodes"] == 0


def test_post_onset_alert_has_negative_lead_and_no_preonset():
    n = 5000
    labels = np.zeros(n, np.int8)
    labels[1000:1800] = 1
    alerts = np.zeros(n, np.int8)
    alerts[1500:1600] = 1          # starts 500 min in → after onset (360)
    ev = UnifiedEvaluator(_ts(n), labels)
    e = ev.evaluate("t", alerts.astype(float), alerts)["episode"]
    assert e["episodes_detected"] == 1
    assert e["pre_onset_recall"] == 0.0
    assert e["lead_time_min_mean"] == pytest.approx(-140.0)


def test_false_alert_episode_counted():
    n = 5000
    labels = np.zeros(n, np.int8)
    labels[1000:1200] = 1
    alerts = np.zeros(n, np.int8)
    alerts[1050:1080] = 1          # true alert
    alerts[3000:3050] = 1          # false alert episode
    ev = UnifiedEvaluator(_ts(n), labels)
    e = ev.evaluate("t", alerts.astype(float), alerts)["episode"]
    assert e["n_alert_episodes"] == 2
    assert e["false_alert_episodes"] == 1
    assert e["episode_precision"] == pytest.approx(0.5)


def test_bootstrap_reproducibility_same_seed():
    rng = np.random.default_rng(1)
    n = 60000
    labels = (rng.random(n) < 0.1).astype(np.int8)
    probs = np.clip(labels * 0.6 + rng.random(n) * 0.4, 0, 1)
    ts = _ts(n)
    r1 = UnifiedEvaluator(ts, labels).evaluate("x", probs, probs > 0.5, auc_ci=False)
    r2 = UnifiedEvaluator(ts, labels).evaluate("x", probs, probs > 0.5, auc_ci=False)
    assert r1["window"]["ci"] == r2["window"]["ci"]
    assert r1["episode"]["ci"] == r2["episode"]["ci"]


def test_paired_delta_zero_for_identical_methods():
    rng = np.random.default_rng(2)
    n = 60000
    labels = (rng.random(n) < 0.1).astype(np.int8)
    probs = rng.random(n)
    ev = UnifiedEvaluator(_ts(n), labels)
    a = ev.evaluate("a", probs, probs > 0.5, auc_ci=False)
    b = ev.evaluate("b", probs, probs > 0.5, auc_ci=False)
    pw = ev.paired_window(a, b)
    assert all(v["delta_point"] == 0.0 and not v["significant"] for v in pw.values())


def test_paired_detects_genuine_difference():
    rng = np.random.default_rng(3)
    n = 200000
    labels = (rng.random(n) < 0.15).astype(np.int8)
    good = np.clip(labels * 0.7 + rng.random(n) * 0.3, 0, 1)   # informative
    bad = rng.random(n)                                        # noise
    ev = UnifiedEvaluator(_ts(n), labels)
    a = ev.evaluate("good", good, good > 0.5, auc_ci=False)
    b = ev.evaluate("bad", bad, bad > 0.5, auc_ci=False)
    d = ev.paired_window(a, b)["TSS"]
    assert d["delta_point"] > 0.3 and d["significant"]
