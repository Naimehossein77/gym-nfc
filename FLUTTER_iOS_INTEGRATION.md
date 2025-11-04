# Flutter iOS Integration for Apple Wallet Pass

## API Overview
The `/api/pass/sign` endpoint generates Apple Wallet `.pkpass` files from your Apple Developer `.p12` certificate for NFC access cards.

## Purpose
- Takes member data and NFC token
- Creates a signed Apple Wallet pass using your `.p12` certificate 
- Returns a `.pkpass` file that can be added to iOS Wallet app
- Enables NFC access using iPhone

## API Call Flow

### 1. Login
```http
POST /api/auth/login
Content-Type: application/x-www-form-urlencoded

username=admin&password=admin123
```

### 2. Generate Pass
```http
POST /api/pass/sign
Authorization: Bearer YOUR_JWT_TOKEN
Content-Type: application/json

{
  "serialNumber": "USER123456",
  "description": "NFC Access Card",
  "organizationName": "New Life Fitness",
  "passTypeIdentifier": "pass.com.newlife.fitness",
  "teamIdentifier": "C4JDUP99R7",
  "nfc": {
    "message": "QkFTRTY0RU5DT0RFRE1FU1NBR0U="
  }
}
```

**Response:** Binary `.pkpass` file with headers:
- `Content-Type: application/vnd.apple.pkpass`
- `Content-Disposition: attachment; filename="nfc_access.pkpass"`

## Certificate Setup
1. Convert your `.p12` file: `./convert_certificates.sh`
2. Place certificates in `./certs/` directory
3. Update `passTypeIdentifier` and `teamIdentifier` with your Apple Developer values

## Flutter Implementation
```dart
// Download the .pkpass file
final response = await http.post(
  Uri.parse('$baseUrl/api/pass/sign'),
  headers: {
    'Authorization': 'Bearer $token',
    'Content-Type': 'application/json',
  },
  body: json.encode({
    'serialNumber': 'USER123456',
    'description': 'NFC Access Card',
    'organizationName': 'New Life Fitness',
    'passTypeIdentifier': 'pass.com.newlife.fitness.nfcaccess',
    'teamIdentifier': 'YOUR_TEAM_ID',
    'nfc': {
      'message': base64EncodedToken
    }
  }),
);

// Save to device
final file = File('${directory.path}/pass.pkpass');
await file.writeAsBytes(response.bodyBytes);

// User taps the file to add to Wallet
```