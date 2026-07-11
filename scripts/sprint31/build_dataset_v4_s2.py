"""
scripts/sprint31/build_dataset_v4_s2.py

Sprint 31 Phase 1 — build dataset_v4.1.0-s2: the F2 arm's 32-feature + 4
disclosure-channel dataset on the frozen Stage-2 split boundaries. Traceability:

  * Split boundaries: artifacts/sprint14c/s2_{train,val,test}.parquet timestamps
    and targets copied and verified identical (03_DATASET_PIPELINE_V4.md §8).
  * Missing data (§2): instrument channels set NaN where the builder's
    per-minute mask is 0 (the raw parquets zero-fill those minutes — the
    Sprint 27 out-of-manifold defect this pipeline exists to fix), then
    apply_gap_policy (ffill <= 15 min); longer gaps stay NaN for neutral
    imputation in normalized space (§6 step 4).
  * Availability/staleness channels (§1, §3): per Aditya instrument, binary
    available_t (observed, not filled) and staleness_t/60 appended as MODEL
    INPUT channels. FLAGGED INTERPRETATION (conservative): §3 says "per
    instrument, two per-timestep channels appended to the model input"; §2
    says GOES handling stays V1-unchanged for baseline comparability, so the
    channels are appended for SoLEXS and HEL1OS only -> model width
    32 + 4 = 36. The 32 "Version 4 model inputs" of 02_FEATURE_PIPELINE_V4.md
    are the scaled features; the 4 disclosure channels carry the §3-specified
    normalization (binary; staleness/60) and are NOT robust-scaled.
  * Features (02_FEATURE_PIPELINE_V4.md): GOES 17 (14 KEEP raw columns +
    goes_T_iso/goes_EM/goes_dT_iso_15m computed on raw fluxes), SoLEXS 10
    (rows 4-13), HEL1OS 5 (rows 14-17 + log_hel1os_band0). Rows 12-13 use the
    train-split-only 95th percentile of log_solexs_soft (observed minutes),
    computed here in the dataset layer and passed as a frozen parameter
    (ADR-0001 stateless-feature rule).
  * Scaling (§6): RobustScaler fit on s2_train only over the 32 features.
  * Side product: s2_test_f1feats.parquet / s2_val_f1feats.parquet — the 17
    GOES features on the S2 splits transformed with the ORIGINAL
    dataset_v4.0.0 scaler (the F1 models' frozen input space) for the
    same-span F1-on-S2 re-evaluation required by 04_FAIR_ADITYA_EXPERIMENT.md.

Output: artifacts/research_v4/dataset_v4.1.0-s2/
"""

import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import numpy as np
import pandas as pd

from app.services.ml.features_v4.framework import FeatureSet
from app.services.ml.features_v4.goes_physics import GoesTIso, GoesEM, GoesDTIso15m
from app.services.ml.features_v4.aditya import aditya_features
from app.services.ml.dataset_v4.scaling import RobustScaler, TrainOnlyViolation
from app.services.ml.dataset_v4.masks import apply_gap_policy
from app.services.ml.dataset_v4.manifest import build_manifest, verify_manifest, ManifestError

SRC = {"train": "artifacts/sprint14c/s2_train.parquet",
       "validation": "artifacts/sprint14c/s2_val.parquet",
       "test": "artifacts/sprint14c/s2_test.parquet"}
OUT_DIR = os.path.join("artifacts", "research_v4", "dataset_v4.1.0-s2")
GOES14 = json.load(open(os.path.join("artifacts", "feature_columns.json")))
TARGETS = ["target_6hr_binary", "target_6hr_class"]
SOLEXS_CH = [f"solexs_rate_ch{i}" for i in range(1, 10)]
HEL1OS_CH = ["hel1os_rate_band0"]
DISCLOSURE = ["solexs_available", "solexs_staleness_n",
              "hel1os_available", "hel1os_staleness_n"]


