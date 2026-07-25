"""
scripts/sprint32/eval_s2_f3.py

Sprint 32 — sealed S2-span evaluation for the F3 late-fusion model. Identical
to scripts/sprint31/eval_s2.py in every respect (frozen Sprint 24 harness on
the S2 span, isotonic calibration on the arm's own validation split, policy
thresholds 0.14/0.95, S2 floors recomputed, NO test metric printed) except it
constructs LateFusionPatchTST instead of PatchTST. The 36-channel feature file
is required so the model's internal GOES/Aditya split matches the dataset.
"""
import argparse, json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import numpy as np
import pandas as pd
import torch
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import brier_score_loss

from app.services.ml.model_f3 import LateFusionPatchTST
from app.services.ml.dataset import SolarFlareWindowDataset, make_eval_loader
from app.services.ml.metrics import find_best_threshold, compute_ece
from scripts.sprint24.eval_framework import UnifiedEvaluator

SEQ = 360
YELLOW, RED = 0.14, 0.95
S2_TEST = "artifacts/sprint14c/s2_test.parquet"
S2_VAL = "artifacts/sprint14c/s2_val.parquet"


def infer(model, parquet, feature_cols, device, tag):
    ds = SolarFlareWindowDataset(parquet, feature_cols=feature_cols, split_name=tag)
    loader = make_eval_loader(ds, batch_size=512, num_workers=1, shuffle=False)
    probs = []
    model.eval()
    with torch.no_grad():
        for X, _ in loader:
            probs.append(torch.sigmoid(model(X.to(device))).squeeze(-1).cpu().numpy())
    return np.concatenate(probs).astype(np.float64), ds.get_labels().astype(np.int8)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_id")
    ap.add_argument("--checkpoint", required=True)
    ap.add_argument("--features-file", required=True)
    ap.add_argument("--cal-val-parquet", required=True)
    ap.add_argument("--test-parquet", required=True)
    args = ap.parse_args()
    t0 = time.time()

    feature_cols = json.load(open(args.features_file))
    rundir = os.path.join("artifacts", "sprint32", "runs", args.run_id)
    os.makedirs(rundir, exist_ok=True)
    ck = torch.load(args.checkpoint, map_location="cpu", weights_only=True)
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    model = LateFusionPatchTST()
    model.load_state_dict(ck["model"]); model.to(device)

    val_probs, val_labels = infer(model, args.cal_val_parquet, feature_cols, device, args.run_id + "_cv")
    ir = IsotonicRegression(out_of_bounds="clip"); ir.fit(val_probs, val_labels)
    val_cal = np.asarray(ir.predict(val_probs), dtype=np.float64)
    swept_thr, swept_val_tss = find_best_threshold(val_labels, val_cal, metric="tss")

    test_probs, test_labels = infer(model, args.test_parquet, feature_cols, device, args.run_id + "_s2")
    test_cal = np.asarray(ir.predict(test_probs), dtype=np.float64)

    tdf = pd.read_parquet(S2_TEST, columns=["timestamp", "target_6hr_binary"])
    target = tdf["target_6hr_binary"].values.astype(np.int8)
    labels = target[SEQ:]; ts = tdf["timestamp"].values[SEQ:]
    assert np.array_equal(labels, test_labels), "S2 label alignment mismatch — abort"

    ev = UnifiedEvaluator(ts, labels)
    np.save(os.path.join(rundir, "test_cal_probs.npy"), test_cal)

    def full(name, probs, alerts, alerts_red=None, auc_ci=True):
        r = ev.evaluate(name, probs, alerts, alerts_red=alerts_red, auc_ci=auc_ci)
        r["window"]["ECE"] = float(compute_ece(probs, test_labels)[0])
        r["window"]["Brier"] = float(brier_score_loss(test_labels, np.clip(probs, 0, 1)))
        return r

    out = {"run_id": args.run_id, "checkpoint": args.checkpoint, "arch": "LateFusionPatchTST",
           "n_features": int(ck.get("n_features", 36)),
           "best_val_tss_training": ck.get("val_tss"), "checkpoint_epoch": ck.get("epoch"),
           "cal_val_parquet": args.cal_val_parquet, "test_parquet": args.test_parquet,
           "val_swept_threshold": float(swept_thr), "val_swept_val_tss": float(swept_val_tss),
           "val_calibration": {"ECE": float(compute_ece(val_cal, val_labels)[0]),
                                "Brier": float(brier_score_loss(val_labels, np.clip(val_cal, 0, 1)))},
           "policy_thresholds": {"yellow": YELLOW, "red": RED},
           "evaluator_span": "S2 test (04_FAIR_ADITYA_EXPERIMENT.md named modification)",
           "n_windows": int(len(labels))}

    out["policy"] = full(args.run_id + "_policy", test_cal,
                         (test_cal >= YELLOW).astype(np.int8),
                         alerts_red=(test_cal >= RED).astype(np.int8), auc_ci=True)
    out["policy"]["alert_stats"]["red_fraction_of_time"] = float((test_cal >= RED).mean())
    out["valswept"] = full(args.run_id + "_valswept", test_cal,
                           (test_cal >= swept_thr).astype(np.int8), auc_ci=False)

    pers = target[:len(labels)].astype(np.float64)
    vdf = pd.read_parquet(S2_VAL, columns=["target_6hr_binary"])
    p_clim = float(vdf["target_6hr_binary"].values[SEQ:].mean())
    res_pers = ev.evaluate("persistence_s2", pers, pers >= 0.5, auc_ci=False)
    res_clim = ev.evaluate("climatology_s2", np.full(len(labels), p_clim),
                           (np.full(len(labels), p_clim) >= YELLOW).astype(np.int8), auc_ci=False)
    out["s2_floors"] = {"climatology_p": p_clim, "persistence_TSS": res_pers["window"]["TSS"],
                        "climatology_TSS": res_clim["window"]["TSS"]}
    out["paired_policy_vs_persistence"] = {"window": ev.paired_window(out["policy"], res_pers),
                                           "episode": ev.paired_episode(out["policy"], res_pers)}

    def strip(o):
        if isinstance(o, dict):
            return {str(k): strip(v) for k, v in o.items()
                    if not (isinstance(k, str) and k.startswith("_"))}
        if isinstance(o, list): return [strip(v) for v in o]
        if isinstance(o, (np.floating, np.integer)): return o.item()
        return o
    out = strip(out)
    out["wall_seconds"] = round(time.time() - t0, 1)
    json.dump(out, open(os.path.join(rundir, "eval.json"), "w"), indent=1)
    print(f"[{args.run_id}] F3 S2 eval complete (val_swept_val_tss={swept_val_tss:.4f}) "
          f"-> eval.json sealed ({out['wall_seconds']}s)", flush=True)


if __name__ == "__main__":
    main()
