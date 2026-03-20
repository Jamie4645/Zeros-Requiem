"""Quick test for OANDA API connection."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("Step 1: Importing modules...")
from src.data.oanda_fetcher import (
    fetch_oanda, is_oanda_available, 
    OANDA_API_KEY, OANDA_ACCOUNT_ID, BASE_URL
)
print("  Import OK")

print(f"\nStep 2: Configuration check...")
print(f"  OANDA available: {is_oanda_available()}")
print(f"  API key: {'***' + OANDA_API_KEY[-8:] if OANDA_API_KEY else 'MISSING'}")
print(f"  Account ID: {OANDA_ACCOUNT_ID or 'MISSING'}")
print(f"  Base URL: {BASE_URL}")

print(f"\nStep 3: Testing raw API connection...")
import requests

url = f"{BASE_URL}/v3/accounts/{OANDA_ACCOUNT_ID}"
headers = {
    'Authorization': f'Bearer {OANDA_API_KEY}',
    'Content-Type': 'application/json',
}

try:
    resp = requests.get(url, headers=headers, timeout=10)
    print(f"  Status: {resp.status_code}")
    if resp.status_code == 200:
        print("  Connection OK!")
    else:
        print(f"  Error: {resp.text[:200]}")
except Exception as e:
    print(f"  Connection failed: {e}")

print(f"\nStep 4: Fetching small Gold sample (1D, 1mo)...")
try:
    df = fetch_oanda('GC=F', '1d', '1mo')
    print(f"  Success: {len(df)} candles")
    if len(df) > 0:
        print(f"  From: {df.index[0]}")
        print(f"  To: {df.index[-1]}")
        print(f"  Last close: ${df['Close'].iloc[-1]:.2f}")
except Exception as e:
    print(f"  Fetch failed: {e}")
    import traceback
    traceback.print_exc()

print("\nDone!")
