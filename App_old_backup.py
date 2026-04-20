from flask import Flask, jsonify
from flask_cors import CORS
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
import re
import ssl
import certifi
import os

# Set SSL certificate environment variable
os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

# ── Config ────────────────────────────────────────────────────────────
SERVICE_ACCOUNT_FILE = r'C:\Users\Oduor\Downloads\JSON Files\retention-484110-9e4520124486.json'
SPREADSHEET_ID       = '1zravAS7NoxjnV-2476eBhMitZYQmxWgef3JTbwD-Rag'
SCOPES               = ['https://www.googleapis.com/auth/spreadsheets.readonly']

_cache = {}

MONTH_ORDER = [
    'January','February','March','April','May','June',
    'July','August','September','October','November','December'
]

PLATFORM_ALIASES = {
    'instagram': 'Instagram', 'ig': 'Instagram', 'insta': 'Instagram',
    'tiktok': 'TikTok', 'tik tok': 'TikTok', 'tt': 'TikTok',
    'twitter': 'Twitter', 'x': 'Twitter', 'x (twitter)': 'Twitter',
    'facebook': 'Facebook', 'fb': 'Facebook', 'facebook ads': 'Facebook',
}
PLATFORM_ICONS = {
    'Instagram': '📷', 'TikTok': '🎵', 'Twitter': '𝕏', 'Facebook': 'f'
}

# ── Helpers ────────────────────────────────────────────────────────────
def get_sheets_data(force=False):
    import time
    cache_files = ['leads_cache.pkl', 'shops_cache.pkl', 'whatsapp_cache.pkl']
    if not force and all(os.path.exists(f) for f in cache_files):
        # Only fetch fresh data from sheets if the local cache is older than 6 hours (21600 seconds).
        if time.time() - os.path.getmtime('shops_cache.pkl') < 21600:
            print("Loading 100k+ rows instantly from local cache...")
            return pd.read_pickle('leads_cache.pkl'), pd.read_pickle('shops_cache.pkl'), pd.read_pickle('whatsapp_cache.pkl')

    print("Fetching thousands of rows from Google Sheets... (this takes ~20 seconds)")
    creds  = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    client = gspread.authorize(creds)
    
    ss     = client.open_by_key(SPREADSHEET_ID)
    leads  = pd.DataFrame(ss.worksheet('Leads_2025').get_all_records())
    shops  = pd.DataFrame(ss.worksheet('Shops').get_all_records())
    try:
        whatsapp = pd.DataFrame(ss.worksheet('Whatsapp').get_all_records())
    except Exception as e:
        print(f"Warning: Could not load Whatsapp sheet: {e}. Continuing with empty Whatsapp data.")
        whatsapp = pd.DataFrame()
    
    leads.to_pickle('leads_cache.pkl')
    shops.to_pickle('shops_cache.pkl')
    whatsapp.to_pickle('whatsapp_cache.pkl')
    return leads, shops, whatsapp


def normalize_phone(val):
    digits = re.sub(r'[^\d]', '', str(val))
    return digits[-9:] if len(digits) >= 9 else digits


def normalize_platform(val):
    s = str(val).strip().lower()
    return PLATFORM_ALIASES.get(s, str(val).strip().title())


def parse_lead_date(month_str):
    if not month_str:
        return None
    s = str(month_str).strip()
    # Updated to handle date formats like '02/01/2025'
    for fmt in ['%d/%m/%Y', '%m/%d/%Y', '%Y-%m-%d', '%B %Y', '%b %Y', '%B', '%b', '%m/%Y', '%Y-%m']:
        try:
            dt = datetime.strptime(s, fmt)
            # If format doesn't include year (e.g. '%B', '%b'), it defaults to 1900
            if dt.year == 1900:
                dt = dt.replace(year=2025)
            return dt  # Return the actual parsed date
        except Exception:
            pass
    return None


def safe_float(x):
    try:
        return float(str(x).replace(',', '').strip())
    except Exception:
        return 0.0


