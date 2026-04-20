#!/usr/bin/env python3
"""
Test script to show what columns exist in your Google Sheets
"""

import sys
import os
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

os.environ['SSL_CERT_FILE'] = __import__('certifi').where()
os.environ['REQUESTS_CA_BUNDLE'] = __import__('certifi').where()

SERVICE_ACCOUNT_FILE = r'C:\Users\Oduor\Downloads\JSON Files\retention-484110-9e4520124486.json'
SPREADSHEET_ID       = '1zravAS7NoxjnV-2476eBhMitZYQmxWgef3JTbwD-Rag'
SCOPES               = ['https://www.googleapis.com/auth/spreadsheets.readonly']

print("=" * 60)
print("TESTING GOOGLE SHEETS COLUMNS")
print("=" * 60)

try:
    print("\n1. Loading Leads sheet...")
    creds  = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    client = gspread.authorize(creds)
    ss     = client.open_by_key(SPREADSHEET_ID)
    
    leads  = pd.DataFrame(ss.worksheet('Leads_2025').get_all_records())
    print(f"   ✅ Loaded {len(leads)} rows")
    print(f"   Columns: {list(leads.columns)}")
    print(f"   First row: {leads.iloc[0].to_dict() if len(leads) > 0 else 'No data'}")
    
except KeyError as e:
    print(f"   ❌ ERROR: {e}")
except Exception as e:
    print(f"   ❌ ERROR: {e}")

try:
    print("\n2. Loading Shops sheet...")
    shops  = pd.DataFrame(ss.worksheet('Shops').get_all_records())
    print(f"   ✅ Loaded {len(shops)} rows")
    print(f"   Columns: {list(shops.columns)}")
    print(f"   First row: {shops.iloc[0].to_dict() if len(shops) > 0 else 'No data'}")
    
except KeyError as e:
    print(f"   ❌ ERROR: {e}")
except Exception as e:
    print(f"   ❌ ERROR: {e}")

try:
    print("\n3. Loading Whatsapp sheet...")
    whatsapp = pd.DataFrame(ss.worksheet('Whatsapp').get_all_records())
    print(f"   ✅ Loaded {len(whatsapp)} rows")
    print(f"   Columns: {list(whatsapp.columns)}")
    print(f"   First row: {whatsapp.iloc[0].to_dict() if len(whatsapp) > 0 else 'No data'}")
    
except gspread.exceptions.WorksheetNotFound:
    print(f"   ℹ️  Whatsapp sheet not found (this is optional)")
except KeyError as e:
    print(f"   ❌ ERROR: {e}")
except Exception as e:
    print(f"   ❌ ERROR: {e}")

print("\n" + "=" * 60)
print("DONE")
print("=" * 60)
