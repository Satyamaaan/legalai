#!/usr/bin/env python3
"""
Quick integration test for the LegalAI backend.
"""

import requests
import time
import json

BASE_URL = "http://localhost:5001"

def test_integration():
    print("🧪 Testing LegalAI Backend Integration")
    print("=" * 50)
    
    # Test 1: Health checks
    print("1. Testing health endpoints...")
    
    endpoints = [
        "/health",
        "/api/upload/health", 
        "/api/translate/health",
        "/api/download/health"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}")
            if response.status_code == 200:
                print(f"   ✅ {endpoint} - OK")
            else:
                print(f"   ❌ {endpoint} - Error {response.status_code}")
        except Exception as e:
            print(f"   ❌ {endpoint} - Connection failed: {e}")
    
    # Test 2: Upload endpoint
    print("\n2. Testing upload endpoint...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/upload/signed-url",
            json={"filename": "test.pdf", "content_type": "application/pdf"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Upload endpoint - OK")
            print(f"   📄 Job ID: {data.get('job_id')}")
            print(f"   📁 File ID: {data.get('file_id')}")
            return data.get('job_id')
        else:
            print(f"   ❌ Upload endpoint - Error {response.status_code}")
            print(f"   📝 Response: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Upload endpoint - Error: {e}")
    
    return None

if __name__ == "__main__":
    test_integration()