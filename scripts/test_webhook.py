import requests
import json

# Use the API key from your test
API_KEY = "nexus_gqLJuK0lwJ1BjL"  # Replace with your actual key

def test_webhook():
    url = "http://localhost:8000/api/v1/ingest/webhook/generic"
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    incident_data = {
        "title": "Database Connection Timeout",
        "message": "Users unable to access application due to database timeouts",
        "severity": "high",
        "source": "generic"
    }
    
    print("Testing webhook endpoint...")
    response = requests.post(url, headers=headers, json=incident_data)
    
    if response.status_code == 202:
        print("✅ Webhook test successful!")
        result = response.json()
        print(f"Status: {result.get('status')}")
        print(f"Incident ID: {result.get('incident_id')}")
        print("🔍 AI analysis will complete in ~10 seconds...")
    else:
        print(f"❌ Webhook test failed: {response.status_code}")
        print(f"Error: {response.text}")

if __name__ == "__main__":
    test_webhook()