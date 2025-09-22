#!/usr/bin/env python3
"""
Quick test script to verify the API is working without NFC hardware.
This script tests all the API endpoints except the actual NFC operations.
"""

import requests
import json
import sys


def test_api():
    """Test the API endpoints"""
    base_url = "http://localhost:8000"
    
    print("🧪 Testing Gym NFC Management System API")
    print("=" * 50)
    
    # Test 1: Health check
    print("\n1. Testing health check...")
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("✅ Health check passed")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to API: {e}")
        print("Make sure the server is running: python main.py")
        return False
    
    # Test 2: Login
    print("\n2. Testing authentication...")
    try:
        response = requests.post(
            f"{base_url}/api/auth/login",
            data={"username": "admin", "password": "admin123"}
        )
        if response.status_code == 200:
            data = response.json()
            token = data["access_token"]
            print("✅ Authentication successful")
        else:
            print(f"❌ Authentication failed: {response.json()}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Authentication error: {e}")
        return False
    
    # Headers for authenticated requests
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test 3: Member search
    print("\n3. Testing member search...")
    try:
        response = requests.post(
            f"{base_url}/api/members/search",
            headers=headers,
            json={"query": "John", "limit": 5}
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Member search successful: found {data['total']} members")
        else:
            print(f"❌ Member search failed: {response.json()}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Member search error: {e}")
        return False
    
    # Test 4: Token generation
    print("\n4. Testing token generation...")
    try:
        response = requests.post(
            f"{base_url}/api/tokens/generate",
            headers=headers,
            json={"member_id": 1, "expires_in_days": 365}
        )
        if response.status_code == 200:
            data = response.json()
            generated_token = data["token"]
            print(f"✅ Token generation successful: {generated_token[:20]}...")
        else:
            print(f"❌ Token generation failed: {response.json()}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Token generation error: {e}")
        return False
    
    # Test 5: Token validation
    print("\n5. Testing token validation...")
    try:
        response = requests.get(
            f"{base_url}/api/tokens/{generated_token}/validate",
            headers=headers
        )
        if response.status_code == 200:
            data = response.json()
            print("✅ Token validation successful")
        else:
            print(f"❌ Token validation failed: {response.json()}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Token validation error: {e}")
        return False
    
    # Test 6: NFC reader status (will likely fail without hardware)
    print("\n6. Testing NFC reader status...")
    try:
        response = requests.get(f"{base_url}/api/nfc/status", headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data["success"]:
                print("✅ NFC reader is connected and working")
            else:
                print("⚠️ NFC reader not connected (this is expected without hardware)")
        else:
            print(f"❌ NFC status check failed: {response.json()}")
    except requests.exceptions.RequestException as e:
        print(f"❌ NFC status error: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 API testing completed successfully!")
    print("✅ All core endpoints are working")
    print("📡 To test NFC functionality:")
    print("   1. Connect your ACS ACR122U NFC reader")
    print("   2. Use the CLI: python cli.py interactive")
    print("   3. Or test via API docs: http://localhost:8000/docs")
    
    return True


if __name__ == "__main__":
    success = test_api()
    sys.exit(0 if success else 1)