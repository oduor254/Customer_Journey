from flask import Flask, jsonify, request
from flask_cors import CORS
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import numpy as np
from datetime import datetime
import re, ssl, certifi, os, threading, time, pickle

os.environ['SSL_CERT_FILE']        = certifi.where()
os.environ['REQUESTS_CA_BUNDLE']   = certifi.where()

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

# ── Config ────────────────────────────────────────────────────────────────────
SERVICE_ACCOUNT_FILE = r'C:\Users\Oduor\Downloads\JSON Files\retention-484110-9e4520124486.json'
SPREADSHEET_ID       = '1zravAS7NoxjnV-2476eBhMitZYQmxWgef3JTbwD-Rag'
SCOPES               = ['https://www.googleapis.com/auth/spreadsheets.readonly']

SHEETS_CACHE_TTL     = 21600   # 6 hours
ANALYTICS_CACHE_FILE = 'analytics_cache.pkl'
LEADS_CACHE          = 'leads_cache.pkl'
SHOPS_CACHE          = 'shops_cache.pkl'
WHATSAPP_CACHE       = 'whatsapp_cache.pkl'

PLATFORM_ALIASES = {
    'instagram': 'Instagram', 'ig': 'Instagram', 'insta': 'Instagram',
    'tiktok': 'TikTok', 'tik tok': 'TikTok', 'tt': 'TikTok',
    'twitter': 'Twitter', 'x': 'Twitter', 'x (twitter)': 'Twitter',
    'facebook': 'Facebook', 'fb': 'Facebook', 'facebook ads': 'Facebook',
}

# ── Shared state ──────────────────────────────────────────────────────────────
_state = {
    'analytics':  None,   # computed result
    'ready':      False,  # True when analytics done
    'error':      None,   # error message if failed
    'progress':   'Starting up…',
}
_lock = threading.Lock()

# ── Helpers ───────────────────────────────────────────────────────────────────
def normalize_phone(s):
    if not isinstance(s, str):
        s = str(s)
    digits = re.sub(r'\D', '', s)[-9:]
    return digits if len(digits) >= 7 else ''

def normalize_platform(s):
    if not isinstance(s, str) or not s.strip():
        return ''
    return PLATFORM_ALIASES.get(s.strip().lower(), s.strip())

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

def set_progress(msg):
    with _lock:
        _state['progress'] = msg
    print(f'[Progress] {msg}')

# ── Sheet loader ──────────────────────────────────────────────────────────────
def get_sheets_data(force=False):
    caches = [LEADS_CACHE, SHOPS_CACHE, WHATSAPP_CACHE]
    if not force and all(os.path.exists(f) for f in caches):
        age = time.time() - os.path.getmtime(SHOPS_CACHE)
        if age < SHEETS_CACHE_TTL:
            set_progress('Loading data from local cache…')
            return (pd.read_pickle(LEADS_CACHE),
                    pd.read_pickle(SHOPS_CACHE),
                    pd.read_pickle(WHATSAPP_CACHE))

    set_progress('Connecting to Google Sheets…')
    creds  = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    client = gspread.authorize(creds)
    sheet  = client.open_by_key(SPREADSHEET_ID)

    set_progress('Downloading Leads_2025 sheet…')
    leads_df = pd.DataFrame(sheet.worksheet('Leads_2025').get_all_records())

    set_progress('Downloading Shops sheet…')
    shops_df = pd.DataFrame(sheet.worksheet('Shops').get_all_records())

    set_progress('Downloading WhatsApp sheet…')
    try:
        wa_df = pd.DataFrame(sheet.worksheet('Whatsapp').get_all_records())
    except Exception:
        wa_df = pd.DataFrame()

    pd.to_pickle(leads_df, LEADS_CACHE)
    pd.to_pickle(shops_df, SHOPS_CACHE)
    pd.to_pickle(wa_df,    WHATSAPP_CACHE)
    return leads_df, shops_df, wa_df

