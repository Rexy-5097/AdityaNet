import pandas as pd
import numpy as np
import json
import os

def audit_split(name, filepath):
    print(f"Auditing split: {name} from {filepath}")
    df = pd.read_parquet(filepath)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    min_ts = df['timestamp'].min()
    max_ts = df['timestamp'].max()
    num_rows = len(df)
    
    # Check masks
    solexs_present_count = int(df['mask_solexs'].sum())
    hel1os_present_count = int(df['mask_hel1os'].sum())
    
    solexs_ratio = solexs_present_count / num_rows
    hel1os_ratio = hel1os_present_count / num_rows
    
    # Get active range
    active_solexs_df = df[df['mask_solexs'] == 1.0]
    if not active_solexs_df.empty:
        solexs_active_min = active_solexs_df['timestamp'].min()
        solexs_active_max = active_solexs_df['timestamp'].max()
    else:
        solexs_active_min, solexs_active_max = None, None
        
    active_hel1os_df = df[df['mask_hel1os'] == 1.0]
    if not active_hel1os_df.empty:
        hel1os_active_min = active_hel1os_df['timestamp'].min()
        hel1os_active_max = active_hel1os_df['timestamp'].max()
    else:
        hel1os_active_min, hel1os_active_max = None, None

    # Check for NaNs
    nulls = df.isnull().sum().sum()
    
    # Check targets
    targets = df['target_6hr_binary'].values
    pos = int(targets.sum())
    neg = num_rows - pos
    
    result = {
        "min_timestamp": str(min_ts),
        "max_timestamp": str(max_ts),
        "total_rows": num_rows,
        "solexs_active_count": solexs_present_count,
        "solexs_active_ratio": solexs_ratio,
        "solexs_active_min": str(solexs_active_min) if solexs_active_min else None,
        "solexs_active_max": str(solexs_active_max) if solexs_active_max else None,
        "hel1os_active_count": hel1os_present_count,
        "hel1os_active_ratio": hel1os_ratio,
        "hel1os_active_min": str(hel1os_active_min) if hel1os_active_min else None,
        "hel1os_active_max": str(hel1os_active_max) if hel1os_active_max else None,
        "null_count": int(nulls),
        "positive_labels": pos,
        "negative_labels": neg,
        "positive_ratio": float(pos / num_rows)
    }
    
    for k, v in result.items():
        print(f"  {k}: {v}")
    print()
    return df, result

splits = {
    "train": "artifacts/research_v3/train_v3.parquet",
    "validation": "artifacts/research_v3/validation_v3.parquet",
    "test": "artifacts/research_v3/test_v3.parquet"
}

audit_results = {}
dfs = {}
for name, path in splits.items():
    df, res = audit_split(name, path)
    dfs[name] = df
    audit_results[name] = res

# Check for temporal overlaps between splits
print("Checking for temporal leakage / overlaps...")
train_times = set(dfs['train']['timestamp'])
val_times = set(dfs['validation']['timestamp'])
test_times = set(dfs['test']['timestamp'])

train_val_overlap = len(train_times.intersection(val_times))
val_test_overlap = len(val_times.intersection(test_times))
train_test_overlap = len(train_times.intersection(test_times))

print(f"Train-Val Overlap count: {train_val_overlap}")
print(f"Val-Test Overlap count: {val_test_overlap}")
print(f"Train-Test Overlap count: {train_test_overlap}")

# Check temporal chronological ordering
max_train = dfs['train']['timestamp'].max()
min_val = dfs['validation']['timestamp'].min()
max_val = dfs['validation']['timestamp'].max()
min_test = dfs['test']['timestamp'].min()

print(f"Max Train Timestamp: {max_train}")
print(f"Min Val Timestamp:   {min_val}")
print(f"Is train strictly before validation? {max_train < min_val}")
print(f"Max Val Timestamp:   {max_val}")
print(f"Min Test Timestamp:  {min_test}")
print(f"Is validation strictly before test? {max_val < min_test}")

out_data = {
    "splits": audit_results,
    "leakage": {
        "train_val_overlap": train_val_overlap,
        "val_test_overlap": val_test_overlap,
        "train_test_overlap": train_test_overlap,
        "train_before_val": bool(max_train < min_val),
        "val_before_test": bool(max_val < min_test)
    }
}

with open("scratch/dataset_audit_results.json", "w") as f:
    json.dump(out_data, f, indent=2)
print("Saved audit to scratch/dataset_audit_results.json")
