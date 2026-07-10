"""
scripts/sprint24/run_evaluation_abc.py

Sprint 24 — evaluate Methods A (persistence), B (climatology), C (V1 + Sprint 23
clean policy) through the ONE UnifiedEvaluator, plus paired block-bootstrap
comparisons and a reproducibility self-check. Method D is evaluated by
run_method_d.py once the validation inference completes.

Persistence definitions (both computed; see 01_evaluation_framework.md):
  A  (causal)      : predict 1 iff an M/X flare occurred in the trailing 360
                     minutes. With window i's label = target[row i+360], the
                     trailing-window indicator at the decision time is exactly
                     target[row i] — fully observable. This is the fair baseline.
  A' (literal/non-causal): the brief's literal "last-window label" = label of
                     window i-1 = target[row i+359], which covers flares up to
                     359 minutes AFTER the decision time. Not a realizable
                     forecaster; reported for completeness, excluded from verdict.
Climatology B      : fixed probability = validation-era positive window rate
                     (computed this session from artifacts/research/validation.parquet).
Method C           : calibrated V1 probabilities (artifacts/calibrator.pkl applied to
                     the canonical archived raw test probabilities) with the deployed
                     policy thresholds (yellow/red from artifacts/policies/
                     operator_policy_v2.json). Deterministic thresholds only:
                     MC-Dropout uncertainty suppression and sequential RED
                     confirmation are NOT simulated here (both only remove alerts,
                     so C's recall and false-alarm counts are upper bounds).
"""

import os, sys, json, time, hashlib
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import numpy as np
import pandas as pd
import pickle

