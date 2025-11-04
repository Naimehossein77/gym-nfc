# Example Certificate Setup Instructions

This directory should contain the following Apple certificate files for signing Wallet passes:

## Required Files:

1. **pass_cert.pem** - Apple Pass Type Certificate
   - Obtained from Apple Developer Portal
   - Used to sign the pass manifest

2. **pass_key.pem** - Apple Pass Type Private Key  
   - The private key corresponding to your pass certificate
   - Should be in PEM format without password protection

3. **WWDR.pem** - Apple WWDR (Worldwide Developer Relations) Certificate
   - Downloaded from Apple Developer Portal
   - Used in the certificate chain

## To obtain these certificates:

1. Go to Apple Developer Portal (developer.apple.com)
2. Navigate to Certificates, Identifiers & Profiles
3. Create a Pass Type ID
4. Generate a Pass Type Certificate
5. Download and convert certificates to PEM format
6. Download the WWDR certificate

## Example OpenSSL commands to convert certificates:

```bash
# Convert .p12 to PEM (if you have a .p12 file)
openssl pkcs12 -in certificate.p12 -out pass_cert.pem -clcerts -nokeys
openssl pkcs12 -in certificate.p12 -out pass_key.pem -nocerts -nodes

# Convert .cer to PEM
openssl x509 -inform DER -in WWDR.cer -out WWDR.pem
```

## Security Note:
- Never commit actual certificate files to version control
- Keep private keys secure and protected
- Use environment variables for production deployments