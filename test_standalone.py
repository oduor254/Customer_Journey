import pandas as pd
import re

# Standalone version without importing App
print("Loading data...")
leads = pd.read_pickle('leads_cache.pkl')
shops = pd.read_pickle('shops_cache.pkl')
whatsapp = pd.read_pickle('whatsapp_cache.pkl')
print(f"✓ Loaded: {len(leads)}, {len(shops)}, {len(whatsapp)}")

def normalize_phone(phone_str):
    if not isinstance(phone_str, str):
        phone_str = str(phone_str)
    digits = re.sub(r'\D', '', phone_str)[-9:]
    return digits if len(digits) >= 7 else ''

print("\nNormalizing leads...")
leads['phone_key'] = leads['CONTACT'].apply(normalize_phone)
leads = leads[leads['phone_key'].str.len() >= 7]
print(f"✓ Leads with valid phones: {len(leads)}")

print("\nNormalizing shops...")
shops['phone_key'] = shops['Phone'].apply(normalize_phone)
shops = shops[shops['phone_key'].str.len() >= 7]
print(f"✓ Shops with valid phones: {len(shops)}")

print("\nNormalizing WhatsApp...")
whatsapp['phone_key'] = whatsapp['CONTACT'].apply(normalize_phone)
whatsapp = whatsapp[whatsapp['phone_key'].str.len() >= 7]
print(f"✓ WhatsApp with valid phones: {len(whatsapp)}")

print("\nBuilding unified dataset...")
leads_phones = set(leads['phone_key'].unique())
whatsapp_phones = set(whatsapp['phone_key'].unique())
all_phones = leads_phones | whatsapp_phones

print(f"  Leads phones: {len(leads_phones)}")
print(f"  WhatsApp phones: {len(whatsapp_phones)}")
print(f"  WhatsApp-only: {len(whatsapp_phones - leads_phones)}")
print(f"  Total unique: {len(all_phones)}")

print("\nCalculating conversions...")
shop_phones = set(shops['phone_key'].unique())
converted = len(all_phones & shop_phones)
print(f"  Converted: {converted}")

print("\n" + "="*50)
print(f"✓ RESTRUCTURED ANALYTICS TEST COMPLETE")
print(f"  Total unique leads (deduplicated): {len(all_phones):,}")
print(f"  Engaged (WhatsApp): {len(whatsapp_phones):,}")
print(f"  Converted: {converted:,}")
print(f"  Conversion rate: {round(100*converted/len(all_phones), 1)}%")
