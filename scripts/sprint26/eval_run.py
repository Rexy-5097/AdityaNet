"""
scripts/sprint26/eval_run.py

Sprint 26 Phase 4 — evaluate one trained checkpoint through the FROZEN Sprint 24
UnifiedEvaluator (imported, not reimplemented). All model selection
(calibration fit, decision threshold) is done on VALIDATION ONLY; the test set
is touched exactly once, for final scoring.

For the checkpoint it computes, at window and episode level:
ROC-AUC, PR-AUC, TSS, HSS, MCC, Precision, Recall, F1, ECE, Brier, Episode
Recall, Pre-onset Recall, Lead Time, False Episodes/Month, Alert Duty Cycle,
plus block-bootstrap 95% CIs and paired bootstrap vs V1(frozen policy),
Persistence, and Climatology.

Two operating points per checkpoint:
  * policy: yellow/red from the deployed clean policy thresholds (0.14/0.95)
    applied to the checkpoint's CALIBRATED probabilities
  * valswept: single threshold maximizing TSS on this checkpoint's VALIDATION
    calibrated probabilities (validation-only selection)

Usage: eval_run.py <run_id> [--calib isotonic|platt]
"""
import argparse, json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import numpy as np
import torch
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss

from app.services.ml.model import PatchTST
from app.services.ml.dataset import SolarFlareWindowDataset, make_eval_loader
from app.services.ml.metrics import find_best_threshold, compute_ece
from scripts.sprint26.eval_framework_ref import get_evaluator, persistence_alerts, climatology_prob

FEATURE_COLS = json.load(open("artifacts/feature_columns.json"))
SEQ = 360
YELLOW, RED = 0.14, 0.95


def infer(model, parquet, device, run_tag):
    ds = SolarFlareWindowDataset(parquet, feature_cols=FEATURE_COLS, split_name=run_tag)
    loader = make_eval_loader(ds, batch_size=512, num_workers=1, shuffle=False)
    probs = []
    model.eval()
    with torch.no_grad():
        for X, _ in loader:
            probs.append(torch.sigmoid(model(X.to(device))).squeeze(-1).cpu().numpy())
    return np.concatenate(probs).astype(np.float64), ds.get_labels().astype(np.int8)


def fit_calibrator(val_probs, val_labels, method):
    eps = 1e-7
    if method == "isotonic":
        ir = IsotonicRegression(out_of_bounds="clip"); ir.fit(val_probs, val_labels)
        return lambda p: ir.predict(p)
    else:  # platt
        vlog = np.log(np.clip(val_probs, eps, 1 - eps) / (1 - np.clip(val_probs, eps, 1 - eps))).reshape(-1, 1)
        lr = LogisticRegression(C=1e5, solver="lbfgs"); lr.fit(vlog, val_labels)
        def f(p):
            lg = np.log(np.clip(p, eps, 1 - eps) / (1 - np.clip(p, eps, 1 - eps))).reshape(-1, 1)
            return lr.predict_proba(lg)[:, 1]
        return f


def full_metrics(ev, name, probs, alerts, labels, alerts_red=None, auc_ci=True):
    r = ev.evaluate(name, probs, alerts, alerts_red=alerts_red, auc_ci=auc_ci)
    # add ECE + Brier (window level), computed on the calibrated probs
    r["window"]["ECE"] = float(compute_ece(probs, labels)[0])
    r["window"]["Brier"] = float(brier_score_loss(labels, np.clip(probs, 0, 1)))
    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_id")
    ap.add_argument("--calib", default="isotonic", choices=["isotonic", "platt"])
    args = ap.parse_args()
    t0 = time.time()

    rundir = os.path.join("artifacts", "sprint26", "runs", args.run_id)
    ck = torch.load(os.path.join(rundir, "best.pt"), map_location="cpu", weights_only=True)
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    model = PatchTST(); model.load_state_dict(ck["model"]); model.to(device)

    # validation-only selection
    val_probs, val_labels = infer(model, "artifacts/research/validation.parquet", device, args.run_id + "_val")
    calibrate = fit_calibrator(val_probs, val_labels, args.calib)
    val_cal = np.asarray(calibrate(val_probs), dtype=np.float64)
    swept_thr, swept_val_tss = find_best_threshold(val_labels, val_cal, metric="tss")

    # test scoring (touched once)
    test_probs, test_labels = infer(model, "artifacts/research/test.parquet", device, args.run_id + "_test")
    test_cal = np.asarray(calibrate(test_probs), dtype=np.float64)

    ev = get_evaluator()   # frozen Sprint 24 UnifiedEvaluator on the test timestamps/labels
    assert np.array_equal(ev.labels.astype(np.int8), test_labels), "label alignment mismatch — abort"

    out = {"run_id": args.run_id, "calibrator": args.calib,
           "best_val_tss_training": ck.get("val_tss"), "checkpoint_epoch": ck.get("epoch"),
           "val_swept_threshold": float(swept_thr), "val_swept_val_tss": float(swept_val_tss),
           "policy_thresholds": {"yellow": YELLOW, "red": RED}}

    # operating point 1: deployed policy thresholds on calibrated test probs
    out["policy"] = full_metrics(ev, args.run_id + "_policy", test_cal,
                                 (test_cal >= YELLOW).astype(np.int8), test_labels,
                                 alerts_red=(test_cal >= RED).astype(np.int8), auc_ci=True)
    # operating point 2: validation-swept single threshold on calibrated test probs
    out["valswept"] = full_metrics(ev, args.run_id + "_valswept", test_cal,
                                   (test_cal >= swept_thr).astype(np.int8), test_labels, auc_ci=False)

    # paired vs persistence and climatology (fixed baselines) on identical resamples
    pers_alerts = persistence_alerts()
    clim = climatology_prob()
    res_pers = ev.evaluate("persistence", pers_alerts.astype(np.float64), pers_alerts, auc_ci=False)
    res_clim = ev.evaluate("climatology", np.full(len(test_labels), clim), (np.full(len(test_labels), clim) >= YELLOW).astype(np.int8), auc_ci=False)
    out["paired_policy_vs_persistence"] = {"window": ev.paired_window(out["policy"], res_pers),
                                           "episode": ev.paired_episode(out["policy"], res_pers)}
    out["paired_policy_vs_climatology"] = {"window": ev.paired_window(out["policy"], res_clim),
                                           "episode": ev.paired_episode(out["policy"], res_clim)}

    def strip(o):
        if isinstance(o, dict): return {k: strip(v) for k, v in o.items() if not k.startswith("_")}
        if isinstance(o, list): return [strip(v) for v in o]
        if isinstance(o, (np.floating, np.integer)): return o.item()
        return o
    out = strip(out)
    out["wall_seconds"] = round(time.time() - t0, 1)
    json.dump(out, open(os.path.join(rundir, "eval.json"), "w"), indent=1)
    p = out["policy"]["window"]; pe = out["policy"]["episode"]
    dp = out["paired_policy_vs_persistence"]["window"]["TSS"]
    print(f"[{args.run_id}] policy TSS={p['TSS']:.4f} ROC={p['ROC_AUC']:.4f} ECE={p['ECE']:.4f} "
          f"ep_recall={pe['episode_recall']:.4f} preonset={pe['pre_onset_recall']:.4f} "
          f"dutycycle={out['policy']['alert_stats']['yellow_fraction_of_time']:.4f} "
          f"dTSS_vs_pers={dp['delta_point']:+.4f} CI={[round(x,4) for x in dp['delta_ci95']]} sig={dp['significant']} "
          f"({out['wall_seconds']}s)", flush=True)


if __name__ == "__main__":
    main()
