"""
scripts/sprint24/run_method_d.py

Sprint 24 — Method D: V1 with a threshold swept on VALIDATION ONLY, evaluated
on the test set through the identical UnifiedEvaluator, with paired
comparisons against Method A (persistence, causal) and Method C recomputed on
the same shared resamples (the evaluator RNG is constant-seeded, so resample
indices are identical across runner processes).

Inputs: artifacts/sprint24/val_probs_raw.npy + val_labels.npy (produced this
session by run_validation_inference.py; manifest proves no test data was read).
"""

import os, sys, json, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import numpy as np
import pandas as pd
import pickle

from scripts.sprint24.eval_framework import UnifiedEvaluator
from app.services.ml.inference import CalibratorWrapper  # unpickle dependency
from app.services.ml.policy import load_policy, ACTIVE_POLICY_PATH

OUT = os.path.join("artifacts", "sprint24")
SEQ = 360

def strip_private(o):
    if isinstance(o, dict):
        return {k: strip_private(v) for k, v in o.items() if not k.startswith("_")}
    if isinstance(o, list):
        return [strip_private(v) for v in o]
    if isinstance(o, (np.floating, np.integer)):
        return o.item()
    return o

def main():
    t0 = time.time()

    # ── validation-only sweep ────────────────────────────────────────────────
    vp = np.load(os.path.join(OUT, "val_probs_raw.npy")).astype(np.float64)
    vl = np.load(os.path.join(OUT, "val_labels.npy")).astype(np.int8)
    man = json.load(open(os.path.join(OUT, "val_inference_manifest.json")))
    assert man["n_windows"] == len(vp) and man["mc_dropout"] is False

    thresholds = np.round(np.arange(0.01, 0.991, 0.005), 4)
    pos = vl == 1
    n_pos, n_neg = int(pos.sum()), int((~pos).sum())
    best_t, best_tss, sweep = None, -2.0, []
    for t in thresholds:
        pred = vp >= t
        tp = int(np.sum(pred & pos)); fp = int(np.sum(pred & ~pos))
        pod = tp / n_pos; pofd = fp / n_neg
        tss = pod - pofd
        sweep.append({"threshold": float(t), "tss": float(tss),
                      "pod": float(pod), "pofd": float(pofd)})
        if tss > best_tss:
            best_tss, best_t = float(tss), float(t)
    print(f"[D] validation sweep: best raw threshold={best_t} (val TSS={best_tss:.4f}) | "
          f"checkpoint stored 0.336667 for reference", flush=True)

    # ── identical framework on test ──────────────────────────────────────────
    tdf = pd.read_parquet(os.path.join("artifacts", "research", "test.parquet"),
                          columns=["timestamp", "target_6hr_binary"])
    target = tdf["target_6hr_binary"].values.astype(np.int8)
    n_windows = len(tdf) - SEQ
    labels = target[SEQ:]; ts = tdf["timestamp"].values[SEQ:]
    probs_raw = np.load("artifacts/calibration/probs.npy").astype(np.float64)

    ev = UnifiedEvaluator(ts, labels)
    res_d = ev.evaluate("D_v1_val_swept", probs_raw, probs_raw >= best_t, auc_ci=True)

    # paired vs A and vs C on the SAME resamples
    pers = target[:n_windows].astype(np.float64)
    res_a = ev.evaluate("A_persistence_causal", pers, pers >= 0.5, auc_ci=False)
    with open("artifacts/calibrator.pkl", "rb") as f:
        cal = pickle.load(f)
    probs_cal = np.asarray(cal(probs_raw), dtype=np.float64)
    policy = load_policy(ACTIVE_POLICY_PATH)
    y = float(policy.thresholds["yellow_threshold"])
    res_c = ev.evaluate("C_v1_policy", probs_cal, probs_cal >= y, auc_ci=False)

    paired = {
        "D_vs_A": {"window": ev.paired_window(res_d, res_a),
                   "episode": ev.paired_episode(res_d, res_a)},
        "D_vs_C": {"window": ev.paired_window(res_d, res_c),
                   "episode": ev.paired_episode(res_d, res_c)},
    }

    out = {
        "validation_sweep": {"best_threshold": best_t, "best_val_tss": best_tss,
                             "n_thresholds": len(thresholds),
                             "checkpoint_stored_threshold": man["checkpoint_stored_val_threshold"],
                             "val_manifest": man, "sweep_top10":
                             sorted(sweep, key=lambda r: -r["tss"])[:10]},
        "result_D": strip_private(res_d),
        "paired": strip_private(paired),
        "wall_seconds": round(time.time() - t0, 1),
    }
    with open(os.path.join(OUT, "results_d.json"), "w") as f:
        json.dump(out, f, indent=1)

    w, e = res_d["window"], res_d["episode"]
    print(f"\n== D_v1_val_swept (raw θ*={best_t}) ==")
    print(f"  window: TSS={w['TSS']:.4f} {w['ci']['TSS']} HSS={w['HSS']:.4f} MCC={w['MCC']:.4f} "
          f"P={w['Precision']:.4f} R={w['Recall']:.4f} AUC={w['ROC_AUC']:.4f}")
    print(f"  episode: recall={e['episode_recall']:.4f} pre_onset={e['pre_onset_recall']:.4f} "
          f"prec={e['episode_precision']:.4f} FEPM={e['false_episodes_per_month']:.2f} "
          f"lead_med={e['lead_time_min_median']}")
    for cmp_name, cmp in paired.items():
        print(f"  {cmp_name}: dTSS={cmp['window']['TSS']['delta_point']:+.4f} "
              f"CI={cmp['window']['TSS']['delta_ci95']} sig={cmp['window']['TSS']['significant']} | "
              f"d_ep_recall={cmp['episode']['episode_recall']['delta_point']:+.4f} "
              f"sig={cmp['episode']['episode_recall']['significant']} | "
              f"d_preonset={cmp['episode']['pre_onset_recall']['delta_point']:+.4f} "
              f"sig={cmp['episode']['pre_onset_recall']['significant']}")
    print(f"[D] TOTAL {time.time()-t0:.0f}s → {OUT}/results_d.json", flush=True)

if __name__ == "__main__":
    main()
