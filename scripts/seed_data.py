import requests
import json
import time
import random
from datetime import datetime

# Configuration
API_BASE = "http://127.0.0.1:8000/api/v1/ingest/webhook"

# Real-world incident scenarios
INCIDENT_SCENARIOS = [
    {
        "endpoint": "datadog",
        "payload": {
            "title": "Payment Gateway Critical Failure",
            "body": "Payment processing completely down. 100% error rate on all payment attempts. Revenue impact: $50k/hour.",
            "alert_type": "error",
            "tags": ["env:production", "service:payment-gateway", "team:payments", "severity:critical"]
        }
    },
    {
        "endpoint": "prometheus",
        "payload": {
            "alerts": [{
                "status": "firing",
                "labels": {
                    "alertname": "DatabaseConnectionPoolExhausted",
                    "severity": "critical",
                    "instance": "prod-db-01",
                    "job": "postgres"
                },
                "annotations": {
                    "description": "Database connection pool at 98% utilization. Query timeouts detected across all services. User authentication failing.",
                    "summary": "Database Connection Pool Exhausted"
                }
            }]
        }
    },
    {
        "endpoint": "pagerduty",
        "payload": {
            "incident": {
                "title": "API Gateway Rate Limiting Malfunction",
                "description": "Rate limiter blocking legitimate traffic. 40% of API requests rejected. Customer integrations failing.",
                "urgency": "high",
                "service": {"name": "API Gateway"}
            }
        }
    },
    {
        "endpoint": "generic",
        "payload": {
            "title": "Kubernetes Cluster Node Failure",
            "message": "3 out of 8 k8s nodes unresponsive. Pod evictions in progress. Service capacity reduced by 40%.",
            "severity": "critical",
            "source": "kubernetes",
            "tags": ["infrastructure", "kubernetes", "node-failure"]
        }
    },
    {
        "endpoint": "datadog",
        "payload": {
            "title": "CDN Cache Miss Rate Spike",
            "body": "CDN cache miss rate jumped from 5% to 85%. Origin server load increased 15x. Page load times > 10 seconds.",
            "alert_type": "warning",
            "tags": ["env:production", "service:cdn", "team:platform"]
        }
    }
]

def create_incident(scenario):
    """Create a single incident from scenario"""
    url = f"{API_BASE}/{scenario['endpoint']}"
    
    try:
        response = requests.post(url, json=scenario['payload'], timeout=10)
        
        if response.status_code == 202:
            data = response.json()
            print(f"SUCCESS: {scenario['payload'].get('title', 'Incident')}")
            print(f"  ID: {data.get('incident_id', 'Unknown')}")
            print(f"  Source: {scenario['endpoint'].upper()}")
            return True
        else:
            print(f"FAILED: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def seed_realistic_incidents():
    """Create multiple realistic incidents for testing"""
    print("=== NEXUS PRIME - REALISTIC INCIDENT SEEDING ===")
    print(f"Creating {len(INCIDENT_SCENARIOS)} real-world incidents...\n")
    
    success_count = 0
    
    for i, scenario in enumerate(INCIDENT_SCENARIOS, 1):
        print(f"[{i}/{len(INCIDENT_SCENARIOS)}] Creating incident...")
        
        if create_incident(scenario):
            success_count += 1
        
        # Stagger incident creation
        if i < len(INCIDENT_SCENARIOS):
            time.sleep(3)
        print()
    
    print(f"=== RESULTS ===")
    print(f"Successfully created: {success_count}/{len(INCIDENT_SCENARIOS)} incidents")
    print(f"\nCheck dashboard at http://localhost:3000")
    print("Watch incidents progress through analysis and remediation phases")

def seed_single_critical():
    """Create a single critical incident for quick testing"""
    print("Creating single critical incident...")
    
    critical_scenario = {
        "endpoint": "datadog",
        "payload": {
            "title": "High Latency in Payment Gateway",
            "body": "P99 Latency > 3000ms on Checkout Service. Error rate 5%.",
            "alert_type": "error",
            "tags": ["env:production", "service:checkout", "team:payments"]
        }
    }
    
    if create_incident(critical_scenario):
        print("AI Analysis is running in the background...")
        print("Check dashboard for real-time updates")
    else:
        print("Failed to create incident. Is the backend running?")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--realistic":
            seed_realistic_incidents()
        elif sys.argv[1] == "--quick":
            seed_single_critical()
        else:
            print("Usage: python seed_data.py [--realistic|--quick]")
    else:
        seed_single_critical()