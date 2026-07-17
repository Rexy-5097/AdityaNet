"""
artifacts/expE_capability_ceiling/run_capability.py

Experiment E — Aditya-L1 Instrument Capability Ceiling.
Executes the FROZEN pre-registration (00_PREREGISTRATION.md, commit 58fe865
tag expE-prereg, reporting amendment r1 commit b9c8e7a tag expE-prereg-r1)
verbatim.

No machine learning. No classifier fitting. No optimisation of the regression
form. Train+validation spans only; the sealed test span is NEVER read.
Episode functions imported verbatim from the frozen Experiment C script.
"""
import hashlib, importlib.util, json, os, sys
sys.path.insert(0, "/Volumes/T7 Shield/Projects/AI/AdityaNet")
os.chdir("/Volumes/T7 Shield/Projects/AI/AdityaNet")

import numpy as np
import pandas as pd
from scipy.stats import norm
from scripts.sprint24.eval_framework import UnifiedEvaluator

# frozen ExpC episode machinery, imported verbatim (audit precedent 2026-07-17)
_spec = importlib.util.spec_from_file_location(
    "expc", "artifacts/expC_class_separation/run_class_separation.py")
XC = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(XC)                      # module level only; main() not called

OUT = "artifacts/expE_capability_ceiling"
DS = "artifacts/research_v4/dataset_v4.1.0-s2"
NDS = "artifacts/research_v4/dataset_adi_nowcast"
RUNS = "artifacts/sprint33_nowcast/runs"
SEEDS = (42, 43, 44, 45, 46)
CATALOG_SHA = "536842648c3891e59b7fb68e86b1dd720fe59c36749d5636c24b61e90bae499a"
PRED = ["log_solexs_soft", "solexs_HR_high_low", "log_hel1os_band0"]
DECADE = {"B": 1e-7, "C": 1e-6, "M": 1e-5, "X": 1e-4}
SEQ = 360
BOOT_N, BOOT_SEED = 1000, 20260717
GRID = np.round(np.arange(-7.0, -4.0 + 1e-9, 0.005), 3)
FE_BUDGET, RECALL_FLOOR, AVAIL_GATE = 5.0, 0.80, 0.80


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def decode_flux(cls_str):
    """'M2.5' -> 2.5e-5; malformed -> None (excluded, counted)."""
    s = str(cls_str).strip().upper()
    if not s or s[0] not in DECADE:
        return None
    try:
        mult = float(s[1:]) if len(s) > 1 else None
    except ValueError:
        return None
    if mult is None or not np.isfinite(mult) or mult <= 0:
        return None
    return DECADE[s[0]] * mult


def ols(X, y):
    A = np.column_stack([np.ones(len(X)), X])
    if np.linalg.matrix_rank(A) < A.shape[1]:
        raise RuntimeError("STOP (rule 4): rank-deficient design matrix")
    beta, *_ = np.linalg.lstsq(A, y, rcond=None)
    resid = y - A @ beta
    return beta, resid


