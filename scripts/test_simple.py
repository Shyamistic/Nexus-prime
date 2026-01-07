#!/usr/bin/env python3
"""
Simple System Test - Debug Version
"""

import requests
import time

BASE_URL = "http://localhost:8000"
API_KEY = "nexus_YaTvj5MmL-U6Mz_Qml0BfDDqnygNXbo0-OALx_arOdE"

def main():
    print("🚀 NEXUS PRIME - SIMPLE TEST")
    print("=" * 40)
    
    try:
        # Test 1: Health check
        print("\n[1] Testing health endpoint...")
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Backend is running")
        else:
            print("❌ Backend health check failed")
            return
        
        # Test 2: Create one incident
        print("\n[2] Creating test incident...")
        incident = {
            "title": "Test Database Issue",
            "message": "Database connection timeout detected",
            "severity": "high",
            "source": "datadog"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/ingest/webhook/generic",
            json=incident,
            headers={"X-API-Key": API_KEY},
            timeout=10
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 202:
            result = response.json()
            incident_id = result["incident_id"]
            print(f"✅ Created incident: {incident_id[:8]}...")
        else:
            print(f"❌ Failed to create incident: {response.text}")
            return
        
        # Test 3: Get incidents
        print("\n[3] Fetching incidents...")
        response = requests.get(f"{BASE_URL}/api/v1/incidents/", timeout=15)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            incidents = response.json()
            print(f"✅ Found {len(incidents)} incidents")
            if incidents:
                print(f"First incident: {incidents[0].get('title', 'No title')}")
        else:
            print(f"❌ Failed to get incidents: {response.text}")
        
        # Test 4: Dashboard metrics
        print("\n[4] Testing dashboard...")
        response = requests.get(f"{BASE_URL}/api/v1/dashboard/metrics", timeout=5)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            metrics = response.json()
            print(f"✅ Total incidents: {metrics.get('total_incidents', 0)}")
        else:
            print(f"❌ Dashboard failed: {response.text}")
        
        print("\n✅ Basic system test complete!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend")
        print("Start backend with: uvicorn app.main:app --reload --app-dir backend --port 8000")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()