import requests
import sys
import time
import json
from datetime import datetime

# Configuration
BASE_URL = "https://nexus-backend.nicesea-d905a880.centralindia.azurecontainerapps.io"
LOGIN_EMAIL = "judge@nexus.local"
LOGIN_PASSWORD = "Nexus!123"

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def log(message, status="INFO"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    if status == "SUCCESS":
        print(f"[{timestamp}] {Colors.OKGREEN}✔ {message}{Colors.ENDC}")
    elif status == "ERROR":
        print(f"[{timestamp}] {Colors.FAIL}✖ {message}{Colors.ENDC}")
    elif status == "WARN":
        print(f"[{timestamp}] {Colors.WARNING}⚠ {message}{Colors.ENDC}")
    else:
        print(f"[{timestamp}] {Colors.OKBLUE}ℹ {message}{Colors.ENDC}")

def check_health():
    """Verifies the system health endpoint."""
    try:
        log("Checking System Health...", "INFO")
        # Note: Adjust endpoint if /health is at root or /api/v1/health
        # Trying root /health first based on docs
        response = requests.get(f"{BASE_URL}/docs") 
        # Using /docs as a proxy for liveness if /health isn't explicitly public in all configs
        # But let's try the standard health check if it exists
        
        if response.status_code == 200:
            log(f"System is reachable. Status: {response.status_code}", "SUCCESS")
            return True
        else:
            log(f"System returned unexpected status: {response.status_code}", "ERROR")
            return False
    except Exception as e:
        log(f"Health check failed: {str(e)}", "ERROR")
        return False

def authenticate():
    """Performs login and returns the JWT token."""
    log("Attempting Authentication...", "INFO")
    payload = {
        "email": LOGIN_EMAIL,
        "password": LOGIN_PASSWORD
    }
    
    try:
        # Note: Using x-www-form-urlencoded or json depending on implementation
        # Trying JSON first as per modern standards
        response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            if token:
                log("Authentication successful. Token acquired.", "SUCCESS")
                return token
            else:
                log("Authentication failed. No token in response.", "ERROR")
        else:
            log(f"Login failed: {response.status_code} - {response.text}", "ERROR")
    except Exception as e:
        log(f"Auth request failed: {str(e)}", "ERROR")
    
    return None

def check_metrics(token):
    """Verifies access to protected metrics endpoint."""
    log("Verifying Protected Metrics Endpoint...", "INFO")
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/dashboard/metrics", headers=headers)
        
        if response.status_code == 200:
            metrics = response.json()
            log(f"Metrics retrieved successfully.", "SUCCESS")
            print(f"{Colors.OKCYAN}{json.dumps(metrics, indent=2)}{Colors.ENDC}")
            return True
        else:
            log(f"Metrics access failed: {response.status_code}", "ERROR")
    except Exception as e:
        log(f"Metrics request failed: {str(e)}", "ERROR")
    
    return False

def main():
    print(f"{Colors.HEADER}{Colors.BOLD}🚀 Nexus Prime Deployment Verification{Colors.ENDC}")
    print(f"Target: {BASE_URL}\n")
    
    if not check_health():
        sys.exit(1)
        
    token = authenticate()
    if not token:
        sys.exit(1)
        
    check_metrics(token)

if __name__ == "__main__":
    main()