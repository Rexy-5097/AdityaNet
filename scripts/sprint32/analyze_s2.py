"""
scripts/sprint32/analyze_s2.py

Sprint 32 Phase 4 — pre-registered analysis. Written and committed BEFORE any
F3 or EraMatchedGOES result was inspected; every interpretive rule is locked
here (Sprint 25 plan + Sprint 31 methodology).

Four paired comparisons, all on the same 261,095-window S2 test span through
the frozen Sprint 24 harness on identical resample indices (2880-window blocks
authoritative; 1440/5760 for sensitivity):
  F3 vs F2   : does late fusion improve single-encoder fusion?  delta = F3 - F2
  F3 vs F0   : does late fusion beat the original GOES baseline? delta = F3 - F0
  F2 vs EMG  : ADITYA EFFECT (era controlled) = F2 - EraMatchedGOES  [PRIMARY]
  EMG vs F0  : ERA EFFECT = EraMatchedGOES - F0

PRE-DECLARED RULES (locked before results):
  * Primary ISRO endpoint = per-seed paired dTSS(F2 - EMG), same seed vs same
    seed, policy operating point. Aditya value SUPPORTED iff dTSS >= +0.02 with
    lower 95% bound > 0 in a majority of shared seeds (>=2/3, or >=3/5 if either
    arm escalated), pre-onset recall not degraded (delta<0 AND CI excludes 0).
  * Late-fusion endpoint = paired dTSS(F3 - F2), same rule.
  * p-values: harness p_boot (two-sided percentile, floor 1/1000).
  * Cohen's d: one-sample on per-seed paired deltas, mean/std(ddof=1).
  * F0 is a single frozen reference (no seed distribution); F0-paired deltas
    use each trained seed's arm vs the one F0 vector.
  * Operator Utility := TSS (Richardson 2000 V_max), pre-declared as Sprint 31.
  * Borderline = point estimate clears +0.02 but CI includes 0; reported as
    borderline, never rounded up to success.
"""
import json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import numpy as np
import pandas as pd

import scripts.sprint24.eval_framework as efm

S31 = "artifacts/sprint31/runs"
S32 = "artifacts/sprint32/runs"
YELLOW, RED = 0.14, 0.95
MIN_EFFECT = 0.02
SEQ = 360
S2_TEST = "artifacts/sprint14c/s2_test.parquet"
V4S2 = "artifacts/research_v4/dataset_v4.1.0-s2"


def strip(o):
    if isinstance(o, dict):
        return {str(k): strip(v) for k, v in o.items()
                if not (isinstance(k, str) and k.startswith("_"))}
    if isinstance(o, list): return [strip(v) for v in o]
    if isinstance(o, (np.floating, np.integer)): return o.item()
    return o


def seeds_present(prefix, base):
    return [s for s in (42, 43, 44, 45, 46)
            if os.path.exists(os.path.join(base, f"{prefix}_s{s}", "eval.json"))]


