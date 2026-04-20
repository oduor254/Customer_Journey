"""Diagnose the data to understand distributions for Time to First Purchase and Branch metrics."""
import pandas as pd
import numpy as np
import pickle, re

def normalize_phone(s):
    if not isinstance(s, str):
        s = str(s)
    digits = re.sub(r'\D', '', s)[-9:]
    return digits if len(digits) >= 7 else ''

def safe_float(v):
    try:
        if pd.isna(v) or v is None: return 0.0
        v_str = str(v).replace(',', '').replace('Ksh', '').replace('₦', '').strip()
        if not v_str: return 0.0
        return float(v_str)
    except Exception:
        return 0.0

def parse_date(v):
    if v is None or (isinstance(v, str) and not v.strip()):
        return pd.NaT
    for fmt in ('%d/%m/%Y', '%m/%d/%Y', '%Y-%m-%d', '%B %Y', '%b %Y'):
        try:
            return pd.to_datetime(v, format=fmt)
        except Exception:
            pass
    try:
        return pd.to_datetime(v)
    except Exception:
        return pd.NaT

PLATFORM_ALIASES = {
    'instagram': 'Instagram', 'ig': 'Instagram', 'insta': 'Instagram',
    'tiktok': 'TikTok', 'tik tok': 'TikTok', 'tt': 'TikTok',
    'twitter': 'Twitter', 'x': 'Twitter', 'x (twitter)': 'Twitter',
    'facebook': 'Facebook', 'fb': 'Facebook', 'facebook ads': 'Facebook',
}

def normalize_platform(s):
    if not isinstance(s, str) or not s.strip():
        return ''
    return PLATFORM_ALIASES.get(s.strip().lower(), s.strip())

# Load cached data
leads_df = pd.read_pickle('leads_cache.pkl')
shops_df = pd.read_pickle('shops_cache.pkl')

print(f"=== RAW DATA ===")
print(f"Total rows in leads_df: {len(leads_df)}")
print(f"Total rows in shops_df: {len(shops_df)}")
print(f"Leads columns: {list(leads_df.columns)}")

# Process leads
leads = leads_df.copy()
leads['phone_key'] = leads['CONTACT'].astype(str).apply(normalize_phone)
leads['platform'] = leads['Source'].apply(normalize_platform)
leads['branch_norm'] = leads['BRANCH'].astype(str).str.strip().str.title()

date_col = next((c for c in ['Date','DATE','Month','Timestamp','Created At','Created', 'Added On'] if c in leads.columns), None)
print(f"Date column found: {date_col}")
if date_col:
    leads['lead_date'] = pd.to_datetime(leads[date_col].apply(parse_date), errors='coerce')

# Filter valid phones
leads = leads[leads['phone_key'].str.len() >= 7].copy()
print(f"Leads after phone filter: {len(leads)}")

# Dedup
leads_dedup = leads.drop_duplicates(subset='phone_key', keep='first').set_index('phone_key')
print(f"Leads after dedup: {len(leads_dedup)}")

# Process shops
shops = shops_df.copy()
shops['phone_key'] = shops['Phone'].astype(str).apply(normalize_phone)
shops['purchase_date'] = pd.to_datetime(shops['Date'], errors='coerce', dayfirst=True)
shops['Price'] = shops['Price'].apply(safe_float)
shops = shops[shops['phone_key'].str.len() >= 7].copy()
print(f"Shops after phone filter: {len(shops)}")

# Total unique leads
total_leads = len(leads_dedup)
print(f"\n=== TOTAL UNIQUE LEADS: {total_leads} ===")

# Converted
shops_phones = set(shops['phone_key'].unique())
all_phones_set = set(leads_dedup.index)
converted_phones = all_phones_set & shops_phones
converted_count = len(converted_phones)
print(f"Converted count (leads who purchased): {converted_count}")

# === TIME TO FIRST PURCHASE ===
print(f"\n=== TIME TO FIRST PURCHASE ANALYSIS ===")

