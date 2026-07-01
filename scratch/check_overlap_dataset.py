import os
import pandas as pd

def main():
    path = "artifacts/aditya_l1/overlap_dataset.parquet"
    if not os.path.exists(path):
        print("Overlap dataset not found")
        return
        
    df = pd.read_parquet(path)
    print("Columns:", list(df.columns))
    print("Row count:", len(df))
    print("Min timestamp:", df["timestamp"].min())
    print("Max timestamp:", df["timestamp"].max())
    print("\nHead:")
    print(df.head(5))

if __name__ == "__main__":
    main()
