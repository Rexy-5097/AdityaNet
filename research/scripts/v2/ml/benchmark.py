"""
scripts/v2/ml/benchmark.py — Milestone XI baseline benchmark.

Reads the FROZEN dataset read-only. Builds the recommended T1 feature set,
defines M/X nowcast + 30-min prediction targets, runs all 8 mandatory baselines,
and reports minute-level AND event-level metrics with day-block-bootstrap CIs.

Protocol (frozen before any model, justified by measurement):
  * Split: CHRONOLOGICAL. Autocorrelation of rate_total is 0.80 at 60 min and
    0.64 at 8 h, so random/k-fold splits leak. Train 2024-02..2025-12,
    Val = last 20% of train by time, Test = 2026-01-01 onward.
  * Threshold + all model selection: TRAIN/VAL only. Test opened once.
  * Effective N: 581 M/X events, not 564,160 minutes -> event-level metrics +
    day-block bootstrap (resample whole days) for all CIs.
  * No imputation: minutes with non-finite rate are dropped (masked), never filled.
"""
import glob, json, os, sys, time, warnings
from datetime import datetime, timezone

sys.path.insert(0, "/Volumes/T7 Shield/Projects/AI/AdityaNet")
os.chdir("/Volumes/T7 Shield/Projects/AI/AdityaNet")
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (roc_auc_score, average_precision_score, brier_score_loss,
                             precision_score, recall_score, f1_score,
                             balanced_accuracy_score, matthews_corrcoef, confusion_matrix)
import lightgbm as lgb

CANON = "artifacts/v2/phase05/canonical"
OUT = "artifacts/v2/ml"
SEED = 20260718
TEST_START = pd.Timestamp("2026-01-01", tz="UTC")
VAL_FRACTION = 0.20            # last 20% of pre-test period, by time

FEATURES = ["log_rate", "roll_mean_5", "roll_mean_15", "roll_mean_30", "roll_mean_60",
            "roll_max_15", "roll_std_15", "roll_std_60", "bg_excess",
            "rise_5", "rise_15", "gti_fraction", "n_seconds_present", "q_partial"]


# ── data + features (per day, no cross-day leakage) ─────────────────────────
def load_t1():
    df = pd.concat([pd.read_parquet(f) for f in sorted(glob.glob(f"{CANON}/T1/*.parquet"))],
                   ignore_index=True)
    df = df.sort_values("timestamp").reset_index(drop=True)
    df["date"] = df.timestamp.dt.date
    return df


def build_features(df):
    df = df.copy()
    df["log_rate"] = np.log1p(df.rate_total)
    g = df.groupby("date", group_keys=False)
    for w in (5, 15, 30, 60):
        df[f"roll_mean_{w}"] = g.log_rate.transform(lambda s: s.rolling(w, min_periods=1).mean())
    df["roll_max_15"] = g.log_rate.transform(lambda s: s.rolling(15, min_periods=1).max())
    df["roll_std_15"] = g.log_rate.transform(lambda s: s.rolling(15, min_periods=1).std()).fillna(0)
    df["roll_std_60"] = g.log_rate.transform(lambda s: s.rolling(60, min_periods=1).std()).fillna(0)
    # background-relative excess: log_rate minus a trailing 6h 10th-percentile
    df["bg_excess"] = df.log_rate - g.log_rate.transform(
        lambda s: s.rolling(360, min_periods=30).quantile(0.10)).bfill()
    df["rise_5"] = g.log_rate.transform(lambda s: s.diff(5)).fillna(0)
    df["rise_15"] = g.log_rate.transform(lambda s: s.diff(15)).fillna(0)
    df["q_partial"] = df.q_partial.astype(float)
    return df


