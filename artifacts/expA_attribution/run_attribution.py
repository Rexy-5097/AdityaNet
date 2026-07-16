"""
artifacts/expA_attribution/run_attribution.py

Experiment A — false-episode physical attribution. Executes the FROZEN
pre-registration (00_PREREGISTRATION.md, commit e7ddc0a, tag expA-prereg)
verbatim. Reads ONLY the frozen input list. Writes attribution.json.

Frozen parameters: candidate window +/-120 min; proximity window +/-360 min;
artifact threshold mean availability < 0.5; precedence 1>2>3>4>5>6; predominance
rule >50% pooled; MEDIUM if precedence exercised or overlap duration < 15 min;
LOW if availability in [0.5, 0.756] or cat-7-considered; representative example
= chronologically first per category (seed 42 first, ascending seeds).

Implementation note (deterministic data handling, conservative direction): a
catalogued event with missing end_time uses peak_time as its end (start_time if
both missing). This SHRINKS event intervals, biasing AGAINST finding overlap —
i.e., toward category 6 / H0, away from the interesting H1 finding.
"""
import hashlib, json, os, sys
sys.path.insert(0, "/Volumes/T7 Shield/Projects/AI/AdityaNet")
os.chdir("/Volumes/T7 Shield/Projects/AI/AdityaNet")

import numpy as np
import pandas as pd
from scripts.sprint24.eval_framework import _runs, _merge_runs, GAP_MIN

SEQ = 360
FROZEN_COUNTS = {42: 304, 43: 237, 44: 134, 45: 165, 46: 233}
CATALOG_SHA = "536842648c3891e59b7fb68e86b1dd720fe59c36749d5636c24b61e90bae499a"
CAND_WIN = np.timedelta64(120, "m")     # frozen +/-120 min
PROX_WIN = np.timedelta64(360, "m")     # frozen +/-360 min
AVAIL_THR = 0.5                          # frozen artifact threshold
MEDIUM_MARGIN_MIN = 15.0                 # frozen


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""): h.update(c)
    return h.hexdigest()