def df_hash(df):
    return hashlib.sha256(pd.util.hash_pandas_object(df, index=False).values.tobytes()).hexdigest()


def prepare_split(path):
    """Load a frozen S2 split; NaN-out masked minutes; apply the §2 gap policy."""
    cols = ["timestamp"] + GOES14 + TARGETS + SOLEXS_CH + HEL1OS_CH + ["mask_solexs", "mask_hel1os"]
    df = pd.read_parquet(path, columns=cols).reset_index(drop=True)
    filled = df.copy()
    stats = {}
    for inst, chans, mcol in (("solexs", SOLEXS_CH, "mask_solexs"),
                              ("hel1os", HEL1OS_CH, "mask_hel1os")):
        observed = df[mcol].to_numpy() >= 0.5
        for c in chans:
            filled[c] = df[c].where(observed)          # zero-filled garbage -> NaN
        f0, m0, s0 = apply_gap_policy(filled[chans[0]])
        for c in chans:                                 # shared mask => shared fill index
            filled[c] = filled[c].ffill(limit=15)
        filled[f"{inst}_available"] = m0.astype(np.int8)
        filled[f"{inst}_staleness_n"] = (s0.to_numpy() / 60.0).astype(np.float32)
        post_avail = filled[chans[0]].notna()
        stats[inst] = {"observed_fraction": float(observed.mean()),
                       "post_ffill_available_fraction": float(post_avail.mean()),
                       "long_gap_nan_fraction": float(1 - post_avail.mean()),
                       "mean_staleness_min": float(s0.mean())}
    return filled, stats


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    report = {"dataset_version": "dataset_v4.1.0-s2", "splits": {}, "checks": {}}

    frames, stats_all = {}, {}
    for split, path in SRC.items():
        frames[split], stats_all[split] = prepare_split(path)
        print(f"[build] {split}: rows={len(frames[split]):,} "
              f"solexs_obs={stats_all[split]['solexs']['observed_fraction']:.4f} "
              f"hel1os_obs={stats_all[split]['hel1os']['observed_fraction']:.4f}", flush=True)

    # train-only activity threshold (rows 12-13), observed minutes only
    tr = frames["train"]
    soft_train = np.log1p(tr.loc[tr["solexs_available"] == 1, SOLEXS_CH].sum(axis=1))
    train_p95 = float(np.percentile(soft_train.dropna(), 95))
    print(f"[build] train_p95(log_solexs_soft, observed)={train_p95:.6f}", flush=True)

    goes_fs = FeatureSet([GoesTIso(), GoesEM(), GoesDTIso15m()])
    adit_fs = FeatureSet(aditya_features(train_p95))

    raw32, passthru = {}, {}
    feat_prov = {}
    det_hashes = []
    for split in SRC:
        df = frames[split]
        gphys, prov_g = goes_fs.compute_all(df)
        adit, prov_a = adit_fs.compute_all(df)
        if split == "validation":
            adit2, _ = adit_fs.compute_all(df)
            det_hashes = [df_hash(adit), df_hash(adit2)]
        feats = pd.concat([df[GOES14].reset_index(drop=True),
                           gphys.reset_index(drop=True),
                           adit.reset_index(drop=True)], axis=1)
        raw32[split] = feats
        passthru[split] = df[["timestamp"] + TARGETS + DISCLOSURE].reset_index(drop=True)
        feat_prov = {"goes_physics": prov_g, "aditya": prov_a}
        report["splits"][split] = {
            "rows": int(len(df)), "positives": int(df["target_6hr_binary"].sum()),
            "instrument_stats": stats_all[split],
            "nan_pre_scaling": {c: int(feats[c].isna().sum()) for c in feats.columns
                                if feats[c].isna().any()}}

    features_32 = list(raw32["train"].columns)
    assert len(features_32) == 32, f"expected 32 features, got {len(features_32)}"

    scaler = RobustScaler().fit(raw32["train"], split_name="train")
    try:
        RobustScaler().fit(raw32["validation"], split_name="validation")
        report["checks"]["train_only_guard"] = "FAIL"
    except TrainOnlyViolation:
        report["checks"]["train_only_guard"] = "PASS (TrainOnlyViolation raised)"

    for split in SRC:
        scaled = scaler.transform(raw32[split])
        n_nan = int(scaled.isna().sum().sum())
        scaled = scaled.fillna(0.0)                     # §6 step 4 neutral imputation
        out = pd.concat([passthru[split][["timestamp"]],
                         scaled.astype(np.float32),
                         passthru[split][DISCLOSURE].astype(np.float32),
                         passthru[split][TARGETS]], axis=1)
        out.to_parquet(os.path.join(OUT_DIR, f"{split}.parquet"), index=False)
        report["splits"][split]["imputed_neutral_values"] = n_nan
        report["splits"][split]["imputed_fraction_of_feature_cells"] = round(
            n_nan / (len(scaled) * 32), 6)
        print(f"[build] {split}: written ({n_nan:,} neutral-imputed cells)", flush=True)

    features_36 = features_32 + DISCLOSURE
    json.dump(features_36, open(os.path.join(OUT_DIR, "feature_columns_36.json"), "w"), indent=1)

    # ── F1-on-S2 side product: GOES 17 in the F1 models' frozen input space ──
    v400 = json.load(open("artifacts/research_v4/dataset_v4.0.0/manifest.json"))
    f1_scaler = RobustScaler.from_params(v400["scaler_params"])
    f1_cols = v400["feature_list"]
    for split, tag in (("validation", "s2_val_f1feats"), ("test", "s2_test_f1feats")):
        df = frames[split]
        gphys, _ = goes_fs.compute_all(df)
        f17 = pd.concat([df[GOES14].reset_index(drop=True), gphys.reset_index(drop=True)], axis=1)
        f17 = f1_scaler.transform(f17[f1_cols]).fillna(0.0)
        out = pd.concat([passthru[split][["timestamp"]], f17.astype(np.float32),
                         passthru[split][TARGETS]], axis=1)
        out.to_parquet(os.path.join(OUT_DIR, f"{tag}.parquet"), index=False)
    report["f1_on_s2_side_product"] = "17 GOES features scaled with dataset_v4.0.0 scaler (F1 frozen input space)"

    # ── validations ──────────────────────────────────────────────────────────
    ck = report["checks"]
    for split, path in SRC.items():
        ref = pd.read_parquet(path, columns=["timestamp"] + TARGETS)
        new = pd.read_parquet(os.path.join(OUT_DIR, f"{split}.parquet"),
                              columns=["timestamp"] + TARGETS)
        ck[f"{split}_timestamps_identical"] = bool(
            np.array_equal(ref["timestamp"].values, new["timestamp"].values))
        ck[f"{split}_targets_identical"] = bool(np.array_equal(ref[TARGETS].values, new[TARGETS].values))
    b = {s: (frames[s]["timestamp"].min(), frames[s]["timestamp"].max()) for s in SRC}
    ck["chronological_no_overlap"] = bool(
        b["train"][1] < b["validation"][0] < b["validation"][1] < b["test"][0])
    report["split_boundaries"] = {s: [str(x[0]), str(x[1])] for s, x in b.items()}

    trs = pd.read_parquet(os.path.join(OUT_DIR, "train.parquet"), columns=features_32)
    med, q1, q3 = trs.median(), trs.quantile(0.25), trs.quantile(0.75)
    sp = scaler.to_params()["columns"]
    degenerate = [c for c in features_32 if sp[c]["iqr"] == 1.0
                  and float(raw32["train"][c].quantile(0.75) - raw32["train"][c].quantile(0.25)) == 0.0]
    nondeg = [c for c in features_32 if c not in degenerate]
    # median-zero holds only for columns without mass imputation at 0; check on
    # nondegenerate, low-imputation columns; report the rest descriptively
    low_imp = [c for c in nondeg if report["splits"]["train"]["nan_pre_scaling"].get(c, 0)
               < 0.25 * len(trs)]
    ck["train_post_scale_median_zero_low_imputation_cols"] = bool(
        (med[low_imp].abs() < 0.02).all())
    ck["train_post_scale_iqr_one_nondegenerate_low_imputation"] = bool(
        (((q3 - q1)[low_imp] - 1.0).abs() < 0.25).all())
    report["degenerate_iqr_features"] = degenerate
    report["train_post_scale_stats"] = {c: {"median": float(med[c]),
                                            "iqr": float(q3[c] - q1[c]),
                                            "min": float(trs[c].min()),
                                            "max": float(trs[c].max())} for c in features_32}

    # physical-range checks on raw (pre-scaling) observed values, train split
    r = raw32["train"]
    ck["hr_ratios_positive"] = bool((r["solexs_HR_high_low"].dropna() >= 0).all()
                                    and (r["solexs_HR_mid_low"].dropna() >= 0).all())
    ck["active_fraction_in_01"] = bool(r["solexs_active_fraction_6h"].dropna().between(0, 1).all())
    ck["minutes_since_active_in_cap"] = bool(
        r["minutes_since_solexs_active"].dropna().between(0, 10080).all())
    ck["fluences_nonnegative"] = bool((r["hel1os_fluence_30m"].dropna() >= 0).all()
                                      and (r["hel1os_fluence_60m"].dropna() >= 0).all())
    ck["disclosure_channels_in_01"] = bool(all(
        pd.read_parquet(os.path.join(OUT_DIR, s + ".parquet"), columns=DISCLOSURE)
        .apply(lambda col: col.between(0, 1).all()).all() for s in SRC))
    ck["aditya_features_deterministic"] = det_hashes[0] == det_hashes[1]

    manifest = build_manifest(
        dataset_version="dataset_v4.1.0-s2",
        generator_script=os.path.join("scripts", "sprint31", "build_dataset_v4_s2.py"),
        source_files=list(SRC.values()) + [
            "app/services/ml/features_v4/aditya.py",
            "app/services/ml/features_v4/goes_physics.py",
            "app/services/ml/features_v4/framework.py",
            "app/services/ml/dataset_v4/scaling.py",
            "app/services/ml/dataset_v4/masks.py",
            "artifacts/feature_columns.json"],
        split_counts={s: {"rows": report["splits"][s]["rows"],
                          "positives": report["splits"][s]["positives"]} for s in SRC},
        scaler_params=scaler.to_params(),
        feature_list=features_36)
    json.dump(manifest, open(os.path.join(OUT_DIR, "manifest.json"), "w"), indent=1)
    verify_manifest(json.load(open(os.path.join(OUT_DIR, "manifest.json"))))
    ck["manifest_verify_roundtrip"] = True
    tam = json.loads(json.dumps(manifest)); tam["scaler_params"]["fitted_on_split"] = "test"
    try:
        verify_manifest(tam); ck["manifest_tamper_detected"] = False
    except ManifestError:
        ck["manifest_tamper_detected"] = True

    feat_prov["train_p95_log_solexs_soft"] = train_p95
    json.dump(feat_prov, open(os.path.join(OUT_DIR, "features_provenance.json"), "w"), indent=1)
    json.dump(report, open(os.path.join(OUT_DIR, "build_report.json"), "w"), indent=1)

    print("\n== VALIDATION CHECKS ==")
    failed = []
    for k, v in ck.items():
        p = (v is True) or (isinstance(v, str) and v.startswith("PASS"))
        if not p: failed.append(k)
        print(f"  {'PASS' if p else 'FAIL'}  {k}" + ("" if p else f" = {v}"))
    print(f"\nBUILD: {'ALL CHECKS PASS' if not failed else 'FAILURES: ' + str(failed)}")
    sys.exit(0 if not failed else 1)


if __name__ == "__main__":
    main()
