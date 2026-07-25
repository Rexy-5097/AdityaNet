"""
scripts/sprint30/analyze.py

Sprint 30 Phase 5 — pre-registered analysis of F1 vs F0, written and committed
BEFORE any test-set result was inspected (integrity rule: interpretations are
locked here, not chosen after seeing numbers).

Plan applied: artifacts/sprint25/07_preregistered_analysis_plan.md +
artifacts/sprint28/04_FAIR_ADITYA_EXPERIMENT.md §Statistics + F1.json.

PRE-DECLARED INTERPRETATIONS (locked before results):
  * Primary endpoint: per-seed paired ΔTSS (F1_seed vs F0) at the policy
    operating point through the frozen harness's paired_window on identical
    resample indices. Success needs ΔTSS >= +0.02 AND lower 95% bound > 0 in
    >= 2 of 3 seeds (F1.json success_criterion), with the co-secondary
    pre-onset episode recall "not degraded".
  * "Not degraded" (co-secondary): a seed degrades pre-onset recall only if
    the paired episode delta is negative AND its 95% CI excludes zero
    (significantly worse). Non-significant negatives are "not degraded" but
    reported in full.
  * F0 is the SINGLE frozen reference (F0.json: training NONE); the three
    seeds are F1 training replicates. Across-seed statistics therefore apply
    to F1 and to the per-seed deltas; F0 has no seed distribution.
  * Cohen's d = mean(ΔTSS across seeds) / sample std(ΔTSS across seeds,
    ddof=1) — the one-sample form against the fixed F0 reference.
  * Seed escalation (F1.json): if F1 across-seed TSS range > 0.015, escalate
    to 5 seeds BEFORE any verdict.
  * Block-size robustness: primary endpoint recomputed at block lengths
    1440/2880/5760 by runtime override of the module constant (the frozen
    harness FILE is never modified — the Sprint 24 precedent,
    artifacts/sprint24/04_bootstrap_analysis.md). 2880 is authoritative.
  * Secondary endpoints (ΔROC-AUC, ΔPR-AUC, Δepisode recall, Δpre-onset
    recall, ΔECE, Δfalse episodes/month, Δduty cycle): point deltas from the
    per-run frozen-harness eval.json records, each arm's own 95% CI reported;
    per the plan's multiple-comparisons stance none can be promoted to the
    headline claim.

Outputs: artifacts/sprint30/analysis.json (full machine-readable record).
"""
import json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import numpy as np

import scripts.sprint24.eval_framework as efm
from scripts.sprint26.eval_framework_ref import get_evaluator

RUNS = os.path.join("artifacts", "sprint30", "runs")
# Escalation (F1.json): observed 3-seed TSS range 0.0426 > 0.015 -> 5 seeds
# before any verdict. PRE-DECLARED before seeds 45/46 completed: with 5 seeds
# the success criterion extends to its stated rationale, a MAJORITY of seeds
# (>= 3 of 5) each meeting the per-seed rule (04_FAIR_ADITYA_EXPERIMENT.md:
# "three seeds is the minimum giving an across-seed range and a majority
# criterion"). Pass --seeds to select the seed set.
SEEDS = [int(s) for s in
         (sys.argv[sys.argv.index("--seeds") + 1].split(",")
          if "--seeds" in sys.argv else ["42", "43", "44"])]
