"""
artifacts/expC_class_separation/run_class_separation.py

Operational Class Separation Experiment — executes the FROZEN pre-registration
(00_PREREGISTRATION.md, commit bbd99a2, tag expC-prereg) verbatim.

Sequence (leakage-critical, enforced by ordering):
  1. Reconstruct alert episodes on VALIDATION from frozen detector probabilities
     at the frozen per-seed thresholds.
  2. Label validation episodes M/X-overlap vs C-overlap by the Experiment A
     strict-intersection rule against the frozen catalog.
  3. Standardise (validation means/stds), fit L2 logistic (C=1.0) on VALIDATION.
  4. Select gate threshold on VALIDATION: highest threshold retaining >=0.90
     validation M/X episode recall after gating.
  5. ONLY THEN open test: apply frozen gate once; compute primary + secondaries.

No retraining. No GOES runtime inputs. Frozen detector probabilities reused, not
recomputed. Frozen Sprint-24 harness imported unmodified.
"""
import hashlib, json, os, sys
sys.path.insert(0, "/Volumes/T7 Shield/Projects/AI/AdityaNet")
os.chdir("/Volumes/T7 Shield/Projects/AI/AdityaNet")

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from scripts.sprint24.eval_framework import UnifiedEvaluator, _runs, _merge_runs, GAP_MIN

SEQ = 360
NDS = "artifacts/research_v4/dataset_adi_nowcast"
RUNS = "artifacts/sprint33_nowcast/runs"
SEEDS = (42, 43, 44, 45, 46)
FROZEN_FALSE = {42: 304, 43: 237, 44: 134, 45: 165, 46: 233}
CATALOG_SHA = "536842648c3891e59b7fb68e86b1dd720fe59c36749d5636c24b61e90bae499a"
# frozen observable list (9 parquet columns + episode duration)
OBS = ["log_solexs_soft", "solexs_peak_30m", "solexs_HR_high_low", "solexs_HR_mid_low",
       "solexs_HR_peak_60m", "log_hel1os_band0", "hel1os_fluence_30m",
       "hel1os_fluence_60m", "nonthermal_thermal_ratio"]
# frozen params
L2_C = 1.0
VAL_RECALL_HOLD = 0.90     # gate threshold selection rule
RECALL_FLOOR = 0.80        # primary gating condition
FE_BUDGET = 5.0            # primary threshold
REDUCTION_CUT = 0.50       # H0/H2 boundary
MAJORITY = 3               # of 5 seeds


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""): h.update(c)
    return h.hexdigest()


def load_split(split):
    df = pd.read_parquet(f"{NDS}/{split}.parquet", columns=["timestamp", "target_6hr_binary"] + OBS)
    ts = df["timestamp"].values[SEQ:].astype("datetime64[s]")
    lab = df["target_6hr_binary"].values[SEQ:].astype(np.int8)
    obs = {c: df[c].values[SEQ:].astype(float) for c in OBS}
    return ts, lab, obs


def catalog():
    fl = pd.read_parquet("artifacts/research/flares_full.parquet")
    for c in ("start_time", "peak_time", "end_time"):
        fl[c] = pd.to_datetime(fl[c])
    fl = fl.dropna(subset=["start_time"]).copy()
    fl["end_eff"] = fl["end_time"].fillna(fl["peak_time"]).fillna(fl["start_time"])
    fl["cls"] = fl["flare_class"].astype(str).str[0].str.upper()
    return (fl["start_time"].values.astype("datetime64[s]"),
            fl["end_eff"].values.astype("datetime64[s]"), fl["cls"].values)


def episodes(ts, probs, thr):
    al = _merge_runs(_runs(probs >= thr), ts, GAP_MIN)
    return al


def ep_features(al, ts, obs):
    """episode-peak (max) of each observable + duration"""
    X = np.zeros((len(al), len(OBS) + 1))
    for i, (s, e) in enumerate(al):
        for j, c in enumerate(OBS):
            X[i, j] = obs[c][s:e + 1].max()
        X[i, len(OBS)] = float((ts[e] - ts[s]) / np.timedelta64(1, "m") + 1.0)
    return X


