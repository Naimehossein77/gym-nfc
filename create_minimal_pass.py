#!/usr/bin/env python3
"""
Create a minimal, standards-compliant Apple Wallet pass for debugging
"""

import json
import zipfile
import hashlib
import tempfile
import subprocess
from pathlib import Path

def create_minimal_pass():
    """Create a minimal pass that follows Apple's strict validation rules"""
    
    # Base directory
    base_dir = Path(__file__).parent
    certs_dir = base_dir / "certs"
    
    # Certificate paths
    pass_cert_path = certs_dir / "pass_cert.pem"
    pass_key_path = certs_dir / "pass_key.pem"
    wwdr_cert_path = certs_dir / "WWDR.pem"
    
    # Check certificates exist
    for cert_path in [pass_cert_path, pass_key_path, wwdr_cert_path]:
        if not cert_path.exists():
            print(f"❌ Missing certificate: {cert_path}")
            return None
    
    with tempfile.TemporaryDirectory() as temp_dir_str:
        temp_dir = Path(temp_dir_str)
        
        # 1. Create minimal pass.json with EXACT standards compliance
        pass_data = {
            "formatVersion": 1,
            "passTypeIdentifier": "pass.com.newlife.fitness",  # Real from cert
            "serialNumber": "MIN123456",
            "teamIdentifier": "C4JDUP99R7",  # Real from cert
            "organizationName": "New Life Fitness",
            "description": "NFC Access Card",
            "logoText": "New Life Fitness",
            "foregroundColor": "rgb(255, 255, 255)",
            "backgroundColor": "rgb(0, 0, 0)",  # Changed to solid black
            "generic": {
                "primaryFields": [
                    {
                        "key": "member",
                        "label": "MEMBER",
                        "value": "Access Card"
                    }
                ]
            },
            # NFC with minimal structure
            "nfc": {
                "message": "dGVzdG1lc3NhZ2U=",  # base64 "testmessage"
                "encryptionPublicKey": ""
            },
            # Standard barcode (required for many passes)
            "barcodes": [
                {
                    "format": "PKBarcodeFormatQR",
                    "message": "TEST123456",
                    "messageEncoding": "iso-8859-1"
                }
            ]
        }
        
        # Write pass.json
        pass_json_path = temp_dir / "pass.json"
        with open(pass_json_path, "w", encoding="utf-8") as f:
            json.dump(pass_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Created pass.json")
        
        # 2. Create minimal icon (1x1 PNG)
        # This creates a minimal valid PNG file
        minimal_png = bytes([
            0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,  # PNG signature
            0x00, 0x00, 0x00, 0x0D,  # IHDR chunk length
            0x49, 0x48, 0x44, 0x52,  # IHDR
            0x00, 0x00, 0x00, 0x01,  # Width: 1
            0x00, 0x00, 0x00, 0x01,  # Height: 1
            0x08, 0x02,              # Bit depth: 8, Color type: 2 (RGB)
            0x00, 0x00, 0x00,        # Compression, filter, interlace
            0x90, 0x77, 0x53, 0xDE,  # IHDR CRC
            0x00, 0x00, 0x00, 0x0C,  # IDAT chunk length
            0x49, 0x44, 0x41, 0x54,  # IDAT
            0x08, 0x99, 0x01, 0x01, 0x00, 0x00, 0x00, 0x00, 0x82, 0x20, 0x82, 0x3D,  # IDAT data + CRC
            0x00, 0x00, 0x00, 0x00,  # IEND chunk length
            0x49, 0x45, 0x4E, 0x44,  # IEND
            0xAE, 0x42, 0x60, 0x82   # IEND CRC
        ])
        
        icon_path = temp_dir / "icon.png"
        with open(icon_path, "wb") as f:
            f.write(minimal_png)
        
        print(f"✅ Created minimal icon.png")
        
        # 3. Create manifest.json with SHA1 hashes
        manifest = {}
        for file_path in temp_dir.glob("*"):
            if file_path.is_file():
                with open(file_path, "rb") as f:
                    content = f.read()
                    sha1_hash = hashlib.sha1(content).hexdigest()
                    manifest[file_path.name] = sha1_hash
        
        manifest_path = temp_dir / "manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)
        
        print(f"✅ Created manifest.json with {len(manifest)} files")
        
        # 4. Sign the manifest
        signature_path = temp_dir / "signature"
        cmd = [
            "openssl", "smime", "-binary", "-sign",
            "-certfile", str(wwdr_cert_path),
            "-signer", str(pass_cert_path),
            "-inkey", str(pass_key_path),
            "-in", str(manifest_path),
            "-out", str(signature_path),
            "-outform", "DER"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            print(f"✅ Signed manifest successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Signing failed: {e.stderr}")
            return None
        
        # 5. Create .pkpass ZIP file
        pkpass_path = temp_dir / "minimal_test.pkpass"
        with zipfile.ZipFile(pkpass_path, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zip_file:
            for file_path in temp_dir.glob("*"):
                if file_path.is_file() and file_path.suffix != ".pkpass":
                    zip_file.write(file_path, file_path.name)
        
        # 6. Copy to current directory
        output_path = base_dir / "minimal_test.pkpass"
        with open(pkpass_path, "rb") as src, open(output_path, "wb") as dst:
            dst.write(src.read())
        
        print(f"✅ Created {output_path}")
        print(f"   File size: {output_path.stat().st_size} bytes")
        
        # 7. Validate structure
        print(f"\n🔍 Validating structure:")
        with zipfile.ZipFile(output_path, 'r') as zip_file:
            files = zip_file.namelist()
            print(f"   Files: {files}")
            
            # Check required files
            required = ["pass.json", "manifest.json", "signature"]
            missing = [f for f in required if f not in files]
            if missing:
                print(f"❌ Missing: {missing}")
            else:
                print(f"✅ All required files present")
        
        return str(output_path)

if __name__ == "__main__":
    print("🧪 Creating Minimal Apple Wallet Pass")
    print("=" * 50)
    
    result = create_minimal_pass()
    if result:
        print(f"\n🎉 Success! Created: {result}")
        print(f"\nNext steps:")
        print(f"1. Transfer {result} to your iOS device")
        print(f"2. Try to open it in Apple Wallet")
        print(f"3. If this works, the issue is in your Flutter implementation")
        print(f"4. If this fails, the issue is in certificate configuration")
    else:
        print(f"\n❌ Failed to create pass")