#!/usr/bin/env python3
import pandas as pd
import os

print("START")

# Load from cache
leads_df = pd.read_pickle('leads_cache.pkl')
shops_df = pd.read_pickle('shops_cache.pkl')
whatsapp_df = pd.read_pickle('whatsapp_cache.pkl')

print(f"DATA LOADED: {len(leads_df)} leads, {len(shops_df)} shops, {len(whatsapp_df)} whatsapp")

# Import
from App import normalize_phone
print("normalize_phone imported")

# Test normalize_phone
test_phone = leads_df['CONTACT'].iloc[0]
print(f"Test phone: {test_phone} -> {normalize_phone(test_phone)}")

# Try building
from App import build_analytics
print("build_analytics imported, starting build...")

try:
    analytics = build_analytics(leads_df, shops_df, whatsapp_df)
    print("BUILD COMPLETE")
    print(f"Summary: {analytics.get('executive_summary', {})}")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
