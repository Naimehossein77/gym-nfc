#!/bin/bash
# Sample curl commands for Apple Wallet Pass API

echo "🔐 Step 1: Login to get JWT token"
echo "================================="

# Login and extract token
TOKEN=$(curl -s -X POST "http://localhost:8001/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123" | \
  python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

echo "✅ Token obtained: ${TOKEN:0:50}..."
echo ""

echo "📋 Step 2: Check certificate status (optional)"
echo "=============================================="

curl -s -X GET "http://localhost:8001/api/pass/certificates/status" \
  -H "Authorization: Bearer $TOKEN" | \
  python3 -m json.tool

echo ""
echo "🔏 Step 3: Generate and sign Apple Wallet pass"
echo "=============================================="

# Create the pass
curl -X POST "http://localhost:8001/api/pass/sign" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "serialNumber": "USER123456",
    "description": "NFC Access Card", 
    "organizationName": "New Life Fitness",
    "passTypeIdentifier": "pass.com.newlife.fitness",
    "teamIdentifier": "C4JDUP99R7",
    "nfc": {
      "message": "QkFTRTY0RU5DT0RFRE1FU1NBR0U="
    }
  }' \
  --output "generated_pass.pkpass"

if [ $? -eq 0 ]; then
  echo "✅ Pass generated successfully!"
  echo "📁 Saved as: generated_pass.pkpass"
  echo "📏 File size: $(wc -c < generated_pass.pkpass) bytes"
  echo ""
  echo "📱 To test on iOS:"
  echo "   1. AirDrop the .pkpass file to your iPhone"
  echo "   2. Or email it to yourself and open on iPhone"
  echo "   3. Tap the file to add it to Apple Wallet"
else
  echo "❌ Failed to generate pass"
fi