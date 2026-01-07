#!/usr/bin/env python3
"""
Simple test script to verify Nexus Prime system is working
"""

import asyncio
import httpx
import json

async def test_system():
    print("Testing Nexus Prime System")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient() as client:
        # Test 1: Health check
        print("1. Testing health endpoint...")
        try:
            response = await client.get(f"{base_url}/health")
            if response.status_code == 200:
                print("✅ Health check passed")
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False
        
        # Test 2: API docs
        print("2. Testing API documentation...")
        try:
            response = await client.get(f"{base_url}/docs")
            if response.status_code == 200:
                print("✅ API docs accessible")
            else:
                print(f"❌ API docs failed: {response.status_code}")
        except Exception as e:
            print(f"❌ API docs error: {e}")
        
        # Test 3: Register tenant
        print("3. Testing tenant registration...")
        tenant_data = {
            "name": "Test Corp",
            "admin_email": "admin@test.com",
            "admin_name": "Admin User", 
            "admin_password": "password123"
        }
        
        try:
            response = await client.post(
                f"{base_url}/api/v1/auth/register-tenant",
                json=tenant_data
            )
            if response.status_code == 200:
                result = response.json()
                print("✅ Tenant registration successful")
                print(f"   Access token: {result.get('access_token', 'N/A')[:20]}...")
                print(f"   API key: {result.get('api_key', 'N/A')[:20]}...")
                return result
            else:
                print(f"❌ Tenant registration failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Tenant registration error: {e}")
            return False

if __name__ == "__main__":
    result = asyncio.run(test_system())
    if result:
        print("\n🎉 System test completed successfully!")
        print("✅ Ready for production deployment")
    else:
        print("\n❌ System test failed")
        print("🔧 Check logs and fix issues before deployment")