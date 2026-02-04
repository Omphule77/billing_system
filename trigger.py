import requests
import time

print("Attempting to trigger send_bill_whatsapp...")
try:
    # Use IDs that likely don't exist or might exist, just to hit the code path
    # ID=1, HotelID=1, BillNo=1
    url = 'http://127.0.0.1:5000/send_bill_whatsapp/1/1/1'
    print(f"Sending POST to {url}")
    # Reduce timeout to fail fast if needed, but 120s is safe for WA
    r = requests.post(url, timeout=120)
    print(f"Status Code: {r.status_code}")
    print(f"Response Body: {r.text}")
except Exception as e:
    print(f"Request failed: {e}")