def ep_class(al, ts, ev_s, ev_e, ev_c):
    """Experiment A strict-intersection rule -> 'MX' / 'C' / 'other'"""
    out = []
    for (s, e) in al:
        s0, e0 = ts[s], ts[e]
        inter = np.where((ev_s <= e0) & (ev_e >= s0))[0]
        cl = {str(ev_c[j]) for j in inter}
        out.append("MX" if (cl & {"M", "X"}) else ("C" if "C" in cl else "other"))
    return np.array(out)


def mx_episode_recall(ts, lab, kept_al):
    """recall of M/X rise-phase label episodes by the KEPT alert episodes"""
    ev = UnifiedEvaluator(ts, lab)
    if len(kept_al) == 0:
        return 0.0, ev
    a_s = ts[kept_al[:, 0]]; a_e = ts[kept_al[:, 1]]
    det = 0
    for i, (s, e) in enumerate(ev.label_eps):
        if np.any((a_s <= ev.ts[e]) & (a_e >= ev.ts[s])): det += 1
    return (det / len(ev.label_eps) if len(ev.label_eps) else 0.0), ev


def false_eps_per_month(ts, lab, kept_al, months):
    ev = UnifiedEvaluator(ts, lab)
    if len(kept_al) == 0: return 0.0, 0
    a_s = ts[kept_al[:, 0]]; a_e = ts[kept_al[:, 1]]
    hit = np.zeros(len(kept_al), bool)
    for i, (s, e) in enumerate(ev.label_eps):
        ov = np.where((a_s <= ev.ts[e]) & (a_e >= ev.ts[s]))[0]
        hit[ov] = True
    n_false = int((~hit).sum())
    return n_false / months, n_false


