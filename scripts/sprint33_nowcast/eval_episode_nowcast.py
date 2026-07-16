"""
scripts/sprint33_nowcast/eval_episode_nowcast.py

Layer 3 Component 2 — sealed episode-level nowcast evaluation for one seed.
Implements the frozen contract (artifacts/sprint33_nowcast/00_PREREGISTRATION.md):

  * isotonic calibration fit on VALIDATION ONLY, serialized and hashed BEFORE
    any test data is read;
  * operating threshold = the highest validation threshold achieving >= 0.90
    validation episode recall (fallback: highest threshold at the maximum
    attainable recall if that is >= 0.80; else STOP per frozen stopping rule 1),
    recorded before the test set is opened;
  * the Stage-2 test set is opened exactly once, scored with a single
    UnifiedEvaluator.evaluate() call; no metric is recomputed with other params;
  * metrics computed in the frozen order — detection latency, false episodes per
    month, episode recall, time under alert, operating-point stability — plus the
    window-level ROC-AUC / PR-AUC references, each with a 2,880-window block
    bootstrap CI where available.

The frozen Sprint-24 UnifiedEvaluator is imported and used UNMODIFIED. Episode
construction (60-minute merge) comes from the harness on the nowcast-label array.
Only detection latency and the false-episodes-per-month CI are new code.

Usage: eval_episode_nowcast.py <ckpt_run_id> <out_seed>
       e.g. eval_episode_nowcast.py NC_s42 42
"""
import hashlib, json, os, pickle, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import numpy as np
import pandas as pd
import torch
from sklearn.isotonic import IsotonicRegression

from app.services.ml.model import PatchTST
from app.services.ml.dataset import SolarFlareWindowDataset, make_eval_loader
from scripts.sprint24.eval_framework import UnifiedEvaluator, GAP_MIN, _runs, _merge_runs

SEQ = 360
NDS = "artifacts/research_v4/dataset_adi_nowcast"
FEATS = json.load(open(f"{NDS}/feature_columns_15.json"))
RECALL_TARGET = 0.90     # frozen operating-point selection target
RECALL_FLOOR = 0.80      # frozen stopping-rule-1 floor


def infer(model, parquet, device, tag):
    ds = SolarFlareWindowDataset(parquet, feature_cols=FEATS, split_name=tag)
    loader = make_eval_loader(ds, batch_size=512, num_workers=0, shuffle=False)  # determinism
    probs = []
    model.eval()
    with torch.no_grad():
        for X, _ in loader:
            probs.append(torch.sigmoid(model(X.to(device))).squeeze(-1).cpu().numpy())
    ts = pd.read_parquet(parquet, columns=["timestamp"])["timestamp"].values[SEQ:]
    return np.concatenate(probs).astype(np.float64), ds.get_labels().astype(np.int8), ts


def episode_recall_at(ev, alerts):
    return ev.episode_level(alerts.astype(np.int8))["episode_recall"]


def detection_latency(ev, alerts):
    """New: minutes from each detected rise-phase episode's start to the first
    in-span alert (0 if already alerting at flare start). Median over detected."""
    lat = []
    a = alerts.astype(bool)
    for (s, e) in ev.label_eps:
        span = np.where(a[s:e + 1])[0]
        if len(span):
            j = s + int(span[0])
            lat.append(max(0.0, (ev.ts[j] - ev.ts[s]) / np.timedelta64(1, "m")))
    return (float(np.median(lat)) if lat else None,
            float(np.mean(lat)) if lat else None, len(lat))


def false_eps_ci(ev, alerts):
    """New: 2,880-window block bootstrap CI for false-episodes-per-month, using
    the harness's own pre-registered resample indices (ev.win_idx) and block
    partition (ev.months). No harness modification."""
    al_eps = _merge_runs(_runs(alerts.astype(bool)), ev.ts, GAP_MIN)
    # false alert episode = one overlapping no label episode
    lab_s = ev.ts[ev.label_eps[:, 0]]; lab_e = ev.ts[ev.label_eps[:, 1]]
    per_block = np.zeros(ev.n_blocks, dtype=np.float64)
    for (s, e) in al_eps:
        st, en = ev.ts[s], ev.ts[e]
        overlaps = np.any((lab_s <= en) & (lab_e >= st))
        if not overlaps:
            per_block[int(ev.block_ids[s])] += 1.0
    boot = per_block[ev.win_idx].sum(axis=1) / ev.months     # (N_BOOT,)
    return [float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))]


