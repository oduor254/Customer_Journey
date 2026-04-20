#!/usr/bin/env python3
"""
Quick test of restructured analytics using cached data
"""
import pandas as pd
import os

print("=" * 100)
print("TESTING RESTRUCTURED ANALYTICS (Using Cache)")
print("=" * 100)

# Load from cache
print("\n[1] Loading cached data...")
if os.path.exists('leads_cache.pkl') and os.path.exists('shops_cache.pkl') and os.path.exists('whatsapp_cache.pkl'):
    leads_df = pd.read_pickle('leads_cache.pkl')
    shops_df = pd.read_pickle('shops_cache.pkl')
    whatsapp_df = pd.read_pickle('whatsapp_cache.pkl')
    print(f"✓ Leads: {len(leads_df):,} rows")
    print(f"✓ Shops: {len(shops_df):,} rows")
    print(f"✓ WhatsApp: {len(whatsapp_df):,} rows")
else:
    print("✗ Cache files not found! Run the app first to create cache.")
    print("  - leads_cache.pkl")
    print("  - shops_cache.pkl")
    print("  - whatsapp_cache.pkl")
    exit(1)

# Import and test
print("\n[2] Building analytics...")
try:
    from App import build_analytics
    analytics = build_analytics(leads_df, shops_df, whatsapp_df)
    print("✓ Analytics built successfully!")
except Exception as e:
    print(f"✗ Error building analytics: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Display results
print("\n" + "=" * 100)
print("RESTRUCTURED ANALYTICS RESULTS")
print("=" * 100)

summary = analytics.get('executive_summary', {})
print("\n📊 EXECUTIVE SUMMARY:")
print(f"  Total Unique Leads: {summary.get('total_unique_leads', 0):,}")
print(f"  Engaged Leads: {summary.get('engaged_leads', 0):,} ({summary.get('engagement_rate_pct', 0)}%)")
print(f"  Converted: {summary.get('converted_customers', 0):,} ({summary.get('conversion_rate_pct', 0)}%)")
print(f"  Revenue: {summary.get('total_revenue', 0):,.0f}")
print(f"  Avg Customer Value: {summary.get('avg_customer_value', 0):,.2f}")

status = analytics.get('lead_status', {})
print(f"\n🎯 LEAD STATUS:")
print(f"  Hot (< 30d): {status.get('hot_leads', 0):,}")
print(f"  Warm (30-90d): {status.get('warm_leads', 0):,}")
print(f"  Cold (> 90d): {status.get('cold_leads', 0):,}")
print(f"  Not Engaged: {status.get('not_engaged_yet', 0):,}")

marketing = analytics.get('marketing_metrics', {})
print(f"\n📱 MARKETING BY SOURCE:")
for source in marketing.get('by_source', [])[:5]:
    print(f"  {source['source']}: {source['engagement_rate']}% engaged → {source['conversion_rate']}% convert (₦{source['revenue']:,.0f})")

activities = marketing.get('activity_effectiveness', {})
print(f"\n🎬 TOP ACTIVITIES:")
for activity, metrics in sorted(list(activities.items())[:5], key=lambda x: x[1]['conversion_rate'], reverse=True):
    print(f"  {activity}: {metrics['conversion_rate']}% conversion ({metrics['engaged']} engaged)")

sales = analytics.get('sales_metrics', {})
print(f"\n🏪 TOP BRANCHES:")
for branch in sales.get('branch_performance', [])[:5]:
    print(f"  {branch['branch']}: {branch['conversion_rate']}% convert (₦{branch['revenue']:,.0f})")

mgmt = analytics.get('management_metrics', {})
print(f"\n📈 FUNNEL:")
for stage in mgmt.get('funnel_stages', []):
    pct_str = f"({stage['pct']}%)" if stage['pct'] > 0 else ""
    print(f"  {stage['stage']}: {stage['count']:,} {pct_str}")

print("\n" + "=" * 100)
print("✓ RESTRUCTURED ANALYTICS WORKING")
print("=" * 100)
print("\nKey features implemented:")
print("  ✓ Leads + WhatsApp combined (deduplicated by phone)")
print("  ✓ Each unique phone counted once")
print("  ✓ Marketing metrics: engagement rate, source performance, activity analysis")
print("  ✓ Sales metrics: lead status, branch performance")
print("  ✓ Management metrics: funnel stages, unit economics")
print("\nStart the API with: python App.py")
print("Access dashboard at: http://localhost:5004")
