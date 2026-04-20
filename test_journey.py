import sys
import os

sys.path.append(os.getcwd())
from App import get_sheets_data, build_analytics

leads, shops = get_sheets_data()
analytics = build_analytics(leads, shops)

jd = analytics['conversion_journey']['time_distribution']
avg = analytics['executive_kpis']['avg_time_to_first_purchase']

print("\n--- JOURNEY DISTRIBUTION ---")
for b in jd:
    print(f"{b['bucket']}: {b['count']}")

print(f"\nAverage Time to First Purchase: {avg} days")
