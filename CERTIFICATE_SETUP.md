# Converting Your Apple .p12 Certificate

Since you have a .p12 file from the App Store Connect, here's how to convert it for use with the Gym NFC system:

## Automatic Conversion (Recommended)

Run the conversion script:

```bash
./convert_certificates.sh
```

The script will:
1. Ask for your .p12 file path
2. Extract the certificate and private key
3. Download and convert the Apple WWDR certificate
4. Set proper file permissions
5. Verify the certificates

## Manual Conversion Steps

If you prefer to do it manually:

### 1. Extract Certificate (Public Key)
```bash
openssl pkcs12 -in your_certificate.p12 -out certs/pass_cert.pem -clcerts -nokeys
```

### 2. Extract Private Key
```bash
openssl pkcs12 -in your_certificate.p12 -out certs/pass_key.pem -nocerts -nodes
```

### 3. Download Apple WWDR Certificate
```bash
# Download the certificate
curl -o certs/WWDR.cer "https://www.apple.com/certificateauthority/AppleWWDRCAG3.cer"

# Convert from DER to PEM format
openssl x509 -inform DER -in certs/WWDR.cer -out certs/WWDR.pem

# Clean up
rm certs/WWDR.cer
```

### 4. Set Secure Permissions
```bash
chmod 600 certs/pass_key.pem    # Private key - restrict access
chmod 644 certs/pass_cert.pem   # Certificate - readable
chmod 644 certs/WWDR.pem        # WWDR - readable
```

## Verify Your Setup

### Check Certificate Status via API
```bash
# Start the server first
python3 main.py

# In another terminal, test the certificate status
python3 test_wallet_api.py
```

### Manual Certificate Verification
```bash
# Verify certificate
openssl x509 -in certs/pass_cert.pem -text -noout

# Verify private key
openssl rsa -in certs/pass_key.pem -check -noout

# Check if certificate and key match
openssl x509 -noout -modulus -in certs/pass_cert.pem | openssl md5
openssl rsa -noout -modulus -in certs/pass_key.pem | openssl md5
# The two MD5 hashes should match
```

## Important Notes

### Certificate Type Requirements
Your .p12 file should be for a **Pass Type ID** certificate, not an iOS Distribution certificate. Make sure you:

1. Created a Pass Type ID in Apple Developer Portal
2. Generated a certificate specifically for that Pass Type ID
3. Downloaded the certificate as a .p12 file

### Pass Type Identifier
When using the API, make sure your `passTypeIdentifier` in the request matches the Pass Type ID you created in Apple Developer Portal.

Example:
- Apple Developer Portal: `pass.com.yourgym.nfcaccess`
- API Request: `"passTypeIdentifier": "pass.com.yourgym.nfcaccess"`

### Team Identifier
Your `teamIdentifier` should match your Apple Developer Team ID (found in your Apple Developer account).

## Troubleshooting

### "Unable to load certificate" Error
- Check that your .p12 file is not corrupted
- Verify you're entering the correct password
- Ensure the certificate is for Pass Type ID, not iOS app distribution

### "Certificate and private key don't match" Error
- The .p12 file should contain both certificate and private key
- Try re-downloading the certificate from Apple Developer Portal

### "WWDR Certificate invalid" Error
- Make sure you downloaded the correct WWDR certificate
- Apple occasionally updates WWDR certificates, try the latest version

## Next Steps

After successful conversion:

1. **Test the API**: Run `python3 test_wallet_api.py`
2. **Update your Flutter app**: Use the pass data format shown in `WALLET_API.md`
3. **Test on iOS device**: Install the generated .pkpass file
4. **Production setup**: Use environment variables for certificate paths in production

## Security Reminder

- **Never commit** certificate files to version control
- Add `certs/*.pem` to your `.gitignore`
- Keep your private key secure and backed up
- Monitor certificate expiration dates (Apple certificates typically last 1-3 years)