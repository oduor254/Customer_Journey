import gspread
from google.oauth2.service_account import Credentials
import time
import ssl
import certifi
import os

# Set SSL certificate environment variable
os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()

SERVICE_ACCOUNT_FILE = r'C:\Users\Oduor\Downloads\JSON Files\retention-484110-9e4520124486.json'
SPREADSHEET_ID = '1zravAS7NoxjnV-2476eBhMitZYQmxWgef3JTbwD-Rag'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

print("Testing Google Sheets connection...")
start_time = time.time()

try:
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    print("Credentials loaded:", time.time() - start_time, "seconds")
    
    client = gspread.authorize(creds)
    print("Client authorized:", time.time() - start_time, "seconds")
    
    ss = client.open_by_key(SPREADSHEET_ID)
    print("Spreadsheet opened:", time.time() - start_time, "seconds")
    
    worksheet = ss.worksheet('Leads_2025')
    print("Worksheet accessed:", time.time() - start_time, "seconds")
    
    data = worksheet.get_all_records()
    print("Data loaded:", time.time() - start_time, "seconds")
    print("Rows loaded:", len(data))
    
except Exception as e:
    print("Error:", str(e))
    print("Time elapsed:", time.time() - start_time, "seconds")