def main():
    # ── input integrity gate ─────────────────────────────────────────────────
    assert sha("artifacts/research/flares_full.parquet") == CATALOG_SHA, \
        "STOP: catalog SHA mismatch vs frozen pre-registration"

    # ground truth (frozen inputs 3, 5)
    tdf = pd.read_parquet("artifacts/research_v4/dataset_adi_nowcast/test.parquet",
                          columns=["timestamp", "target_6hr_binary"])
    lab = tdf["target_6hr_binary"].values[SEQ:].astype(np.int8)
    ts = tdf["timestamp"].values[SEQ:].astype("datetime64[s]")
    disc = pd.read_parquet("artifacts/research_v4/dataset_v4.1.0-s2/test.parquet",
                           columns=["solexs_available", "hel1os_available"])
    sav = disc["solexs_available"].values[SEQ:].astype(float)
    hav = disc["hel1os_available"].values[SEQ:].astype(float)

    # catalog (frozen input 4); conservative end handling per implementation note
    fl = pd.read_parquet("artifacts/research/flares_full.parquet")
    for c in ("start_time", "peak_time", "end_time"):
        fl[c] = pd.to_datetime(fl[c])
    fl = fl.dropna(subset=["start_time"]).copy()
    fl["end_eff"] = fl["end_time"].fillna(fl["peak_time"]).fillna(fl["start_time"])
    fl["cls"] = fl["flare_class"].astype(str).str[0].str.upper()
    ev_start = fl["start_time"].values.astype("datetime64[s]")
    ev_end = fl["end_eff"].values.astype("datetime64[s]")
    ev_cls = fl["cls"].values
    ev_id = fl["event_id"].astype(str).values

    label_eps = _merge_runs(_runs(lab == 1), ts, GAP_MIN)
    lab_s = ts[label_eps[:, 0]]; lab_e = ts[label_eps[:, 1]]

    def cat_of_classes(classes):
        s = set(classes)
        if s & {"M", "X"}: return 1
        if "C" in s: return 2
        if "B" in s: return 3
        return 4  # intersecting catalogued event of other/unknown class

    records = []
    for seed in (42, 43, 44, 45, 46):
        thr = json.load(open(f"artifacts/sprint33_nowcast/runs/s{seed}/operating_point.json"))["selected_threshold"]
        cal = np.load(f"artifacts/sprint33_nowcast/runs/s{seed}/test_cal_probs.npy")
        alerts = (cal >= thr)
        al_eps = _merge_runs(_runs(alerts), ts, GAP_MIN)
        a_s = ts[al_eps[:, 0]]; a_e = ts[al_eps[:, 1]]
        hit = np.zeros(len(al_eps), bool)
        for i in range(len(label_eps)):
            ov = np.where((a_s <= lab_e[i]) & (a_e >= lab_s[i]))[0]
            hit[ov] = True
        false_idx = np.where(~hit)[0]
        # Step-1 stop condition: reconstructed count must equal frozen count
        assert len(false_idx) == FROZEN_COUNTS[seed], \
            f"STOP: seed {seed} reconstructed {len(false_idx)} != frozen {FROZEN_COUNTS[seed]}"

        for k in false_idx:
            s0, e0 = a_s[k], a_e[k]
            i0, i1 = int(al_eps[k, 0]), int(al_eps[k, 1])
            mean_sav = float(sav[i0:i1 + 1].mean()); mean_hav = float(hav[i0:i1 + 1].mean())
            # Step 2: candidates within +/-120 min
            cand = np.where((ev_start <= e0 + CAND_WIN) & (ev_end >= s0 - CAND_WIN))[0]
            # Step 3: strict intersection
            inter = cand[(ev_start[cand] <= e0) & (ev_end[cand] >= s0)]
            # Step 4: timing (event start minus first-alert minute)
            timings = {ev_id[j]: float((ev_start[j] - s0) / np.timedelta64(1, "m")) for j in cand}
            # Step 5: classes of intersecting events
            inter_cls = [str(ev_cls[j]) for j in inter]
            # Step 6: proximity (+/-360, non-intersecting) — confidence only
            prox = np.where((ev_start <= e0 + PROX_WIN) & (ev_end >= s0 - PROX_WIN))[0]
            prox_nonint = [j for j in prox if j not in set(inter.tolist())]
            prox_cls = sorted({str(ev_cls[j]) for j in prox_nonint})
            # Step 7: category + precedence + confidence
            artifact = (mean_sav < AVAIL_THR) or (mean_hav < AVAIL_THR)
            explanation = None
            if len(inter):
                cat = cat_of_classes(inter_cls)
                n_groups = len({cat_of_classes([c]) for c in inter_cls})
                ov_min = min(float((min(e0, ev_end[j]) - max(s0, ev_start[j])) / np.timedelta64(1, "m"))
                             for j in inter)
                precedence_used = n_groups > 1 or artifact
                conf = "MEDIUM" if (precedence_used or ov_min < MEDIUM_MARGIN_MIN) else "HIGH"
                if conf == "HIGH" and any(c in ("M", "X") for c in prox_cls) and cat != 1:
                    conf = "MEDIUM"  # higher-class near-miss => not single-category-clean
            elif artifact:
                cat = 5
                conf = "HIGH" if not len(cand) else "MEDIUM"
            elif len(cand) == 0:
                cat = 6
                conf = "LOW" if (AVAIL_THR <= min(mean_sav, mean_hav) <= 0.756) else "HIGH"
            else:
                cat = 7   # candidate within +/-120 min but no strict intersection
                conf = "LOW"
                near = min(cand, key=lambda j: abs(timings[ev_id[j]]))
                explanation = (f"catalogued {ev_cls[near]}-class event {ev_id[near]} lies within the "
                               f"+/-120-minute candidate window (start offset {timings[ev_id[near]]:.0f} min "
                               f"from first alert) but does not strictly intersect the episode; the frozen "
                               f"inputs cannot distinguish real-activity response with catalog timing "
                               f"imprecision from a genuine false detection; a high-resolution flux "
                               f"inspection around the episode would be required.")
            records.append({"seed": seed, "ep_start": str(s0), "ep_end": str(e0),
                            "duration_min": float((e0 - s0) / np.timedelta64(1, "m") + 1.0),
                            "category": cat, "confidence": conf,
                            "intersecting_classes": inter_cls,
                            "n_candidates_120m": int(len(cand)),
                            "proximity_nonintersecting_classes": prox_cls,
                            "mean_solexs_avail": round(mean_sav, 4), "mean_hel1os_avail": round(mean_hav, 4),
                            "explanation": explanation})
        print(f"seed {seed}: {len(false_idx)} false episodes attributed", flush=True)

    # ── aggregation & frozen hypothesis rule ─────────────────────────────────
    df = pd.DataFrame(records)
    names = {1: "1_MX_overlap", 2: "2_C_overlap", 3: "3_B_overlap", 4: "4_other_catalogued",
             5: "5_instrument_artifact", 6: "6_genuine_false", 7: "7_ambiguous"}
    pooled = {names[c]: int((df.category == c).sum()) for c in names}
    total = len(df)
    pct = {k: round(100 * v / total, 2) for k, v in pooled.items()}
    per_seed = {int(s): {names[c]: int(((df.seed == s) & (df.category == c)).sum()) for c in names}
                for s in (42, 43, 44, 45, 46)}
    conf_tot = df.confidence.value_counts().to_dict()
    h1_share = (pooled["2_C_overlap"] + pooled["3_B_overlap"] + pooled["4_other_catalogued"]) / total
    h0_share = pooled["6_genuine_false"] / total
    h2_share = pooled["1_MX_overlap"] / total
    verdict = ("H1_REAL_SUBTHRESHOLD_ACTIVITY" if h1_share > 0.5 else
               "H0_GENUINE_FALSE_DETECTIONS" if h0_share > 0.5 else
               "H2_MX_ADJACENT" if h2_share > 0.5 else "MIXED")
    # frozen representative-example rule: chronologically first per category
    reps = {}
    for c in names:
        sub = df[df.category == c].sort_values(["ep_start", "seed"])
        if len(sub):
            reps[names[c]] = sub.iloc[0].to_dict()
    out = {"preregistration": "artifacts/expA_attribution/00_PREREGISTRATION.md @ e7ddc0a (expA-prereg)",
           "counts_verified_against_frozen": FROZEN_COUNTS, "total_pooled": total,
           "pooled_counts": pooled, "pooled_percent": pct, "per_seed_counts": per_seed,
           "confidence_totals": conf_tot,
           "hypothesis_shares": {"H0_cat6": round(h0_share, 4), "H1_cat234": round(h1_share, 4),
                                  "H2_cat1": round(h2_share, 4)},
           "hypothesis_verdict": verdict,
           "representative_examples": reps,
           "records": records}
    json.dump(out, open("artifacts/expA_attribution/attribution.json", "w"), indent=1, default=str)
    print(json.dumps({k: out[k] for k in ("pooled_counts", "pooled_percent", "confidence_totals",
                                           "hypothesis_shares", "hypothesis_verdict")}, indent=1))


if __name__ == "__main__":
    main()
