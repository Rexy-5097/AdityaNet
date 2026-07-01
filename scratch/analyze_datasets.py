import pandas as pd
import hashlib
import os
import json

REPO_ROOT = "/Users/soumyadebtripathy/AdityaNet"

datasets = {
    "train.parquet": "artifacts/research/train.parquet",
    "validation.parquet": "artifacts/research/validation.parquet",
    "test.parquet": "artifacts/research/test.parquet",
    "goes_full.parquet": "artifacts/research/goes_full.parquet",
    "flares_full.parquet": "artifacts/research/flares_full.parquet",
}

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

results = {}
for name, rel in datasets.items():
    abs_path = os.path.join(REPO_ROOT, rel)
    if not os.path.exists(abs_path):
        results[name] = "NOT FOUND"
        continue
    
    size_bytes = os.path.getsize(abs_path)
    file_hash = sha256(abs_path)
    
    print(f"Reading {name}...")
    
    # We only read the timestamp and target column if they exist to save memory
    try:
        df = pd.read_parquet(abs_path)
    except Exception as e:
        print(f"Error reading {name}: {e}")
        continue
    
    total_samples = len(df)
    
    # Date range
    ts_col = "timestamp" if "timestamp" in df.columns else None
    if ts_col:
        df[ts_col] = pd.to_datetime(df[ts_col])
        min_date = df[ts_col].min().strftime("%Y-%m-%d %H:%M:%S")
        max_date = df[ts_col].max().strftime("%Y-%m-%d %H:%M:%S")
        date_range = f"{min_date} to {max_date}"
    else:
        date_range = "N/A"
        
    # Labels
    TARGET_COL = "target_6hr_binary"
    SEQ_LEN = 360
    if TARGET_COL in df.columns:
        labels = df[TARGET_COL].values.astype(float)
        n_samples = len(labels) - SEQ_LEN
        pos_labels = int(labels[SEQ_LEN:].sum())
        neg_labels = n_samples - pos_labels
    else:
        n_samples = total_samples
        pos_labels = "N/A"
        neg_labels = "N/A"
        
    results[name] = {
        "relative_path": rel,
        "version": "1.0.0" if name in ["train.parquet", "validation.parquet", "test.parquet"] else "raw",
        "date_range": date_range,
        "number_of_rows": total_samples,
        "number_of_windows": n_samples,
        "number_of_positive_labels": pos_labels,
        "number_of_negative_labels": neg_labels,
        "sha256": file_hash,
        "size_bytes": size_bytes
    }

print(json.dumps(results, indent=2))
with open(os.path.join(REPO_ROOT, "scratch/datasets_info.json"), "w") as f:
    json.dump(results, f, indent=2)