def add_labels(df):
    fl = pd.read_parquet("artifacts/research/flares_full.parquet")
    for c in ("start_time", "peak_time", "end_time"):
        fl[c] = pd.to_datetime(fl[c])
    fl = fl.dropna(subset=["start_time"])
    fl["cls"] = fl.flare_class.astype(str).str[0].str.upper()
    fl["end_eff"] = fl.end_time.fillna(fl.peak_time).fillna(fl.start_time)
    mx = fl[fl.cls.isin(["M", "X"])].copy()
    ts = df.timestamp.dt.tz_localize(None).to_numpy()

    # nowcast: an M/X flare is in progress at t
    s = np.sort(mx.start_time.to_numpy())
    order = np.argsort(mx.start_time.to_numpy())
    en = mx.end_eff.to_numpy()[order]
    i = np.searchsorted(s, ts, side="right") - 1
    y_now = np.zeros(len(ts), bool); v = i >= 0
    y_now[v] = ts[v] <= np.maximum.accumulate(en)[i[v]]

    # prediction: an M/X flare STARTS within (t, t+30min]
    ev = np.sort(mx.start_time.to_numpy())
    idx = np.searchsorted(ev, ts, side="right")
    nxt = np.where(idx < len(ev), ev[np.minimum(idx, len(ev) - 1)], np.datetime64("2100-01-01"))
    y_pred = ((nxt - ts) / np.timedelta64(1, "m")) <= 30

    df["y_nowcast"] = y_now
    df["y_predict30"] = y_pred
    return df


# ── event grouping ──────────────────────────────────────────────────────────
def make_events(y, ts_date):
    """Contiguous positive runs = events. Returns per-minute event id (-1 if neg)."""
    ev = np.full(len(y), -1, dtype=np.int64)
    cur, in_ev = -1, False
    for i in range(len(y)):
        if y[i]:
            if not in_ev:
                cur += 1; in_ev = True
            ev[i] = cur
        else:
            in_ev = False
    return ev


# ── metrics ─────────────────────────────────────────────────────────────────
def minute_metrics(y, p, thr):
    yhat = p >= thr
    tn, fp, fn, tp = confusion_matrix(y, yhat, labels=[0, 1]).ravel()
    out = {"roc_auc": roc_auc_score(y, p) if len(set(y)) > 1 else float("nan"),
           "pr_auc": average_precision_score(y, p) if y.sum() else float("nan"),
           "precision": precision_score(y, yhat, zero_division=0),
           "recall": recall_score(y, yhat, zero_division=0),
           "f1": f1_score(y, yhat, zero_division=0),
           "balanced_acc": balanced_accuracy_score(y, yhat),
           "mcc": matthews_corrcoef(y, yhat) if len(set(yhat)) > 1 else 0.0,
           "brier": brier_score_loss(y, np.clip(p, 0, 1)) if p.max() <= 1.0 else float("nan"),
           "false_alarm_rate": fp / (fp + tn) if (fp + tn) else float("nan"),
           "miss_rate": fn / (fn + tp) if (fn + tp) else float("nan"),
           "confusion": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)}}
    return out


def event_metrics(y, p, thr, ev_ids):
    """Event recall = fraction of events with >=1 predicted-positive minute.
    False events = predicted-positive runs not overlapping any true event."""
    yhat = p >= thr
    ev_true = set(ev_ids[ev_ids >= 0])
    detected = set(ev_ids[(ev_ids >= 0) & yhat])
    ev_recall = len(detected) / len(ev_true) if ev_true else float("nan")
    # false-positive minute runs not overlapping a true event
    pred = yhat.astype(int); runs = 0; falserun = 0; in_run = False; run_hit = False
    for i in range(len(pred)):
        if pred[i]:
            if not in_run:
                in_run = True; run_hit = False; runs += 1
            if ev_ids[i] >= 0:
                run_hit = True
        else:
            if in_run and not run_hit:
                falserun += 1
            in_run = False
    if in_run and not run_hit:
        falserun += 1
    return {"n_events": len(ev_true), "events_detected": len(detected),
            "event_recall": ev_recall, "n_pred_runs": runs, "false_event_runs": falserun}


