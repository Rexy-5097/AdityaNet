"""
artifacts/expD_probe/run_probe.py

VALIDATION-ONLY diagnostic: does the frozen nowcaster's learned representation
carry class-discriminative (C vs M/X) information beyond what its detection head
exposes and beyond the hand-engineered observables?

Touches NO test data. Changes NO frozen verdict. Frozen encoder is used for
inference only (no training of the encoder). All fitting/evaluation is on the
VALIDATION split with an internal chronological split so the probe is scored
out-of-sample within validation.

Baselines compared on the identical validation alert-episode population:
  B1  detector's own calibrated probability (the current readout, 1 direction)
  B2  the 10 hand-engineered episode-peak observables (Experiment C: test AUC 0.8745)
  P1  linear probe on the frozen 128-d CLS embedding
  P2  small nonlinear probe (MLP) on the same embedding  [run only if asked]
"""
import json, os, sys
sys.path.insert(0, "/Volumes/T7 Shield/Projects/AI/AdityaNet")
os.chdir("/Volumes/T7 Shield/Projects/AI/AdityaNet")

import numpy as np
import pandas as pd
import torch
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import roc_auc_score

from app.services.ml.model import PatchTST, PatchEmbedding, PositionalEncoding
from app.services.ml.dataset import SolarFlareWindowDataset, make_eval_loader
from scripts.sprint24.eval_framework import _runs, _merge_runs, GAP_MIN

SEQ = 360
NDS = "artifacts/research_v4/dataset_adi_nowcast"
RUNS = "artifacts/sprint33_nowcast/runs"
SEEDS = (42, 43, 44, 45, 46)
OBS = ["log_solexs_soft", "solexs_peak_30m", "solexs_HR_high_low", "solexs_HR_mid_low",
       "solexs_HR_peak_60m", "log_hel1os_band0", "hel1os_fluence_30m",
       "hel1os_fluence_60m", "nonthermal_thermal_ratio"]
FEATS = json.load(open(f"{NDS}/feature_columns_15.json"))
RUN_NONLINEAR = "--nonlinear" in sys.argv


@torch.no_grad()
def cls_embeddings(model, parquet, device, tag):
    """Frozen encoder forward pass -> 128-d CLS embedding per window (pre-head)."""
    ds = SolarFlareWindowDataset(parquet, feature_cols=FEATS, split_name=tag)
    loader = make_eval_loader(ds, batch_size=512, num_workers=0, shuffle=False)
    out = []
    model.eval()
    for X, _ in loader:
        x = X.to(device)
        B = x.size(0)
        h = model.patch_embed(x)
        cls = model.cls_token.expand(B, -1, -1)
        h = torch.cat([cls, h], dim=1)
        h = model.pos_enc(h)
        for layer in model.encoder_layers:
            h, _ = layer(h, return_attn=False)
        h = model.norm(h)
        out.append(h[:, 0, :].cpu().numpy())   # CLS token, pre-head
    return np.concatenate(out)


def episode_class(al, ts, ev_s, ev_e, ev_c):
    lab = []
    for (s, e) in al:
        s0, e0 = ts[s], ts[e]
        inter = np.where((ev_s <= e0) & (ev_e >= s0))[0]
        cl = {str(ev_c[j]) for j in inter}
        lab.append("MX" if (cl & {"M", "X"}) else ("C" if "C" in cl else "other"))
    return np.array(lab)


