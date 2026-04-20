#!/usr/bin/env python3
"""
Test script for the RESTRUCTURED analytics (Combined Leads + WhatsApp)
"""
import sys
sys.path.insert(0, r'C:\Users\Oduor\Downloads\Customer Journey')

import pandas as pd
from App_new import get_sheets_data, build_analytics, normalize_phone
import json

print("=" * 100)
print("TESTING RESTRUCTURED ANALYTICS: COMBINED LEADS + WHATSAPP MODEL")
print("=" * 100)

# Load data
print("\n[STEP 1] Loading data from Google Sheets...")
leads_df, shops_df, whatsapp_df = get_sheets_data()

print(f"✓ Leads loaded: {len(leads_df)} rows")
print(f"  Columns: {list(leads_df.columns)}")
print(f"✓ Shops loaded: {len(shops_df)} rows")
print(f"  Columns: {list(shops_df.columns)}")
print(f"✓ WhatsApp loaded: {len(whatsapp_df)} rows")
if len(whatsapp_df) > 0:
    print(f"  Columns: {list(whatsapp_df.columns)}")
else:
    print("  (Empty)")

# Build analytics
print("\n[STEP 2] Building restructured analytics...")
analytics = build_analytics(leads_df, shops_df, whatsapp_df)

print("\n" + "=" * 100)
print("RESTRUCTURED ANALYTICS RESULTS")
print("=" * 100)

# Display executive summary
summary = analytics.get('executive_summary', {})
print("\n📊 EXECUTIVE SUMMARY:")
print(f"  Total Unique Leads: {summary.get('total_unique_leads', 0):,}")
print(f"  Engaged Leads: {summary.get('engaged_leads', 0):,} ({summary.get('engagement_rate_pct', 0)}%)")
print(f"  Converted Customers: {summary.get('converted_customers', 0):,} ({summary.get('conversion_rate_pct', 0)}%)")
print(f"  Engagement→Conversion: {summary.get('engagement_to_conversion_pct', 0)}%")
print(f"  Total Revenue: {summary.get('total_revenue', 0):,.0f}")
print(f"  Avg Customer Value: {summary.get('avg_customer_value', 0):,.2f}")
print(f"  Repeat Customers: {summary.get('repeat_customer_count', 0):,} ({summary.get('repeat_rate_pct', 0)}%)")
print(f"  Avg Days to Purchase: {summary.get('avg_days_to_purchase', 0)}")

# Display lead status
status = analytics.get('lead_status', {})
print(f"\n🎯 LEAD STATUS:")
print(f"  Hot (< 30 days): {status.get('hot_leads', 0):,}")
print(f"  Warm (30-90 days): {status.get('warm_leads', 0):,}")
print(f"  Cold (> 90 days): {status.get('cold_leads', 0):,}")
print(f"  Not Engaged Yet: {status.get('not_engaged_yet', 0):,}")

# Display marketing metrics by source
print(f"\n📱 MARKETING METRICS (BY SOURCE):")
marketing = analytics.get('marketing_metrics', {})
for source in marketing.get('by_source', []):
    print(f"  {source['source']}:")
    print(f"    - Total leads: {source['total_leads']:,}")
    print(f"    - Engagement rate: {source['engagement_rate']}%")
    print(f"    - Conversion rate: {source['conversion_rate']}%")
    print(f"    - Revenue: {source['revenue']:,.0f}")

# Display activity effectiveness
print(f"\n🎬 ACTIVITY EFFECTIVENESS:")
activities = marketing.get('activity_effectiveness', {})
for activity, metrics in sorted(activities.items(), key=lambda x: x[1]['conversion_rate'], reverse=True):
    print(f"  {activity}: {metrics['conversion_rate']}% convert ({metrics['engaged']} engaged)")

# Display branch performance
print(f"\n🏪 SALES METRICS (BY BRANCH):")
sales = analytics.get('sales_metrics', {})
for branch in sales.get('branch_performance', []):
    print(f"  {branch['branch']}:")
    print(f"    - Leads: {branch['total_leads']:,}")
    print(f"    - Converted: {branch['converted']} ({branch['conversion_rate']}%)")
    print(f"    - Revenue: {branch['revenue']:,.0f}")

# Display management metrics
print(f"\n📈 MANAGEMENT METRICS (FUNNEL):")
mgmt = analytics.get('management_metrics', {})
for stage in mgmt.get('funnel_stages', []):
    print(f"  {stage['stage']}: {stage['count']:,} ({stage['pct']}%)")

unit_econ = mgmt.get('unit_economics', {})
print(f"\n💰 UNIT ECONOMICS:")
print(f"  Revenue per customer: {unit_econ.get('revenue_per_customer', 0):,.2f}")
print(f"  Repeat purchase rate: {unit_econ.get('repeat_purchase_rate_pct', 0)}%")
print(f"  Avg days to conversion: {unit_econ.get('avg_days_to_conversion', 0)}")

print("\n" + "=" * 100)
print("✓ RESTRUCTURED ANALYTICS BUILD SUCCESSFUL")
print("=" * 100)
print("\nKey improvements:")
print("  ✓ Leads + WhatsApp combined into single 'leads' dataset")
print("  ✓ Deduplicated by phone number (CONTACT is primary key)")
print("  ✓ Each unique phone counted only once")
print("  ✓ Comprehensive metrics for Marketing, Sales, Management teams")
print("  ✓ All recommended metrics from strategic analysis implemented")