def day_block_bootstrap(df_test, p, thr, ev_ids, n=1000, seed=SEED):
    """Resample whole DAYS with replacement -> CI on event recall + minute ROC-AUC.
    Days are the block because autocorrelation exceeds 8 h."""
    rng = np.random.default_rng(seed)
    days = df_test.date.to_numpy()
    uday = np.unique(days)
    idx_by_day = {d: np.where(days == d)[0] for d in uday}
    y = df_test.y.to_numpy()
    rec, auc = [], []
    for _ in range(n):
        pick = rng.choice(uday, size=len(uday), replace=True)
        ix = np.concatenate([idx_by_day[d] for d in pick])
        yb, pb, eb = y[ix], p[ix], ev_ids[ix]
        if len(set(yb)) > 1:
            auc.append(roc_auc_score(yb, pb))
        et = set(eb[eb >= 0]); det = set(eb[(eb >= 0) & (pb >= thr)])
        if et:
            rec.append(len(det) / len(et))
    ci = lambda a: [float(np.percentile(a, 2.5)), float(np.percentile(a, 97.5))] if a else [float("nan")]*2
    return {"event_recall_ci95": ci(rec), "roc_auc_ci95": ci(auc)}


# ── models ──────────────────────────────────────────────────────────────────
def fit_models(Xtr, ytr, Xva, yva):
    models = {}
    models["logistic"] = LogisticRegression(max_iter=2000, class_weight="balanced").fit(Xtr, ytr)
    models["random_forest"] = RandomForestClassifier(
        n_estimators=200, max_depth=8, min_samples_leaf=50, class_weight="balanced",
        random_state=SEED, n_jobs=-1).fit(Xtr, ytr)
    models["lightgbm"] = lgb.LGBMClassifier(
        n_estimators=300, num_leaves=31, learning_rate=0.05, min_child_samples=100,
        class_weight="balanced", random_state=SEED, verbose=-1).fit(Xtr, ytr)
    return models


