import pickle
import pandas as pd
import json

def safe_float(v):
    try:
        return float(v) if v and str(v).strip() else 0.0
    except Exception:
        return 0.0

try:
    with open('shops_cache.pkl', 'rb') as f:
        shops = pickle.load(f)
    mkt_col = next((c for c in shops.columns if 'MARKET' in c.upper()), None)
    
    if mkt_col:
        shops['mkt'] = shops[mkt_col].apply(safe_float)
        total_mkt = shops['mkt'].sum()
        
        # Are there many duplicates of the same phone with marketing spend?
        unique_phones_mkt = shops.drop_duplicates(subset=['Phone'])['mkt'].sum()
        
        print("="*50)
        print(f"MARKETING COLUMN FOUND: {mkt_col}")
        print(f"TOTAL MARKETING SUM (ALL ROWS): {total_mkt}")
        print(f"TOTAL MARKETING SUM (UNIQUE PHONES ONLY): {unique_phones_mkt}")
        print(f"Rows with marketing > 0: {len(shops[shops['mkt'] > 0])}")
        
        print("\nFIRST 5 ROWS WITH MARKETING SPEND:")
        cols_to_show = [c for c in ['Phone', 'Date', 'Price', mkt_col] if c in shops.columns]
        print(shops[shops['mkt'] > 0][cols_to_show].head(5).to_string())
        print("="*50)
    else:
        print("NO MARKETING COLUMN FOUND in Shops sheet. Columns are:")
        print(list(shops.columns))

    with open('analytics_cache.pkl', 'rb') as f:
        data = pickle.load(f)
        print("\nAnalytics time_to_first_purchase data:")
        dist = data.get('management_metrics', {}).get('time_to_first_purchase', None)
        print(json.dumps(dist, indent=2))
        
except Exception as e:
    import traceback
    traceback.print_exc()
