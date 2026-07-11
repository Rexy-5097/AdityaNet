"""
scripts/sprint30/build_dataset_v4.py

Sprint 30 Phase 1 — build dataset_v4.0.0 (the F1 arm's 17-feature GOES dataset)
through the Version 4 pipeline. Every choice traces to its Sprint 28 spec:

  * Split boundaries: IDENTICAL to the frozen artifacts/research/*.parquet
    splits (03_DATASET_PIPELINE_V4.md §8) — timestamps and targets are copied,
    never recomputed, and verified equal.
  * Processing order (03 §6): physics features computed on RAW physical units
    first (goes_EM is stored as log10 per 02_FEATURE_PIPELINE_V4.md row 2 —
    that IS its feature definition, not a separate transform step); then robust
    median/IQR scaling fit on the TRAIN split only; then normalized-space
    neutral imputation (0.0) for any remaining NaN.
  * Masks and staleness (03 §1-§3): per-timestep goes_available and
    goes_staleness recorded as dataset METADATA columns. They are NOT model
    inputs for the F1 arm (F1.json fixes n_features=17; §2: "GOES gaps ...
    keep the existing V1 handling unchanged for baseline comparability").
  * Quality score (03 §5): per-split aggregate recorded in the build report
    (metadata, not a model input in Version 4.0).
  * Provenance manifest (03 §7): app/services/ml/dataset_v4/manifest.py,
    source-file SHA-256 pinning + canonical self-hash; feature-code provenance
    from the features_v4 framework written alongside.

Output: artifacts/research_v4/dataset_v4.0.0/{train,validation,test}.parquet
        + manifest.json + features_provenance.json + build_report.json
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
from app.services.ml.dataset_v4.scaling import RobustScaler, TrainOnlyViolation
from app.services.ml.dataset_v4.masks import build_availability
from app.services.ml.dataset_v4.manifest import build_manifest, verify_manifest, ManifestError

SRC = {s: os.path.join("artifacts", "research", f"{s}.parquet")
       for s in ("train", "validation", "test")}
OUT_DIR = os.path.join("artifacts", "research_v4", "dataset_v4.0.0")
FEATURES_14 = json.load(open(os.path.join("artifacts", "feature_columns.json")))
PHYSICS = ["goes_T_iso", "goes_EM", "goes_dT_iso_15m"]
FEATURES_17 = FEATURES_14 + PHYSICS
TARGETS = ["target_6hr_binary", "target_6hr_class"]
STALENESS_CAP = 60  # 03 §1


def df_hash(df: pd.DataFrame) -> str:
    return hashlib.sha256(
        pd.util.hash_pandas_object(df, index=False).values.tobytes()).hexdigest()


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    report = {"dataset_version": "dataset_v4.0.0", "splits": {}, "checks": {}}
    fs = FeatureSet([GoesTIso(), GoesEM(), GoesDTIso15m()])

    raw = {}          # per-split: unscaled 17-feature frame (physical units)
    frames = {}       # per-split: passthrough columns
    nan_pre = {}      # per-split per-feature NaN counts before scaling
    feat_prov = None
    physics_val_hashes = []

    for split, path in SRC.items():
        df = pd.read_parquet(path, columns=["timestamp"] + FEATURES_14 + TARGETS)
        # §6 step 1: physics on raw physical units (framework passes each
        # feature only its declared columns; labels structurally excluded)
        phys, feat_prov = fs.compute_all(df)
        if split == "validation":  # determinism check target (cheapest split)
            physics_val_hashes.append(df_hash(phys))
            phys2, _ = fs.compute_all(df)
            physics_val_hashes.append(df_hash(phys2))
        feats = pd.concat(
            [df[FEATURES_14].reset_index(drop=True), phys.reset_index(drop=True)], axis=1)
        raw[split] = feats
        frames[split] = df[["timestamp"] + TARGETS].reset_index(drop=True)
        nan_pre[split] = {c: int(feats[c].isna().sum()) for c in FEATURES_17}
        # §1-§3 masks: availability from genuinely observed flux values
        avail = (build_availability(df["short_flux"])
                 & build_availability(df["long_flux"])).astype(np.int8)
        frames[split]["goes_available"] = avail.values if hasattr(avail, "values") else avail
        # staleness: minutes since last observed sample, capped (03 §1);
        # all-available split => all zero
        a = np.asarray(frames[split]["goes_available"], dtype=np.int8)
        stale = np.zeros(len(a), dtype=np.int16)
        run = 0
        if (a == 0).any():
            for i in range(len(a)):
                run = 0 if a[i] == 1 else min(run + 1, STALENESS_CAP)
                stale[i] = run
        frames[split]["goes_staleness"] = stale
        report["splits"][split] = {
            "rows": int(len(df)),
            "positives": int(df["target_6hr_binary"].sum()),
            "availability_fraction": float(a.mean()),
            "quality_score": float(a.mean() * (1 - stale.mean() / STALENESS_CAP)),
            "nan_pre_scaling": nan_pre[split],
            "source_sha_pinned_in_manifest": True,
        }
        print(f"[build] {split}: rows={len(df):,} pos={report['splits'][split]['positives']:,} "
              f"avail={a.mean():.6f} nan_total={sum(nan_pre[split].values())}", flush=True)

    # §6 step 3: robust scaling fit on TRAIN ONLY
    scaler = RobustScaler().fit(raw["train"], split_name="train")
    # negative control: fitting on validation must raise
    try:
        RobustScaler().fit(raw["validation"], split_name="validation")
        report["checks"]["train_only_guard"] = "FAIL — no exception raised"
    except TrainOnlyViolation:
        report["checks"]["train_only_guard"] = "PASS (TrainOnlyViolation raised on non-train fit)"

    imputed = {}
    for split in SRC:
        scaled = scaler.transform(raw[split])
        n_nan = int(scaled.isna().sum().sum())
        imputed[split] = n_nan
        if n_nan:
            scaled = scaled.fillna(0.0)  # §6 step 4 / §2: normalized-space neutral
        out = pd.concat(
            [frames[split][["timestamp"]],
             scaled.astype(np.float32),
             frames[split][TARGETS + ["goes_available", "goes_staleness"]]], axis=1)
        out.to_parquet(os.path.join(OUT_DIR, f"{split}.parquet"), index=False)
        report["splits"][split]["imputed_neutral_values"] = n_nan
        print(f"[build] {split}: scaled+written ({n_nan} neutral-imputed)", flush=True)

    # ── validations ──────────────────────────────────────────────────────────
    ck = report["checks"]
    for split, path in SRC.items():
        ref = pd.read_parquet(path, columns=["timestamp"] + TARGETS)
        new = pd.read_parquet(os.path.join(OUT_DIR, f"{split}.parquet"),
                              columns=["timestamp"] + TARGETS)
        ck[f"{split}_timestamps_identical"] = bool(
            np.array_equal(ref["timestamp"].values, new["timestamp"].values))
        ck[f"{split}_targets_identical"] = bool(
            np.array_equal(ref[TARGETS].values, new[TARGETS].values))

    bounds = {s: (frames[s]["timestamp"].min(), frames[s]["timestamp"].max()) for s in SRC}
    ck["chronological_no_overlap"] = bool(
        bounds["train"][1] < bounds["validation"][0] < bounds["validation"][1] < bounds["test"][0])
    report["split_boundaries"] = {s: [str(b[0]), str(b[1])] for s, b in bounds.items()}

    tr = pd.read_parquet(os.path.join(OUT_DIR, "train.parquet"), columns=FEATURES_17)
    med = tr.median()
    iqr = tr.quantile(0.75) - tr.quantile(0.25)
    ck["train_post_scale_median_zero"] = bool((med.abs() < 1e-6).all())
    # IQR==1 post-scale holds only where the raw IQR was nonzero; the frozen
    # RobustScaler substitutes 1.0 for degenerate (zero) IQR, leaving such
    # columns center-shifted but unscaled — spec behavior, reported below.
    sp = scaler.to_params()["columns"]
    degenerate = [c for c in FEATURES_17
                  if sp[c]["iqr"] == 1.0 and abs(float(raw["train"][c].quantile(0.75)
                     - raw["train"][c].quantile(0.25))) == 0.0]
    nondeg = [c for c in FEATURES_17 if c not in degenerate]
    ck["train_post_scale_iqr_one_nondegenerate"] = bool(
        ((iqr[nondeg] - 1.0).abs() < 1e-3).all())
    report["degenerate_iqr_features"] = degenerate
    report["train_post_scale_stats"] = {
        c: {"median": float(med[c]), "iqr": float(iqr[c]),
            "min": float(tr[c].min()), "max": float(tr[c].max())} for c in FEATURES_17}

    # physics sanity in PHYSICAL units (pre-scaling): analytic range of the
    # TSC85 cubic on the clipped domain is T(0.02)=4.630 .. T(0.7)=47.145 MK
    t = raw["train"]["goes_T_iso"]; em = raw["train"]["goes_EM"]
    ck["physics_T_in_inversion_range"] = bool(t.min() >= 4.629 and t.max() <= 47.146)
    ck["physics_EM_finite"] = bool(np.isfinite(em.dropna()).all())
    report["physics_physical_ranges"] = {
        "goes_T_iso_MK": [float(t.min()), float(t.max())],
        "goes_EM_log10": [float(em.min()), float(em.max())],
        "goes_dT_iso_15m_MK": [float(raw['train']['goes_dT_iso_15m'].min()),
                                float(raw['train']['goes_dT_iso_15m'].max())]}

    ck["physics_determinism_validation_split"] = physics_val_hashes[0] == physics_val_hashes[1]
    report["physics_determinism_hashes"] = physics_val_hashes

    # §7 provenance manifest
    manifest = build_manifest(
        dataset_version="dataset_v4.0.0",
        generator_script=os.path.join("scripts", "sprint30", "build_dataset_v4.py"),
        source_files=list(SRC.values()) + [
            os.path.join("app", "services", "ml", "features_v4", "goes_physics.py"),
            os.path.join("app", "services", "ml", "features_v4", "framework.py"),
            os.path.join("app", "services", "ml", "dataset_v4", "scaling.py"),
            os.path.join("artifacts", "feature_columns.json")],
        split_counts={s: {"rows": report["splits"][s]["rows"],
                          "positives": report["splits"][s]["positives"]} for s in SRC},
        scaler_params=scaler.to_params(),
        feature_list=FEATURES_17)
    with open(os.path.join(OUT_DIR, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=1)
    verify_manifest(json.load(open(os.path.join(OUT_DIR, "manifest.json"))))
    ck["manifest_verify_roundtrip"] = True
    tampered = json.loads(json.dumps(manifest))
    tampered["scaler_params"]["fitted_on_split"] = "test"
    try:
        verify_manifest(tampered)
        ck["manifest_tamper_detected"] = False
    except ManifestError:
        ck["manifest_tamper_detected"] = True

    with open(os.path.join(OUT_DIR, "features_provenance.json"), "w") as f:
        json.dump(feat_prov, f, indent=1)

    with open(os.path.join(OUT_DIR, "build_report.json"), "w") as f:
        json.dump(report, f, indent=1)

    print("\n== VALIDATION CHECKS ==")
    failed = []
    for k, v in ck.items():
        passed = (v is True) or (isinstance(v, str) and v.startswith("PASS"))
        if not passed:
            failed.append(k)
        print(f"  {'PASS' if passed else 'FAIL'}  {k}" + ("" if passed else f" = {v}"))
    print(f"\nBUILD: {'ALL CHECKS PASS' if not failed else 'FAILURES: ' + str(failed)}")
    sys.exit(0 if not failed else 1)


if __name__ == "__main__":
    main()