def main():
    t0 = time.time()
    f3_seeds = seeds_present("F3", S32)
    emg_seeds = seeds_present("EMG", S32)
    f2_seeds = seeds_present("F2", S31)

    # probability arrays (all aligned to the same s2_test windows)
    probs = {}
    evals = {}
    def load(run, base):
        probs[run] = np.load(os.path.join(base, run, "test_cal_probs.npy"))
        evals[run] = json.load(open(os.path.join(base, run, "eval.json")))
    load("F0_s2", S31)
    for s in f2_seeds: load(f"F2_s{s}", S31)
    for s in f3_seeds: load(f"F3_s{s}", S32)
    for s in emg_seeds: load(f"EMG_s{s}", S32)

    tdf = pd.read_parquet(S2_TEST, columns=["timestamp", "target_6hr_binary"])
    target = tdf["target_6hr_binary"].values.astype(np.int8)
    labels = target[SEQ:]; ts = tdf["timestamp"].values[SEQ:]

    def evaluate_all(block_len):
        orig = efm.BLOCK_LEN
        try:
            efm.BLOCK_LEN = block_len
            ev = efm.UnifiedEvaluator(ts, labels)
            res = {r: ev.evaluate(r, p, (p >= YELLOW).astype(np.int8),
                                  alerts_red=(p >= RED).astype(np.int8), auc_ci=False)
                   for r, p in probs.items()}
            return ev, res
        finally:
            efm.BLOCK_LEN = orig

    def paired(ev, res, a, b):
        return {"window": strip(ev.paired_window(res[a], res[b])),
                "episode": strip(ev.paired_episode(res[a], res[b]))}

    ev, res = evaluate_all(2880)

    def comparison(name, seeds_a, prefix_a, ref_b):
        """ref_b is either 'F0_s2' (single ref) or a prefix for same-seed pairing."""
        rows = []
        for s in seeds_a:
            a = f"{prefix_a}_s{s}"
            b = "F0_s2" if ref_b == "F0_s2" else f"{ref_b}_s{s}"
            if b not in res: continue
            pw = paired(ev, res, a, b)["window"]["TSS"]
            pe = paired(ev, res, a, b)["episode"]["pre_onset_recall"]
            rows.append({"seed": s, "dTSS": pw["delta_point"], "ci": pw["delta_ci95"],
                         "p_boot": pw["p_boot"], "significant": pw["significant"],
                         "pre_onset_delta": pe["delta_point"], "pre_onset_sig": pe["significant"]})
        d = np.array([r["dTSS"] for r in rows])
        lo = np.array([r["ci"][0] for r in rows])
        passes = [bool(r["dTSS"] >= MIN_EFFECT and r["ci"][0] > 0 and
                       not (r["pre_onset_delta"] < 0 and r["pre_onset_sig"])) for r in rows]
        maj = 2 if len(rows) <= 3 else (len(rows) // 2 + 1)
        return {"per_seed": rows, "n": len(rows),
                "dTSS_mean": float(d.mean()) if len(d) else None,
                "dTSS_std": float(d.std(ddof=1)) if len(d) > 1 else None,
                "cohens_d": float(d.mean() / d.std(ddof=1)) if len(d) > 1 and d.std(ddof=1) > 0 else None,
                "n_passing": int(sum(passes)), "majority_required": maj,
                "success": bool(sum(passes) >= maj)}

    comparisons = {
        "F3_vs_F2": comparison("F3_vs_F2", [s for s in f3_seeds if s in f2_seeds], "F3", "F2"),
        "F3_vs_F0": comparison("F3_vs_F0", f3_seeds, "F3", "F0_s2"),
        "F2_vs_EMG_ADITYA_EFFECT": comparison("F2_vs_EMG", [s for s in f2_seeds if s in emg_seeds], "F2", "EMG"),
        "EMG_vs_F0_ERA_EFFECT": comparison("EMG_vs_F0", emg_seeds, "EMG", "F0_s2"),
    }

    # block sensitivity for the two headline deltas
    block_sens = {}
    for bl in (1440, 2880, 5760):
        evb, resb = evaluate_all(bl)
        block_sens[str(bl)] = {
            "F2_vs_EMG": {s: strip(evb.paired_window(resb[f"F2_s{s}"], resb[f"EMG_s{s}"]))["TSS"]
                          for s in f2_seeds if s in emg_seeds},
            "F3_vs_F2": {s: strip(evb.paired_window(resb[f"F3_s{s}"], resb[f"F2_s{s}"]))["TSS"]
                         for s in f3_seeds if s in f2_seeds},
            "F3_vs_F0": {s: strip(evb.paired_window(resb[f"F3_s{s}"], resb["F0_s2"]))["TSS"]
                         for s in f3_seeds},
        }

    def pol(run):
        w = evals[run]["policy"]["window"]; e = evals[run]["policy"]["episode"]
        a = evals[run]["policy"]["alert_stats"]
        return {"TSS": w["TSS"], "TSS_ci": w["ci"]["TSS"], "ROC_AUC": w["ROC_AUC"],
                "PR_AUC": w["PR_AUC"], "ECE": w["ECE"], "Brier": w["Brier"],
                "episode_recall": e["episode_recall"], "pre_onset_recall": e["pre_onset_recall"],
                "false_episodes_per_month": e["false_episodes_per_month"],
                "lead_time_min_median": e["lead_time_min_median"],
                "yellow_duty_cycle": a["yellow_fraction_of_time"],
                "red_duty_cycle": a.get("red_fraction_of_time"),
                "operator_utility_Vmax": w["TSS"]}
    table = {r: pol(r) for r in evals}

    def arm_stats(prefix, seeds):
        v = np.array([table[f"{prefix}_s{s}"]["TSS"] for s in seeds])
        return {"seeds": seeds, "TSS_mean": float(v.mean()), "TSS_std": float(v.std(ddof=1)) if len(v) > 1 else 0.0,
                "TSS_range": float(v.max() - v.min()) if len(v) else 0.0, "per_seed": {s: table[f"{prefix}_s{s}"]["TSS"] for s in seeds}}
    arm_summ = {"F0": {"TSS": table["F0_s2"]["TSS"], "note": "single frozen reference"},
                "F2": arm_stats("F2", f2_seeds),
                "F3": arm_stats("F3", f3_seeds),
                "EMG": arm_stats("EMG", emg_seeds)}

    out = {"generated": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "seeds": {"F3": f3_seeds, "EMG": emg_seeds, "F2": f2_seeds},
           "arm_summary": arm_summ, "policy_metrics": table,
           "comparisons": comparisons, "block_sensitivity": block_sens,
           "s2_floors": evals[f"F2_s{f2_seeds[0]}"]["s2_floors"],
           "validation_side": {r: {"best_val_tss_training": evals[r].get("best_val_tss_training"),
                                   "val_swept_val_tss": evals[r].get("val_swept_val_tss")} for r in evals},
           "wall_seconds": round(time.time() - t0, 1)}
    json.dump(strip(out), open("artifacts/sprint32/analysis.json", "w"), indent=1)
    print(json.dumps({"arm_summary": {k: (v if "note" in v else {"mean": round(v["TSS_mean"], 4),
                                          "std": round(v["TSS_std"], 4), "range": round(v["TSS_range"], 4),
                                          "seeds": v["seeds"]}) for k, v in strip(arm_summ).items()},
                      "comparisons": {k: {"dTSS_mean": (round(v["dTSS_mean"], 4) if v["dTSS_mean"] is not None else None),
                                          "n_passing": v["n_passing"], "n": v["n"],
                                          "success": v["success"]} for k, v in strip(comparisons).items()}}, indent=1))
    print(f"[analyze_s2] DONE {out['wall_seconds']}s -> artifacts/sprint32/analysis.json", flush=True)


if __name__ == "__main__":
    main()
