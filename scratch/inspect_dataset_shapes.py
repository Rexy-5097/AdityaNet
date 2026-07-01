import os
import sys
import torch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.services.ml.dataset import SolarFlareWindowDataset

def main():
    test_ds = SolarFlareWindowDataset(
        "artifacts/research/test.parquet",
        seq_len=360,
        feature_cols=["minutes_since_last_flare"],
        split_name="test_audit"
    )
    print("Dataset type:", type(test_ds))
    print("Dataset length:", len(test_ds))
    x, y = test_ds[0]
    print("Feature tensor shape:", x.shape)
    print("Label tensor shape:", y.shape)

if __name__ == "__main__":
    main()
