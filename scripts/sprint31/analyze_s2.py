"""
scripts/sprint31/analyze_s2.py

Sprint 31 Phase 5 — pre-registered analysis of F2 vs F1 and F2 vs F0 on the
Stage-2 test span. Written and committed BEFORE any sealed result was
inspected; every interpretive rule is locked here.

Plan: artifacts/sprint25/07_preregistered_analysis_plan.md + the statistics
section of artifacts/sprint28/04_FAIR_ADITYA_EXPERIMENT.md. (The brief's
cited path artifacts/sprint28/07_preregistered_analysis_plan.md does not
exist; the Sprint 25 plan is the plan of record, as in Sprint 30.)

PRE-DECLARED RULES (locked before results):
  * Primary endpoint: per-seed paired dTSS (F2_seed vs F1_seed, SAME seed) at
    the policy operating point via the frozen harness paired_window on
    identical resample indices, S2 span. Success (04): dTSS >= +0.02 AND
    lower 95% bound > 0 in >= 2 of 3 seeds (majority >= 3 of 5 if the
    escalation ran — the Sprint 30 pre-declared extension), with pre-onset
    episode recall not degraded ("degraded" = paired delta negative AND its
    95% CI excludes zero; the Sprint 30 pre-declared reading).
  * p-values: the harness's p_boot (two-sided percentile bootstrap p, floor
    1/1000).
  * Cohen's d: one-sample form on per-seed paired deltas, mean/std(ddof=1).
  * Operator Utility := TSS (Richardson 2000: maximum relative economic value
    over all cost/loss ratios in the cost-loss model equals H - F = TSS).
    Chosen pre-verdict because the repository contains no other pre-registered
    utility definition; parameter-free by construction. RED duty cycle from
    the sealed eval alert stats.
  * Block-size sensitivity: paired dTSS recomputed at BLOCK_LEN 1440/2880/5760
    via runtime constant override (frozen file untouched; Sprint 24
    precedent). 2880 authoritative.
  * Stratification (04 + 03 SS5): per-window SoLEXS quality on s2_test from
    the disclosure channels (trailing 360-min mean availability x
    (1 - mean staleness/60)); strata quality >= 0.9 vs < 0.9, and
    "present vs absent" (availability_fraction >= 0.5 vs < 0.5). Point TSS /
    recall / precision per stratum per arm. Degenerate strata reported as
    such (pre-declared in Missing_Data_Report.md).
  * Cross-span rule (04): every comparison here is same-span S2-paired.
"""
import json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import numpy as np
import pandas as pd

import scripts.sprint24.eval_framework as efm

RUNS = os.path.join("artifacts", "sprint31", "runs")
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