def main():
    os.makedirs("artifacts/expD_probe", exist_ok=True)
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")

    # catalog (ground truth for episode class; same rule as Experiment A)
    fl = pd.read_parquet("artifacts/research/flares_full.parquet")
    for c in ("start_time", "peak_time", "end_time"):
        fl[c] = pd.to_datetime(fl[c])
    fl = fl.dropna(subset=["start_time"]).copy()
    fl["end_eff"] = fl["end_time"].fillna(fl["peak_time"]).fillna(fl["start_time"])
    fl["cls"] = fl["flare_class"].astype(str).str[0].str.upper()
    ev_s = fl["start_time"].values.astype("datetime64[s]")
    ev_e = fl["end_eff"].values.astype("datetime64[s]")
    ev_c = fl["cls"].values

    vdf = pd.read_parquet(f"{NDS}/validation.parquet", columns=["timestamp"] + OBS)
    vts = vdf["timestamp"].values[SEQ:].astype("datetime64[s]")
    vobs = {c: vdf[c].values[SEQ:].astype(float) for c in OBS}

    results = {}
    for seed in SEEDS:
        op = json.load(open(f"{RUNS}/s{seed}/operating_point.json"))
        thr = op["selected_threshold"]
        vp = np.load(f"{RUNS}/s{seed}/val_cal_probs.npy")
        al = _merge_runs(_runs(vp >= thr), vts, GAP_MIN)
        cls = episode_class(al, vts, ev_s, ev_e, ev_c)
        keep = np.isin(cls, ["MX", "C"])
        al_k = al[keep]; y = (cls[keep] == "MX").astype(int)
        if y.sum() < 5 or (1 - y).sum() < 5:
            results[seed] = {"SKIP": "insufficient episodes"}; continue

        ck = torch.load(f"artifacts/sprint33/runs/NC_s{seed}/best.pt", map_location="cpu", weights_only=True)
        model = PatchTST(n_features=15); model.load_state_dict(ck["model"]); model.to(device)
        emb = cls_embeddings(model, f"{NDS}/validation.parquet", device, f"probe_s{seed}")

        # episode-level aggregation: mean CLS embedding over the episode's windows
        E = np.stack([emb[s:e + 1].mean(axis=0) for (s, e) in al_k])
        # baselines on the identical population
        B1 = np.array([vp[s:e + 1].max() for (s, e) in al_k])                      # detector probability
        B2 = np.stack([[vobs[c][s:e + 1].max() for c in OBS] +
                       [float((vts[e] - vts[s]) / np.timedelta64(1, "m") + 1.0)] for (s, e) in al_k])

        # chronological split WITHIN validation: fit on first 70%, score on last 30%
        order = np.argsort([s for (s, e) in al_k]); n = len(order); cut = int(0.7 * n)
        tr, te = order[:cut], order[cut:]
        if y[te].sum() < 3 or (1 - y[te]).sum() < 3:
            results[seed] = {"SKIP": "insufficient holdout episodes"}; continue

        def fit_score(X, nonlinear=False):
            mu, sd = X[tr].mean(0), X[tr].std(0); sd[sd == 0] = 1.0
            Xs = (X - mu) / sd
            if nonlinear:
                m = MLPClassifier(hidden_layer_sizes=(32,), alpha=1.0, max_iter=3000, random_state=seed)
            else:
                m = LogisticRegression(C=1.0, max_iter=5000)
            m.fit(Xs[tr], y[tr])
            return float(roc_auc_score(y[te], m.predict_proba(Xs[te])[:, 1]))

        row = {"n_episodes": int(n), "n_mx": int(y.sum()), "n_c": int((1 - y).sum()),
               "n_holdout": int(len(te)),
               "B1_detector_prob_auc": float(roc_auc_score(y[te], B1[te])),
               "B2_observables_auc": fit_score(B2),
               "P1_linear_probe_emb_auc": fit_score(E)}
        if RUN_NONLINEAR:
            row["P2_nonlinear_probe_emb_auc"] = fit_score(E, nonlinear=True)
        results[seed] = row
        print(f"s{seed}: n={n} (MX={row['n_mx']}, C={row['n_c']}, holdout={row['n_holdout']}) | "
              f"B1 detector={row['B1_detector_prob_auc']:.4f} | B2 observables={row['B2_observables_auc']:.4f} | "
              f"P1 linear-probe={row['P1_linear_probe_emb_auc']:.4f}"
              + (f" | P2 nonlinear={row['P2_nonlinear_probe_emb_auc']:.4f}" if RUN_NONLINEAR else ""), flush=True)

    ok = [s for s in SEEDS if "SKIP" not in results[s]]
    agg = {k: round(float(np.mean([results[s][k] for s in ok])), 4)
           for k in ("B1_detector_prob_auc", "B2_observables_auc", "P1_linear_probe_emb_auc")
           }
    if RUN_NONLINEAR:
        agg["P2_nonlinear_probe_emb_auc"] = round(float(np.mean([results[s]["P2_nonlinear_probe_emb_auc"] for s in ok])), 4)
    agg["linear_gain_over_observables"] = round(agg["P1_linear_probe_emb_auc"] - agg["B2_observables_auc"], 4)
    agg["linear_gain_over_detector"] = round(agg["P1_linear_probe_emb_auc"] - agg["B1_detector_prob_auc"], 4)
    out = {"scope": "VALIDATION ONLY — no test data touched, no frozen verdict affected",
           "per_seed": results, "aggregate": agg}
    json.dump(out, open("artifacts/expD_probe/probe_validation.json", "w"), indent=1)
    print(json.dumps(agg, indent=1))


if __name__ == "__main__":
    main()
