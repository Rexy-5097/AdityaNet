import pandas as pd
import glob
import numpy as np

def check_missing_rates(name, pattern):
    files = sorted(glob.glob(pattern))
    if not files:
        print(f"No files for {name}")
        return
    
    total_rows = 0
    missing_counts = {}
    
    # Read first file to get columns
    sample_df = pd.read_parquet(files[0])
    cols = sample_df.columns
    for c in cols:
        missing_counts[c] = 0
        
    # Read a sample of files (e.g. 50 files evenly spaced)
    sampled_files = [files[i] for i in np.linspace(0, len(files)-1, min(50, len(files)), dtype=int)]
    
    for f in sampled_files:
        df = pd.read_parquet(f)
        total_rows += len(df)
        for c in cols:
            missing_counts[c] += df[c].isna().sum()
            
    print(f"--- {name} Missing Data Analysis (sampled {len(sampled_files)} files) ---")
    for c in cols:
        pct = (missing_counts[c] / total_rows) * 100 if total_rows > 0 else 0
        print(f"Col {c}: {missing_counts[c]} missing out of {total_rows} ({pct:.4f}%)")

def main():
    check_missing_rates("SoLEXS", "data/aditya_l1/processed/solexs/*.parquet")
    check_missing_rates("HEL1OS", "data/aditya_l1/processed/hel1os/*.parquet")
    
if __name__ == "__main__":
    main()