def main():
    os.makedirs(OUT, exist_ok=True)

    # ── stopping rule 1: catalog SHA ─────────────────────────────────────────
    assert sha("artifacts/research/flares_full.parquet") == CATALOG_SHA, \
        "STOP (rule 1): catalog SHA mismatch"

    # ── stopping rule 3: cross-dataset provenance gate (validation split) ────
    a = pd.read_parquet(f"{DS}/validation.parquet", columns=["log_solexs_soft"])["log_solexs_soft"].values
    b = pd.read_parquet(f"{NDS}/validation.parquet", columns=["log_solexs_soft"])["log_solexs_soft"].values
    assert len(a) == len(b) and float(np.nanmax(np.abs(a - b))) <= 1e-9, \
        "STOP (rule 3): log_solexs_soft mismatch between datasets"
    del a, b

    # ── observables + availability over the analysis span (train+validation) ─
    cols = ["timestamp"] + PRED + ["solexs_available", "hel1os_available"]
    df = pd.concat([pd.read_parquet(f"{DS}/train.parquet", columns=cols),
                    pd.read_parquet(f"{DS}/validation.parquet", columns=cols)],
                   ignore_index=True)
    ts_all = df["timestamp"].values.astype("datetime64[s]")
    assert np.all(np.diff(ts_all).astype(int) > 0), "timestamps not strictly increasing"
    P = {c: df[c].values.astype(float) for c in PRED}
    SAV = df["solexs_available"].values.astype(float)
    HAV = df["hel1os_available"].values.astype(float)
    span_lo, span_hi = ts_all[0], ts_all[-1]

    # ── catalog: decode target, build per-flare window stats ─────────────────
    fl = pd.read_parquet("artifacts/research/flares_full.parquet")
    for c in ("start_time", "peak_time", "end_time"):
        fl[c] = pd.to_datetime(fl[c])
    fl = fl.dropna(subset=["start_time"]).copy()
    fl["peak_eff"] = fl["peak_time"].fillna(fl["start_time"])
    fl["cls"] = fl["flare_class"].astype(str).str.strip().str.upper().str[0]

    excl = {"outside_span": 0, "malformed_class": 0, "class_not_BCMX": 0,
            "availability_lt_0.5": 0, "nonfinite_predictor": 0}
    rows = []          # included flares for regression
    avail_audit = []   # ALL B/C/M/X flares intersecting span (no avail filter)
    for st, pk, cstr, cl in zip(fl["start_time"].values.astype("datetime64[s]"),
                                fl["peak_eff"].values.astype("datetime64[s]"),
                                fl["flare_class"].values, fl["cls"].values):
        if cl not in DECADE:
            excl["class_not_BCMX"] += 1
            continue
        w0, w1 = st - np.timedelta64(15, "m"), pk + np.timedelta64(15, "m")
        if w1 < span_lo or w0 > span_hi:
            excl["outside_span"] += 1
            continue
        F = decode_flux(cstr)
        if F is None:
            excl["malformed_class"] += 1
            continue
        i0 = int(np.searchsorted(ts_all, w0, side="left"))
        i1 = int(np.searchsorted(ts_all, w1, side="right"))
        if i1 <= i0:
            excl["outside_span"] += 1
            continue
        m_sav = float(np.nanmean(SAV[i0:i1]))
        m_hav = float(np.nanmean(HAV[i0:i1]))
        avail_audit.append((cl, m_sav, m_hav))
        if m_sav < 0.5:
            excl["availability_lt_0.5"] += 1
            continue
        with np.errstate(all="ignore"):
            px = [np.nanmax(P[c][i0:i1]) for c in PRED]
        if not all(np.isfinite(v) for v in px):
            excl["nonfinite_predictor"] += 1
            continue
        rows.append((cl, np.log10(F), *px, m_sav, m_hav,
                     str(np.datetime64(st, "D")), str(st)))

    R = pd.DataFrame(rows, columns=["cls", "y"] + PRED + ["m_sav", "m_hav", "day", "start"])
    counts = {c: int((R.cls == c).sum()) for c in "BCMX"}
    n_C, n_MX = counts["C"], counts["M"] + counts["X"]
    assert n_C >= 300 and n_MX >= 100, \
        f"STOP (rule 2): insufficient sample C={n_C} MX={n_MX}"

    # ── Primary A: single frozen OLS ─────────────────────────────────────────
    X = R[PRED].values
    y = R["y"].values
    beta, resid = ols(X, y)
    sigma = float(resid.std(ddof=X.shape[1] + 1))
    r2 = float(1.0 - resid.var() / y.var())
    diag = {"n_included": int(len(R)), "counts_by_class": counts,
            "excluded_by_reason": excl,
            "intercept_beta0": float(beta[0]),
            "slope_beta1_log_solexs_soft": float(beta[1]),
            "slope_beta2_solexs_HR_high_low": float(beta[2]),
            "slope_beta3_log_hel1os_band0": float(beta[3]),
            "R2": r2, "residual_mean": float(resid.mean()),
            "residual_SD_sigma_dex": sigma,
            "MAE_dex": float(np.abs(resid).mean()),
            "RMSE_dex": float(np.sqrt((resid ** 2).mean()))}

    # ── uncertainty: day-cluster bootstrap ───────────────────────────────────
    rng = np.random.default_rng(BOOT_SEED)
    days = R["day"].values
    uday = np.unique(days)
    idx_by_day = {d: np.where(days == d)[0] for d in uday}
    boot = []
    for _ in range(BOOT_N):
        pick = rng.choice(uday, size=len(uday), replace=True)
        idx = np.concatenate([idx_by_day[d] for d in pick])
        try:
            _, rb = ols(X[idx], y[idx])
            boot.append(float(rb.std(ddof=X.shape[1] + 1)))
        except RuntimeError:
            continue
    boot = np.array(boot)
    s_lo, s_hi = float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))
    diag["sigma_CI95"] = [s_lo, s_hi]
    diag["bootstrap"] = {"n_reps_effective": int(len(boot)), "n_days": int(len(uday)),
                         "seed": BOOT_SEED}

    # ── Primary B: availability audit (no availability filter) ───────────────
    A = pd.DataFrame(avail_audit, columns=["cls", "sav", "hav"])
    audit = {}
    for grp, mask in (("MX", A.cls.isin(["M", "X"])), ("C", A.cls == "C")):
        g = A[mask]
        audit[grp] = {"n": int(len(g)),
                      "solexs_usable": float((g.sav >= 0.5).mean()),
                      "hel1os_usable": float((g.hav >= 0.5).mean()),
                      "both": float(((g.sav >= 0.5) & (g.hav >= 0.5)).mean()),
                      "neither": float(((g.sav < 0.5) & (g.hav < 0.5)).mean())}
    h_avail_supported = bool(audit["MX"]["solexs_usable"] < AVAIL_GATE)

    # ── Primary C: FE_impl bridge over frozen validation streams ─────────────
    ev_s, ev_e, ev_c = XC.catalog()
    fx_all = np.array([decode_flux(c) or np.nan
                       for c in pd.read_parquet("artifacts/research/flares_full.parquet")
                       .dropna(subset=["start_time"])["flare_class"].values])
    lf_all = np.log10(fx_all)
    vts, vlab, _ = XC.load_split("validation")
    v_ev = UnifiedEvaluator(vts, vlab)
    months = v_ev.months

    def max_flux_over(interval_s, interval_e, classes):
        m = np.isin(ev_c, list(classes)) & (ev_s <= interval_e) & (ev_e >= interval_s)
        return float(np.nanmax(lf_all[m])) if m.any() else np.nan

    per_seed_pop = {}
    for seed in SEEDS:
        op = json.load(open(f"{RUNS}/s{seed}/operating_point.json"))
        vp = np.load(f"{RUNS}/s{seed}/val_cal_probs.npy")
        v_al = XC.episodes(vts, vp, op["selected_threshold"])
        v_cls = XC.ep_class(v_al, vts, ev_s, ev_e, ev_c)
        rec_un, _ = XC.mx_episode_recall(vts, vlab, v_al)
        # false episodes = alert episodes not overlapping any M/X LABEL episode
        a_s, a_e = vts[v_al[:, 0]], vts[v_al[:, 1]]
        hit = np.zeros(len(v_al), bool)
        det_le = []
        for (s, e) in v_ev.label_eps:
            ov = np.where((a_s <= vts[e]) & (a_e >= vts[s]))[0]
            if len(ov):
                det_le.append((vts[s], vts[e]))
                hit[ov] = True
        false_idx = np.where(~hit)[0]
        c_false = [i for i in false_idx if v_cls[i] == "C"]
        F_C = np.array([max_flux_over(vts[v_al[i, 0]], vts[v_al[i, 1]], {"C"})
                        for i in c_false])
        F_C = F_C[np.isfinite(F_C)]
        n_other = int(len(false_idx) - len(c_false))
        F_MX = np.array([max_flux_over(s, e, {"M", "X"}) for (s, e) in det_le])
        F_MX = F_MX[np.isfinite(F_MX)]
        per_seed_pop[seed] = {"rec_un": rec_un, "n_other": n_other,
                              "F_C": F_C, "F_MX": F_MX,
                              "n_false": int(len(false_idx)), "n_C_false": int(len(c_false))}

    def fe_impl(sig):
        vals = []
        for seed in SEEDS:
            p = per_seed_pop[seed]
            keepC = norm.cdf((p["F_C"][None, :] - GRID[:, None]) / sig).sum(axis=1)
            keepM = norm.cdf((p["F_MX"][None, :] - GRID[:, None]) / sig).mean(axis=1)
            rec = p["rec_un"] * keepM
            fe = (p["n_other"] + keepC) / months
            ok = rec >= RECALL_FLOOR
            vals.append(float(fe[ok].min()) if ok.any() else float("inf"))
        return float(np.mean(vals)), [round(v, 3) for v in vals]

    fe_hat, fe_hat_seeds = fe_impl(sigma)
    fe_lo, fe_lo_seeds = fe_impl(s_lo)
    fe_hi, fe_hi_seeds = fe_impl(s_hi)
    assert fe_lo <= fe_hat <= fe_hi, "STOP (rule 5): FE_impl not monotone in sigma"

    # ── frozen decision rule ─────────────────────────────────────────────────
    if h_avail_supported:
        outcome, decision = "GATE0_AVAILABILITY", "does_not_support_further_modelling"
    elif fe_hi <= FE_BUDGET:
        outcome, decision = "A", "supports_further_modelling"
    elif fe_lo > FE_BUDGET:
        outcome, decision = "B", "does_not_support_further_modelling"
    else:
        outcome, decision = "C", "inconclusive"

    # ── secondaries (EXPLORATORY; cannot change the primary) ─────────────────
    sec = {}
    q = np.quantile(y, [0.25, 0.5, 0.75])
    sec["residual_SD_by_flux_quartile"] = [
        float(resid[(y <= q[0])].std()), float(resid[(y > q[0]) & (y <= q[1])].std()),
        float(resid[(y > q[1]) & (y <= q[2])].std()), float(resid[(y > q[2])].std())]
    sec["residual_mean_SD_by_class"] = {
        c: [float(resid[R.cls == c].mean()), float(resid[R.cls == c].std())]
        for c in "BCMX" if (R.cls == c).any()}
    sec["residual_SD_boundary_local_C4_to_M4"] = float(
        resid[(y >= np.log10(4e-6)) & (y <= np.log10(4e-5))].std())
    sec["residual_SD_hel1os_usable_vs_not"] = [
        float(resid[R.m_hav >= 0.5].std()), float(resid[R.m_hav < 0.5].std())]
    sec["residual_corr_with_solexs_avail"] = float(np.corrcoef(R.m_sav, resid)[0, 1])
    t_ord = np.argsort(R["start"].values)
    half = len(t_ord) // 2
    sec["residual_SD_first_vs_second_half"] = [
        float(resid[t_ord[:half]].std()), float(resid[t_ord[half:]].std())]
    _, resid_uni = ols(X[:, :1], y)
    sec["sigma_univariate_solexs_only"] = float(resid_uni.std(ddof=2))
    aucs = []
    for seed in SEEDS:
        p = per_seed_pop[seed]
        d = p["F_MX"][:, None] - p["F_C"][None, :]
        aucs.append(float(norm.cdf(d / (sigma * np.sqrt(2))).mean()))
    sec["implied_max_class_AUC_at_sigma_hat"] = {"per_seed": [round(a, 4) for a in aucs],
                                                 "mean": float(np.mean(aucs))}
    # missed M/X label episodes vs availability (validation, frozen streams)
    vav = pd.read_parquet(f"{DS}/validation.parquet", columns=["solexs_available"])
    vsav = vav["solexs_available"].values[SEQ:].astype(float)
    missed_low = []
    for seed in SEEDS:
        op = json.load(open(f"{RUNS}/s{seed}/operating_point.json"))
        vp = np.load(f"{RUNS}/s{seed}/val_cal_probs.npy")
        v_al = XC.episodes(vts, vp, op["selected_threshold"])
        a_s, a_e = vts[v_al[:, 0]], vts[v_al[:, 1]]
        n_missed = n_low = 0
        for (s, e) in v_ev.label_eps:
            if not np.any((a_s <= vts[e]) & (a_e >= vts[s])):
                n_missed += 1
                if np.nanmean(vsav[s:e + 1]) < 0.5:
                    n_low += 1
        missed_low.append((n_missed, n_low))
    sec["missed_MX_label_eps__n_and_lowavail"] = missed_low

    out = {"preregistration": "00_PREREGISTRATION.md @ 58fe865 (expE-prereg) + r1 @ b9c8e7a",
           "layer1_measurements": {"regression": diag, "availability_audit": audit},
           "layer2_bridge_HYPOTHESIS": {
               "assumptions": "S14 (i)-(vi): Gaussian homoscedastic; independent; "
                              "real method achieves exactly sigma; window-to-episode "
                              "transfer; one decision per label episode; non-C false retained",
               "FE_impl_sigma_hat": fe_hat, "FE_impl_sigma_lo": fe_lo,
               "FE_impl_sigma_hi": fe_hi,
               "per_seed": {"hat": fe_hat_seeds, "lo": fe_lo_seeds, "hi": fe_hi_seeds},
               "population_sizes": {s: {k: (int(v) if isinstance(v, (int, np.integer))
                                            else len(v) if isinstance(v, np.ndarray) else v)
                                        for k, v in per_seed_pop[s].items() if k != "rec_un"}
                                    | {"rec_un": round(per_seed_pop[s]["rec_un"], 4)}
                                    for s in SEEDS}},
           "layer3_interpretation": {"H_availability_supported": h_avail_supported,
                                     "outcome": outcome},
           "layer4_decision": decision,
           "secondaries_EXPLORATORY": sec}
    json.dump(out, open(f"{OUT}/capability.json", "w"), indent=1)

    print(f"sigma = {sigma:.4f} dex  CI95 [{s_lo:.4f}, {s_hi:.4f}]  R2={r2:.4f}")
    print(f"included n={len(R)} {counts} | excluded {excl}")
    print(f"availability MX: {audit['MX']} | gate0 supported={h_avail_supported}")
    print(f"FE_impl: hat={fe_hat:.3f} lo={fe_lo:.3f} hi={fe_hi:.3f} (budget {FE_BUDGET})")
    print(f"OUTCOME {outcome} -> {decision}")
    print(f"implied max class AUC @ sigma_hat: {sec['implied_max_class_AUC_at_sigma_hat']['mean']:.4f}")
    print(f"boundary-local sigma (C4-M4): {sec['residual_SD_boundary_local_C4_to_M4']:.4f}")
    print(f"sigma by flux quartile: {[round(v,4) for v in sec['residual_SD_by_flux_quartile']]}")


if __name__ == "__main__":
    main()
