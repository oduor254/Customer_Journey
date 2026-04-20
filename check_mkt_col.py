import pandas as pd
import os
import pickle

if os.path.exists('shops_cache.pkl'):
    with open('shops_cache.pkl', 'rb') as f:
        df = pickle.load(f)
    print("Columns:", list(df.columns))
    mkt_col = next((c for c in df.columns if 'MARKET' in c.upper()), None)
    print("Detected mkt_col:", mkt_col)
    if mkt_col:
        print("Mkt Col Values:", df[mkt_col].head(5).tolist())
else:
    print("Shops cache not found")
