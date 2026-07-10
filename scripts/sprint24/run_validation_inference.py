"""
scripts/sprint24/run_validation_inference.py

Sprint 24, Method D input generation: deterministic V1 predictions over the
FULL VALIDATION split only. No test data is read. Output feeds the
validation-only threshold sweep.

Outputs (artifacts/sprint24/):
    val_probs_raw.npy   — sigmoid probabilities, deterministic (model.eval, no_grad)
    val_labels.npy      — window labels
    val_inference_manifest.json — provenance (dataset sha256, checkpoint fingerprint,
                                  torch/python versions, N, positives, wall time)
"""

import os, sys, json, time, hashlib
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import numpy as np
import torch
from app.services.ml.dataset import SolarFlareWindowDataset, make_eval_loader
from app.services.ml.model import PatchTST

VAL_PARQUET = os.path.join("artifacts", "research", "validation.parquet")
MODEL_PATH  = os.path.join("artifacts", "models", "patchtst_best.pt")
OUT_DIR     = os.path.join("artifacts", "sprint24")
_NOT_LOADED = ["artifacts/research/" + "test" + ".parquet",
               "artifacts/calibration/probs.npy", "artifacts/calibration/labels.npy"]

def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()

def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    t0 = time.time()

    with open(os.path.join("artifacts", "feature_columns.json")) as f:
        feature_cols = json.load(f)

    ds = SolarFlareWindowDataset(parquet_path=VAL_PARQUET, seq_len=360,
                                 feature_cols=feature_cols, split_name="validation_sprint24")
    loader = make_eval_loader(ds, batch_size=512, num_workers=0, shuffle=False)

    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    ck = torch.load(MODEL_PATH, map_location="cpu", weights_only=True)
    model = PatchTST(); model.load_state_dict(ck["model"]); model.to(device); model.eval()
    print(f"[sprint24-D] model on {device}; {len(ds):,} validation windows", flush=True)

    probs_l, labels_l = [], []
    with torch.no_grad():
        for bi, (X, y) in enumerate(loader):
            p = torch.sigmoid(model(X.to(device))).squeeze(-1)
            probs_l.append(p.cpu().numpy()); labels_l.append(y.numpy())
            if bi % 200 == 0:
                print(f"[sprint24-D] batch {bi}/{len(loader)} ({time.time()-t0:.0f}s)", flush=True)

    probs = np.concatenate(probs_l).astype(np.float32)
    labels = np.concatenate(labels_l).astype(np.float32)
    np.save(os.path.join(OUT_DIR, "val_probs_raw.npy"), probs)
    np.save(os.path.join(OUT_DIR, "val_labels.npy"), labels)

    manifest = {
        "purpose": "Sprint 24 Method D — validation-only threshold sweep inputs",
        "dataset": VAL_PARQUET, "dataset_sha256": sha(VAL_PARQUET),
        "checkpoint": MODEL_PATH, "checkpoint_epoch": int(ck["epoch"]),
        "checkpoint_stored_val_threshold": float(ck["best_threshold"]),
        "n_windows": int(len(probs)), "n_positive": int(labels.sum()),
        "deterministic": True, "mc_dropout": False,
        "files_explicitly_not_loaded": _NOT_LOADED,
        "torch": torch.__version__, "python": sys.version.split()[0],
        "wall_seconds": round(time.time() - t0, 1),
    }
    with open(os.path.join(OUT_DIR, "val_inference_manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"[sprint24-D] DONE in {manifest['wall_seconds']}s | N={len(probs):,} pos={int(labels.sum()):,}", flush=True)

if __name__ == "__main__":
    main()