# Check date availability
lead_dates = leads_dedup['lead_date']
has_lead_date = lead_dates.notna().sum()
no_lead_date = lead_dates.isna().sum()
print(f"Leads with lead_date: {has_lead_date}")
print(f"Leads without lead_date: {no_lead_date}")

# Converted phones with lead dates
conv_with_lead_date = sum(1 for p in converted_phones if pd.notna(leads_dedup.loc[p, 'lead_date']))
conv_without_lead_date = converted_count - conv_with_lead_date
print(f"Converted with lead_date: {conv_with_lead_date}")
print(f"Converted without lead_date: {conv_without_lead_date}")

# Current logic merge
lead_dates_all = leads_dedup[['lead_date']].dropna().rename(columns={'lead_date': 'lead_dt'})
shop_dates_all = shops[['phone_key', 'purchase_date']].dropna().rename(columns={'purchase_date': 'shop_dt'})

merged_all = lead_dates_all.merge(shop_dates_all, left_index=True, right_on='phone_key')
print(f"Merged pairs (lead+shop dates): {len(merged_all)}")

merged_valid = merged_all[merged_all['shop_dt'] >= merged_all['lead_dt']].copy()
print(f"Merged pairs with shop >= lead date: {len(merged_valid)}")

if len(merged_valid) > 0:
    merged_valid['days'] = (merged_valid['shop_dt'] - merged_valid['lead_dt']).dt.days
    first_conv = merged_valid.sort_values('shop_dt').groupby('phone_key').first()
    print(f"Unique phones with valid first purchase after lead: {len(first_conv)}")
    
    has_dates = first_conv.copy()
    has_dates['cat'] = np.where(has_dates['days'] == 0, 'Same Day',
                       np.where((has_dates['days'] >= 1) & (has_dates['days'] <= 7), '1-7 Days',
                       np.where((has_dates['days'] >= 8) & (has_dates['days'] <= 30), '8-30 Days', '31+ Days')))
    
    dist_counts = has_dates['cat'].value_counts()
    print(f"\nDistribution (current logic):")
    for cat, cnt in dist_counts.items():
        print(f"  {cat}: {cnt}")
    
    matched_phones = set(first_conv.index)
else:
    matched_phones = set()

prior_not_since = len(converted_phones - matched_phones)
print(f"\nPrior Customer / Missing: {prior_not_since}")
print(f"Total distribution sum: {sum(dist_counts.values) + prior_not_since}")
print(f"Expected (converted_count): {converted_count}")

# === BRANCH ANALYSIS ===
print(f"\n=== BRANCH ANALYSIS ===")
leads_all = leads_dedup.copy()
leads_all['branch'] = leads_all['branch_norm']
branch_counts = leads_all['branch'].value_counts()
print(f"Branch value counts:")
for br, cnt in branch_counts.items():
    print(f"  {br}: {cnt}")
print(f"Total across branches: {branch_counts.sum()}")
print(f"Expected: {total_leads}")

# Check for Unknown/empty branches
empty_branches = leads_all[leads_all['branch'].isin(['', 'Unknown', 'Nan', 'None']) | leads_all['branch'].isna()]
print(f"\nEmpty/Unknown branches: {len(empty_branches)}")

# Look at current analytics cache
print(f"\n=== CURRENT ANALYTICS CACHE ===")
with open('analytics_cache.pkl', 'rb') as f:
    analytics = pickle.load(f)

print(f"Executive summary total_unique_leads: {analytics['executive_summary']['total_unique_leads']}")
print(f"Executive summary converted: {analytics['executive_summary']['converted_customers']}")

ttp = analytics['management_metrics']['time_to_first_purchase']
print(f"\nTime to First Purchase distribution:")
ttp_sum = 0
for k, v in ttp.items():
    print(f"  {k}: {v}")
    ttp_sum += v
print(f"  SUM: {ttp_sum}")

branch_perf = analytics['sales_metrics']['branch_performance']
br_total = 0
print(f"\nBranch leads distribution:")
for b in branch_perf:
    print(f"  {b['branch']}: leads={b['leads']}, converted={b['converted']}, revenue={b['revenue']}")
    br_total += b['leads']
print(f"  TOTAL LEADS across branches: {br_total}")
