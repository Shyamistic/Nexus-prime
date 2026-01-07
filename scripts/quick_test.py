import requests

BASE_URL = "http://localhost:8000"

try:
    print("Testing incidents endpoint...")
    response = requests.get(f"{BASE_URL}/api/v1/incidents/", timeout=30)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        incidents = response.json()
        print(f"✅ Found {len(incidents)} incidents")
        if incidents:
            print(f"First incident: {incidents[0].get('title', 'No title')}")
    else:
        print(f"❌ Error: {response.text}")
except Exception as e:
    print(f"❌ Exception: {e}")