# Common Apple Wallet PassKit Validation Issues

Based on the error `PlatformException(invalid, Received data is not a valid PKPass, The pass cannot be read because it isn't valid., null)`, here are the most likely causes:

## 1. **Certificate/Team ID Mismatch** ✅ FIXED
- **Issue**: TeamIdentifier in pass.json doesn't match certificate
- **Solution**: Updated to use real values from your certificate:
  - `teamIdentifier`: `"C4JDUP99R7"`
  - `passTypeIdentifier`: `"pass.com.newlife.fitness"`

## 2. **Data Transfer Issues in Flutter**
The error might be happening during data transfer to the PassKit package:

```dart
// ❌ WRONG - Passing file path
await ApplePassKit.addPass('/path/to/file.pkpass');

// ✅ CORRECT - Passing raw bytes
final bytes = await File('path/to/file.pkpass').readAsBytes();
await ApplePassKit.addPass(bytes);

// ✅ CORRECT - From HTTP response
final response = await http.get(Uri.parse('your-api-url'));
await ApplePassKit.addPass(response.bodyBytes);
```

## 3. **Content-Type Headers**
Ensure your API returns correct headers:

```dart
headers: {
  'Content-Type': 'application/vnd.apple.pkpass',
  'Content-Disposition': 'attachment; filename="pass.pkpass"'
}
```

## 4. **Apple Developer Portal Configuration**
Verify in your Apple Developer account:

1. **Pass Type ID**: `pass.com.newlife.fitness`
2. **Team ID**: `C4JDUP99R7`
3. **Certificate**: Must be generated for exactly this Pass Type ID
4. **Bundle ID**: Should match your Flutter app's bundle ID

## 5. **Flutter Implementation Debug Steps**

### Step 1: Verify Raw Data
```dart
// Save the received data to see if it's valid
final bytes = response.bodyBytes;
final file = File('${directory.path}/debug.pkpass');
await file.writeAsBytes(bytes);
print('Saved ${bytes.length} bytes to ${file.path}');

// Try to open this file manually on iOS
```

### Step 2: Check PassKit Package Usage
```dart
import 'package:apple_passkit/apple_passkit.dart';

try {
  final bytes = await getPassBytesFromAPI();
  
  // Verify bytes are not empty
  if (bytes.isEmpty) {
    print('ERROR: Received empty bytes from API');
    return;
  }
  
  print('Attempting to add pass with ${bytes.length} bytes');
  
  final result = await ApplePassKit.addPass(bytes);
  print('PassKit result: $result');
  
} catch (e) {
  print('PassKit error: $e');
  // Check the exact error details
}
```

### Step 3: Network Request Debug
```dart
final response = await http.post(
  Uri.parse('your-api-endpoint'),
  headers: {
    'Authorization': 'Bearer $token',
    'Content-Type': 'application/json',
  },
  body: jsonEncode(passData),
);

print('Response status: ${response.statusCode}');
print('Response headers: ${response.headers}');
print('Response content-type: ${response.headers['content-type']}');
print('Response body length: ${response.bodyBytes.length}');

// Verify it's actually a pkpass file
if (response.headers['content-type'] != 'application/vnd.apple.pkpass') {
  print('WARNING: Unexpected content type');
}
```

## 6. **API Endpoint Testing**

Test your API endpoint directly:

```bash
# Test with curl
curl -X POST http://your-server:8001/api/pass/sign \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "serialNumber": "TEST123",
    "description": "NFC Access Card",
    "organizationName": "New Life Fitness", 
    "passTypeIdentifier": "pass.com.newlife.fitness",
    "teamIdentifier": "C4JDUP99R7",
    "nfc": {"message": "dGVzdA=="}
  }' \
  --output test.pkpass

# Verify the file
file test.pkpass  # Should show "Zip archive data"
unzip -l test.pkpass  # Should show pass.json, manifest.json, signature
```

## 7. **Common Fix Patterns**

### Pattern A: File vs Bytes Issue
```dart
// Instead of this:
ApplePassKit.addPass(file.path)

// Use this:
final bytes = await file.readAsBytes();
ApplePassKit.addPass(bytes);
```

### Pattern B: Async/Await Issues
```dart
// Ensure proper async handling
Future<void> addPassToWallet() async {
  try {
    final response = await apiCall();
    final result = await ApplePassKit.addPass(response.bodyBytes);
    print('Success: $result');
  } catch (e) {
    print('Error: $e');
  }
}
```

### Pattern C: Data Validation
```dart
// Validate before passing to PassKit
bool isValidPkpass(Uint8List bytes) {
  // Check if it starts with ZIP signature
  if (bytes.length < 4) return false;
  return bytes[0] == 0x50 && bytes[1] == 0x4B;
}

if (!isValidPkpass(passBytes)) {
  print('ERROR: Invalid pkpass data');
  return;
}
```

## 8. **Testing Priority**

1. **Test the minimal pass**: Use `minimal_test.pkpass` created above
2. **Verify certificate config**: Ensure Apple Developer Portal matches
3. **Debug Flutter data flow**: Print all data at each step
4. **Test API independently**: Use curl/Postman to verify API works
5. **Check PassKit package version**: Ensure you're using latest version

The most likely issue is in steps 2-3 (Flutter data handling) since the pass structure itself appears correct.