def main():
    ckpt_run, out_seed = sys.argv[1], sys.argv[2]
    t0 = time.time()
    outdir = os.path.join("artifacts", "sprint33_nowcast", "runs", f"s{out_seed}")
    os.makedirs(outdir, exist_ok=True)
    ck = torch.load(f"artifacts/sprint33/runs/{ckpt_run}/best.pt", map_location="cpu", weights_only=True)
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    model = PatchTST(n_features=15); model.load_state_dict(ck["model"]); model.to(device)

    # ── VALIDATION ONLY: infer, fit calibrator, freeze + hash, select threshold ──
    val_raw, val_lab, val_ts = infer(model, f"{NDS}/validation.parquet", device, f"{ckpt_run}_val")
    iso = IsotonicRegression(out_of_bounds="clip"); iso.fit(val_raw, val_lab)
    cal_bytes = pickle.dumps(iso)
    cal_sha = hashlib.sha256(cal_bytes).hexdigest()
    with open(os.path.join(outdir, "calibrator.pkl"), "wb") as f:
        f.write(cal_bytes)
    val_cal = np.asarray(iso.predict(val_raw), dtype=np.float64)
    np.save(os.path.join(outdir, "val_cal_probs.npy"), val_cal)

    val_ev = UnifiedEvaluator(val_ts, val_lab)
    thresholds = np.round(np.arange(0.01, 0.991, 0.005), 4)
    recalls = np.array([episode_recall_at(val_ev, val_cal >= t) for t in thresholds])
    ok = np.where(recalls >= RECALL_TARGET)[0]
    if len(ok):
        pick = int(ok[-1]); sel_thr = float(thresholds[pick]); sel_recall = float(recalls[pick])
        rule = f"highest threshold with val episode recall >= {RECALL_TARGET}"
    else:
        pick = int(np.argmax(recalls)); sel_thr = float(thresholds[pick]); sel_recall = float(recalls[pick])
        rule = f"fallback: highest threshold at max attainable val recall ({sel_recall:.4f})"
    op = {"selected_threshold": sel_thr, "validation_episode_recall_at_threshold": sel_recall,
          "selection_rule": rule, "calibrator_sha256": cal_sha,
          "max_attainable_val_episode_recall": float(recalls.max()),
          "calibrator_fitted_on": "validation", "threshold_selected_on": "validation"}
    json.dump(op, open(os.path.join(outdir, "operating_point.json"), "w"), indent=1)

    if recalls.max() < RECALL_FLOOR:      # frozen stopping rule 1
        out = {"seed": int(out_seed), "STOP": "stopping_rule_1_recall_floor",
               "max_attainable_val_episode_recall": float(recalls.max()),
               "verdict": "not usable — no validation threshold reaches 0.80 episode recall"}
        json.dump(out, open(os.path.join(outdir, "eval.json"), "w"), indent=1)
        print(f"[s{out_seed}] STOP stopping_rule_1 (max val recall {recalls.max():.4f} < 0.80)", flush=True)
        return

    # ── TEST OPENED EXACTLY ONCE ────────────────────────────────────────────────
    test_raw, test_lab, test_ts = infer(model, f"{NDS}/test.parquet", device, f"{ckpt_run}_test")
    test_cal = np.asarray(iso.predict(test_raw), dtype=np.float64)
    np.save(os.path.join(outdir, "test_cal_probs.npy"), test_cal)
    ev = UnifiedEvaluator(test_ts, test_lab)
    alerts = (test_cal >= sel_thr).astype(np.int8)
    res = ev.evaluate("nowcast", test_cal, alerts, auc_ci=True)     # single sealed call

    # metrics in the frozen order
    lat_med, lat_mean, n_det = detection_latency(ev, alerts)
    fe_pm = res["episode"]["false_episodes_per_month"]
    fe_ci = false_eps_ci(ev, alerts)
    ep_recall = res["episode"]["episode_recall"]; ep_recall_ci = res["episode"]["ci"]["episode_recall"]
    time_under_alert = res["alert_stats"]["yellow_fraction_of_time"]
    op_stability = abs(sel_recall - ep_recall)

    def strip(o):
        if isinstance(o, dict): return {k: strip(v) for k, v in o.items() if not k.startswith("_")}
        if isinstance(o, list): return [strip(v) for v in o]
        if isinstance(o, (np.floating, np.integer)): return o.item()
        return o

    out = {"seed": int(out_seed), "checkpoint": f"artifacts/sprint33/runs/{ckpt_run}/best.pt",
           "calibrator_sha256": cal_sha, "operating_threshold": sel_thr,
           "validation_episode_recall": sel_recall, "test_opened_once": True,
           "primary_metrics": {
               "detection_latency_min_median": lat_med, "detection_latency_min_mean": lat_mean,
               "n_detected_episodes": n_det,
               "false_episodes_per_month": fe_pm, "false_episodes_per_month_ci95": fe_ci,
               "episode_recall": ep_recall, "episode_recall_ci95": ep_recall_ci,
               "time_under_alert_fraction": time_under_alert,
               "operating_point_stability_abs_recall_diff": op_stability},
           "reference_metrics": {
               "window_roc_auc": res["window"]["ROC_AUC"], "window_pr_auc": res["window"]["PR_AUC"],
               "n_label_episodes": res["episode"]["n_label_episodes"],
               "n_alert_episodes": res["episode"]["n_alert_episodes"],
               "months": ev.months},
           "seed_passes_primary": bool(fe_pm <= 5.0 and ep_recall >= 0.80),
           "full_harness_episode": strip(res["episode"]), "full_harness_window": strip(res["window"]),
           "wall_seconds": round(time.time() - t0, 1)}
    json.dump(out, open(os.path.join(outdir, "eval.json"), "w"), indent=1)
    print(f"[s{out_seed}] sealed nowcast eval complete -> {outdir}/eval.json ({out['wall_seconds']}s)", flush=True)


if __name__ == "__main__":
    main()
