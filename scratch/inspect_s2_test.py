import pandas as pd

df = pd.read_parquet("artifacts/sprint14c/s2_test.parquet")
print("Columns in s2_test.parquet:")
print(list(df.columns))
print("Shape of s2_test.parquet:", df.shape)
