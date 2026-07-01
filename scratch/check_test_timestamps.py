import os
import pandas as pd

def main():
    path = "artifacts/research/test.parquet"
    if os.path.exists(path):
        # Read only the timestamp column to save memory
        df = pd.read_parquet(path, columns=["timestamp"])
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        print("Test split start:", df["timestamp"].min())
        print("Test split end:", df["timestamp"].max())
        print("Total rows:", len(df))
    else:
        print("test.parquet not found")

if __name__ == "__main__":
    main()
