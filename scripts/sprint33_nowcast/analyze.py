"""
scripts/sprint33_nowcast/analyze.py

Layer 3 Component 3 — aggregate seeds, build the recall-vs-false-episodes
trade-off curve, apply the frozen decision rule (incl. escalation), classify
signal- vs policy-limited, run the sensitivity labels.

Inputs are FROZEN Component 2 outputs only:
  * per-seed eval.json (metrics at the frozen operating point)
  * per-seed test_cal_probs.npy (sealed test predictions — NOT re-inferred)
plus the deterministic ground-truth labels/timestamps from the fingerprinted
dataset_adi_nowcast and flares_full catalog. No model is re-run; no prediction
is recomputed; the frozen operating point is unchanged. The frozen Sprint-24
UnifiedEvaluator is imported unmodified.

Frozen decision rule: a seed passes iff test false-episodes-per-month <= 5.0 and
test episode recall >= 0.80; primary CONFIRMED iff >= majority of seeds pass;
escalate to 5 seeds iff across-seed FE/month range > 1.0.
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import numpy as np
import pandas as pd
from scripts.sprint24.eval_framework import UnifiedEvaluator, _runs, _merge_runs, GAP_MIN

SEQ = 360
NDS = "artifacts/research_v4/dataset_adi_nowcast"
RUNS = "artifacts/sprint33_nowcast/runs"
FE_BUDGET = 5.0          # frozen primary threshold
RECALL_FLOOR = 0.80      # frozen gating floor
ESCALATION_RANGE = 1.0   # frozen escalation trigger


def seeds_present():
    return [s for s in (42, 43, 44, 45, 46) if os.path.exists(f"{RUNS}/s{s}/eval.json")]


def test_ground_truth(label_kind="rise"):
    """Deterministic ground-truth test labels + timestamps from frozen sources.
    rise = [start,peak] (frozen primary); whole = [start,end]; onset = [start,start]."""
    tdf = pd.read_parquet(f"{NDS}/test.parquet", columns=["timestamp"])
    ts = tdf["timestamp"].values[SEQ:]
    if label_kind == "rise":
        lab = pd.read_parquet(f"{NDS}/test.parquet", columns=["target_6hr_binary"])["target_6hr_binary"].values[SEQ:].astype(np.int8)
        return ts, lab
    fl = pd.read_parquet("artifacts/research/flares_full.parquet")
    fl["start_time"] = pd.to_datetime(fl["start_time"]); fl["peak_time"] = pd.to_datetime(fl["peak_time"]); fl["end_time"] = pd.to_datetime(fl["end_time"])
    mx = fl[fl["flare_class"].astype(str).str[0].isin(["M", "X"])].dropna(subset=["start_time"])
    starts = mx["start_time"].values.astype("datetime64[ns]")
    ends = (mx["peak_time"] if label_kind == "onset" else mx["end_time"]).values.astype("datetime64[ns]")
    if label_kind == "onset":
        ends = starts  # onset-only: the start minute
    tsn = ts.astype("datetime64[ns]")
    idx = np.searchsorted(starts, tsn, side="right") - 1
    lab = np.zeros(len(tsn), dtype=np.int8); v = idx >= 0
    lab[v] = (tsn[v] <= ends[idx[v]]).astype(np.int8)
    return ts, lab


def curve_for_seed(ev, cal_probs, thresholds):
    pts = []
    for t in thresholds:
        r = ev.episode_level((cal_probs >= t).astype(np.int8))
        pts.append((float(t), float(r["episode_recall"]), float(r["false_episodes_per_month"])))
    return pts


def main():
    seeds = seeds_present()
    evals = {s: json.load(open(f"{RUNS}/s{s}/eval.json")) for s in seeds}

    # ── aggregation + first-principles verification ─────────────────────────
    fe = {s: evals[s]["primary_metrics"]["false_episodes_per_month"] for s in seeds}
    rec = {s: evals[s]["primary_metrics"]["episode_recall"] for s in seeds}
    fe_vals = np.array([fe[s] for s in seeds]); rec_vals = np.array([rec[s] for s in seeds])
    agg = {"seeds": seeds,
           "fe_per_month_per_seed": {str(s): fe[s] for s in seeds},
           "episode_recall_per_seed": {str(s): rec[s] for s in seeds},
           "fe_mean": float(fe_vals.mean()), "fe_std": float(fe_vals.std(ddof=1)),
           "fe_range": float(fe_vals.max() - fe_vals.min()),
           "recall_mean": float(rec_vals.mean()), "recall_std": float(rec_vals.std(ddof=1))}
    # first-principles recompute
    fp_mean = sum(fe[s] for s in seeds) / len(seeds)
    agg["fe_mean_first_principles"] = fp_mean
    agg["aggregation_verified"] = abs(fp_mean - agg["fe_mean"]) < 1e-12

    # ── decision rule + escalation ──────────────────────────────────────────
    passes = {s: bool(fe[s] <= FE_BUDGET and rec[s] >= RECALL_FLOOR) for s in seeds}
    n_pass = sum(passes.values()); majority = len(seeds) // 2 + 1
    escalate = bool(agg["fe_range"] > ESCALATION_RANGE and len(seeds) < 5)
    decision = {"passes_per_seed": {str(s): passes[s] for s in seeds}, "n_pass": n_pass,
                "majority_required": majority, "n_seeds": len(seeds),
                "escalation_triggered": escalate, "escalation_range_threshold": ESCALATION_RANGE,
                "observed_fe_range": agg["fe_range"],
                "primary_verdict": ("PENDING ESCALATION (train seeds 45,46)" if escalate
                                    else ("CONFIRMED" if n_pass >= majority else "REJECTED"))}

    # ── trade-off curve (frozen test predictions + ground-truth labels) ─────
    ts, lab = test_ground_truth("rise")
    ev = UnifiedEvaluator(ts, lab)
    thresholds = np.round(np.arange(0.005, 0.30, 0.005), 4)
    curves = {}
    for s in seeds:
        cal = np.load(f"{RUNS}/s{s}/test_cal_probs.npy")
        curves[str(s)] = curve_for_seed(ev, cal, thresholds)
    # aggregate: at each threshold, mean recall and mean FE/month
    agg_curve = []
    for i, t in enumerate(thresholds):
        recs = [curves[str(s)][i][1] for s in seeds]; fes = [curves[str(s)][i][2] for s in seeds]
        agg_curve.append({"threshold": float(t), "mean_recall": float(np.mean(recs)),
                          "mean_fe_per_month": float(np.mean(fes))})

    # ── signal- vs policy-limited ───────────────────────────────────────────
    # does ANY operating point satisfy the deployment criterion (recall>=0.80 AND FE<=5.0)?
    feasible = [c for c in agg_curve if c["mean_recall"] >= RECALL_FLOOR and c["mean_fe_per_month"] <= FE_BUDGET]
    if feasible:
        classification = "POLICY-LIMITED"
        best = min(feasible, key=lambda c: c["mean_fe_per_month"])
        detail = {"classification": classification,
                  "feasible_point": best,
                  "note": "a point with recall>=0.80 and FE/month<=5.0 exists; the 0.90-recall requirement is the binding constraint"}
    else:
        classification = "SIGNAL-LIMITED"
        # at the recall floor, the minimum achievable FE/month
        at_floor = [c for c in agg_curve if c["mean_recall"] >= RECALL_FLOOR]
        min_fe_at_floor = min((c["mean_fe_per_month"] for c in at_floor), default=None)
        # highest recall attainable at FE<=5.0
        at_budget = [c for c in agg_curve if c["mean_fe_per_month"] <= FE_BUDGET]
        max_recall_at_budget = max((c["mean_recall"] for c in at_budget), default=0.0)
        detail = {"classification": classification,
                  "min_fe_per_month_at_recall_floor": min_fe_at_floor,
                  "max_recall_at_fe_budget": max_recall_at_budget,
                  "note": "no operating point reaches recall>=0.80 AND FE/month<=5.0 — the curve does not intersect the deployment region"}

    # ── sensitivity labels (frozen predictions; alternative ground truth) ───
    sensitivity = {}
    for kind in ("whole", "onset"):
        ts2, lab2 = test_ground_truth(kind)
        ev2 = UnifiedEvaluator(ts2, lab2)
        rows = {}
        for s in seeds:
            cal = np.load(f"{RUNS}/s{s}/test_cal_probs.npy")
            thr = evals[s]["operating_threshold"]
            r = ev2.episode_level((cal >= thr).astype(np.int8))
            rows[str(s)] = {"episode_recall": round(r["episode_recall"], 4),
                            "fe_per_month": round(r["false_episodes_per_month"], 2),
                            "passes": bool(r["false_episodes_per_month"] <= FE_BUDGET and r["episode_recall"] >= RECALL_FLOOR)}
        sensitivity[kind] = rows

    out = {"aggregation": agg, "decision": decision, "trade_off_curve": agg_curve,
           "per_seed_curves": curves, "signal_vs_policy": detail, "sensitivity_labels": sensitivity,
           "inputs": "frozen Component 2 test_cal_probs.npy + eval.json; ground-truth labels from fingerprinted dataset/catalog; no model re-inference"}
    json.dump(out, open("artifacts/sprint33_nowcast/analysis.json", "w"), indent=1)
    print(json.dumps({"aggregation_verified": agg["aggregation_verified"], "fe_mean": round(agg["fe_mean"], 2),
                      "fe_range": round(agg["fe_range"], 2), "n_pass": n_pass, "escalate": escalate,
                      "primary_verdict": decision["primary_verdict"], "classification": classification,
                      "signal_policy_detail": detail}, indent=1))


if __name__ == "__main__":
    main()