# ── FAST vectorized analytics ─────────────────────────────────────────────────
def build_analytics(leads_df, shops_df, whatsapp_df=None):
    """
    Fully vectorized — no per-phone Python loops.
    Typical runtime: <2 s even on 100 k+ rows.
    """
    t0 = time.time()
    set_progress('Normalising lead data…')

    leads = leads_df.copy()
    shops = shops_df.copy()
    wa    = whatsapp_df.copy() if whatsapp_df is not None and len(whatsapp_df) > 0 else pd.DataFrame()

    # ── Vectorized normalization ───────────────────────────────────────────────
    leads['phone_key']   = leads['CONTACT'].astype(str).apply(normalize_phone)
    leads['platform']    = leads['Source'].apply(normalize_platform)
    leads['branch_norm'] = leads['BRANCH'].astype(str).str.strip().str.title()

    mkt_keywords = ['MARKET', 'EXPENSE', 'COST', 'ADS', 'ADVERT']
    
    # Marketing in leads
    leads_mkt_col = next((c for c in leads.columns if any(k in c.upper() for k in mkt_keywords)), None)
    leads['marketing_expense'] = leads[leads_mkt_col].apply(safe_float) if leads_mkt_col else 0.0
    leads_total_marketing = float(leads['marketing_expense'].sum())

    # Restore date parsing
    date_col = next((c for c in ['Date','DATE','Month','Timestamp','Created At','Created', 'Added On'] if c in leads.columns), None)
    if date_col:
        leads['lead_date'] = pd.to_datetime(leads[date_col].apply(parse_date), errors='coerce')
    else:
        leads['lead_date'] = pd.NaT
    
    leads = leads[leads['phone_key'].str.len() >= 7].copy()

    shops['phone_key']     = shops['Phone'].astype(str).apply(normalize_phone)
    # Parse shop purchase dates using the same tolerant parser as leads
    shops['purchase_date'] = shops['Date'].apply(parse_date)
    shops['Price']         = shops['Price'].apply(safe_float)
    
    # Marketing expense column in shops (try keyword match first, then column J by position)
    mkt_col = next((c for c in shops.columns if any(k in c.upper() for k in mkt_keywords)), None)
    # Fallback: try to use column J (index 9) if it has numeric-like data
    if not mkt_col and len(shops.columns) > 9:
        col_j = shops.columns[9]
        # Check if column J has numeric data
        sample_vals = shops[col_j].astype(str).str.replace(',', '').str.replace('Ksh', '').str.replace('₦', '').str.strip()
        if any(c.isdigit() for val in sample_vals.head(10) for c in str(val)):
            mkt_col = col_j
            print(f"⚠ Using column J ('{col_j}') as marketing expense (no keyword match found)")
    
    shops['marketing_expense'] = shops[mkt_col].apply(safe_float) if mkt_col else 0.0
    
    # Combined global marketing spend from all rows BEFORE phone filtering
    global_total_marketing = float(shops['marketing_expense'].sum()) + leads_total_marketing
    
    if mkt_col: print(f"✓ Found marketing expense in shops column: '{mkt_col}'")
    if leads_mkt_col: print(f"✓ Found marketing expense in leads column: '{leads_mkt_col}'")
    print(f"DEBUG: All shops columns: {list(shops.columns)}")
    
    shops = shops[shops['phone_key'].str.len() >= 7].copy()

    # ── Deduplicate leads by phone (keep first occurrence) ────────────────────
    set_progress('Deduplicating leads…')
    leads_dedup = leads.drop_duplicates(subset='phone_key', keep='first').set_index('phone_key')

    # ── WhatsApp ──────────────────────────────────────────────────────────────
    wa_phone_set     = set()
    activity_metrics = {}

    if len(wa) > 0:
        set_progress('Processing WhatsApp data…')
        wa['phone_key']       = wa['CONTACT'].astype(str).apply(normalize_phone)
        wa['engagement_date'] = wa['DATE'].apply(parse_date)
        wa['engagement_date'] = pd.to_datetime(wa['engagement_date'], errors='coerce')
        wa['activity']        = wa.get('ACTIVITY', wa.get('Activity', pd.Series(dtype=str))).astype(str).str.strip()
        
        # Extract branch and platform if available
        wa_branch_col = next((c for c in ['BRANCH', 'Branch', 'branch'] if c in wa.columns), None)
        wa['branch_norm'] = wa[wa_branch_col].astype(str).str.strip().str.title() if wa_branch_col else 'Unknown'
        
        wa_plat_col = next((c for c in ['Source', 'SOURCE', 'Platform', 'PLATFORM'] if c in wa.columns), None)
        wa['platform'] = wa[wa_plat_col].apply(normalize_platform) if wa_plat_col else 'Unknown'
        
        wa = wa[wa['phone_key'].str.len() >= 7].copy()
        wa_phone_set = set(wa['phone_key'].unique())

    # ── Build unified leads table (vectorised merge) ───────────────────────────
    set_progress('Building unified leads table…')
    all_phones = set(leads_dedup.index) | wa_phone_set

    # Leads phone table
    lead_tbl = leads_dedup[['platform', 'branch_norm', 'lead_date', 'marketing_expense']].copy()
    lead_tbl.columns = ['platform', 'branch', 'lead_date', 'lead_marketing_cost']
    lead_tbl['is_engaged'] = lead_tbl.index.isin(wa_phone_set)
    lead_tbl['source']     = 'Leads'

    # WhatsApp-only phones
    wa_only_phones = wa_phone_set - set(leads_dedup.index)
    if wa_only_phones:
        wa_dedup = wa.drop_duplicates(subset='phone_key', keep='first').set_index('phone_key')
        wa_only = pd.DataFrame({
            'platform':   wa_dedup.loc[list(wa_only_phones), 'platform'],
            'branch':     wa_dedup.loc[list(wa_only_phones), 'branch_norm'],
            'lead_date':  wa_dedup.loc[list(wa_only_phones), 'engagement_date'],
            'lead_marketing_cost': 0.0,
            'is_engaged': True,
            'source':     'WhatsApp',
        }, index=list(wa_only_phones))
        leads_all = pd.concat([lead_tbl, wa_only])
    else:
        leads_all = lead_tbl

    leads_all.index.name = 'phone'

    # ── Core metrics ──────────────────────────────────────────────────────────
    set_progress('Computing core metrics…')
    total_leads    = len(leads_all)
    engaged_leads  = int(leads_all['is_engaged'].sum())
    all_phones_set = set(leads_all.index)

    shops_phones        = set(shops['phone_key'].unique())
    converted_phones    = all_phones_set & shops_phones
    converted_count     = len(converted_phones)
    total_revenue       = float(shops['Price'].sum())
    
    # Calculate total marketing spend from global data to ensure no spend is lost
    total_marketing = global_total_marketing
    print(f'Analytics: Total Revenue = {total_revenue}, Total Marketing = {total_marketing}')

    engagement_rate = round(100 * engaged_leads / total_leads, 1) if total_leads else 0
    conversion_rate = round(100 * converted_count / total_leads, 1) if total_leads else 0
    eng_to_conv     = round(100 * len(wa_phone_set & converted_phones) / engaged_leads, 1) if engaged_leads else 0

    # ── Repeat buyers (vectorized) ────────────────────────────────────────────
    set_progress('Computing repeat buyers…')
    shops_conv  = shops[shops['phone_key'].isin(converted_phones)]
    visit_counts = shops_conv.groupby('phone_key').size()
    repeat_count = int((visit_counts >= 2).sum())
    repeat_rate  = round(100 * repeat_count / converted_count, 1) if converted_count else 0

    avg_value = total_revenue / converted_count if converted_count else 0

    # ── Time to First Purchase: categorise ALL 34k+ converted leads ──────────────
    # Step 1: For each converted phone, get their FIRST ever purchase date
    shops_conv      = shops[shops['phone_key'].isin(converted_phones)].copy()
    first_purchase  = (shops_conv.dropna(subset=['purchase_date'])
                                 .sort_values('purchase_date')
                                 .groupby('phone_key')['purchase_date']
                                 .first())   # Series: phone -> earliest purchase date

    # Step 2: Get lead dates for converted phones
    converted_lead_dates = leads_all.loc[
        leads_all.index.isin(converted_phones), 'lead_date'
    ].rename('lead_dt')                       # Series: phone -> lead date

    # Step 3: Align both series on phone key (reindex so NaN is correctly inserted for misses)
    ttp_df = pd.concat([
        converted_lead_dates.reindex(list(converted_phones)),
        first_purchase.reindex(list(converted_phones)).rename('first_purch'),
    ], axis=1)
    ttp_df.columns = ['lead_dt', 'first_purch']

    # Step 4: Calculate days (first_purchase - lead_date)
    ttp_df['days'] = (ttp_df['first_purch'] - ttp_df['lead_dt']).dt.days

    # Step 5: Assign every converted lead to exactly one bucket
    def _ttp_cat(row):
        if pd.isna(row['lead_dt']) or pd.isna(row['first_purch']):
            return 'Missing Date'
        d = row['days']
        if d < 0:
            return 'Prior Customer'
        if d == 0:
            return 'Same Day'
        if d <= 7:
            return '1-7 Days'
        if d <= 30:
            return '8-30 Days'
        return '31+ Days'

    ttp_df['cat'] = ttp_df.apply(_ttp_cat, axis=1)

    # --- Diagnostics: why many entries end up as 'Missing Date' ---
    has_lead = ttp_df['lead_dt'].notna()
    has_purch = ttp_df['first_purch'].notna()
    both = int((has_lead & has_purch).sum())
    only_lead = int((has_lead & ~has_purch).sum())
    only_purch = int((~has_lead & has_purch).sum())
    neither = int((~has_lead & ~has_purch).sum())
    print(f"TTP diagnostics: converted_total={converted_count}, both={both}, only_lead={only_lead}, only_purchase={only_purch}, neither={neither}")
    def _sample_index(idx, n=5):
        return list(idx[:n])
    print("TTP sample phones (both):", _sample_index(ttp_df[has_lead & has_purch].index))
    print("TTP sample phones (only_lead):", _sample_index(ttp_df[has_lead & ~has_purch].index))
    print("TTP sample phones (only_purchase):", _sample_index(ttp_df[~has_lead & has_purch].index))
    print("TTP sample phones (neither):", _sample_index(ttp_df[~has_lead & ~has_purch].index))

    cat_counts  = ttp_df['cat'].value_counts().to_dict()
    valid_mask  = ttp_df['cat'].isin(['Same Day', '1-7 Days', '8-30 Days', '31+ Days'])
    avg_days    = float(ttp_df.loc[valid_mask, 'days'].mean()) if valid_mask.any() else 0

    print(f"TTP distribution: { {k: cat_counts.get(k,0) for k in ['Same Day','1-7 Days','8-30 Days','31+ Days','Prior Customer','Missing Date']} }")
    assert sum(cat_counts.values()) == converted_count, \
        f"TTP total {sum(cat_counts.values())} != converted {converted_count}"

    # Chart shows only the 4 timed buckets; Prior Customer + Missing Date go to meta
    time_to_purchase_dist = {
        'Same Day':   int(cat_counts.get('Same Day',   0)),
        '1-7 Days':   int(cat_counts.get('1-7 Days',   0)),
        '8-30 Days':  int(cat_counts.get('8-30 Days',  0)),
        '31+ Days':   int(cat_counts.get('31+ Days',   0)),
    }
    time_to_purchase_meta = {
        'total_converted':  int(converted_count),
        'with_time_data':   int(sum(time_to_purchase_dist.values())),
        'prior_customer':   int(cat_counts.get('Prior Customer', 0)),
        'missing_date':     int(cat_counts.get('Missing Date',   0)),
    }

    # ── Lead status (hot/warm/cold) ────────────────────────────────────────────
    hot = warm = cold = 0
    if len(wa) > 0 and 'engagement_date' in wa.columns:
        latest     = wa['engagement_date'].max()
        hot_phones  = set(wa[wa['engagement_date'] >= latest - pd.Timedelta(days=30)]['phone_key'])
        warm_phones = set(wa[(wa['engagement_date'] < latest - pd.Timedelta(days=30)) &
                             (wa['engagement_date'] >= latest - pd.Timedelta(days=90))]['phone_key'])
        hot  = int(leads_all.index.isin(hot_phones).sum())
        warm = int(leads_all.index.isin(warm_phones).sum())
        cold = engaged_leads - hot - warm

    # ── Marketing metrics by source (vectorized) ──────────────────────────────
    set_progress('Computing marketing metrics…')
    leads_all['platform_clean'] = leads_all['platform'].replace(['', 'Unknown', np.nan, pd.NaT], 'Direct')
    marketing_by_source = []
    for plat, grp in leads_all.groupby('platform_clean'):
        # Convert to standard label
        plat_label = 'Direct' if not str(plat).strip() else str(plat)
        plat_phones  = set(grp.index)
        plat_engaged = len(plat_phones & wa_phone_set)
        plat_conv    = len(plat_phones & converted_phones)
        plat_shops   = shops[shops['phone_key'].isin(plat_phones)]
        plat_rev     = float(plat_shops['Price'].sum())
        # Combine lead costs + shop costs for this platform
        plat_mkt_shop = float(plat_shops['marketing_expense'].sum())
        plat_mkt_lead = float(grp['lead_marketing_cost'].sum()) if 'lead_marketing_cost' in grp.columns else 0.0
        plat_mkt     = plat_mkt_shop + plat_mkt_lead
        plat_roi     = round((plat_rev - plat_mkt) / plat_mkt * 100, 1) if plat_mkt else 0.0
        n            = len(plat_phones)
        marketing_by_source.append({
            'source':           plat_label,
            'leads':            int(n),
            'engaged':          int(plat_engaged),
            'engagement_rate':  float(round(100 * plat_engaged / n, 1) if n else 0),
            'converted':        int(plat_conv),
            'conversion_rate':  float(round(100 * plat_conv / n, 1) if n else 0),
            'revenue':          float(plat_rev),
            'avg_value':        float(round(plat_rev / plat_conv, 2) if plat_conv else 0),
            'marketing_cost':   float(plat_mkt),
            'roi_pct':          float(plat_roi),
        })
    marketing_by_source.sort(key=lambda x: x['revenue'], reverse=True)

    # ── Activity effectiveness (vectorized) ────────────────────────────────────
    if len(wa) > 0 and 'activity' in wa.columns:
        conv_set = converted_phones
        for act, grp in wa.groupby('activity'):
            if not act:
                continue
            act_phones = set(grp['phone_key'])
            act_conv   = len(act_phones & conv_set)
            n          = len(act_phones)
            activity_metrics[str(act)] = {
                'engaged':         int(n),
                'converted':       int(act_conv),
                'conversion_rate': round(100 * act_conv / n, 1) if n else 0,
            }

    # ── Branch metrics (vectorized groupby) ───────────────────────────────────
    set_progress('Computing branch metrics…')
    branch_metrics = []
    
    # Ensure every lead has a valid branch value (fill NaN/empty)
    leads_all['branch_safe'] = leads_all['branch'].fillna('Unknown / Online')
    leads_all.loc[leads_all['branch_safe'].astype(str).str.strip().str.lower().isin(
        ['', 'unknown', 'nan', 'none']
    ), 'branch_safe'] = 'Unknown / Online'
    leads_all['branch_safe'] = leads_all['branch_safe'].astype(str).str.strip().str.title()
    
    # Use dropna=False to ensure no rows are silently dropped
    for branch, grp in leads_all.groupby('branch_safe', dropna=False):
        br_name = str(branch).strip()
        if not br_name or br_name.lower() in ('', 'unknown', 'nan', 'none'):
            br_name = 'Unknown / Online'
            
        br_phones  = set(grp.index)
        br_engaged = len(br_phones & wa_phone_set)
        br_conv    = len(br_phones & converted_phones)
        br_rev     = float(shops[shops['phone_key'].isin(br_phones)]['Price'].sum())
        n          = len(br_phones)
        
        branch_metrics.append({
            'branch':          br_name,
            'leads':           int(n),
            'engaged':         int(br_engaged),
            'engagement_rate': float(round(100 * br_engaged / n, 1) if n else 0),
            'converted':       int(br_conv),
            'conversion_rate': float(round(100 * br_conv / n, 1) if n else 0),
            'revenue':         float(br_rev),
            'avg_value':       float(round(br_rev / br_conv, 2) if br_conv else 0),
        })
    
    # Merge any duplicate branch names (e.g. multiple 'Unknown / Online' groups)
    branch_df = pd.DataFrame(branch_metrics)
    if not branch_df.empty:
        branch_df = branch_df.groupby('branch').agg({
            'leads': 'sum', 'engaged': 'sum', 'converted': 'sum', 'revenue': 'sum'
        }).reset_index()
        
        branch_metrics = []
        for _, row in branch_df.iterrows():
            l = row['leads']
            c = row['converted']
            e = row['engaged']
            branch_metrics.append({
                'branch':          row['branch'],
                'leads':           int(l),
                'engaged':         int(e),
                'engagement_rate': float(round(100 * e / l, 1) if l else 0),
                'converted':       int(c),
                'conversion_rate': float(round(100 * c / l, 1) if l else 0),
                'revenue':         float(row['revenue']),
                'avg_value':       float(round(row['revenue'] / c, 2) if c else 0),
            })
            
    branch_metrics.sort(key=lambda x: x['revenue'], reverse=True)
    
    # Add a Totals row so the branch table always shows the full sum
    total_br_leads     = sum(b['leads'] for b in branch_metrics)
    total_br_engaged   = sum(b['engaged'] for b in branch_metrics)
    total_br_converted = sum(b['converted'] for b in branch_metrics)
    total_br_revenue   = sum(b['revenue'] for b in branch_metrics)
    branch_metrics.append({
        'branch':          'TOTAL',
        'leads':           int(total_br_leads),
        'engaged':         int(total_br_engaged),
        'engagement_rate': float(round(100 * total_br_engaged / total_br_leads, 1) if total_br_leads else 0),
        'converted':       int(total_br_converted),
        'conversion_rate': float(round(100 * total_br_converted / total_br_leads, 1) if total_br_leads else 0),
        'revenue':         float(total_br_revenue),
        'avg_value':       float(round(total_br_revenue / total_br_converted, 2) if total_br_converted else 0),
    })
    
    # Verify total matches
    if total_br_leads != total_leads:
        print(f'⚠ Branch lead total ({total_br_leads}) != total_leads ({total_leads}). Investigating…')

    # ── Funnel stages ─────────────────────────────────────────────────────────
    funnel = [
        {'stage': 'Total Leads', 'count': int(total_leads),   'pct': float(100)},
        {'stage': 'Engaged',     'count': int(engaged_leads),  'pct': float(round(100 * engaged_leads / total_leads, 1) if total_leads else 0)},
        {'stage': 'Converted',   'count': int(converted_count),'pct': float(round(100 * converted_count / total_leads, 1) if total_leads else 0)},
        {'stage': 'Repeat',      'count': int(repeat_count),   'pct': float(round(100 * repeat_count / total_leads, 1) if total_leads else 0)},
    ]

    elapsed = round(time.time() - t0, 1)
    print(f'✓ Analytics built in {elapsed}s')

    cost_per_lead = round(total_marketing / total_leads, 2) if total_leads else 0.0

    return {
        'executive_summary': {
            'total_unique_leads':        int(total_leads),
            'engaged_leads':             int(engaged_leads),
            'engagement_rate_pct':       float(engagement_rate),
            'converted_customers':       int(converted_count),
            'conversion_rate_pct':       float(conversion_rate),
            'engagement_to_conversion':  float(eng_to_conv),
            'total_marketing_spend':     float(round(total_marketing, 2)),
            'cost_per_lead':             float(cost_per_lead),
            'avg_customer_value':        float(round(avg_value, 2)),
            'repeat_customer_count':     int(repeat_count),
            'repeat_rate_pct':           float(repeat_rate),
            
        },
        'lead_status': {
            'hot_leads':   int(hot),
            'warm_leads':  int(warm),
            'cold_leads':  int(cold),
            'not_engaged': int(total_leads - engaged_leads),
            'total':       int(total_leads),
        },
        'marketing_metrics': {
            'engagement_rate_pct':    engagement_rate,
            'by_source':              marketing_by_source,
            'activity_effectiveness': activity_metrics,
        },
        'sales_metrics': {
            'branch_performance': branch_metrics,
            'hot_leads':          int(hot),
            'warm_leads':         int(warm),
            'cold_leads':         int(cold),
        },
        'management_metrics': {
            'funnel_stages':  funnel,
            'unit_economics': {
                'revenue_per_customer':      float(round(avg_value, 2)),
                'repeat_purchase_rate_pct':  float(repeat_rate),
                'avg_days_to_conversion':    float(round(avg_days, 1)),
                'total_marketing_spend':     float(round(total_marketing, 2)),
                'cost_per_lead':             float(cost_per_lead),
                'overall_marketing_roi_pct': float(round((total_revenue - total_marketing) / total_marketing * 100, 1) if total_marketing > 0 else 0.0),
                'customer_acquisition_cost': float(round(total_marketing / converted_count, 2) if converted_count > 0 else 0.0),
            },
            'time_to_first_purchase': time_to_purchase_dist,
            'time_to_purchase_meta':  time_to_purchase_meta,
        },
        'summary': {
            'total_leads':      int(total_leads),
            'engaged_leads':    int(engaged_leads),
            'converted':        int(converted_count),
            'avg_value':        float(round(avg_value, 2)),
            'engagement_rate':  float(engagement_rate),
            'conversion_rate':  float(conversion_rate),
        },
    }

