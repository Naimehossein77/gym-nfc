#!/usr/bin/env python3
"""
Test script for the Apple Wallet pass signing endpoint
"""

import requests
import json
import base64
import os

# Configuration
API_BASE_URL = "http://localhost:8001"
USERNAME = "admin"
PASSWORD = "admin123"


def login():
    """Login and get JWT token"""
    response = requests.post(
        f"{API_BASE_URL}/api/auth/login",
        data={"username": USERNAME, "password": PASSWORD}
    )
    
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        raise Exception(f"Login failed: {response.json()}")


def test_certificate_status(token):
    """Test the certificate status endpoint"""
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(
        f"{API_BASE_URL}/api/pass/certificates/status",
        headers=headers
    )
    
    print("Certificate Status:")
    print(json.dumps(response.json(), indent=2))
    return response.json()


def test_pass_signing(token):
    """Test the pass signing endpoint"""
    headers = {"Authorization": f"Bearer {token}"}
    
    # Example NFC token (base64 encoded)
    nfc_message = base64.b64encode("EXAMPLE_NFC_TOKEN_DATA_12345".encode()).decode()
    
    # Pass data matching the Flutter example
    pass_data = {
        "serialNumber": "USER123456",
        "description": "NFC Access Test",
        "organizationName": "New Life Fitness",
        "passTypeIdentifier": "pass.com.newlife.fitness",
        "teamIdentifier": "C4JDUP99R7",
        "nfc": {
            "message": nfc_message
        }
    }
    
    print(f"\nSigning pass with data:")
    print(json.dumps(pass_data, indent=2))
    
    response = requests.post(
        f"{API_BASE_URL}/api/pass/sign",
        headers=headers,
        json=pass_data
    )
    
    if response.status_code == 200:
        # Save the .pkpass file
        filename = "test_nfc_access.pkpass"
        with open(filename, "wb") as f:
            f.write(response.content)
        
        print(f"\n✅ Pass signed successfully!")
        print(f"📁 Saved to: {filename}")
        print(f"📏 File size: {len(response.content)} bytes")
        print(f"📋 Content-Type: {response.headers.get('content-type')}")
        
        return True
    else:
        print(f"\n❌ Pass signing failed:")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        return False


def main():
    """Main test function"""
    print("🧪 Testing Apple Wallet Pass Signing API")
    print("=" * 50)
    
    try:
        # Login
        print("🔐 Logging in...")
        token = login()
        print("✅ Login successful")
        
        # Check certificate status
        print("\n📋 Checking certificate status...")
        cert_status = test_certificate_status(token)
        
        if not cert_status.get("ready", False):
            print("\n⚠️ Warning: Not all certificate files are present.")
            print("The signing will likely fail with OpenSSL errors.")
            print("See ./certs/README.md for setup instructions.")
        
        # Test pass signing
        print("\n🔏 Testing pass signing...")
        success = test_pass_signing(token)
        
        if success:
            print("\n🎉 All tests passed!")
            print("\nNext steps:")
            print("1. Replace placeholder certificates with real Apple certificates")
            print("2. Test with a real iOS device")
            print("3. Integrate with your Flutter app")
        else:
            print("\n❌ Pass signing test failed")
            print("Check the server logs for more details")
            
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")


if __name__ == "__main__":
    main()