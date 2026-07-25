import os
import sys
import glob
import hashlib
import json
import logging
import pandas as pd
import numpy as np

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

RESEARCH_DIR = "artifacts/research"
OUTPUT_DIR = "artifacts/research_v3"
FINGERPRINT_PATH = "artifacts/sprint12b/dataset_fingerprint_v3.json"
COLUMNS_PATH = "artifacts/feature_columns_v3.json"

def compute_sha256(filepath):
    sha = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            sha.update(chunk)
    return sha.hexdigest()

def process_instrument_data(name, glob_pattern, is_solexs=True):
    logger.info(f"Aggregating {name} daily processed files...")
    files = sorted(glob.glob(glob_pattern))
    if not files:
        logger.warning(f"No files found for {name} using pattern {glob_pattern}")
        return pd.DataFrame()

    days_list = []
    # Loop and resample daily parquets
    for f in files:
        try:
            df = pd.read_parquet(f)
            if df.empty:
                continue
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Pivot channel or energy_band column to column-space
            pivot_col = 'channel' if is_solexs else 'energy_band'
            df_pivot = df.pivot(index='timestamp', columns=pivot_col, values=['rate', 'counts'])
            
            # Separate rate and counts to resample differently (mean for rate, sum for counts)
            rate_df = df_pivot['rate'].resample('1Min').mean()
            counts_df = df_pivot['counts'].resample('1Min').sum()
            
            # Rename columns
            prefix = "solexs" if is_solexs else "hel1os"
            suffix = "ch" if is_solexs else "band"
            rate_df.columns = [f"{prefix}_rate_{suffix}{col}" for col in rate_df.columns]
            counts_df.columns = [f"{prefix}_counts_{suffix}{col}" for col in counts_df.columns]
            
            day_df = pd.concat([rate_df, counts_df], axis=1)
            days_list.append(day_df)
        except Exception as e:
            logger.error(f"Error processing {f}: {e}")
            
    if days_list:
        df_all = pd.concat(days_list).sort_index()
        # Handle duplicates if any files overlap
        df_all = df_all.groupby(df_all.index).mean()
        logger.info(f"Finished {name} aggregation: {df_all.shape[0]} rows, {df_all.shape[1]} features.")
        return df_all
    return pd.DataFrame()

def main():
    logger.info("Initializing causal multi-instrument dataset builder...")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(FINGERPRINT_PATH), exist_ok=True)

    # 1. Process SoLEXS (channels 1-9)
    solexs_df = process_instrument_data("SoLEXS", "data/aditya_l1/processed/solexs/*.parquet", is_solexs=True)
    
    # 2. Process HEL1OS (bands 0-1)
    hel1os_df = process_instrument_data("HEL1OS", "data/aditya_l1/processed/hel1os/*.parquet", is_solexs=False)

    # Combine Aditya-L1 instruments
    if not solexs_df.empty and not hel1os_df.empty:
        aditya_df = solexs_df.join(hel1os_df, how='outer')
    elif not solexs_df.empty:
        aditya_df = solexs_df
    else:
        aditya_df = hel1os_df

    logger.info(f"Combined Aditya-L1 dataset shape: {aditya_df.shape}")

    # 3. Read feature columns to identify GOES columns
    with open("artifacts/feature_columns.json") as f:
        goes_cols = json.load(f)

    # Load splits, align with Aditya-L1 data, and write v3 files
    splits = ["train", "validation", "test"]
    fingerprints = {}

    for s in splits:
        goes_path = os.path.join(RESEARCH_DIR, f"{s}.parquet")
        logger.info(f"Aligning split: {goes_path}...")
        
        df_goes = pd.read_parquet(goes_path)
        df_goes['timestamp'] = pd.to_datetime(df_goes['timestamp'])
        
        # Left-join ensures we preserve the exact row counts and chronological ordering of GOES baseline
        df_merged = pd.merge(df_goes, aditya_df, on='timestamp', how='left')
        
        # Create masks (1.0 = present, 0.0 = missing)
        # SoLEXS is considered present if at least one column is non-null
        if not solexs_df.empty:
            sample_col = solexs_df.columns[0]
            df_merged['mask_solexs'] = np.where(df_merged[sample_col].notna(), 1.0, 0.0)
        else:
            df_merged['mask_solexs'] = 0.0

        if not hel1os_df.empty:
            sample_col = hel1os_df.columns[0]
            df_merged['mask_hel1os'] = np.where(df_merged[sample_col].notna(), 1.0, 0.0)
        else:
            df_merged['mask_hel1os'] = 0.0

        # Fill missing values with 0.0
        feature_cols_new = [c for c in aditya_df.columns]
        df_merged[feature_cols_new] = df_merged[feature_cols_new].fillna(0.0)

        # Cast everything to float32/int32 to be consistent
        for c in feature_cols_new:
            df_merged[c] = df_merged[c].astype(np.float32)
        df_merged['mask_solexs'] = df_merged['mask_solexs'].astype(np.float32)
        df_merged['mask_hel1os'] = df_merged['mask_hel1os'].astype(np.float32)
        
        # Save split
        v3_path = os.path.join(OUTPUT_DIR, f"{s}_v3.parquet")
        df_merged.to_parquet(v3_path, index=False)
        logger.info(f"Saved aligned split to {v3_path}")

        # Compute fingerprint metrics
        size_bytes = os.path.getsize(v3_path)
        sha256 = compute_sha256(v3_path)
        pos = int(df_merged['target_6hr_binary'].sum())
        neg = len(df_merged) - pos
        
        fingerprints[f"{s}_v3.parquet"] = {
            "relative_path": v3_path,
            "sha256": sha256,
            "size_bytes": size_bytes,
            "number_of_rows": len(df_merged),
            "number_of_positive_labels": pos,
            "number_of_negative_labels": neg,
            "positive_label_ratio": pos / len(df_merged) if len(df_merged) > 0 else 0
        }

    # Save feature columns metadata for v3
    v3_feature_columns = {
        "goes": goes_cols,
        "solexs": [c for c in solexs_df.columns],
        "hel1os": [c for c in hel1os_df.columns]
    }
    with open(COLUMNS_PATH, "w") as f:
        json.dump(v3_feature_columns, f, indent=2)
    logger.info(f"Saved Version 3 feature columns inventory to {COLUMNS_PATH}")

    # Save final fingerprint manifest
    manifest = {
        "version": "3.0.0",
        "status": "ALIGNED_AND_FROZEN",
        "fingerprints": fingerprints
    }
    with open(FINGERPRINT_PATH, "w") as f:
        json.dump(manifest, f, indent=2)
    logger.info(f"Saved Version 3 dataset fingerprint manifest to {FINGERPRINT_PATH}")
    print("Multi-instrument dataset builder complete!")

if __name__ == "__main__":
    main()