# ── Core analytics ────────────────────────────────────────────────────
def build_analytics(leads_df, shops_df, whatsapp_df=None):
    leads = leads_df.copy()
    shops = shops_df.copy()
    whatsapp = whatsapp_df.copy() if whatsapp_df is not None and len(whatsapp_df) > 0 else pd.DataFrame()

    # ── Normalise ────────────────────────────────────────────────────
    print(f"DEBUG: Leads columns: {list(leads.columns)}")
    print(f"DEBUG: Shops columns: {list(shops.columns)}")
    if len(whatsapp) > 0:
        print(f"DEBUG: WhatsApp columns: {list(whatsapp.columns)}")
    
    leads['phone_key']   = leads['CONTACT'].apply(normalize_phone)
    leads['platform']    = leads['Source'].apply(normalize_platform)
    
    # Handle date column - the Leads sheet has 'Date', not 'Month'
    if 'Date' in leads.columns:
        leads['lead_date'] = leads['Date'].apply(parse_lead_date)
    elif 'Month' in leads.columns:
        leads['lead_date'] = leads['Month'].apply(parse_lead_date)
    elif 'DATE' in leads.columns:
        leads['lead_date'] = leads['DATE'].apply(parse_lead_date)
    else:
        print(f"WARNING: No date column found ('Date', 'Month', or 'DATE'). Available columns: {list(leads.columns)}")
        leads['lead_date'] = None
    
    leads['branch_norm'] = leads['BRANCH'].astype(str).str.strip().str.title()
    
    # Convert dates to month period if date was successfully parsed
    try:
        if leads['lead_date'].notna().any():
            leads['lead_month'] = leads['lead_date'].dt.to_period('M').astype(str)
        else:
            leads['lead_month'] = 'Unknown'
    except Exception as e:
        print(f"WARNING: Could not convert lead_date to period: {e}")
        leads['lead_month'] = 'Unknown'

    shops['phone_key']     = shops['Phone'].apply(normalize_phone)
    shops['purchase_date'] = pd.to_datetime(shops['Date'], errors='coerce', dayfirst=True)
    shops['Price']         = shops['Price'].apply(safe_float)
    shops['purchase_month'] = shops['purchase_date'].dt.to_period('M').astype(str) if shops['purchase_date'].notna().any() else 'Unknown'

    # ── Normalise WhatsApp data ────────────────────────────────────────────
    if len(whatsapp) > 0:
        whatsapp['phone_key']       = whatsapp['CONTACT'].apply(normalize_phone) if 'CONTACT' in whatsapp.columns else ''
        whatsapp['engagement_date'] = whatsapp['DATE'].apply(parse_lead_date) if 'DATE' in whatsapp.columns else None
        whatsapp['activity']        = whatsapp['ACTIVITY'].astype(str).str.strip() if 'ACTIVITY' in whatsapp.columns else ''
        whatsapp['source']          = whatsapp['SOURCE'].apply(normalize_platform) if 'SOURCE' in whatsapp.columns else ''
        whatsapp = whatsapp[whatsapp['phone_key'].str.len() >= 7].copy()

    leads = leads[leads['phone_key'].str.len() >= 7].copy()
    shops = shops[shops['phone_key'].str.len() >= 7].copy()
    leads = leads[leads['platform'].str.strip() != ''].copy()

    converted_keys = set(shops['phone_key'].unique()) & set(leads['phone_key'].unique())

    # ── Prepare lead_dates early (needed for engagement analysis) ────────────────────────────────────────────
    first_purchase_df = (
        shops.groupby('phone_key')['purchase_date'].min()
             .reset_index()
             .rename(columns={'purchase_date': 'first_purchase_date'})
    )
    
    lead_dates = leads[['phone_key', 'lead_date']].drop_duplicates('phone_key')
    lead_dates = lead_dates[lead_dates['lead_date'].notna()]  # Only keep rows with valid dates

    # ── WhatsApp Engagement Analysis ────────────────────────────────────────────
    engaged_keys = set()
    engagement_by_activity = {}
    engagement_by_source = {}
    engagement_customer_journey = []
    
    if len(whatsapp) > 0:
        engaged_keys = set(whatsapp['phone_key'].unique())
        
        # Activity-level conversion analysis
        for activity in whatsapp['activity'].unique():
            if not activity or activity == '':
                continue
            activity_leads = set(whatsapp[whatsapp['activity'] == activity]['phone_key'].unique())
            activity_converted = len(activity_leads & converted_keys)
            activity_total = len(activity_leads)
            engagement_by_activity[str(activity)] = {
                'engaged': activity_total,
                'converted': activity_converted,
                'conversion_rate': round(activity_converted / activity_total * 100, 1) if activity_total else 0
            }
        
        # Source-level engagement tracking
        for source in whatsapp['source'].unique():
            if not source or source == '':
                continue
            source_engaged = len(set(whatsapp[whatsapp['source'] == source]['phone_key'].unique()))
            source_converted = len(set(whatsapp[whatsapp['source'] == source]['phone_key'].unique()) & converted_keys)
            engagement_by_source[str(source)] = {
                'engaged': source_engaged,
                'converted': source_converted,
                'conversion_rate': round(source_converted / source_engaged * 100, 1) if source_engaged else 0
            }
        
        # Time from engagement to purchase
        first_engagement = whatsapp.groupby('phone_key')['engagement_date'].min().reset_index()
        first_engagement = first_engagement.rename(columns={'engagement_date': 'first_engagement_date'})
        engagement_jt = lead_dates.merge(first_engagement, on='phone_key', how='right')
        engagement_jt = engagement_jt.merge(first_purchase_df, on='phone_key', how='left')
        engagement_jt = engagement_jt.dropna(subset=['first_engagement_date', 'first_purchase_date'])
        engagement_jt['days_to_purchase'] = (engagement_jt['first_purchase_date'] - engagement_jt['first_engagement_date']).dt.days
        engagement_jt = engagement_jt[engagement_jt['days_to_purchase'] >= 0]
        avg_days_engagement_to_purchase = float(engagement_jt['days_to_purchase'].mean()) if len(engagement_jt) > 0 else 0
    else:
        avg_days_engagement_to_purchase = 0

    # ── Executive Dashboard KPIs ────────────────────────────────────────────
    total_leads     = len(leads)
    total_engaged   = len(engaged_keys)
    engagement_rate = round(total_engaged / total_leads * 100, 1) if total_leads else 0
    
    total_converted = len(converted_keys)
    conv_rate       = round(total_converted / total_leads * 100, 1) if total_leads else 0
    
    # Conversion rate from engagement (of engaged leads, how many converted)
    engagement_to_conversion_rate = round(len(engaged_keys & converted_keys) / total_engaged * 100, 1) if total_engaged else 0
    
    total_revenue   = shops['Price'].sum()
    total_purchases = len(shops)

    qualified     = leads[leads['branch_norm'].str.strip().str.len() > 0]
    qual_count    = len(qualified)
    qual_rate     = round(qual_count / total_leads * 100, 1) if total_leads else 0

    rev_per_cust  = shops.groupby('phone_key')['Price'].sum()
    avg_customer_value = float(rev_per_cust.mean()) if len(rev_per_cust) else 0

    # Time to first purchase
    # (first_purchase_df and lead_dates already defined above)
    
    jt = lead_dates.merge(first_purchase_df, on='phone_key')
    jt = jt.dropna(subset=['lead_date', 'first_purchase_date'])
    jt['days'] = (jt['first_purchase_date'] - jt['lead_date']).dt.days
    jt = jt[jt['days'] >= 0]
    
    # DEBUG: Print journey time calculation details
    print(f"DEBUG: Total leads with dates: {len(lead_dates)}")
    print(f"DEBUG: Total first purchases: {len(first_purchase_df)}")
    print(f"DEBUG: Journey merge result: {len(jt)}")
    print(f"DEBUG: Journey records with both dates: {len(jt.dropna(subset=['lead_date', 'first_purchase_date']))}")
    print(f"DEBUG: Journey records after filtering >=0 days: {len(jt[jt['days'] >= 0])}")
    print(f"DEBUG: Sample journey days: {jt['days'].head(10).tolist() if len(jt) > 0 else 'None'}")
    
    avg_time_to_purchase = float(jt['days'].mean()) if len(jt) else 0
    
    # ── Customer Conversion Journey ────────────────────────────────────────────
    def bucket(d):
        if d == 0:      return 'Same day'
        elif d <= 7:    return '1–7 days'
        elif d <= 30:   return '8–30 days'
        elif d <= 60:   return '31–60 days'
        elif d <= 90:   return '61–90 days'
        else:           return '90+ days'

    bucket_order  = ['Same day', '1–7 days', '8–30 days', '31–60 days', '61–90 days', '90+ days']
    bucket_counts = jt['days'].apply(bucket).value_counts()
    journey_distribution = [
        {'bucket': b, 'count': int(bucket_counts.get(b, 0))} for b in bucket_order
    ]
    
    print(f"DEBUG: Journey distribution: {journey_distribution}")
    print(f"DEBUG: Average time to purchase: {avg_time_to_purchase}")

    # Repeat purchase rate - customers who purchased on 2+ different days
    unique_purchase_days = shops.groupby('phone_key')['purchase_date'].nunique()
    buying_custs = len(unique_purchase_days)
    repeat_buyers = int((unique_purchase_days >= 2).sum())
    repeat_purchase_rate = round(repeat_buyers / buying_custs * 100, 1) if buying_custs else 0

    # Churn rate (customers who haven't purchased in last 30 days)
    latest_date = shops['purchase_date'].max()
    cutoff_date = latest_date - pd.Timedelta(days=30)
    active_customers = set(shops[shops['purchase_date'] >= cutoff_date]['phone_key'])
    churned_customers = buying_custs - len(active_customers)
    churn_rate = round(churned_customers / buying_custs * 100, 1) if buying_custs else 0

    # Best performing platform and branch
    platform_performance = {}
    for plat, grp in leads.groupby('platform'):
        plat_phones = set(grp['phone_key'])
        conv = len(plat_phones & converted_keys)
        rev = float(shops[shops['phone_key'].isin(plat_phones)]['Price'].sum())
        platform_performance[plat] = {'leads': len(grp), 'converted': conv, 'revenue': rev, 'conv_rate': round(conv/len(grp)*100, 1) if len(grp) else 0}
    
    best_platform = max(platform_performance, key=lambda x: platform_performance[x]['revenue']) if platform_performance else 'N/A'
    
    branch_performance = {}
    for branch, grp in leads.groupby('branch_norm'):
        if not str(branch).strip() or str(branch).lower() in ['nan', '']:
            continue
        branch_phones = set(grp['phone_key'])
        conv = len(branch_phones & converted_keys)
        rev = float(shops[shops['phone_key'].isin(branch_phones)]['Price'].sum())
        branch_performance[branch] = {'leads': len(grp), 'converted': conv, 'revenue': rev, 'conv_rate': round(conv/len(grp)*100, 1) if len(grp) else 0}
    
    best_branch = max(branch_performance, key=lambda x: branch_performance[x]['revenue']) if branch_performance else 'N/A'

    # ── Lead Quality Analysis ────────────────────────────────────────────
    lead_quality = []
    for plat, grp in leads.groupby('platform'):
        plat_phones = set(grp['phone_key'])
        conv = len(plat_phones & converted_keys)
        rev = float(shops[shops['phone_key'].isin(plat_phones)]['Price'].sum())
        lead_quality.append({
            'platform': plat,
            'leads': len(grp),
            'converted': conv,
            'conversion_rate': round(conv/len(grp)*100, 1) if len(grp) else 0,
            'revenue': rev,
            'avg_revenue_per_lead': round(rev/len(grp), 2) if len(grp) else 0
        })
    lead_quality.sort(key=lambda x: x['revenue'], reverse=True)

    # ── Customer Conversion Journey ────────────────────────────────────────────
    conversion_by_source = []
    for plat, grp in leads.groupby('platform'):
        plat_phones = set(grp['phone_key'])
        plat_jt = jt[jt['phone_key'].isin(plat_phones)]
        avg_days = float(plat_jt['days'].mean()) if len(plat_jt) else 0
        conversion_by_source.append({
            'platform': plat,
            'avg_days_to_convert': round(avg_days, 1),
            'converted_customers': len(plat_jt)
        })
    
    conversion_by_branch = []
    for branch, grp in leads.groupby('branch_norm'):
        if not str(branch).strip() or str(branch).lower() in ['nan', '']:
            continue
        branch_phones = set(grp['phone_key'])
        branch_jt = jt[jt['phone_key'].isin(branch_phones)]
        avg_days = float(branch_jt['days'].mean()) if len(branch_jt) else 0
        conversion_by_branch.append({
            'branch': branch,
            'avg_days_to_convert': round(avg_days, 1),
            'converted_customers': len(branch_jt)
        })

    # ── Enhanced Funnel Analysis ────────────────────────────────────────────
    # NEW: 5-Stage Funnel with engagement layer
    # Calculate active engaged (recent activity in last 30 days)
    if len(whatsapp) > 0:
        latest_engagement_date = whatsapp['engagement_date'].max()
        cutoff_engagement = latest_engagement_date - pd.Timedelta(days=30) if pd.notna(latest_engagement_date) else pd.Timestamp.min
        active_engaged_keys = set(whatsapp[whatsapp['engagement_date'] >= cutoff_engagement]['phone_key'].unique())
    else:
        active_engaged_keys = set()
    
    # Calculate loyal customers (repeat buyers)
    loyal_customers = len([p for p in unique_purchase_days if unique_purchase_days[p] >= 2])
    
    # Build enhanced 5-stage funnel
    enhanced_funnel = [
        {
            'stage': 'Total Leads',
            'count': total_leads,
            'pct': 100.0,
            'drop_rate': 0.0,
            'description': 'All leads from social media channels'
        },
        {
            'stage': 'Engaged (WhatsApp)',
            'count': total_engaged,
            'pct': round(total_engaged / total_leads * 100, 1) if total_leads else 0,
            'drop_rate': round((total_leads - total_engaged) / total_leads * 100, 1) if total_leads else 0,
            'description': 'Leads transferred to WhatsApp for deeper engagement'
        },
        {
            'stage': 'Active Engaged',
            'count': len(active_engaged_keys),
            'pct': round(len(active_engaged_keys) / total_leads * 100, 1) if total_leads else 0,
            'drop_rate': round((total_engaged - len(active_engaged_keys)) / total_engaged * 100, 1) if total_engaged else 0,
            'description': 'Recent activity in last 30 days (hot leads)'
        },
        {
            'stage': 'First Purchase',
            'count': total_converted,
            'pct': round(total_converted / total_leads * 100, 1) if total_leads else 0,
            'drop_rate': round((len(active_engaged_keys) - total_converted) / len(active_engaged_keys) * 100, 1) if len(active_engaged_keys) else 0,
            'description': 'Converted to first purchase'
        },
        {
            'stage': 'Loyal Customers',
            'count': loyal_customers,
            'pct': round(loyal_customers / total_leads * 100, 1) if total_leads else 0,
            'drop_rate': round((total_converted - loyal_customers) / total_converted * 100, 1) if total_converted else 0,
            'description': 'Repeat customers (2+ purchases)'
        }
    ]
    
    # Calculate engaged leads (proxy for qualified)
    engaged_leads = qualified  # Using qualified as proxy for engaged
    engaged_count = len(engaged_leads)
    
    # Calculate assigned leads (leads assigned to branch)
    assigned_leads = qualified  # Same as qualified for now
    assigned_count = len(assigned_leads)
    
    # Calculate purchased customers
    purchased_count = total_converted
    
    # Calculate repeat customers
    repeat_count = repeat_buyers
    
    # Calculate active customers (recent purchasers)
    active_count = len(active_customers)
    
    old_enhanced_funnel = [
        {
            'stage': 'Total Leads',
            'count': total_leads,
            'pct': 100.0,
            'drop_rate': 0.0
        },
        {
            'stage': 'Engaged Leads',
            'count': engaged_count,
            'pct': round(engaged_count / total_leads * 100, 1) if total_leads else 0,
            'drop_rate': round((total_leads - engaged_count) / total_leads * 100, 1) if total_leads else 0
        },
        {
            'stage': 'Assigned to Branch',
            'count': assigned_count,
            'pct': round(assigned_count / total_leads * 100, 1) if total_leads else 0,
            'drop_rate': round((engaged_count - assigned_count) / engaged_count * 100, 1) if engaged_count else 0
        },
        {
            'stage': 'First Purchase',
            'count': purchased_count,
            'pct': round(purchased_count / total_leads * 100, 1) if total_leads else 0,
            'drop_rate': round((assigned_count - purchased_count) / assigned_count * 100, 1) if assigned_count else 0
        },
        {
            'stage': 'Repeat Purchase',
            'count': repeat_count,
            'pct': round(repeat_count / total_leads * 100, 1) if total_leads else 0,
            'drop_rate': round((purchased_count - repeat_count) / purchased_count * 100, 1) if purchased_count else 0
        },
        {
            'stage': 'Active Customers',
            'count': active_count,
            'pct': round(active_count / total_leads * 100, 1) if total_leads else 0,
            'drop_rate': round((repeat_count - active_count) / repeat_count * 100, 1) if repeat_count else 0
        }
    ]

    # Funnel gap by source
    funnel_by_source = []
    for plat, grp in leads.groupby('platform'):
        plat_phones = set(grp['phone_key'])
        plat_converted = len(plat_phones & converted_keys)
        plat_repeat = len([p for p in plat_phones if p in unique_purchase_days and unique_purchase_days[p] >= 2])
        plat_active = len(plat_phones & active_customers)
        
        funnel_by_source.append({
            'platform': plat,
            'total_leads': len(grp),
            'converted': plat_converted,
            'repeat': plat_repeat,
            'active': plat_active,
            'conversion_rate': round(plat_converted / len(grp) * 100, 1) if len(grp) else 0,
            'repeat_rate': round(plat_repeat / plat_converted * 100, 1) if plat_converted else 0
        })

    # ── Branch Performance Analysis ────────────────────────────────────────────
    branch_analysis = []
    for branch, grp in leads.groupby('branch_norm'):
        if not str(branch).strip() or str(branch).lower() in ['nan', '']:
            continue
        branch_phones = set(grp['phone_key'])
        conv = len(branch_phones & converted_keys)
        # Time to convert for this branch
        branch_jt = jt[jt['phone_key'].isin(branch_phones)]
        avg_days = float(branch_jt['days'].mean()) if len(branch_jt) else 0
        
        # Retention rate (customers who purchased on 2+ different days)
        branch_buyers = unique_purchase_days.reindex(list(branch_phones)).dropna()
        branch_repeat = int((branch_buyers >= 2).sum())
        retention_rate = round(branch_repeat / len(branch_buyers) * 100, 1) if len(branch_buyers) else 0
        
        # Assigned vs actual purchase location
        branch_shops = shops[shops['phone_key'].isin(branch_phones)]
        assigned_branch_purchases = len(branch_shops[branch_shops['Location'] == branch])
        other_branch_purchases = len(branch_shops[branch_shops['Location'] != branch])
        
        rev = float(shops[shops['phone_key'].isin(branch_phones)]['Price'].sum())
        branch_analysis.append({
            'branch': branch,
            'leads_assigned': len(grp),
            'converted': conv,
            'conversion_rate': round(conv / len(grp) * 100, 1) if len(grp) else 0,
            'avg_days_to_convert': round(avg_days, 1),
            'avg_revenue_per_customer': round(rev / conv, 2) if conv else 0,
            'retention_rate': retention_rate,
            'assigned_branch_purchases': assigned_branch_purchases,
            'other_branch_purchases': other_branch_purchases,
            'branch_fidelity': round(assigned_branch_purchases / len(branch_shops) * 100, 1) if len(branch_shops) else 0
        })
    branch_analysis.sort(key=lambda x: x['conversion_rate'], reverse=True)

    # ── Customer Behavior & Retention ────────────────────────────────────
    # Purchase frequency analysis
    customer_behavior = {
        'total_customers': buying_custs,
        'repeat_customers': len([p for p in unique_purchase_days if unique_purchase_days[p] >= 2]),
        'repeat_purchase_rate': round(len([p for p in unique_purchase_days if unique_purchase_days[p] >= 2]) / buying_custs * 100, 1) if buying_custs else 0,
        'avg_purchases_per_customer': round(total_purchases / buying_custs, 2) if buying_custs else 0,
        'single_purchase_customers': int((unique_purchase_days == 1).sum()),
        'multiple_purchase_customers': int((unique_purchase_days >= 2).sum())
    }
    
    # Purchase frequency (days between purchases)
    purchase_freq = []
    for phone, purchases in shops.groupby('phone_key'):
        if len(purchases) > 1:
            dates = sorted(purchases['purchase_date'])
            for i in range(1, len(dates)):
                days_diff = (dates[i] - dates[i-1]).days
                if days_diff > 0 and days_diff <= 365:  # Within a year
                    purchase_freq.append(days_diff)
    
    avg_days_between_purchases = sum(purchase_freq) / len(purchase_freq) if purchase_freq else 0
    
    # Cohort Analysis
    cohorts = []
    for month, grp in leads.groupby('lead_month'):
        month_phones = set(grp['phone_key'])
        month_converted = month_phones & converted_keys
        
        # Track retention over time for this cohort
        cohort_data = {
            'cohort_month': month,
            'initial_leads': len(grp),
            'converted_customers': len(month_converted),
            'retention_data': []
        }
        
        # Calculate retention at different time periods
        for months_after in [1, 2, 3, 6]:
            retained = len([p for p in month_converted if p in active_customers])
            retention_rate = round(retained / len(month_converted) * 100, 1) if len(month_converted) else 0
            cohort_data['retention_data'].append({
                'months_after': months_after,
                'retention_rate': retention_rate
            })
        
        cohorts.append(cohort_data)

    # ── Customer Value (CLV Analysis) ────────────────────────────────────
    clv_analysis = []
    for plat, grp in leads.groupby('platform'):
        plat_phones = set(grp['phone_key'])
        plat_customers = plat_phones & converted_keys
        plat_revenue = float(shops[shops['phone_key'].isin(plat_phones)]['Price'].sum())
        plat_clv = round(plat_revenue / len(plat_customers), 2) if len(plat_customers) else 0
        
        clv_analysis.append({
            'platform': plat,
            'customers': len(plat_customers),
            'total_revenue': plat_revenue,
            'avg_clv': plat_clv
        })
    
    # CLV by Branch
    clv_by_branch = []
    for branch, grp in leads.groupby('branch_norm'):
        if not str(branch).strip() or str(branch).lower() in ['nan', '']:
            continue
        branch_phones = set(grp['phone_key'])
        branch_customers = branch_phones & converted_keys
        branch_revenue = float(shops[shops['phone_key'].isin(branch_phones)]['Price'].sum())
        branch_clv = round(branch_revenue / len(branch_customers), 2) if len(branch_customers) else 0
        
        clv_by_branch.append({
            'branch': branch,
            'customers': len(branch_customers),
            'total_revenue': branch_revenue,
            'avg_clv': branch_clv
        })
    
    # CLV by Gender
    clv_by_gender = []
    for gender, grp in shops.groupby('Gender'):
        gender_phones = set(grp['phone_key'])
        gender_customers = gender_phones & converted_keys
        gender_revenue = float(grp['Price'].sum())
        gender_clv = round(gender_revenue / len(gender_customers), 2) if len(gender_customers) else 0
        
        clv_by_gender.append({
            'gender': gender,
            'customers': len(gender_customers),
            'total_revenue': gender_revenue,
            'avg_clv': gender_clv
        })

    # ── Product Journey Insights ────────────────────────────────────────────
    # First product analysis
    first_products = shops.groupby('phone_key')['Category'].first().value_counts()
    product_paths = []
    
    for category, count in first_products.head(10).items():
        category_customers = set(first_products[first_products == category].index)
        category_repeat = len([c for c in category_customers if c in unique_purchase_days and unique_purchase_days[c] >= 2])
        repeat_likelihood = round(category_repeat / len(category_customers) * 100, 1) if len(category_customers) else 0
        
        product_paths.append({
            'first_category': category,
            'customers': len(category_customers),
            'repeat_customers': category_repeat,
            'repeat_likelihood': repeat_likelihood
        })
    
    # Top product combinations
    product_combinations = shops.groupby('phone_key')['Category'].apply(list)
    common_paths = {}
    for path in product_combinations:
        if len(path) >= 2:
            path_tuple = tuple(path[:2])  # First two products
            common_paths[path_tuple] = common_paths.get(path_tuple, 0) + 1
    
    top_paths = sorted(common_paths.items(), key=lambda x: x[1], reverse=True)[:10]
    top_product_paths = [{'path': list(path), 'count': count} for path, count in top_paths]

    # ── Churn Analysis ────────────────────────────────────────────────────
    # Calculate churn metrics
    churn_analysis = {
        'total_customers': buying_custs,
        'active_customers': len(active_customers),
        'churned_customers': churned_customers,
        'churn_rate': churn_rate,
        'avg_time_to_churn': 0  # Would need more complex analysis for accurate calculation
    }
    
    # Last product before churn (simplified)
    last_products = shops[shops['phone_key'].isin(set(converted_keys) - active_customers)].groupby('phone_key')['Category'].last().value_counts()
    churn_products = [{'product': cat, 'count': int(count)} for cat, count in last_products.head(5).items()]

    # ── Platform x Branch Heatmap ────────────────────────────────────────
    heatmap_data = []
    for branch, grp in leads.groupby('branch_norm'):
        if not str(branch).strip() or str(branch).lower() in ['nan', '']:
            continue
        branch_phones = set(grp['phone_key'])
        values = {}
        
        for plat, plat_grp in leads.groupby('platform'):
            plat_phones = set(plat_grp['phone_key'])
            converted_phones = branch_phones & plat_phones & converted_keys
            values[plat] = {
                'count': len(converted_phones),
                'pct': round(len(converted_phones) / len(branch_phones) * 100, 1) if len(branch_phones) else 0
            }
        
        total_converted = len(branch_phones & converted_keys)
        heatmap_data.append({
            'branch': branch,
            'values': values,
            'total': total_converted
        })
    
    # ── Additional Backwards Compatibility Sections ──
    cat_rev = shops[shops['phone_key'].isin(converted_keys)].groupby('Category')['Price'].sum().reset_index()
    cat_rev = cat_rev.sort_values(by='Price', ascending=False)
    categories = [{'category': row['Category'], 'revenue': int(row['Price'])} for _, row in cat_rev.iterrows()]

    shops['purchase_ym'] = shops['purchase_date'].dt.strftime('%Y-%m')
    current_ym = datetime.now().strftime('%Y-%m')
    valid_shops = shops[(shops['purchase_ym'].notna()) & (shops['purchase_ym'] <= current_ym)]
    pt_df = valid_shops.groupby('purchase_ym').agg(purchases=('phone_key','count'), revenue=('Price','sum')).reset_index()
    purchase_trend = [{'month': row['purchase_ym'], 'purchases': int(row['purchases']), 'revenue': int(row['revenue'])} for _, row in pt_df.sort_values('purchase_ym').iterrows()]

    by_branch_list = []
    for branch, grp in leads.groupby('branch_norm'):
        if not str(branch).strip() or str(branch).lower() in ['nan', '']: continue
        branch_phones = set(grp['phone_key'])
        conv = len(branch_phones & converted_keys)
        rev = float(shops[shops['phone_key'].isin(branch_phones)]['Price'].sum())
        br_unique_days = shops[shops['phone_key'].isin(branch_phones)].groupby('phone_key')['purchase_date'].nunique()
        rep_buyers = int((br_unique_days >= 2).sum())
        top_src_icon = '📱'
        top_src = 'Unknown'
        if len(grp) > 0:
            top_src = str(grp['platform'].value_counts().index[0])
            top_src_icon = PLATFORM_ICONS.get(top_src, '📱')
        by_branch_list.append({
            'branch': branch, 'leads_transferred': len(grp), 'converted': conv,
            'conversion_rate': round(conv / len(grp) * 100, 1) if len(grp) > 0 else 0,
            'repeat_buyers': rep_buyers, 'top_source': top_src, 'top_source_icon': top_src_icon, 'revenue': rev
        })
    by_branch_list.sort(key=lambda x: x['revenue'], reverse=True)

    top_custs = shops[shops['phone_key'].isin(converted_keys)].groupby('phone_key').agg(
        total_revenue=('Price', 'sum'), total_purchases=('purchase_date', 'count')
    ).reset_index().sort_values('total_revenue', ascending=False).head(10)
    
    top_customers_list = []
    for _, row in top_custs.iterrows():
        phone = row['phone_key']
        l_info = leads[leads['phone_key'] == phone]
        s_info = shops[shops['phone_key'] == phone].iloc[0]
        fst_dt_df = first_purchase_df[first_purchase_df['phone_key'] == phone]['first_purchase_date']
        fst = fst_dt_df.iloc[0] if len(fst_dt_df) > 0 else None
        
        has_lead = len(l_info) > 0
        l_first = l_info.iloc[0] if has_lead else None
        ld_dt = l_first['lead_date'] if has_lead else None
        
        days_diff = None
        if fst is not None and pd.notna(fst) and ld_dt is not None and pd.notna(ld_dt):
            days_diff = (fst - ld_dt).days
            if days_diff < 0: days_diff = 0
            
        top_customers_list.append({
            'name': str(l_first.get('NAME', s_info.get('First Name', 'Unknown')))[:-4] + "****" if has_lead else str(s_info.get('First Name', 'Unknown'))[:-2] + "**",
            'source_icon': PLATFORM_ICONS.get(str(l_first['platform']), '📱') if has_lead else '?',
            'source': str(l_first['platform']) if has_lead else 'Unknown',
            'branch': str(l_first['branch_norm']) if has_lead else str(s_info.get('Location', 'Unknown')),
            'lead_month': l_first['lead_month'] if has_lead else 'Unknown',
            'first_purchase': fst.strftime('%Y-%m-%d') if fst is not None and pd.notna(fst) else 'Unknown',
            'days_to_first_purchase': days_diff,
            'total_purchases': int(row['total_purchases']),
            'total_revenue': float(row['total_revenue'])
        })

    # ── Compile Final Analytics ────────────────────────────────────────────
    analytics = {
        # Executive Dashboard - Updated with Engagement Metrics
        'executive_kpis': {
            'total_leads': total_leads,
            'total_engaged': total_engaged,
            'engagement_rate': engagement_rate,
            'engagement_to_conversion_rate': engagement_to_conversion_rate,
            'conversion_rate': conv_rate,
            'avg_time_to_first_purchase': round(avg_time_to_purchase, 1),
            'avg_time_engagement_to_purchase': round(avg_days_engagement_to_purchase, 1),
            'repeat_purchase_rate': repeat_purchase_rate,
            'avg_customer_value': round(avg_customer_value, 2),
            'churn_rate': churn_rate,
            'best_performing_platform': best_platform,
            'best_performing_branch': best_branch
        },
        
        # WhatsApp Engagement Analysis - NEW
        'engagement_analytics': {
            'total_leads': total_leads,
            'engaged_leads': total_engaged,
            'engagement_rate': engagement_rate,
            'active_engaged': len(active_engaged_keys),
            'active_engagement_rate': round(len(active_engaged_keys) / total_engaged * 100, 1) if total_engaged else 0,
            'engaged_converted': len(engaged_keys & converted_keys),
            'engagement_to_conversion': engagement_to_conversion_rate,
            'avg_days_to_purchase_from_engagement': round(avg_days_engagement_to_purchase, 1),
            'by_activity': engagement_by_activity,
            'by_source': engagement_by_source
        },
        
        # Lead Quality
        'lead_quality': lead_quality,
        
        # Customer Conversion Journey
        'conversion_journey': {
            'time_distribution': journey_distribution,
            'by_source': conversion_by_source,
            'by_branch': conversion_by_branch
        },
        
        # Funnel Analysis - Enhanced with engagement stage
        'funnel_analysis': {
            'five_stage_funnel': enhanced_funnel,
            'enhanced_funnel': old_enhanced_funnel,
            'by_source': funnel_by_source
        },
        
        # Branch Performance
        'branch_performance': branch_analysis,
        
        # Customer Behavior & Retention
        'customer_behavior': {
            'behavior_metrics': customer_behavior,
            'avg_days_between_purchases': round(avg_days_between_purchases, 1),
            'cohorts': cohorts
        },
        
        # CLV Analysis
        'clv_analysis': {
            'by_platform': clv_analysis,
            'by_branch': clv_by_branch,
            'by_gender': clv_by_gender
        },
        
        # Product Journey
        'product_journey': {
            'first_product_analysis': product_paths,
            'top_product_paths': top_product_paths
        },
        
        # Churn Analysis
        'churn_analysis': {
            'churn_metrics': churn_analysis,
            'last_products_before_churn': churn_products
        },
        
        # Platform trend for backward compatibility
        'platform_trend': {
            'months': sorted(list(set([m for m in leads['lead_month'].unique() if m != 'Unknown']))) if len(leads) > 0 else [],
            'series': [
                {
                    'platform': str(plat),
                    'icon': PLATFORM_ICONS.get(str(plat), '[PHONE]'),
                    'data': [
                        len(grp[grp['lead_month'] == m])
                        for m in sorted(list(set([m for m in leads['lead_month'].unique() if m != 'Unknown'])))
                    ] if len(leads) > 0 else []
                }
                for plat, grp in leads.groupby('platform')
            ]
        },
        
        # Monthly Funnel Performance
        'by_month': [
            {
                'month': month,
                'leads': len(leads[leads['lead_month'] == month]),
                'qualified': len(leads[(leads['lead_month'] == month) & (leads['branch_norm'].str.strip().str.len() > 0)]),
                'conversions': len(set(leads[leads['lead_month'] == month]['phone_key']) & converted_keys)
            }
            for month in sorted(leads['lead_month'].unique())
            if month != 'Unknown'
        ],
        
        # Additional backward compatibility sections
        'categories': categories,
        'purchase_trend': purchase_trend,
        'top_customers': top_customers_list,
        'by_branch': by_branch_list,
        
        # Platform x Branch Heatmap
        'heatmap': heatmap_data,
        
        # Existing data for backward compatibility
        'summary': {
            'total_leads': int(total_leads),
            'total_qualified': int(qual_count),
            'qualification_rate': float(qual_rate),
            'total_converted': int(total_converted),
            'conversion_rate': float(conv_rate),
            'total_revenue': round(float(total_revenue), 2),
            'avg_revenue_per_customer': round(avg_customer_value, 2),
            'avg_days_to_first_purchase': round(avg_time_to_purchase, 1),
            'repeat_buyers': repeat_buyers,
            'repeat_buyer_rate': float(repeat_purchase_rate),
            'total_purchases': int(total_purchases),
            'total_branches': int(leads['branch_norm'].nunique()),
            'total_platforms': int(leads['platform'].nunique()),
        },
        'funnel': [
            {
                'stage': 'Ad Click & Conversation',
                'icon': '[SPEAK]',
                'count': total_leads,
                'pct': 100.0,
                'description': 'Clicked ad on Instagram / TikTok / Facebook / Twitter and messaged community team'
            },
            {
                'stage': 'Qualified & Branch Transfer',
                'icon': '[OK]',
                'count': qual_count,
                'pct': round(qual_count / total_leads * 100, 1) if total_leads else 0,
                'description': 'Passed community screening and referred to their nearest branch'
            },
            {
                'stage': 'First Purchase',
                'icon': '[CART]',
                'count': total_converted,
                'pct': round(total_converted / total_leads * 100, 1) if total_leads else 0,
                'description': 'Completed at least one purchase at branch'
            },
            {
                'stage': 'Repeat Buyers',
                'icon': '[REPEAT]',
                'count': repeat_buyers,
                'pct': round(repeat_buyers / total_leads * 100, 1) if total_leads else 0,
                'description': 'Returned for two or more purchases — retained customers'
            },
        ],
        'by_platform': [
            {
                'platform': str(plat),
                'icon': PLATFORM_ICONS.get(str(plat), '[PHONE]'),
                'leads': len(grp),
                'qualified': len(grp[grp['branch_norm'].str.strip().str.len() > 0]),
                'converted': len(set(grp['phone_key']) & converted_keys),
                'qualification_rate': round(len(grp[grp['branch_norm'].str.strip().str.len() > 0]) / len(grp) * 100, 1) if len(grp) else 0,
                'conversion_rate': round(len(set(grp['phone_key']) & converted_keys) / len(grp) * 100, 1) if len(grp) else 0,
                'revenue': round(float(shops[shops['phone_key'].isin(set(grp['phone_key']))]['Price'].sum()), 2),
                'avg_revenue_per_customer': round(float(shops[shops['phone_key'].isin(set(grp['phone_key']))]['Price'].sum()) / len(set(grp['phone_key']) & converted_keys), 2) if len(set(grp['phone_key']) & converted_keys) else 0,
            }
            for plat, grp in leads.groupby('platform')
        ],
        'journey_distribution': journey_distribution,
        'avg_days_to_first_purchase': round(avg_time_to_purchase, 1),
        'repeat_rate': repeat_purchase_rate,
        'total_revenue': round(total_revenue, 2),
        'total_purchases': total_purchases,
        'avg_revenue': round(avg_customer_value, 2)
    }
    
    return analytics


# ── Routes ────────────────────────────────────────────────────────────
@app.route('/')
def index():
    return app.send_static_file('templates/Index.html')

@app.route('/api/data')
def api_data():
    try:
        if 'analytics' not in _cache:
            leads_df, shops_df, whatsapp_df = get_sheets_data()
            _cache['analytics'] = build_analytics(leads_df, shops_df, whatsapp_df)
        return jsonify({'status': 'ok', 'data': _cache['analytics']})
    except Exception as e:
        import traceback
        return jsonify({'status': 'error', 'message': str(e), 'trace': traceback.format_exc()}), 500

@app.route('/api/refresh')
def api_refresh():
    try:
        _cache.clear()
        leads_df, shops_df, whatsapp_df = get_sheets_data(force=True)
        _cache['analytics'] = build_analytics(leads_df, shops_df, whatsapp_df)
        return jsonify({'status': 'refreshed'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    print("Customer Journey Dashboard -> http://localhost:5004")
    app.run(debug=True, port=5004)
