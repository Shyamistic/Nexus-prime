import requests

BASE_URL = "http://localhost:8000"

def test_dashboard_endpoints():
    print("🔍 Testing Dashboard Endpoints")
    print("=" * 40)
    
    # Test metrics endpoint
    print("\n[1] Testing metrics endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/dashboard/metrics", timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Metrics: {data.get('total_incidents', 0)} total incidents")
            print(f"   Open: {data.get('open_incidents', 0)}")
            print(f"   Investigating: {data.get('investigating_incidents', 0)}")
            print(f"   Resolved: {data.get('resolved_incidents', 0)}")
        else:
            print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Test recent incidents endpoint
    print("\n[2] Testing recent incidents endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/dashboard/recent", timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Recent incidents: {len(data)} found")
            if data:
                first = data[0]
                print(f"   First: {first.get('title', 'No title')}")
                print(f"   Status: {first.get('status', 'Unknown')}")
                print(f"   AI Summary: {first.get('ai_summary', 'None')[:50]}...")
                print(f"   Remediation Steps: {len(first.get('remediation_steps', []))} steps")
        else:
            print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Test direct incidents endpoint for comparison
    print("\n[3] Testing direct incidents endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/incidents/", timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Direct incidents: {len(data)} found")
            if data:
                first = data[0]
                print(f"   First: {first.get('title', 'No title')}")
                print(f"   Status: {first.get('status', 'Unknown')}")
                print(f"   Root Cause: {first.get('root_cause', 'None')[:50]}...")
                print(f"   Recommended Actions: {len(first.get('recommended_actions', []))} actions")
        else:
            print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_dashboard_endpoints()