MAJORITY = 2 if len(SEEDS) == 3 else (len(SEEDS) // 2 + 1)
YELLOW, RED = 0.14, 0.95
MIN_EFFECT = 0.02
SEED_RANGE_ESCALATION = 0.015


def load_probs(run_id):
    return np.load(os.path.join(RUNS, run_id, "test_cal_probs.npy"))


def strip(o):
    if isinstance(o, dict):
        return {str(k): strip(v) for k, v in o.items()
                if not (isinstance(k, str) and k.startswith("_"))}
    if isinstance(o, list): return [strip(v) for v in o]
    if isinstance(o, (np.floating, np.integer)): return o.item()
    return o


def paired_at_block(block_len, f0_probs, f1_probs_by_seed):
    """Fresh evaluator at the given block length; paired F1-vs-F0 per seed."""
    orig = efm.BLOCK_LEN
    try:
        efm.BLOCK_LEN = block_len
        base = get_evaluator()
        ev = efm.UnifiedEvaluator(base.ts, base.labels)   # fresh, new block partition
        res_f0 = ev.evaluate("F0", f0_probs, (f0_probs >= YELLOW).astype(np.int8),
                             alerts_red=(f0_probs >= RED).astype(np.int8), auc_ci=False)
        out = {}
        for seed, p in f1_probs_by_seed.items():
            res = ev.evaluate(f"F1_s{seed}", p, (p >= YELLOW).astype(np.int8),
                              alerts_red=(p >= RED).astype(np.int8), auc_ci=False)
            out[seed] = {"window": strip(ev.paired_window(res, res_f0)),
                         "episode": strip(ev.paired_episode(res, res_f0))}
        return out
    finally:
        efm.BLOCK_LEN = orig


def main():
    t0 = time.time()
    evals = {"F0": json.load(open(os.path.join(RUNS, "F0", "eval.json")))}
    for s in SEEDS:
        evals[f"F1_s{s}"] = json.load(open(os.path.join(RUNS, f"F1_s{s}", "eval.json")))

    f0_probs = load_probs("F0")
    f1_probs = {s: load_probs(f"F1_s{s}") for s in SEEDS}

    # ── primary machinery at the authoritative block length ─────────────────
    paired_2880 = paired_at_block(2880, f0_probs, f1_probs)

    # ── per-seed policy metrics from the sealed frozen-harness evals ─────────
    def pol(run):
        w = evals[run]["policy"]["window"]; e = evals[run]["policy"]["episode"]
        return {"TSS": w["TSS"], "TSS_ci": w["ci"]["TSS"],
                "ROC_AUC": w["ROC_AUC"], "PR_AUC": w["PR_AUC"], "ECE": w["ECE"],
                "Brier": w["Brier"], "HSS": w["HSS"], "MCC": w["MCC"],
                "Precision": w["Precision"], "Recall": w["Recall"],
                "episode_recall": e["episode_recall"],
                "pre_onset_recall": e["pre_onset_recall"],
                "false_episodes_per_month": e["false_episodes_per_month"],
                "lead_time_min_median": e["lead_time_min_median"],
                "duty_cycle": evals[run]["policy"]["alert_stats"]["yellow_fraction_of_time"]}
    table = {r: pol(r) for r in evals}

    # ── across-seed statistics (F1 only; F0 fixed) ───────────────────────────
    f1_tss = np.array([table[f"F1_s{s}"]["TSS"] for s in SEEDS])
    deltas = np.array([paired_2880[s]["window"]["TSS"]["delta_point"] for s in SEEDS])
    lower_bounds = np.array([paired_2880[s]["window"]["TSS"]["delta_ci95"][0] for s in SEEDS])
    seed_stats = {
        "F1_TSS_mean": float(f1_tss.mean()), "F1_TSS_std": float(f1_tss.std(ddof=1)),
        "F1_TSS_range": float(f1_tss.max() - f1_tss.min()),
        "escalation_triggered": bool(f1_tss.max() - f1_tss.min() > SEED_RANGE_ESCALATION),
        "dTSS_per_seed": deltas.tolist(),
        "dTSS_mean": float(deltas.mean()), "dTSS_std": float(deltas.std(ddof=1)),
        "cohens_d_one_sample": float(deltas.mean() / deltas.std(ddof=1))
                               if deltas.std(ddof=1) > 0 else None,
    }

    # ── success criterion (F1.json, mechanical) ──────────────────────────────
    per_seed_pass = []
    for i, s in enumerate(SEEDS):
        pre = paired_2880[s]["episode"]["pre_onset_recall"]
        degraded = pre["delta_point"] < 0 and pre["significant"]
        per_seed_pass.append({
            "seed": s, "dTSS": float(deltas[i]), "ci_lower": float(lower_bounds[i]),
            "meets_min_effect": bool(deltas[i] >= MIN_EFFECT),
            "ci_lower_positive": bool(lower_bounds[i] > 0),
            "pre_onset_degraded_significantly": bool(degraded),
            "seed_passes": bool(deltas[i] >= MIN_EFFECT and lower_bounds[i] > 0 and not degraded)})
    n_pass = sum(p["seed_passes"] for p in per_seed_pass)
    primary = {"per_seed": per_seed_pass, "n_seeds_passing": n_pass,
               "n_seeds": len(SEEDS), "majority_required": MAJORITY,
               "success": bool(n_pass >= MAJORITY), "criterion":
               f"paired dTSS >= +0.02 with lower 95% bound > 0 in >= {MAJORITY} "
               f"of {len(SEEDS)} seeds, pre-onset recall not significantly degraded"}

    # ── secondary endpoints: point deltas vs F0 (mean over seeds + per seed) ──
    sec_keys = ["ROC_AUC", "PR_AUC", "episode_recall", "pre_onset_recall",
                "ECE", "false_episodes_per_month", "duty_cycle"]
    secondary = {}
    for k in sec_keys:
        per = {s: table[f"F1_s{s}"][k] - table["F0"][k] for s in SEEDS}
        secondary[f"delta_{k}"] = {"per_seed": per,
                                   "mean": float(np.mean(list(per.values())))}

    # ── block-size robustness of the primary endpoint ────────────────────────
    robustness = {"2880": {s: paired_2880[s]["window"]["TSS"] for s in SEEDS}}
    for bl in (1440, 5760):
        pb = paired_at_block(bl, f0_probs, f1_probs)
        robustness[str(bl)] = {s: pb[s]["window"]["TSS"] for s in SEEDS}

    out = {"generated": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "policy_metrics": table, "paired_2880": paired_2880,
           "seed_stats": seed_stats, "primary_endpoint": primary,
           "secondary_endpoints": secondary, "block_robustness": robustness,
           "validation_side": {r: {"best_val_tss_training": evals[r].get("best_val_tss_training"),
                                   "checkpoint_epoch": evals[r].get("checkpoint_epoch"),
                                   "val_swept_val_tss": evals[r].get("val_swept_val_tss"),
                                   "val_calibration": evals[r].get("val_calibration")}
                               for r in evals},
           "wall_seconds": round(time.time() - t0, 1)}
    with open(os.path.join("artifacts", "sprint30", "analysis.json"), "w") as f:
        json.dump(strip(out), f, indent=1)
    print(json.dumps({"seed_stats": strip(seed_stats), "primary": strip(primary),
                      "F0_TSS": table["F0"]["TSS"]}, indent=1))
    print(f"[analyze] DONE {out['wall_seconds']}s -> artifacts/sprint30/analysis.json", flush=True)


if __name__ == "__main__":
    main()
