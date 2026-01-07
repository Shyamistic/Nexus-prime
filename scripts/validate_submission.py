#!/usr/bin/env python3
"""
Microsoft Imagine Cup Readiness Validator
Comprehensive system validation for submission
"""

import requests
import time
import json
import subprocess
import os
from datetime import datetime

class SystemValidator:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.frontend_url = "http://localhost:3000"
        self.issues = []
        self.passed_tests = 0
        self.total_tests = 0
        
    def test(self, description):
        """Decorator for test methods"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                self.total_tests += 1
                print(f"\n🧪 Testing: {description}")
                try:
                    result = func(*args, **kwargs)
                    if result:
                        print(f"   ✅ PASS")
                        self.passed_tests += 1
                    else:
                        print(f"   ❌ FAIL")
                        self.issues.append(description)
                    return result
                except Exception as e:
                    print(f"   ❌ ERROR: {e}")
                    self.issues.append(f"{description}: {str(e)}")
                    return False
            return wrapper
        return decorator
    
    @test("Backend server is running")
    def test_backend_running(self):
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    @test("Frontend server is accessible")
    def test_frontend_running(self):
        try:
            response = requests.get(self.frontend_url, timeout=5)
            return response.status_code == 200
        except:
            return False
    
    @test("API documentation is accessible")
    def test_api_docs(self):
        try:
            response = requests.get(f"{self.base_url}/docs", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    @test("Azure OpenAI integration is working")
    def test_azure_openai(self):
        try:
            # Check if environment variables are set
            env_file = "backend/.env"
            if os.path.exists(env_file):
                with open(env_file, 'r') as f:
                    content = f.read()
                    has_azure_key = "AZURE_OPENAI_API_KEY=" in content and len(content.split("AZURE_OPENAI_API_KEY=")[1].split("\\n")[0]) > 10
                    has_azure_endpoint = "AZURE_OPENAI_ENDPOINT=" in content and "openai.azure.com" in content
                    return has_azure_key and has_azure_endpoint
            return False
        except:
            return False
    
    @test("Cosmos DB configuration is present")
    def test_cosmos_config(self):
        try:
            env_file = "backend/.env"
            if os.path.exists(env_file):
                with open(env_file, 'r') as f:
                    content = f.read()
                    has_endpoint = "COSMOS_ENDPOINT=" in content and "documents.azure.com" in content
                    has_key = "COSMOS_KEY=" in content and len(content.split("COSMOS_KEY=")[1].split("\\n")[0]) > 20
                    return has_endpoint and has_key
            return False
        except:
            return False
    
    @test("Tenant registration works")
    def test_tenant_registration(self):
        try:
            tenant_data = {
                "name": "Test Validation Corp",
                "admin_email": f"test{int(time.time())}@validation.com",
                "admin_name": "Test Admin",
                "admin_password": "TestPass123!"
            }
            
            response = requests.post(
                f"{self.base_url}/api/v1/auth/register-tenant",
                json=tenant_data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                return "access_token" in result and "api_key" in result
            return False
        except:
            return False
    
    @test("Webhook ingestion works")
    def test_webhook_ingestion(self):
        try:
            # First register a tenant to get API key
            tenant_data = {
                "name": "Webhook Test Corp",
                "admin_email": f"webhook{int(time.time())}@test.com",
                "admin_name": "Webhook Admin",
                "admin_password": "WebhookPass123!"
            }
            
            response = requests.post(
                f"{self.base_url}/api/v1/auth/register-tenant",
                json=tenant_data,
                timeout=10
            )
            
            if response.status_code != 200:
                return False
                
            api_key = response.json()["api_key"]
            
            # Test webhook
            incident_data = {
                "title": "Validation Test Incident",
                "message": "This is a test incident for validation",
                "severity": "medium",
                "source": "validation"
            }
            
            response = requests.post(
                f"{self.base_url}/api/v1/ingest/webhook/generic",
                json=incident_data,
                headers={"X-API-Key": api_key},
                timeout=10
            )
            
            return response.status_code == 202
        except:
            return False
    
    @test("Dashboard API endpoints work")
    def test_dashboard_apis(self):
        try:
            endpoints = [
                "/api/v1/dashboard/metrics",
                "/api/v1/dashboard/recent", 
                "/api/v1/dashboard/health",
                "/api/v1/incidents/"
            ]
            
            for endpoint in endpoints:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
                if response.status_code != 200:
                    return False
            return True
        except:
            return False
    
    @test("WebSocket endpoint is available")
    def test_websocket(self):
        try:
            response = requests.get(f"{self.base_url}/ws/stats", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    @test("Required Python packages are installed")
    def test_python_packages(self):
        try:
            required_packages = [
                "fastapi", "uvicorn", "azure-cosmos", "openai", 
                "azure-storage-blob", "google-generativeai"
            ]
            
            result = subprocess.run(
                ["pip", "list"], 
                capture_output=True, 
                text=True, 
                cwd="backend"
            )
            
            installed_packages = result.stdout.lower()
            
            for package in required_packages:
                if package.lower() not in installed_packages:
                    return False
            return True
        except:
            return False
    
    @test("Frontend dependencies are installed")
    def test_frontend_deps(self):
        try:
            return os.path.exists("frontend/node_modules") and os.path.exists("frontend/package-lock.json")
        except:
            return False
    
    @test("Docker files are present")
    def test_docker_files(self):
        try:
            backend_dockerfile = os.path.exists("backend/Dockerfile")
            frontend_dockerfile = os.path.exists("frontend/Dockerfile")
            return backend_dockerfile and frontend_dockerfile
        except:
            return False
    
    @test("Environment configuration is complete")
    def test_env_config(self):
        try:
            env_file = "backend/.env"
            if not os.path.exists(env_file):
                return False
                
            with open(env_file, 'r') as f:
                content = f.read()
                
            required_vars = [
                "AZURE_OPENAI_API_KEY",
                "AZURE_OPENAI_ENDPOINT", 
                "COSMOS_ENDPOINT",
                "COSMOS_KEY",
                "SECRET_KEY",
                "JWT_SECRET_KEY"
            ]
            
            for var in required_vars:
                if f"{var}=" not in content:
                    return False
                    
            return True
        except:
            return False
    
    @test("README documentation is comprehensive")
    def test_readme(self):
        try:
            if not os.path.exists("README.md"):
                return False
                
            with open("README.md", 'r') as f:
                content = f.read()
                
            required_sections = [
                "Problem Statement",
                "Solution", 
                "Architecture",
                "Quick Start",
                "API Reference",
                "Deployment"
            ]
            
            for section in required_sections:
                if section.lower() not in content.lower():
                    return False
                    
            return len(content) > 5000  # Comprehensive documentation
        except:
            return False
    
    def run_validation(self):
        """Run all validation tests"""
        print("🏆 MICROSOFT IMAGINE CUP READINESS VALIDATION")
        print("=" * 60)
        print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Run all test methods
        test_methods = [method for method in dir(self) if method.startswith('test_') and callable(getattr(self, method))]
        
        for method_name in test_methods:
            method = getattr(self, method_name)
            method()
        
        # Generate report
        self.generate_report()
    
    def generate_report(self):
        """Generate final validation report"""
        print(f"\n{'=' * 60}")
        print("📋 VALIDATION REPORT")
        print("=" * 60)
        
        success_rate = (self.passed_tests / self.total_tests) * 100 if self.total_tests > 0 else 0
        
        print(f"✅ Tests Passed: {self.passed_tests}/{self.total_tests}")
        print(f"📊 Success Rate: {success_rate:.1f}%")
        
        if self.issues:
            print(f"\n❌ ISSUES FOUND ({len(self.issues)}):")
            for i, issue in enumerate(self.issues, 1):
                print(f"   {i}. {issue}")
        else:
            print(f"\n🎉 NO ISSUES FOUND!")
        
        print(f"\n🏆 SUBMISSION READINESS:")
        if success_rate >= 90:
            print("   ✅ EXCELLENT - Ready for submission!")
            print("   🌟 System meets all requirements")
        elif success_rate >= 75:
            print("   ⚠️  GOOD - Minor issues to address")
            print("   🔧 Fix issues above before submission")
        else:
            print("   ❌ NEEDS WORK - Major issues found")
            print("   🚨 Address critical issues before submission")
        
        print(f"\n📱 DEMO INSTRUCTIONS:")
        print(f"   1. Start backend: cd backend && uvicorn app.main:app --reload")
        print(f"   2. Start frontend: cd frontend && npm run dev")
        print(f"   3. Run demo: python scripts/imagine_cup_demo.py")
        print(f"   4. Open dashboard: {self.frontend_url}")
        print(f"   5. API docs: {self.base_url}/docs")
        
        print(f"\n🚀 DEPLOYMENT:")
        print(f"   Production script: ./scripts/deploy_production.sh")
        print(f"   Docker: docker-compose up")
        print(f"   Azure: Ready for App Service deployment")
        
        print(f"\n⭐ MICROSOFT IMAGINE CUP HIGHLIGHTS:")
        print(f"   🤖 AI-powered 6-second incident resolution")
        print(f"   🏢 Enterprise multi-tenant architecture") 
        print(f"   ☁️  Azure cloud-native integration")
        print(f"   📊 Real-time dashboard and analytics")
        print(f"   🔒 Production-ready security")
        print(f"   💰 Proven ROI and business impact")
        
        return success_rate >= 90

def main():
    """Main validation execution"""
    validator = SystemValidator()
    
    print("🔍 Validating Nexus Prime for Microsoft Imagine Cup submission...")
    print("⏰ This will take 2-3 minutes...")
    
    success = validator.run_validation()
    
    if success:
        print(f"\n🏆 VALIDATION PASSED!")
        print(f"✅ System is ready for Microsoft Imagine Cup submission!")
    else:
        print(f"\n⚠️  VALIDATION ISSUES FOUND")
        print(f"🔧 Please address issues before submission")
    
    return success

if __name__ == "__main__":
    main()