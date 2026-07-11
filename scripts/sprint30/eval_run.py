"""
scripts/sprint30/eval_run.py

Sprint 30 — evaluate one checkpoint through the FROZEN Sprint 24 UnifiedEvaluator
(imported, not reimplemented). Derived from scripts/sprint26/eval_run.py with
the Sprint 30 minimum changes:
  * --features-file / --val-parquet / --test-parquet parameters (V4 datasets),
  * PatchTST width read from the checkpoint's n_features (default 14),
  * calibrated validation/test probability arrays SAVED to the run directory
    (Phase 5 needs them for per-seed paired F1-vs-F0 bootstrap comparisons),
  * NO metric is printed to stdout — the Sprint 30 integrity rule forbids
    inspecting test-set performance before the formal Phase 5 analysis, so this
    runner writes eval.json + arrays silently and prints only completion status.

All model selection (calibration fit, threshold sweep) uses VALIDATION ONLY;
the test set is touched exactly once, for final scoring. Operating points:
policy (deployed clean thresholds 0.14/0.95 on calibrated probabilities) and
valswept (validation-only swept single threshold).
"""
import argparse, json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import numpy as np
import torch
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import brier_score_loss

from app.services.ml.model import PatchTST
from app.services.ml.dataset import SolarFlareWindowDataset, make_eval_loader
from app.services.ml.metrics import find_best_threshold, compute_ece
from scripts.sprint26.eval_framework_ref import get_evaluator, persistence_alerts, climatology_prob

YELLOW, RED = 0.14, 0.95


def infer(model, parquet, feature_cols, device, run_tag):
    ds = SolarFlareWindowDataset(parquet, feature_cols=feature_cols, split_name=run_tag)
    loader = make_eval_loader(ds, batch_size=512, num_workers=1, shuffle=False)
    probs = []
    model.eval()
    with torch.no_grad():
        for X, _ in loader:
            probs.append(torch.sigmoid(model(X.to(device))).squeeze(-1).cpu().numpy())
    return np.concatenate(probs).astype(np.float64), ds.get_labels().astype(np.int8)


def full_metrics(ev, name, probs, alerts, labels, alerts_red=None, auc_ci=True):
    r = ev.evaluate(name, probs, alerts, alerts_red=alerts_red, auc_ci=auc_ci)
    r["window"]["ECE"] = float(compute_ece(probs, labels)[0])
    r["window"]["Brier"] = float(brier_score_loss(labels, np.clip(probs, 0, 1)))
    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_id")
    ap.add_argument("--features-file", default=os.path.join("artifacts", "feature_columns.json"))
    ap.add_argument("--val-parquet", default="artifacts/research/validation.parquet")
    ap.add_argument("--test-parquet", default="artifacts/research/test.parquet")
    ap.add_argument("--checkpoint", default=None,
                    help="default: artifacts/sprint30/runs/<run_id>/best.pt")
    args = ap.parse_args()
    t0 = time.time()

    feature_cols = json.load(open(args.features_file))
    rundir = os.path.join("artifacts", "sprint30", "runs", args.run_id)
    os.makedirs(rundir, exist_ok=True)
    ckpath = args.checkpoint or os.path.join(rundir, "best.pt")
    ck = torch.load(ckpath, map_location="cpu", weights_only=True)
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    model = PatchTST(n_features=ck.get("n_features", 14))
    model.load_state_dict(ck["model"]); model.to(device)

    # validation-only selection (isotonic calibration per the frozen protocol)
    val_probs, val_labels = infer(model, args.val_parquet, feature_cols, device, args.run_id + "_val")
    ir = IsotonicRegression(out_of_bounds="clip"); ir.fit(val_probs, val_labels)
    val_cal = np.asarray(ir.predict(val_probs), dtype=np.float64)
    swept_thr, swept_val_tss = find_best_threshold(val_labels, val_cal, metric="tss")
    val_ece = float(compute_ece(val_cal, val_labels)[0])
    val_brier = float(brier_score_loss(val_labels, np.clip(val_cal, 0, 1)))

    # test scoring (touched once; results written, not printed)
    test_probs, test_labels = infer(model, args.test_parquet, feature_cols, device, args.run_id + "_test")
    test_cal = np.asarray(ir.predict(test_probs), dtype=np.float64)

    ev = get_evaluator()   # frozen Sprint 24 UnifiedEvaluator on the test timestamps/labels
    assert np.array_equal(ev.labels.astype(np.int8), test_labels), "label alignment mismatch — abort"

    np.save(os.path.join(rundir, "test_cal_probs.npy"), test_cal)
    np.save(os.path.join(rundir, "val_cal_probs.npy"), val_cal)

    out = {"run_id": args.run_id, "calibrator": "isotonic",
           "checkpoint": ckpath, "n_features": int(ck.get("n_features", 14)),
           "best_val_tss_training": ck.get("val_tss"), "checkpoint_epoch": ck.get("epoch"),
           "val_swept_threshold": float(swept_thr), "val_swept_val_tss": float(swept_val_tss),
           "val_calibration": {"ECE": val_ece, "Brier": val_brier},
           "policy_thresholds": {"yellow": YELLOW, "red": RED}}

    out["policy"] = full_metrics(ev, args.run_id + "_policy", test_cal,
                                 (test_cal >= YELLOW).astype(np.int8), test_labels,
                                 alerts_red=(test_cal >= RED).astype(np.int8), auc_ci=True)
    out["valswept"] = full_metrics(ev, args.run_id + "_valswept", test_cal,
                                   (test_cal >= swept_thr).astype(np.int8), test_labels, auc_ci=False)

    pers_alerts = persistence_alerts()
    clim = climatology_prob()
    res_pers = ev.evaluate("persistence", pers_alerts.astype(np.float64), pers_alerts, auc_ci=False)
    res_clim = ev.evaluate("climatology", np.full(len(test_labels), clim),
                           (np.full(len(test_labels), clim) >= YELLOW).astype(np.int8), auc_ci=False)
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
    # Integrity rule: no test metrics on stdout before Phase 5.
    print(f"[{args.run_id}] eval complete (val_swept_val_tss={swept_val_tss:.4f}, "
          f"val_ECE={val_ece:.4f}) -> eval.json sealed ({out['wall_seconds']}s)", flush=True)


if __name__ == "__main__":
    main()