from scripts.sprint24.eval_framework import UnifiedEvaluator, BLOCK_LEN, N_BOOT, N_BOOT_AUC, GAP_MIN, SEED
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
    os.makedirs(OUT, exist_ok=True)

    # ── shared dataset (identical for every method) ───────────────────────────
    tdf = pd.read_parquet(os.path.join("artifacts", "research", "test.parquet"),
                          columns=["timestamp", "target_6hr_binary"])
    target = tdf["target_6hr_binary"].values.astype(np.int8)
    ts_all = tdf["timestamp"].values
    n_windows = len(tdf) - SEQ
    labels = target[SEQ:]
    ts = ts_all[SEQ:]

    arch_labels = np.load("artifacts/calibration/labels.npy")
    assert np.array_equal(labels.astype(np.float32), arch_labels.astype(np.float32)), \
        "label alignment mismatch — abort"
    probs_raw = np.load("artifacts/calibration/probs.npy").astype(np.float64)

    with open("artifacts/calibrator.pkl", "rb") as f:
        calibrator = pickle.load(f)
    probs_cal = np.asarray(calibrator(probs_raw), dtype=np.float64)

    policy = load_policy(ACTIVE_POLICY_PATH)
    yellow = float(policy.thresholds["yellow_threshold"])
    red = float(policy.thresholds["red_threshold"])

    vdf = pd.read_parquet(os.path.join("artifacts", "research", "validation.parquet"),
                          columns=["target_6hr_binary"])
    p_clim = float(vdf["target_6hr_binary"].values[SEQ:].mean())
    print(f"[abc] windows={n_windows:,} | climatology p={p_clim:.6f} | "
          f"policy yellow={yellow} red={red}", flush=True)

    ev = UnifiedEvaluator(ts, labels)
    print(f"[abc] label episodes={len(ev.label_eps)} | months={ev.months:.2f} | "
          f"blocks={ev.n_blocks} (len {BLOCK_LEN})", flush=True)

    # ── method arrays ─────────────────────────────────────────────────────────
    pers_causal = target[:n_windows].astype(np.float64)          # trailing-6h flare indicator
    pers_literal = np.r_[0, labels[:-1]].astype(np.float64)      # NON-CAUSAL, flagged
    clim = np.full(n_windows, p_clim)

    results, t = {}, time.time()
    results["A_persistence_causal"] = ev.evaluate(
        "A_persistence_causal", pers_causal, pers_causal >= 0.5, auc_ci=True)
    print(f"[abc] A done {time.time()-t:.0f}s", flush=True); t = time.time()
    results["A_literal_noncausal"] = ev.evaluate(
        "A_literal_noncausal", pers_literal, pers_literal >= 0.5, auc_ci=False)
    print(f"[abc] A' done {time.time()-t:.0f}s", flush=True); t = time.time()
    results["B_climatology"] = ev.evaluate(
        "B_climatology", clim, clim >= yellow, auc_ci=False)
    print(f"[abc] B done {time.time()-t:.0f}s", flush=True); t = time.time()
    results["C_v1_policy"] = ev.evaluate(
        "C_v1_policy", probs_cal, probs_cal >= yellow, alerts_red=(probs_cal >= red), auc_ci=True)
    print(f"[abc] C done {time.time()-t:.0f}s", flush=True)

    # ── paired comparisons (identical resamples by construction) ─────────────
    paired = {
        "C_vs_A": {"window": ev.paired_window(results["C_v1_policy"], results["A_persistence_causal"]),
                   "episode": ev.paired_episode(results["C_v1_policy"], results["A_persistence_causal"])},
        "C_vs_B": {"window": ev.paired_window(results["C_v1_policy"], results["B_climatology"]),
                   "episode": ev.paired_episode(results["C_v1_policy"], results["B_climatology"])},
        "A_vs_B": {"window": ev.paired_window(results["A_persistence_causal"], results["B_climatology"])},
    }

    # ── reproducibility self-check: fresh evaluator + method A, twice ────────
    r1 = strip_private(UnifiedEvaluator(ts, labels).evaluate(
        "A_persistence_causal", pers_causal, pers_causal >= 0.5, auc_ci=False))
    r2 = strip_private(UnifiedEvaluator(ts, labels).evaluate(
        "A_persistence_causal", pers_causal, pers_causal >= 0.5, auc_ci=False))
    h1 = hashlib.sha256(json.dumps(r1, sort_keys=True).encode()).hexdigest()
    h2 = hashlib.sha256(json.dumps(r2, sort_keys=True).encode()).hexdigest()
    repro = {"run1_sha256": h1, "run2_sha256": h2, "identical": h1 == h2}
    print(f"[abc] reproducibility identical={h1 == h2} ({h1[:16]})", flush=True)

    out = {
        "protocol": {"block_len_windows": BLOCK_LEN, "n_boot": N_BOOT,
                     "n_boot_auc": N_BOOT_AUC, "gap_min": GAP_MIN, "seed": SEED,
                     "n_windows": n_windows, "n_label_episodes": int(len(ev.label_eps)),
                     "months": ev.months, "climatology_p": p_clim,
                     "policy_id": policy.raw["policy_id"],
                     "yellow": yellow, "red": red,
                     "mc_suppression_simulated": False},
        "results": strip_private(results),
        "paired": strip_private(paired),
        "reproducibility": repro,
        "wall_seconds": round(time.time() - t0, 1),
    }
    with open(os.path.join(OUT, "results_abc.json"), "w") as f:
        json.dump(out, f, indent=1)

    for name, r in results.items():
        w, e = r["window"], r["episode"]
        print(f"\n== {name} ==")
        print(f"  window: TSS={w['TSS']:.4f} {w['ci']['TSS']} HSS={w['HSS']:.4f} "
              f"MCC={w['MCC']:.4f} P={w['Precision']:.4f} R={w['Recall']:.4f} "
              f"AUC={w['ROC_AUC']:.4f} PRAUC={w['PR_AUC']:.4f}")
        print(f"  episode: recall={e['episode_recall']:.4f} {e['ci']['episode_recall']} "
              f"pre_onset={e['pre_onset_recall']:.4f} {e['ci']['pre_onset_recall']} "
              f"prec={e['episode_precision']:.4f} FEPM={e['false_episodes_per_month']:.2f} "
              f"lead_med={e['lead_time_min_median']}")
    print(f"\n[abc] TOTAL {time.time()-t0:.0f}s → {OUT}/results_abc.json", flush=True)

if __name__ == "__main__":
    main()
