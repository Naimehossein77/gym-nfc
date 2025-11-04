# Apple Wallet Pass Integration

## Overview
The Gym NFC Management System now supports generating Apple Wallet passes for NFC access cards. This allows gym members to add their access credentials directly to their iPhone's Wallet app.

## New API Endpoints

### `POST /api/pass/sign`
Signs and creates an Apple Wallet (.pkpass) file for NFC access.

**Request Body:**
```json
{
  "serialNumber": "USER123456",
  "description": "NFC Access Card", 
  "organizationName": "Your Gym Name",
  "passTypeIdentifier": "pass.com.yourgym.nfcaccess",
  "teamIdentifier": "ABCD1234EF",
  "nfc": {
    "message": "QkFTRTY0RU5DT0RFRE1FU1NBR0U="  // Base64 encoded token
  }
}
```

**Response:**
- Content-Type: `application/vnd.apple.pkpass`
- Binary .pkpass file for download

### `GET /api/pass/certificates/status`
Check the status of required certificate files for pass signing.

## Setup Requirements

### 1. Apple Developer Certificates
You need three certificate files in the `./certs/` directory:

- `pass_cert.pem` - Apple Pass Type Certificate
- `pass_key.pem` - Apple Pass Type Private Key  
- `WWDR.pem` - Apple WWDR Certificate

See `./certs/README.md` for detailed setup instructions.

### 2. Static Assets
Place these files in the `./static/` directory:

- `icon.png` - Pass icon (recommended: 32x32px)
- `logo.png` - Pass logo (recommended: 64x32px)

### 3. OpenSSL
The system uses OpenSSL for pass signing. Ensure it's installed:

**macOS:** Usually pre-installed or via Homebrew
**Linux:** `sudo apt-get install openssl`  
**Windows:** Download from OpenSSL website

## Integration with Flutter

Example Flutter code using the `flutter_wallet_card` plugin:

```dart
import 'package:http/http.dart' as http;
import 'package:flutter_wallet_card/flutter_wallet_card.dart';

Future<void> downloadAndInstallPass(String nfcToken) async {
  // 1. Prepare pass data
  final passData = {
    'serialNumber': 'USER123456',
    'description': 'NFC Access Card',
    'organizationName': 'Your Gym',
    'passTypeIdentifier': 'pass.com.yourgym.nfcaccess', 
    'teamIdentifier': 'ABCD1234EF',
    'nfc': {
      'message': base64Encode(utf8.encode(nfcToken))
    }
  };

  // 2. Call the API
  final response = await http.post(
    Uri.parse('$API_BASE_URL/api/pass/sign'),
    headers: {
      'Authorization': 'Bearer $jwtToken',
      'Content-Type': 'application/json',
    },
    body: jsonEncode(passData),
  );

  if (response.statusCode == 200) {
    // 3. Save and install the pass
    final passBytes = response.bodyBytes;
    await FlutterWalletCard.addPassFromBytes(passBytes);
  }
}
```

## Testing

Use the provided test script:

```bash
python3 test_wallet_api.py
```

This will:
1. Login to the API
2. Check certificate status
3. Create a test pass
4. Download the .pkpass file

## Security Notes

- Never commit real certificate files to version control
- Use environment variables for production certificate paths
- Ensure proper file permissions on certificate files (600)
- Validate all input data before pass generation
- Consider rate limiting for the signing endpoint

## Troubleshooting

**OpenSSL not found:**
- Install OpenSSL and ensure it's in your PATH

**Certificate errors:**
- Verify certificate files are in PEM format
- Check that certificates are valid and not expired
- Ensure private key matches the certificate

**Pass not installing on iOS:**
- Verify the pass type identifier matches your Apple Developer setup
- Check that team identifier is correct
- Ensure NFC payload is properly base64 encoded

**File not found errors:**
- Confirm icon.png and logo.png exist in ./static/
- Verify certificate files exist in ./certs/
- Check file permissions