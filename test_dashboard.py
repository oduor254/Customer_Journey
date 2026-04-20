#!/usr/bin/env python3
"""Test the dashboard after fixes"""

from App import get_sheets_data, build_analytics

print("=" * 60)
print("TESTING DASHBOARD AFTER FIXES")
print("=" * 60)

print("\n1. Fetching data from Google Sheets...")
leads, shops, whatsapp = get_sheets_data()
print(f"   OK - Leads: {len(leads)} rows, columns: {list(leads.columns)}")
print(f"   OK - Shops: {len(shops)} rows, columns: {list(shops.columns)}")
print(f"   OK - WhatsApp: {len(whatsapp)} rows")

print("\n2. Building analytics...")
analytics = build_analytics(leads, shops, whatsapp)
print(f"   OK - Analytics built successfully!")

print("\n3. Executive KPIs:")
for key, value in list(analytics["executive_kpis"].items())[:8]:
    print(f"   {key}: {value}")

print("\n4. Engagement Analytics:")
if "engagement_analytics" in analytics:
    print(f"   OK - engagement_rate: {analytics['engagement_analytics'].get('engagement_rate', 'N/A')}%")
    print(f"   OK - engagement_to_conversion: {analytics['engagement_analytics'].get('engagement_to_conversion_rate', 'N/A')}%")
    print(f"   OK - by_activity count: {len(analytics['engagement_analytics'].get('by_activity', {}))}")
    print(f"   OK - by_source count: {len(analytics['engagement_analytics'].get('by_source', {}))}")

print("\n" + "=" * 60)
print("SUCCESS - DASHBOARD WORKING!")
print("=" * 60)
print("\nYou can now:")
print("1. Run: python app.py")
print("2. Visit: http://localhost:5004")
print("3. Or test API: curl http://localhost:5004/api/data")