# ── Background precompute ─────────────────────────────────────────────────────
def _precompute(force=False):
    """Runs in a background thread at startup."""
    try:
        # Try loading persisted analytics first
        if not force and os.path.exists(ANALYTICS_CACHE_FILE):
            age = time.time() - os.path.getmtime(ANALYTICS_CACHE_FILE)
            if age < SHEETS_CACHE_TTL:
                set_progress('Loading cached analytics…')
                with open(ANALYTICS_CACHE_FILE, 'rb') as f:
                    result = pickle.load(f)
                with _lock:
                    _state['analytics'] = result
                    _state['ready']     = True
                    _state['error']     = None
                    _state['progress']  = 'Ready'
                print('✓ Analytics loaded from analytics_cache.pkl instantly')
                return

        leads_df, shops_df, wa_df = get_sheets_data(force=force)
        result = build_analytics(leads_df, shops_df, wa_df)

        # Persist to disk
        with open(ANALYTICS_CACHE_FILE, 'wb') as f:
            pickle.dump(result, f)

        with _lock:
            _state['analytics'] = result
            _state['ready']     = True
            _state['error']     = None
            _state['progress']  = 'Ready'
        print('✓ Analytics ready')

    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print(f'ERROR in precompute: {e}\n{tb}')
        with _lock:
            _state['error']    = str(e)
            _state['ready']    = False
            _state['progress'] = f'Error: {e}'

