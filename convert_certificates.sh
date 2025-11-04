#!/bin/bash
# Convert Apple .p12 certificate to PEM format for pass signing

echo "🔐 Apple Certificate Converter for Gym NFC System"
echo "=================================================="

# Check if OpenSSL is available
if ! command -v openssl &> /dev/null; then
    echo "❌ OpenSSL not found. Please install OpenSSL first."
    echo "   macOS: brew install openssl"
    echo "   Linux: sudo apt-get install openssl"
    exit 1
fi

# Create certs directory if it doesn't exist
mkdir -p certs

echo ""
echo "📋 This script will help you convert your .p12 file to PEM format."
echo "You'll need:"
echo "  1. Your .p12 certificate file from Apple Developer Portal"
echo "  2. The password for the .p12 file (if any)"
echo "  3. The Apple WWDR certificate (downloaded separately)"
echo ""

# Ask for .p12 file path
read -p "📁 Enter the path to your .p12 file: " P12_FILE

if [ ! -f "$P12_FILE" ]; then
    echo "❌ File not found: $P12_FILE"
    exit 1
fi

echo ""
echo "🔓 Converting .p12 to PEM format..."

# Extract certificate (public key)
echo "1. Extracting certificate..."
openssl pkcs12 -in "$P12_FILE" -out certs/pass_cert.pem -clcerts -nokeys
if [ $? -eq 0 ]; then
    echo "✅ Certificate extracted to certs/pass_cert.pem"
else
    echo "❌ Failed to extract certificate"
    exit 1
fi

echo ""

# Extract private key
echo "2. Extracting private key..."
openssl pkcs12 -in "$P12_FILE" -out certs/pass_key.pem -nocerts -nodes
if [ $? -eq 0 ]; then
    echo "✅ Private key extracted to certs/pass_key.pem"
else
    echo "❌ Failed to extract private key"
    exit 1
fi

echo ""

# Download WWDR certificate if needed
if [ ! -f "certs/WWDR.pem" ]; then
    echo "3. Downloading Apple WWDR certificate..."
    
    # Try to download the WWDR certificate
    if command -v curl &> /dev/null; then
        curl -o certs/WWDR.cer "https://www.apple.com/certificateauthority/AppleWWDRCAG3.cer"
        if [ $? -eq 0 ]; then
            # Convert from DER to PEM
            openssl x509 -inform DER -in certs/WWDR.cer -out certs/WWDR.pem
            rm certs/WWDR.cer
            echo "✅ WWDR certificate downloaded and converted to certs/WWDR.pem"
        else
            echo "⚠️ Failed to download WWDR certificate automatically"
            echo "Please download it manually from:"
            echo "https://www.apple.com/certificateauthority/AppleWWDRCAG3.cer"
            echo "Then convert with: openssl x509 -inform DER -in AppleWWDRCAG3.cer -out certs/WWDR.pem"
        fi
    else
        echo "⚠️ curl not found. Please download WWDR certificate manually:"
        echo "https://www.apple.com/certificateauthority/AppleWWDRCAG3.cer"
        echo "Then convert with: openssl x509 -inform DER -in AppleWWDRCAG3.cer -out certs/WWDR.pem"
    fi
else
    echo "3. WWDR certificate already exists at certs/WWDR.pem"
fi

echo ""
echo "🔍 Verifying certificates..."

# Check certificate
if openssl x509 -in certs/pass_cert.pem -text -noout > /dev/null 2>&1; then
    echo "✅ Certificate is valid"
    # Show certificate info
    echo "📋 Certificate details:"
    openssl x509 -in certs/pass_cert.pem -subject -issuer -dates -noout
else
    echo "❌ Certificate appears to be invalid"
fi

echo ""

# Check private key
if openssl rsa -in certs/pass_key.pem -check -noout > /dev/null 2>&1; then
    echo "✅ Private key is valid"
else
    echo "❌ Private key appears to be invalid"
fi

echo ""

# Set secure permissions
chmod 600 certs/pass_key.pem
chmod 644 certs/pass_cert.pem
chmod 644 certs/WWDR.pem 2>/dev/null

echo "🔒 Set secure file permissions"
echo ""
echo "✅ Certificate conversion complete!"
echo ""
echo "📁 Generated files:"
echo "   certs/pass_cert.pem  - Apple Pass Type Certificate"
echo "   certs/pass_key.pem   - Private key (keep this secure!)"
echo "   certs/WWDR.pem       - Apple WWDR Certificate"
echo ""
echo "🧪 Test your setup with:"
echo "   python3 test_wallet_api.py"
echo ""
echo "🔐 Security reminder:"
echo "   - Never commit certificate files to version control"
echo "   - Keep private keys secure and backed up"
echo "   - Check certificate expiration dates regularly"