def run_task(df, target, tag):
    print(f"\n{'='*60}\nTASK: {tag} (target={target})\n{'='*60}", flush=True)
    d = df[df.rate_total.notna()].copy()           # mask: drop unobserved minutes
    d["y"] = d[target].astype(int)
    tr = d[d.timestamp < TEST_START].copy()
    te = d[d.timestamp >= TEST_START].copy()
    # validation = last VAL_FRACTION of train by time
    cut = tr.timestamp.quantile(1 - VAL_FRACTION)
    va = tr[tr.timestamp >= cut].copy(); trf = tr[tr.timestamp < cut].copy()
    print(f"  train {len(trf):,} | val {len(va):,} | test {len(te):,} minutes | "
          f"test positives {int(te.y.sum()):,} ({100*te.y.mean():.2f}%)", flush=True)

    ev_te = make_events(te.y.to_numpy(), te.date.to_numpy())
    Xtr, ytr = trf[FEATURES].to_numpy(), trf.y.to_numpy()
    Xva, yva = va[FEATURES].to_numpy(), va.y.to_numpy()
    Xte, yte = te[FEATURES].to_numpy(), te.y.to_numpy()

    results = {}

    # ── baselines 1-5 (probability-like scores) ──────────────────────────────
    rng = np.random.default_rng(SEED)
    base_rate_tr = ytr.mean()
    scores = {
        "random": rng.random(len(yte)),
        "majority": np.full(len(yte), 0.0),            # predicts negative (majority)
        "climatology": np.full(len(yte), base_rate_tr),  # constant train base rate
        "persistence": te.groupby("date").y.shift(1).fillna(0).to_numpy().astype(float),
    }
    # threshold detector on rate_total, threshold chosen on TRAIN by F1
    rt_tr = np.log1p(trf.rate_total.to_numpy())
    grid = np.quantile(rt_tr, np.linspace(0.5, 0.999, 200))
    f1s = [f1_score(ytr, rt_tr >= t, zero_division=0) for t in grid]
    thr_rate = grid[int(np.argmax(f1s))]
    scores["threshold_rate"] = np.log1p(te.rate_total.to_numpy())

    for name, sc in scores.items():
        thr = thr_rate if name == "threshold_rate" else 0.5
        mm = minute_metrics(yte, sc, thr)
        em = event_metrics(yte, sc, thr, ev_te)
        bb = day_block_bootstrap(te.assign(y=yte), sc, thr, ev_te)
        results[name] = {"minute": mm, "event": em, "bootstrap": bb, "threshold": float(thr)}
        print(f"  {name:16s} AUC={mm['roc_auc']:.4f} ev_recall={em['event_recall']:.3f} "
              f"false_runs={em['false_event_runs']}", flush=True)

    # ── models 6-8 ───────────────────────────────────────────────────────────
    models = fit_models(Xtr, ytr, Xva, yva)
    for name, m in models.items():
        t0 = time.time()
        p = m.predict_proba(Xte)[:, 1]
        latency_us = 1e6 * (time.time() - t0) / len(Xte)
        # operating threshold: maximize F1 on VALIDATION
        pv = m.predict_proba(Xva)[:, 1]
        vg = np.quantile(pv, np.linspace(0.5, 0.999, 200))
        thr = vg[int(np.argmax([f1_score(yva, pv >= t, zero_division=0) for t in vg]))]
        mm = minute_metrics(yte, p, thr)
        em = event_metrics(yte, p, thr, ev_te)
        bb = day_block_bootstrap(te.assign(y=yte), p, thr, ev_te)
        results[name] = {"minute": mm, "event": em, "bootstrap": bb,
                         "threshold": float(thr), "latency_us_per_sample": latency_us}
        print(f"  {name:16s} AUC={mm['roc_auc']:.4f} ev_recall={em['event_recall']:.3f} "
              f"false_runs={em['false_event_runs']} lat={latency_us:.1f}us", flush=True)

    # feature importance / coefficients for interpretability
    imp = {}
    imp["logistic_coef"] = dict(zip(FEATURES, models["logistic"].coef_[0].tolist()))
    imp["random_forest_importance"] = dict(zip(FEATURES, models["random_forest"].feature_importances_.tolist()))
    imp["lightgbm_importance"] = dict(zip(FEATURES, (models["lightgbm"].feature_importances_ /
                                                     max(models["lightgbm"].feature_importances_.sum(), 1)).tolist()))
    # store the raw predictions for later paired significance testing
    preds = {"y_test": yte.tolist(),
             "test_dates": [str(x) for x in te.date.to_numpy()],
             "lightgbm": models["lightgbm"].predict_proba(Xte)[:, 1].tolist(),
             "threshold_rate": np.log1p(te.rate_total.to_numpy()).tolist(),
             "thr_rate": float(thr_rate)}
    return {"n_train": len(trf), "n_val": len(va), "n_test": len(te),
            "test_positive_rate": float(yte.mean()),
            "results": results, "interpretability": imp,
            "threshold_rate_logspace": float(thr_rate)}, preds


def main():
    os.makedirs(OUT, exist_ok=True)
    df = add_labels(build_features(load_t1()))
    out, allpreds = {}, {}
    for target, tag in (("y_nowcast", "M/X NOWCAST"), ("y_predict30", "M/X 30-MIN PREDICTION")):
        out[tag], allpreds[tag] = run_task(df, target, tag)
    out["meta"] = {"generated_utc": datetime.now(timezone.utc).isoformat(),
                   "features": FEATURES, "seed": SEED,
                   "test_start": str(TEST_START), "val_fraction": VAL_FRACTION,
                   "effective_n_note": "581 M/X events; day-block bootstrap CIs"}
    json.dump(out, open(f"{OUT}/benchmark_results.json", "w"), indent=1)
    json.dump(allpreds, open(f"{OUT}/benchmark_predictions.json", "w"))
    print("\nwritten: benchmark_results.json + benchmark_predictions.json")


if __name__ == "__main__":
    main()