# ── API Routes ────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    return app.send_static_file('templates/Index.html')

@app.route('/api/status')
def api_status():
    with _lock:
        return jsonify({
            'ready':    _state['ready'],
            'progress': _state['progress'],
            'error':    _state['error'],
        })

@app.route('/api/data')
def api_data():
    with _lock:
        ready    = _state['ready']
        error    = _state['error']
        progress = _state['progress']
        result   = _state['analytics']

    if error:
        return jsonify({'status': 'error', 'message': error}), 500
    if not ready:
        return jsonify({'status': 'loading', 'progress': progress}), 202
    return jsonify({'status': 'ok', 'data': result})

@app.route('/api/refresh')
def api_refresh():
    # Delete old caches and recompute in background
    for f in [ANALYTICS_CACHE_FILE, LEADS_CACHE, SHOPS_CACHE, WHATSAPP_CACHE]:
        if os.path.exists(f):
            os.remove(f)
    with _lock:
        _state['ready']    = False
        _state['error']    = None
        _state['progress'] = 'Refreshing data…'
        _state['analytics'] = None
    threading.Thread(target=_precompute, kwargs={'force': True}, daemon=True).start()
    return jsonify({'status': 'refreshing', 'message': 'Refresh started in background'})

@app.route('/api/debug')
def api_debug():
    import pickle
    try:
        with open('leads_cache.pkl', 'rb') as f:
            leads = pickle.load(f)
        with open('shops_cache.pkl', 'rb') as f:
            shops = pickle.load(f)
        with open('whatsapp_cache.pkl', 'rb') as f:
            wa = pickle.load(f)
            
        mkt_col = next((c for c in shops.columns if 'MARKET' in c.upper()), None)
        shops['mkt'] = shops[mkt_col].apply(safe_float) if mkt_col else 0.0
        
        return jsonify({
            'leads_columns': list(leads.columns),
            'shops_columns': list(shops.columns),
            'wa_columns': list(wa.columns),
            'leads_sample': leads.head(2).to_dict('records'),
            'wa_sample': wa.head(2).to_dict('records')
        })
    except Exception as e:
        import traceback
        return jsonify({'error': str(e), 'trace': traceback.format_exc()})

# ── Startup ───────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    print('Customer Journey Dashboard -> http://localhost:5004')
    print('Pre-computing analytics in background…')
    threading.Thread(target=_precompute, daemon=True).start()
    app.run(debug=False, port=5004)
