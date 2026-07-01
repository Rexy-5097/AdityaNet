import pandas as pd
import glob

def print_unique_values(name, pattern):
    files = sorted(glob.glob(pattern))
    if not files:
        print(f"No files for {name}")
        return
    df = pd.read_parquet(files[0])
    print(f"\n--- {name} Sample Data ---")
    print(df.head())
    print("Columns:", list(df.columns))
    for col in df.columns:
        if col != 'timestamp' and col != 'rate' and col != 'counts':
            print(f"Unique values in {col}:", df[col].unique())

def main():
    print_unique_values("SoLEXS", "data/aditya_l1/processed/solexs/*.parquet")
    print_unique_values("HEL1OS", "data/aditya_l1/processed/hel1os/*.parquet")
    
if __name__ == "__main__":
    main()
