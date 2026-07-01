import pandas as pd
import os

REPO_ROOT = "/Users/soumyadebtripathy/AdityaNet"

h_file = os.path.join(REPO_ROOT, "data/aditya_l1/processed/hel1os/ad1_hel1os_l2_20231029.parquet")
s_file = os.path.join(REPO_ROOT, "data/aditya_l1/processed/solexs/ad1_solexs_l2_20231213.parquet")

if os.path.exists(h_file):
    df_h = pd.read_parquet(h_file)
    print("HEL1OS columns:")
    print(df_h.columns.tolist())
    print(df_h.head(2))
else:
    print(f"HEL1OS file not found: {h_file}")
    
if os.path.exists(s_file):
    df_s = pd.read_parquet(s_file)
    print("\nSoLEXS columns:")
    print(df_s.columns.tolist())
    print(df_s.head(2))
else:
    print(f"SoLEXS file not found: {s_file}")
