#!/bin/bash
# Debug Apple Wallet Pass (.pkpass) file

echo "🔍 Debugging .pkpass file issues"
echo "================================="

# Check if we have any .pkpass files
PKPASS_FILES=(*.pkpass)
if [ ! -e "${PKPASS_FILES[0]}" ]; then
    echo "❌ No .pkpass files found. Generate one first:"
    echo "   python test_wallet_api.py"
    echo "   or"
    echo "   ./test_pass_curl.sh"
    exit 1
fi

# Use the first .pkpass file found
PKPASS_FILE="${PKPASS_FILES[0]}"
echo "📁 Analyzing file: $PKPASS_FILE"
echo "📏 File size: $(wc -c < "$PKPASS_FILE") bytes"
echo ""

# Create temp directory for extraction
TEMP_DIR=$(mktemp -d)
echo "📂 Extracting to: $TEMP_DIR"

# Extract the .pkpass file (it's a zip)
if unzip -q "$PKPASS_FILE" -d "$TEMP_DIR"; then
    echo "✅ Successfully extracted .pkpass file"
else
    echo "❌ Failed to extract .pkpass file - file may be corrupted"
    rm -rf "$TEMP_DIR"
    exit 1
fi

echo ""
echo "📋 Contents of .pkpass file:"
echo "----------------------------"
ls -la "$TEMP_DIR"

echo ""
echo "🔍 Checking required files:"
echo "---------------------------"

# Check required files
REQUIRED_FILES=("pass.json" "manifest.json" "signature")
for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$TEMP_DIR/$file" ]; then
        echo "✅ $file exists ($(wc -c < "$TEMP_DIR/$file") bytes)"
    else
        echo "❌ $file missing"
    fi
done

echo ""
echo "🎨 Checking optional image files:"
echo "---------------------------------"
IMAGE_FILES=("icon.png" "logo.png" "icon@2x.png" "logo@2x.png")
for file in "${IMAGE_FILES[@]}"; do
    if [ -f "$TEMP_DIR/$file" ]; then
        echo "✅ $file exists ($(wc -c < "$TEMP_DIR/$file") bytes)"
    else
        echo "⚠️  $file missing (optional)"
    fi
done

echo ""
echo "📄 Examining pass.json:"
echo "-----------------------"
if [ -f "$TEMP_DIR/pass.json" ]; then
    cat "$TEMP_DIR/pass.json" | python3 -m json.tool
else
    echo "❌ pass.json not found"
fi

echo ""
echo "🔐 Checking signature file:"
echo "---------------------------"
if [ -f "$TEMP_DIR/signature" ]; then
    echo "✅ Signature file exists ($(wc -c < "$TEMP_DIR/signature") bytes)"
    
    # Try to verify the signature
    echo "🔍 Verifying signature..."
    if openssl smime -verify -in "$TEMP_DIR/signature" -inform DER -content "$TEMP_DIR/manifest.json" -CAfile certs/WWDR.pem -noverify > /dev/null 2>&1; then
        echo "✅ Signature verification passed"
    else
        echo "❌ Signature verification failed"
        echo "   This is likely why iOS won't accept the pass"
    fi
else
    echo "❌ signature file not found"
fi

echo ""
echo "📋 Checking manifest.json hashes:"
echo "---------------------------------"
if [ -f "$TEMP_DIR/manifest.json" ]; then
    echo "Manifest contents:"
    cat "$TEMP_DIR/manifest.json" | python3 -m json.tool
    
    echo ""
    echo "Verifying file hashes..."
    
    # Read manifest and verify each file hash
    python3 -c "
import json
import hashlib
import os

manifest_path = '$TEMP_DIR/manifest.json'
temp_dir = '$TEMP_DIR'

with open(manifest_path, 'r') as f:
    manifest = json.load(f)

all_valid = True
for filename, expected_hash in manifest.items():
    file_path = os.path.join(temp_dir, filename)
    if os.path.exists(file_path):
        with open(file_path, 'rb') as f:
            content = f.read()
            actual_hash = hashlib.sha1(content).hexdigest()
            if actual_hash == expected_hash:
                print(f'✅ {filename}: hash matches')
            else:
                print(f'❌ {filename}: hash mismatch')
                print(f'   Expected: {expected_hash}')
                print(f'   Actual:   {actual_hash}')
                all_valid = False
    else:
        print(f'❌ {filename}: file not found')
        all_valid = False

if all_valid:
    print('\n✅ All file hashes are valid')
else:
    print('\n❌ Some file hashes are invalid')
"
else
    echo "❌ manifest.json not found"
fi

echo ""
echo "🩺 Common Issues and Solutions:"
echo "==============================="
echo "1. ❌ 'Unable to open' on iPhone:"
echo "   - Invalid certificate or signing"
echo "   - Wrong passTypeIdentifier"
echo "   - Incorrect teamIdentifier"
echo ""
echo "2. ❌ Signature verification failed:"
echo "   - Use real Apple certificates (not placeholder)"
echo "   - Ensure WWDR certificate is correct"
echo "   - Check certificate expiration"
echo ""
echo "3. ❌ Pass not appearing in Wallet:"
echo "   - Check passTypeIdentifier matches Apple Developer Portal"
echo "   - Verify teamIdentifier is your real Apple Team ID"
echo "   - Ensure certificates are for Pass Type (not iOS Distribution)"
echo ""
echo "🔧 Next steps if issues found:"
echo "1. Get real Apple Pass Type certificates"
echo "2. Update passTypeIdentifier and teamIdentifier"
echo "3. Re-generate the pass"

# Cleanup
rm -rf "$TEMP_DIR"