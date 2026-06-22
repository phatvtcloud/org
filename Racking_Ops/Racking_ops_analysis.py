import os
import sys
import io
import pandas as pd
import glob

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

INV03_DIR = r"C:\Users\phatvt\OneDrive - WIN\DR-WCM - 15.9.3 Operation\INV03\Data_pq"

files = glob.glob(os.path.join(INV03_DIR, "*.parquet"))
if files:
    # Read the first parquet file
    df = pd.read_parquet(files[0])
    print("Columns in INV03:")
    for col in sorted(df.columns):
        print(f"  - {col}")
else:
    print("No INV03 parquet files found.")