def main():
    assert sha("artifacts/research/flares_full.parquet") == CATALOG_SHA, "STOP: catalog SHA mismatch"
    ev_s, ev_e, ev_c = catalog()
    vts, vlab, vobs = load_split("validation")
    tts, tlab, tobs = load_split("test")
    v_ev = UnifiedEvaluator(vts, vlab); t_ev = UnifiedEvaluator(tts, tlab)
    results = {}

    for seed in SEEDS:
        op = json.load(open(f"{RUNS}/s{seed}/operating_point.json"))
        thr = op["selected_threshold"]
        # ── VALIDATION ONLY ──────────────────────────────────────────────────
        vp = np.load(f"{RUNS}/s{seed}/val_cal_probs.npy")
        v_al = episodes(vts, vp, thr)
        v_X = ep_features(v_al, vts, vobs)
        v_cls = ep_class(v_al, vts, ev_s, ev_e, ev_c)
        fit_mask = np.isin(v_cls, ["MX", "C"])
        y = (v_cls[fit_mask] == "MX").astype(int)
        Xf = v_X[fit_mask]
        mu, sd = Xf.mean(axis=0), Xf.std(axis=0); sd[sd == 0] = 1.0
        clf = LogisticRegression(C=L2_C, penalty="l2", max_iter=5000)
        clf.fit((Xf - mu) / sd, y)
        if clf.n_iter_[0] >= 5000: raise RuntimeError("STOP: validation classifier did not converge")
        v_pmx = clf.predict_proba((v_X - mu) / sd)[:, 1]
        # gate threshold: highest retaining >=0.90 val M/X episode recall after gating
        grid = np.round(np.arange(0.005, 0.999, 0.005), 4)
        sel_g, sel_r = None, None
        for g in grid:
            kept = v_al[v_pmx >= g]
            r, _ = mx_episode_recall(vts, vlab, kept)
            if r >= VAL_RECALL_HOLD: sel_g, sel_r = float(g), float(r)
        if sel_g is None:                    # stopping rule 1
            results[seed] = {"STOP": "stopping_rule_1_no_gate_holds_val_recall"}
            print(f"[s{seed}] STOP rule 1", flush=True); continue

        # ── TEST OPENED ONCE ────────────────────────────────────────────────
        tp = np.load(f"{RUNS}/s{seed}/test_cal_probs.npy")
        t_al = episodes(tts, tp, thr)
        # stopping rule 2: reconstructed ungated false count must match frozen
        fe_un, n_false_un = false_eps_per_month(tts, tlab, t_al, t_ev.months)
        assert n_false_un == FROZEN_FALSE[seed], \
            f"STOP: seed {seed} reconstructed {n_false_un} != frozen {FROZEN_FALSE[seed]}"
        t_X = ep_features(t_al, tts, tobs)
        t_pmx = clf.predict_proba((t_X - mu) / sd)[:, 1]
        kept = t_al[t_pmx >= sel_g]
        r_gated, _ = mx_episode_recall(tts, tlab, kept)
        fe_gated, n_false_gated = false_eps_per_month(tts, tlab, kept, t_ev.months)
        R = 1.0 - (fe_gated / fe_un) if fe_un > 0 else 0.0
        # secondary: class-separation AUC on test episodes
        t_cls = ep_class(t_al, tts, ev_s, ev_e, ev_c)
        am = np.isin(t_cls, ["MX", "C"])
        auc = float(roc_auc_score((t_cls[am] == "MX").astype(int), t_pmx[am])) if am.sum() > 1 and len(set((t_cls[am]=="MX"))) > 1 else float("nan")
        results[seed] = {
            "detector_threshold": thr, "gate_threshold": sel_g, "val_mx_recall_at_gate": sel_r,
            "ungated_fe_per_month": fe_un, "ungated_false_count": n_false_un,
            "gated_fe_per_month": fe_gated, "gated_false_count": n_false_gated,
            "gated_mx_episode_recall": r_gated, "reduction_R": R,
            "class_separation_auc_test": auc,
            "op_point_stability": abs(sel_r - r_gated),
            "n_alert_episodes_ungated": int(len(t_al)), "n_alert_episodes_gated": int(len(kept)),
            "seed_passes_primary": bool(fe_gated <= FE_BUDGET and r_gated >= RECALL_FLOOR),
            "coefficients": {c: float(v) for c, v in zip(OBS + ["episode_duration_min"], clf.coef_[0])},
        }
        print(f"[s{seed}] gate={sel_g} | FE/mo {fe_un:.2f}->{fe_gated:.2f} (R={R:.3f}) | "
              f"MX recall {r_gated:.4f} | AUC={auc:.4f} | pass={results[seed]['seed_passes_primary']}", flush=True)

    # ── frozen hypothesis adjudication ──────────────────────────────────────
    ok = [s for s in SEEDS if "STOP" not in results[s]]
    n_pass = sum(results[s]["seed_passes_primary"] for s in ok)
    Rs = [results[s]["reduction_R"] for s in ok]
    meanR = float(np.mean(Rs)) if Rs else 0.0
    if n_pass >= MAJORITY: verdict = "H1_SUFFICIENT_SEPARATION"
    elif meanR >= REDUCTION_CUT: verdict = "H2_PARTIAL_SEPARATION"
    else: verdict = "H0_NO_OPERATIONAL_CLASS_SIGNAL"
    out = {"preregistration": "artifacts/expC_class_separation/00_PREREGISTRATION.md @ bbd99a2 (expC-prereg)",
           "per_seed": results, "n_pass": n_pass, "majority_required": MAJORITY,
           "mean_reduction_R": meanR, "hypothesis_verdict": verdict,
           "mean_gated_fe_per_month": float(np.mean([results[s]["gated_fe_per_month"] for s in ok])),
           "mean_gated_mx_recall": float(np.mean([results[s]["gated_mx_episode_recall"] for s in ok])),
           "mean_class_auc": float(np.mean([results[s]["class_separation_auc_test"] for s in ok]))}
    json.dump(out, open("artifacts/expC_class_separation/class_separation.json", "w"), indent=1, default=str)
    print(json.dumps({k: out[k] for k in ("n_pass", "mean_reduction_R", "mean_gated_fe_per_month",
                                          "mean_gated_mx_recall", "mean_class_auc", "hypothesis_verdict")}, indent=1))


if __name__ == "__main__":
    main()
