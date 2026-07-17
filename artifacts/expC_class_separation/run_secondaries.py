"""
artifacts/expC_class_separation/run_secondaries.py

Experiment C mandatory secondary endpoints (frozen pre-registration bbd99a2):
per-class episode recall (M, X, C, B) of the frozen ungated detector, and
false-episodes-per-month under alternative label definitions (M/X-only, >=C,
all-flare). Reported prominently; CANNOT override the primary verdict.

Frozen episode streams only; no model inference; no retraining.
"""
import json, os, sys
sys.path.insert(0, "/Volumes/T7 Shield/Projects/AI/AdityaNet")
os.chdir("/Volumes/T7 Shield/Projects/AI/AdityaNet")

import numpy as np
import pandas as pd
from scripts.sprint24.eval_framework import UnifiedEvaluator, _runs, _merge_runs, GAP_MIN

SEQ = 360
NDS = "artifacts/research_v4/dataset_adi_nowcast"
RUNS = "artifacts/sprint33_nowcast/runs"
SEEDS = (42, 43, 44, 45, 46)

df = pd.read_parquet(f"{NDS}/test.parquet", columns=["timestamp", "target_6hr_binary"])
ts = df["timestamp"].values[SEQ:].astype("datetime64[s]")
lab_mx = df["target_6hr_binary"].values[SEQ:].astype(np.int8)
months = UnifiedEvaluator(ts, lab_mx).months

fl = pd.read_parquet("artifacts/research/flares_full.parquet")
for c in ("start_time", "peak_time", "end_time"):
    fl[c] = pd.to_datetime(fl[c])
fl = fl.dropna(subset=["start_time"]).copy()
fl["end_eff"] = fl["end_time"].fillna(fl["peak_time"]).fillna(fl["start_time"])
fl["cls"] = fl["flare_class"].astype(str).str[0].str.upper()
span = (fl["start_time"].values.astype("datetime64[s]") >= ts[0]) & \
       (fl["start_time"].values.astype("datetime64[s]") <= ts[-1])
fl = fl[span]
ES = fl["start_time"].values.astype("datetime64[s]")
EE = fl["end_eff"].values.astype("datetime64[s]")
EC = fl["cls"].values


def rise_label(classes):
    """per-window label: window-end minute within [start, peak] of a flare in `classes`"""
    m = np.isin(EC, list(classes))
    s = ES[m]; p = fl["peak_time"].values.astype("datetime64[s]")[m]
    order = np.argsort(s); s = s[order]; p = p[order]
    idx = np.searchsorted(s, ts, side="right") - 1
    out = np.zeros(len(ts), dtype=np.int8); v = idx >= 0
    out[v] = (ts[v] <= p[idx[v]]).astype(np.int8)
    return out


def alerts_for(seed):
    op = json.load(open(f"{RUNS}/s{seed}/operating_point.json"))
    p = np.load(f"{RUNS}/s{seed}/test_cal_probs.npy")
    return _merge_runs(_runs(p >= op["selected_threshold"]), ts, GAP_MIN)


def recall_and_false(al, lab):
    ev = UnifiedEvaluator(ts, lab)
    if len(al) == 0 or len(ev.label_eps) == 0: return 0.0, 0.0, 0
    a_s = ts[al[:, 0]]; a_e = ts[al[:, 1]]
    hit = np.zeros(len(al), bool); det = 0
    for (s, e) in ev.label_eps:
        ov = np.where((a_s <= ts[e]) & (a_e >= ts[s]))[0]
        if len(ov): det += 1; hit[ov] = True
    n_false = int((~hit).sum())
    return det / len(ev.label_eps), n_false / months, len(ev.label_eps)


out = {"months": months, "per_seed": {}}
labels = {"MX_only": rise_label({"M", "X"}), "geC": rise_label({"C", "M", "X"}),
          "all_flare": rise_label({"B", "C", "M", "X"})}
per_class = {c: rise_label({c}) for c in ("M", "X", "C", "B")}

for seed in SEEDS:
    al = alerts_for(seed)
    row = {"n_alert_episodes": int(len(al))}
    for name, lab in labels.items():
        r, fe, n_ep = recall_and_false(al, lab)
        row[f"{name}_recall"] = round(r, 4); row[f"{name}_fe_per_month"] = round(fe, 2)
        row[f"{name}_n_label_episodes"] = n_ep
        row[f"{name}_passes_budget"] = bool(fe <= 5.0 and r >= 0.80)
    for c, lab in per_class.items():
        r, _, n_ep = recall_and_false(al, lab)
        row[f"recall_{c}_class"] = round(r, 4); row[f"n_{c}_episodes"] = n_ep
    out["per_seed"][seed] = row
    print(f"s{seed}: MX rec={row['MX_only_recall']} FE={row['MX_only_fe_per_month']} | "
          f">=C rec={row['geC_recall']} FE={row['geC_fe_per_month']} pass={row['geC_passes_budget']} | "
          f"all rec={row['all_flare_recall']} FE={row['all_flare_fe_per_month']} pass={row['all_flare_passes_budget']} | "
          f"per-class M={row['recall_M_class']} X={row['recall_X_class']} C={row['recall_C_class']} B={row['recall_B_class']}", flush=True)

agg = {}
for k in ("MX_only", "geC", "all_flare"):
    agg[k] = {"mean_recall": round(float(np.mean([out["per_seed"][s][f"{k}_recall"] for s in SEEDS])), 4),
              "mean_fe_per_month": round(float(np.mean([out["per_seed"][s][f"{k}_fe_per_month"] for s in SEEDS])), 2),
              "n_seeds_passing_budget": int(sum(out["per_seed"][s][f"{k}_passes_budget"] for s in SEEDS))}
for c in ("M", "X", "C", "B"):
    agg[f"recall_{c}_class_mean"] = round(float(np.mean([out["per_seed"][s][f"recall_{c}_class"] for s in SEEDS])), 4)
out["aggregate"] = agg
json.dump(out, open("artifacts/expC_class_separation/secondaries.json", "w"), indent=1)
print(json.dumps(agg, indent=1))
