#!/usr/bin/env python3
"""
Simulate the exact data flow that your Flutter app would experience
to identify where the PassKit validation might be failing.
"""

import requests
import json
import zipfile
import tempfile
from pathlib import Path

def test_flutter_data_flow():
    """Simulate what Flutter does with the API response"""
    
    # Your server details
    BASE_URL = "http://192.168.10.14:8001"
    
    # Login to get token (OAuth2PasswordRequestForm expects form data)
    login_response = requests.post(f"{BASE_URL}/api/auth/login", data={
        "username": "admin",
        "password": "admin123"
    })
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        return False
    
    token = login_response.json()["access_token"]
    print(f"✅ Login successful")
    
    # Request pass with real certificate values
    pass_data = {
        "serialNumber": "FLUTTER_TEST_123",
        "description": "NFC Access Card",
        "organizationName": "New Life Fitness",
        "passTypeIdentifier": "pass.com.newlife.fitness",  # Real from cert
        "teamIdentifier": "C4JDUP99R7",  # Real from cert
        "nfc": {
            "message": "RkxVVFRFUlRFU1Q="  # base64 "FLUTTERTEST"
        }
    }
    
    print(f"🎫 Requesting pass with data:")
    print(f"   Team ID: {pass_data['teamIdentifier']}")
    print(f"   Pass Type: {pass_data['passTypeIdentifier']}")
    
    # Make the API request (same as Flutter would)
    response = requests.post(
        f"{BASE_URL}/api/pass/sign",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json=pass_data
    )
    
    print(f"\n📡 API Response:")
    print(f"   Status: {response.status_code}")
    print(f"   Content-Type: {response.headers.get('content-type', 'Missing')}")
    print(f"   Content-Length: {response.headers.get('content-length', 'Missing')}")
    print(f"   Body bytes length: {len(response.content)}")
    
    if response.status_code != 200:
        print(f"❌ API request failed: {response.text}")
        return False
    
    # Check the raw response (this is what Flutter receives)
    raw_bytes = response.content
    print(f"\n🔍 Raw Response Analysis:")
    print(f"   First 10 bytes (hex): {raw_bytes[:10].hex()}")
    print(f"   First 4 bytes (should be PK for ZIP): {raw_bytes[:4]}")
    
    # Verify ZIP signature
    if len(raw_bytes) >= 4 and raw_bytes[0:2] == b'PK':
        print(f"   ✅ Valid ZIP signature detected")
    else:
        print(f"   ❌ Invalid ZIP signature")
        return False
    
    # Test ZIP extraction (what iOS would do internally)
    try:
        with tempfile.NamedTemporaryFile(suffix='.pkpass', delete=False) as temp_file:
            temp_file.write(raw_bytes)
            temp_file.flush()
            
            print(f"\n📦 ZIP Content Analysis:")
            with zipfile.ZipFile(temp_file.name, 'r') as zip_file:
                file_list = zip_file.namelist()
                print(f"   Files in ZIP: {file_list}")
                
                # Check required files
                required_files = ["pass.json", "manifest.json", "signature"]
                missing = [f for f in required_files if f not in file_list]
                
                if missing:
                    print(f"   ❌ Missing required files: {missing}")
                    return False
                else:
                    print(f"   ✅ All required files present")
                
                # Analyze pass.json content
                try:
                    with zip_file.open("pass.json") as pass_file:
                        pass_content = json.loads(pass_file.read().decode('utf-8'))
                        
                        print(f"\n📄 Pass.json Analysis:")
                        print(f"   Format Version: {pass_content.get('formatVersion')}")
                        print(f"   Pass Type ID: {pass_content.get('passTypeIdentifier')}")
                        print(f"   Team ID: {pass_content.get('teamIdentifier')}")
                        print(f"   Serial Number: {pass_content.get('serialNumber')}")
                        
                        # Check critical fields that cause PassKit failures
                        critical_checks = [
                            ("formatVersion", lambda x: x == 1),
                            ("passTypeIdentifier", lambda x: x == "pass.com.newlife.fitness"),
                            ("teamIdentifier", lambda x: x == "C4JDUP99R7"),
                            ("serialNumber", lambda x: x and len(str(x)) > 0),
                            ("description", lambda x: x and len(str(x)) > 0),
                            ("organizationName", lambda x: x and len(str(x)) > 0)
                        ]
                        
                        print(f"\n🔬 Critical Field Validation:")
                        all_valid = True
                        for field_name, validator in critical_checks:
                            value = pass_content.get(field_name)
                            is_valid = validator(value) if value is not None else False
                            status = "✅" if is_valid else "❌"
                            print(f"   {status} {field_name}: {value}")
                            if not is_valid:
                                all_valid = False
                        
                        if not all_valid:
                            print(f"\n❌ Pass validation failed - critical fields are invalid")
                            return False
                        
                        # Check for common PassKit rejection causes
                        print(f"\n🧪 PassKit Compatibility Checks:")
                        
                        # Check NFC structure
                        nfc_data = pass_content.get('nfc', {})
                        if 'message' not in nfc_data:
                            print(f"   ❌ NFC message missing")
                            all_valid = False
                        else:
                            print(f"   ✅ NFC message present")
                        
                        # Check generic structure
                        generic_data = pass_content.get('generic', {})
                        if 'primaryFields' not in generic_data:
                            print(f"   ❌ Primary fields missing")
                            all_valid = False
                        else:
                            print(f"   ✅ Primary fields present")
                        
                        # Check colors
                        if 'foregroundColor' not in pass_content or 'backgroundColor' not in pass_content:
                            print(f"   ❌ Colors not specified")
                            all_valid = False
                        else:
                            print(f"   ✅ Colors specified")
                        
                        return all_valid
                        
                except Exception as e:
                    print(f"   ❌ Failed to parse pass.json: {e}")
                    return False
                    
    except Exception as e:
        print(f"❌ ZIP analysis failed: {e}")
        return False
    
    finally:
        # Clean up
        try:
            Path(temp_file.name).unlink()
        except:
            pass

def main():
    print("🧪 Flutter PassKit Data Flow Simulation")
    print("=" * 60)
    print("This simulates exactly what your Flutter app receives")
    print("and validates it against PassKit requirements.")
    print()
    
    success = test_flutter_data_flow()
    
    print(f"\n" + "=" * 60)
    if success:
        print(f"🎉 PASS VALIDATION SUCCESSFUL!")
        print(f"\nThe .pkpass file structure is correct.")
        print(f"If PassKit still fails in Flutter, the issue is likely:")
        print(f"")
        print(f"1. 🔄 Data Transfer Issue:")
        print(f"   - Ensure you're using response.bodyBytes (not response.body)")
        print(f"   - Pass Uint8List directly to ApplePassKit.addPass()")
        print(f"")
        print(f"2. 📱 Apple Developer Portal:")
        print(f"   - Verify Pass Type ID: pass.com.newlife.fitness")
        print(f"   - Verify Team ID: C4JDUP99R7")
        print(f"   - Check certificate expiration")
        print(f"")
        print(f"3. 📲 Device/App Issues:")
        print(f"   - Test on real device (not simulator)")
        print(f"   - Ensure Wallet capability in entitlements")
        print(f"   - Check app bundle ID configuration")
        
    else:
        print(f"❌ PASS VALIDATION FAILED!")
        print(f"\nThe .pkpass file has structural issues that need to be fixed.")
        print(f"Check the detailed output above for specific problems.")

if __name__ == "__main__":
    main()