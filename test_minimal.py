import pandas as pd
import os
import sys
sys.path.insert(0, '.')

print("TEST 1: Load cache")
leads = pd.read_pickle('leads_cache.pkl')
shops = pd.read_pickle('shops_cache.pkl')
whatsapp = pd.read_pickle('whatsapp_cache.pkl')
print(f"Loaded: {len(leads)}, {len(shops)}, {len(whatsapp)}")

print("\nTEST 2: Test normalize_phone")
from App import normalize_phone
test_phones = leads['CONTACT'].head(3).tolist()
print(f"Sample phones: {test_phones}")
print(f"Normalized: {[normalize_phone(p) for p in test_phones]}")

print("\nTEST 3: Quick analytics test")
leads_short = leads.head(100)
shops_short= shops.head(100)
whatsapp_short = whatsapp.head(100)

from App import build_analytics
result = build_analytics(leads_short, shops_short, whatsapp_short)
print(f"Result keys: {list(result.keys())}")
print(f"Summary: {result['summary']}")
print("\n✓ BASIC TEST COMPLETE")
