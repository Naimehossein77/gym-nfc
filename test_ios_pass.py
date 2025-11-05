#!/usr/bin/env python3
"""
Test script to generate and validate Apple Wallet pass with real certificate values
"""

import requests
import json
import sys
from pathlib import Path

# API Configuration
BASE_URL = "http://192.168.1.1:8001"  # Your router/server IP
USERNAME = "admin"
PASSWORD = "admin123"

def login():
    """Login and get JWT token"""
    login_data = {
        "username": USERNAME,
        "password": PASSWORD
    }
    
    print("🔐 Logging in...")
    response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
    
    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code} - {response.text}")
        return None
    
    token_data = response.json()
    print(f"✅ Login successful")
    return token_data["access_token"]

def generate_pass(token):
    """Generate Apple Wallet pass with real certificate values"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Updated with real values from your certificate
    pass_data = {
        "serialNumber": "TEST123456",
        "description": "NFC Access Card",
        "organizationName": "New Life Fitness",
        "passTypeIdentifier": "pass.com.newlife.fitness",  # Real value from cert
        "teamIdentifier": "C4JDUP99R7",  # Real value from cert
        "nfc": {
            "message": "QkFTRTY0RU5DT0RFRE1FU1NBR0U="  # Base64 test message
        }
    }
    
    print("🎫 Generating Apple Wallet pass...")
    print(f"   Team ID: {pass_data['teamIdentifier']}")
    print(f"   Pass Type: {pass_data['passTypeIdentifier']}")
    
    response = requests.post(
        f"{BASE_URL}/api/pass/sign",
        json=pass_data,
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"❌ Pass generation failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return None
    
    # Save the .pkpass file
    output_file = "test_nfc_access.pkpass"
    with open(output_file, "wb") as f:
        f.write(response.content)
    
    print(f"✅ Pass generated successfully: {output_file}")
    print(f"   File size: {len(response.content)} bytes")
    
    return output_file

def validate_pass_structure(pkpass_file):
    """Validate the internal structure of the .pkpass file"""
    import zipfile
    import hashlib
    
    print(f"\n🔍 Validating pass structure: {pkpass_file}")
    
    try:
        with zipfile.ZipFile(pkpass_file, 'r') as zip_file:
            file_list = zip_file.namelist()
            print(f"   Files in pass: {file_list}")
            
            # Check required files
            required_files = ["pass.json", "manifest.json", "signature"]
            missing_files = [f for f in required_files if f not in file_list]
            
            if missing_files:
                print(f"❌ Missing required files: {missing_files}")
                return False
            
            print("✅ All required files present")
            
            # Validate pass.json
            with zip_file.open("pass.json") as f:
                pass_data = json.loads(f.read().decode('utf-8'))
                print(f"   Pass Type ID: {pass_data.get('passTypeIdentifier')}")
                print(f"   Team ID: {pass_data.get('teamIdentifier')}")
                print(f"   Serial: {pass_data.get('serialNumber')}")
                print(f"   Format Version: {pass_data.get('formatVersion')}")
                
                # Check critical fields
                critical_fields = ["passTypeIdentifier", "teamIdentifier", "serialNumber", "formatVersion"]
                for field in critical_fields:
                    if field not in pass_data:
                        print(f"❌ Missing critical field: {field}")
                        return False
                
                print("✅ Pass.json structure valid")
            
            # Validate manifest integrity
            with zip_file.open("manifest.json") as f:
                manifest = json.loads(f.read().decode('utf-8'))
                print(f"   Manifest entries: {len(manifest)}")
                
                # Verify hashes
                hash_errors = []
                for filename, expected_hash in manifest.items():
                    if filename in file_list:
                        with zip_file.open(filename) as file_content:
                            actual_hash = hashlib.sha1(file_content.read()).hexdigest()
                            if actual_hash != expected_hash:
                                hash_errors.append(f"{filename}: expected {expected_hash}, got {actual_hash}")
                
                if hash_errors:
                    print(f"❌ Hash verification failed:")
                    for error in hash_errors:
                        print(f"     {error}")
                    return False
                
                print("✅ Manifest hash verification passed")
            
            # Check signature file
            signature_info = zip_file.getinfo("signature")
            print(f"   Signature size: {signature_info.file_size} bytes")
            
            if signature_info.file_size == 0:
                print("❌ Signature file is empty")
                return False
            
            print("✅ Signature file present and non-empty")
            
    except zipfile.BadZipFile:
        print("❌ Invalid ZIP file format")
        return False
    except Exception as e:
        print(f"❌ Validation error: {e}")
        return False
    
    print("✅ Pass structure validation completed successfully")
    return True

def check_certificate_status(token):
    """Check certificate status on server"""
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n🔒 Checking certificate status...")
    response = requests.get(f"{BASE_URL}/api/pass/certificates/status", headers=headers)
    
    if response.status_code != 200:
        print(f"❌ Certificate check failed: {response.status_code}")
        return False
    
    status = response.json()
    print(f"   Ready for signing: {status.get('ready', False)}")
    
    for cert_name, cert_info in status.get('certificates', {}).items():
        exists = cert_info.get('exists', False)
        status_icon = "✅" if exists else "❌"
        print(f"   {status_icon} {cert_info.get('description', cert_name)}")
    
    return status.get('ready', False)

def main():
    print("🧪 iOS Apple Wallet Pass Test")
    print("=" * 50)
    
    # Step 1: Login
    token = login()
    if not token:
        sys.exit(1)
    
    # Step 2: Check certificates
    if not check_certificate_status(token):
        print("\n❌ Certificates not ready - check server setup")
        sys.exit(1)
    
    # Step 3: Generate pass
    pkpass_file = generate_pass(token)
    if not pkpass_file:
        sys.exit(1)
    
    # Step 4: Validate structure
    if not validate_pass_structure(pkpass_file):
        print("\n❌ Pass validation failed")
        sys.exit(1)
    
    print("\n🎉 Test completed successfully!")
    print(f"\nNext steps:")
    print(f"1. Transfer {pkpass_file} to your iOS device")
    print(f"2. Try opening it with Apple Wallet")
    print(f"3. Check if it installs properly")
    print(f"\nFor Flutter integration:")
    print(f"- Ensure your app uses the same teamIdentifier: C4JDUP99R7")
    print(f"- Ensure your app uses the same passTypeIdentifier: pass.com.newlife.fitness")

if __name__ == "__main__":
    main()