def main():
    t0 = time.time()
    seeds = [s for s in (42, 43, 44, 45, 46)
             if os.path.exists(os.path.join(RUNS, f"F2_s{s}", "eval.json"))]
    majority = 2 if len(seeds) == 3 else (len(seeds) // 2 + 1)

    evals = {"F0_s2": json.load(open(os.path.join(RUNS, "F0_s2", "eval.json")))}
    for s in seeds:
        evals[f"F2_s{s}"] = json.load(open(os.path.join(RUNS, f"F2_s{s}", "eval.json")))
        evals[f"F1_s{s}_s2"] = json.load(open(os.path.join(RUNS, f"F1_s{s}_s2", "eval.json")))

    probs = {r: np.load(os.path.join(RUNS, r, "test_cal_probs.npy")) for r in evals}

    tdf = pd.read_parquet(S2_TEST, columns=["timestamp", "target_6hr_binary"])
    target = tdf["target_6hr_binary"].values.astype(np.int8)
    labels = target[SEQ:]; ts = tdf["timestamp"].values[SEQ:]

    def paired_at_block(block_len):
        orig = efm.BLOCK_LEN
        try:
            efm.BLOCK_LEN = block_len
            ev = efm.UnifiedEvaluator(ts, labels)
            res = {r: ev.evaluate(r, p, (p >= YELLOW).astype(np.int8),
                                  alerts_red=(p >= RED).astype(np.int8), auc_ci=False)
                   for r, p in probs.items()}
            out = {}
            for s in seeds:
                out[s] = {
                    "F2_vs_F1": {"window": strip(ev.paired_window(res[f"F2_s{s}"], res[f"F1_s{s}_s2"])),
                                 "episode": strip(ev.paired_episode(res[f"F2_s{s}"], res[f"F1_s{s}_s2"]))},
                    "F2_vs_F0": {"window": strip(ev.paired_window(res[f"F2_s{s}"], res["F0_s2"])),
                                 "episode": strip(ev.paired_episode(res[f"F2_s{s}"], res["F0_s2"]))}}
            # F1-vs-F0 on S2 for context (same resamples)
            out["F1_vs_F0_per_seed"] = {
                s: strip(ev.paired_window(res[f"F1_s{s}_s2"], res["F0_s2"]))["TSS"] for s in seeds}
            return out
        finally:
            efm.BLOCK_LEN = orig

    paired = paired_at_block(2880)
    robustness = {"2880": {s: paired[s]["F2_vs_F1"]["window"]["TSS"] for s in seeds}}
    for bl in (1440, 5760):
        pb = paired_at_block(bl)
        robustness[str(bl)] = {s: pb[s]["F2_vs_F1"]["window"]["TSS"] for s in seeds}

    def pol(run):
        w = evals[run]["policy"]["window"]; e = evals[run]["policy"]["episode"]
        a = evals[run]["policy"]["alert_stats"]
        return {"TSS": w["TSS"], "TSS_ci": w["ci"]["TSS"], "ROC_AUC": w["ROC_AUC"],
                "PR_AUC": w["PR_AUC"], "ECE": w["ECE"], "Brier": w["Brier"],
                "Precision": w["Precision"], "Recall": w["Recall"],
                "episode_recall": e["episode_recall"], "pre_onset_recall": e["pre_onset_recall"],
                "false_episodes_per_month": e["false_episodes_per_month"],
                "lead_time_min_median": e["lead_time_min_median"],
                "yellow_duty_cycle": a["yellow_fraction_of_time"],
                "red_duty_cycle": a.get("red_fraction_of_time"),
                "operator_utility_Vmax": w["TSS"]}   # Richardson 2000, pre-declared
    table = {r: pol(r) for r in evals}

    f2_tss = np.array([table[f"F2_s{s}"]["TSS"] for s in seeds])
    d21 = np.array([paired[s]["F2_vs_F1"]["window"]["TSS"]["delta_point"] for s in seeds])
    lo21 = np.array([paired[s]["F2_vs_F1"]["window"]["TSS"]["delta_ci95"][0] for s in seeds])
    d20 = np.array([paired[s]["F2_vs_F0"]["window"]["TSS"]["delta_point"] for s in seeds])

    per_seed = []
    for i, s in enumerate(seeds):
        pre = paired[s]["F2_vs_F1"]["episode"]["pre_onset_recall"]
        degraded = pre["delta_point"] < 0 and pre["significant"]
        per_seed.append({"seed": s, "dTSS_F2_F1": float(d21[i]), "ci_lower": float(lo21[i]),
                         "p_boot": paired[s]["F2_vs_F1"]["window"]["TSS"]["p_boot"],
                         "meets_min_effect": bool(d21[i] >= MIN_EFFECT),
                         "ci_lower_positive": bool(lo21[i] > 0),
                         "pre_onset_degraded_significantly": bool(degraded),
                         "seed_passes": bool(d21[i] >= MIN_EFFECT and lo21[i] > 0 and not degraded)})
    n_pass = sum(p["seed_passes"] for p in per_seed)

    seed_stats = {"seeds": seeds,
                  "F2_TSS_mean": float(f2_tss.mean()), "F2_TSS_std": float(f2_tss.std(ddof=1)),
                  "F2_TSS_range": float(f2_tss.max() - f2_tss.min()),
                  "escalation_was_triggered": len(seeds) > 3,
                  "dTSS_F2_F1_mean": float(d21.mean()), "dTSS_F2_F1_std": float(d21.std(ddof=1)),
                  "cohens_d_F2_F1": float(d21.mean() / d21.std(ddof=1)) if d21.std(ddof=1) > 0 else None,
                  "dTSS_F2_F0_mean": float(d20.mean()),
                  "cohens_d_F2_F0": float(d20.mean() / d20.std(ddof=1)) if d20.std(ddof=1) > 0 else None}

    primary = {"per_seed": per_seed, "n_seeds_passing": n_pass, "n_seeds": len(seeds),
               "majority_required": majority, "success": bool(n_pass >= majority),
               "criterion": f"paired dTSS(F2 vs F1) >= +0.02 with lower 95% bound > 0 in >= "
                            f"{majority} of {len(seeds)} seeds, pre-onset recall not degraded"}

    sec_keys = ["ROC_AUC", "PR_AUC", "ECE", "episode_recall", "pre_onset_recall",
                "false_episodes_per_month", "yellow_duty_cycle", "red_duty_cycle",
                "operator_utility_Vmax"]
    secondary = {}
    for k in sec_keys:
        per = {s: (table[f"F2_s{s}"][k] - table[f"F1_s{s}_s2"][k])
               if table[f"F1_s{s}_s2"][k] is not None and table[f"F2_s{s}"][k] is not None else None
               for s in seeds}
        vals = [v for v in per.values() if v is not None]
        secondary[f"delta_{k}_F2_F1"] = {"per_seed": per,
                                         "mean": float(np.mean(vals)) if vals else None}

    # availability stratification on s2_test windows
    disc = pd.read_parquet(os.path.join(V4S2, "test.parquet"),
                           columns=["solexs_available", "solexs_staleness_n"])
    av = disc["solexs_available"].rolling(SEQ).mean().to_numpy()[SEQ - 1:-1]
    stn = disc["solexs_staleness_n"].rolling(SEQ).mean().to_numpy()[SEQ - 1:-1]
    quality = av * (1 - stn)
    strata = {"quality_ge_0.9": quality >= 0.9, "quality_lt_0.9": quality < 0.9,
              "aditya_present(avail>=0.5)": av >= 0.5, "aditya_absent(avail<0.5)": av < 0.5}
    strat = {"quality_distribution": {"p01": float(np.percentile(quality, 1)),
                                      "p50": float(np.percentile(quality, 50)),
                                      "p99": float(np.percentile(quality, 99))},
             "strata_populations": {k: int(m.sum()) for k, m in strata.items()},
             "metrics": {}}
    for name, m in strata.items():
        if m.sum() == 0 or m.sum() == len(quality):
            strat["metrics"][name] = "DEGENERATE stratum" if m.sum() == 0 else "ALL windows"
        entry = {}
        if m.sum() > 0:
            lab = labels[m]
            for arm in ["F0_s2"] + [f"F1_s{s}_s2" for s in seeds] + [f"F2_s{s}" for s in seeds]:
                al = (probs[arm][m] >= YELLOW).astype(int)
                tp = int(((al == 1) & (lab == 1)).sum()); fp = int(((al == 1) & (lab == 0)).sum())
                fn = int(((al == 0) & (lab == 1)).sum()); tn = int(((al == 0) & (lab == 0)).sum())
                pod = tp / max(tp + fn, 1); pofd = fp / max(fp + tn, 1)
                entry[arm] = {"n": int(m.sum()), "TSS_point": round(pod - pofd, 4),
                              "recall": round(pod, 4),
                              "precision": round(tp / max(tp + fp, 1), 4)}
            strat["metrics"][name] = entry

    out = {"generated": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "policy_metrics": table, "paired_2880": {str(s): paired[s] for s in seeds},
           "F1_vs_F0_on_S2": paired["F1_vs_F0_per_seed"],
           "seed_stats": seed_stats, "primary_endpoint": primary,
           "secondary_endpoints": secondary, "block_robustness": robustness,
           "stratification": strat,
           "floors_s2": evals[f"F2_s{seeds[0]}"]["s2_floors"],
           "validation_side": {r: {"best_val_tss_training": evals[r].get("best_val_tss_training"),
                                   "checkpoint_epoch": evals[r].get("checkpoint_epoch"),
                                   "val_swept_val_tss": evals[r].get("val_swept_val_tss")}
                               for r in evals},
           "wall_seconds": round(time.time() - t0, 1)}
    json.dump(strip(out), open(os.path.join("artifacts", "sprint31", "analysis.json"), "w"), indent=1)
    print(json.dumps({"seeds": seeds, "seed_stats": strip(seed_stats),
                      "primary": strip(primary),
                      "F0_s2_TSS": table["F0_s2"]["TSS"],
                      "F1_s2_TSS_by_seed": {s: table[f"F1_s{s}_s2"]["TSS"] for s in seeds}}, indent=1))
    print(f"[analyze_s2] DONE {out['wall_seconds']}s -> artifacts/sprint31/analysis.json", flush=True)


if __name__ == "__main__":
    main()
