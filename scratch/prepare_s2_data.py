import os
import gc
import pandas as pd

def main():
    os.makedirs("artifacts/sprint14c", exist_ok=True)
    test_v3_path = "artifacts/research_v3/test_v3.parquet"
    print(f"Loading {test_v3_path}...")
    df = pd.read_parquet(test_v3_path)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Split into Stage 2 train, validation, and test
    s2_train = df[(df['timestamp'] >= "2023-12-13 00:00:00") & (df['timestamp'] <= "2025-06-14 23:59:00")]
    s2_val = df[(df['timestamp'] >= "2025-06-15 00:00:00") & (df['timestamp'] <= "2025-12-14 23:59:00")]
    s2_test = df[(df['timestamp'] >= "2025-12-15 00:00:00") & (df['timestamp'] <= "2026-06-14 23:59:00")]
    
    print(f"Stage 2 Train: {len(s2_train):,} rows")
    print(f"Stage 2 Val:   {len(s2_val):,} rows")
    print(f"Stage 2 Test:  {len(s2_test):,} rows")
    
    s2_train.to_parquet("artifacts/sprint14c/s2_train.parquet", index=False)
    s2_val.to_parquet("artifacts/sprint14c/s2_val.parquet", index=False)
    s2_test.to_parquet("artifacts/sprint14c/s2_test.parquet", index=False)
    
    print("Stage 2 parquets successfully saved to artifacts/sprint14c/")

if __name__ == "__main__":
    main()
