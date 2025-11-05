import 'dart:typed_data';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:apple_passkit/apple_passkit.dart';
import 'package:path_provider/path_provider.dart';

class PassKitDebugHelper {
  static const String baseUrl = "http://192.168.1.21:8001"; // Your server IP
  
  /// Debug method to test Apple Wallet pass generation and installation
  static Future<void> debugPassKitFlow({
    required String token,
    required String serialNumber,
    bool saveToFile = true,
  }) async {
    print('🔍 Starting PassKit Debug Flow');
    print('=' * 50);
    
    try {
      // Step 1: Prepare pass data with real certificate values
      final passData = {
        "serialNumber": serialNumber,
        "description": "NFC Access Card",
        "organizationName": "New Life Fitness",
        "passTypeIdentifier": "pass.com.newlife.fitness",  // Real from cert
        "teamIdentifier": "C4JDUP99R7",  // Real from cert
        "nfc": {
          "message": "dGVzdG1lc3NhZ2U="  // base64 "testmessage"
        }
      };
      
      print('📝 Pass Data:');
      print('   Serial: ${passData["serialNumber"]}');
      print('   Team ID: ${passData["teamIdentifier"]}');
      print('   Pass Type: ${passData["passTypeIdentifier"]}');
      
      // Step 2: Make API request
      print('\n🌐 Making API Request...');
      final response = await http.post(
        Uri.parse('$baseUrl/api/pass/sign'),
        headers: {
          'Authorization': 'Bearer $token',
          'Content-Type': 'application/json',
        },
        body: jsonEncode(passData),
      );
      
      print('   Status Code: ${response.statusCode}');
      print('   Content-Type: ${response.headers['content-type']}');
      print('   Content-Length: ${response.headers['content-length']}');
      print('   Body Length: ${response.bodyBytes.length} bytes');
      
      if (response.statusCode != 200) {
        print('❌ API Error: ${response.body}');
        return;
      }
      
      // Step 3: Validate response data
      final bytes = response.bodyBytes;
      print('\n🔍 Validating Response Data:');
      print('   Bytes length: ${bytes.length}');
      print('   First 4 bytes: ${bytes.take(4).map((b) => b.toRadixString(16).padLeft(2, '0')).join(' ')}');
      
      // Check ZIP signature
      if (bytes.length >= 4 && bytes[0] == 0x50 && bytes[1] == 0x4B) {
        print('   ✅ Valid ZIP signature detected');
      } else {
        print('   ❌ Invalid ZIP signature - not a valid .pkpass file');
        return;
      }
      
      // Step 4: Save to file for manual testing (optional)
      if (saveToFile) {
        final directory = await getApplicationDocumentsDirectory();
        final file = File('${directory.path}/debug_test.pkpass');
        await file.writeAsBytes(bytes);
        print('\n💾 Saved to: ${file.path}');
        print('   You can manually transfer this file to test');
      }
      
      // Step 5: Validate with PassKit
      print('\n🎫 Attempting PassKit Installation...');
      print('   Calling ApplePassKit.addPass() with ${bytes.length} bytes');
      
      try {
        // This is the critical call that's failing
        final result = await ApplePassKit.addPass(bytes);
        print('   ✅ Success! Result: $result');
        
      } catch (passKitError) {
        print('   ❌ PassKit Error: $passKitError');
        print('   Error Type: ${passKitError.runtimeType}');
        
        // Additional debugging for common error types
        if (passKitError.toString().contains('invalid')) {
          print('\n🔬 PassKit Validation Failed - Possible Causes:');
          print('   1. Team ID mismatch in Apple Developer Portal');
          print('   2. Pass Type ID not configured correctly');
          print('   3. Certificate issues');
          print('   4. Pass.json format problems');
          
          // Try to extract more details
          await _analyzePassContent(bytes);
        }
      }
      
    } catch (e) {
      print('❌ Unexpected Error: $e');
      print('   Type: ${e.runtimeType}');
    }
  }
  
  /// Analyze the internal structure of the .pkpass data
  static Future<void> _analyzePassContent(Uint8List bytes) async {
    try {
      print('\n🔬 Analyzing Pass Structure:');
      
      // Save to temporary file for analysis
      final tempDir = await getTemporaryDirectory();
      final tempFile = File('${tempDir.path}/temp_analysis.pkpass');
      await tempFile.writeAsBytes(bytes);
      
      // In a real app, you'd need to use a ZIP library to extract and analyze
      // For now, we'll just validate the basics
      print('   File saved for analysis: ${tempFile.path}');
      print('   File size: ${await tempFile.length()} bytes');
      
      // Clean up
      await tempFile.delete();
      
    } catch (e) {
      print('   Analysis failed: $e');
    }
  }
  
  /// Test with a minimal pass request
  static Future<void> testMinimalPass(String token) async {
    print('\n🧪 Testing Minimal Pass Configuration');
    
    await debugPassKitFlow(
      token: token,
      serialNumber: 'MIN${DateTime.now().millisecondsSinceEpoch}',
      saveToFile: true,
    );
  }
  
  /// Validate that the token and API are working
  static Future<bool> validateApiAccess(String token) async {
    print('🔐 Validating API Access...');
    
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/api/pass/certificates/status'),
        headers: {'Authorization': 'Bearer $token'},
      );
      
      if (response.statusCode == 200) {
        final status = jsonDecode(response.body);
        final ready = status['ready'] ?? false;
        print('   ✅ API accessible, certificates ready: $ready');
        return ready;
      } else {
        print('   ❌ API access failed: ${response.statusCode}');
        return false;
      }
    } catch (e) {
      print('   ❌ API validation error: $e');
      return false;
    }
  }
}

// Example usage in your Flutter app:
class PassKitTestWidget extends StatelessWidget {
  final String jwtToken;
  
  const PassKitTestWidget({Key? key, required this.jwtToken}) : super(key: key);
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('PassKit Debug')),
      body: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          children: [
            ElevatedButton(
              onPressed: () async {
                // First validate API access
                final apiReady = await PassKitDebugHelper.validateApiAccess(jwtToken);
                if (!apiReady) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text('API not ready - check server and certificates')),
                  );
                  return;
                }
                
                // Then test pass creation
                await PassKitDebugHelper.testMinimalPass(jwtToken);
              },
              child: Text('Test PassKit Integration'),
            ),
            
            SizedBox(height: 20),
            
            Text(
              'This will:\n'
              '1. Validate API access\n'
              '2. Generate a test pass\n'
              '3. Attempt to add to Wallet\n'
              '4. Show detailed debug info\n\n'
              'Check the console for detailed logs.',
              style: TextStyle(fontSize: 14),
            ),
          ],
        ),
      ),
    );
  }
}

/*
CRITICAL DEBUGGING CHECKLIST:

1. ✅ Server Response Validation:
   - HTTP 200 status
   - Correct Content-Type: application/vnd.apple.pkpass
   - Valid ZIP signature (PK bytes)
   - Non-empty response body

2. ✅ Certificate Configuration:
   - Team ID: C4JDUP99R7 (from your real certificate)
   - Pass Type: pass.com.newlife.fitness
   - These MUST match Apple Developer Portal exactly

3. ❌ PassKit Package Usage:
   - Use response.bodyBytes (Uint8List), not response.body (String)
   - Don't convert to String and back
   - Pass raw bytes directly to ApplePassKit.addPass()

4. ❌ Apple Developer Portal:
   - Verify Pass Type ID exists: pass.com.newlife.fitness
   - Verify Team ID matches: C4JDUP99R7
   - Ensure certificates are not expired
   - Check if your app's bundle ID has passbook capability

5. ❌ Device/Simulator Issues:
   - Test on real iOS device (Simulator doesn't support Wallet)
   - Ensure Wallet app is enabled
   - Check iOS version compatibility

MOST LIKELY FIXES:

1. Data Type Issue:
   ```dart
   // ❌ WRONG
   final String stringData = response.body;
   await ApplePassKit.addPass(stringData);
   
   // ✅ CORRECT
   final Uint8List bytes = response.bodyBytes;
   await ApplePassKit.addPass(bytes);
   ```

2. Apple Developer Portal:
   - Double-check Pass Type ID configuration
   - Regenerate certificates if needed
   - Verify bundle ID has passbook entitlement

3. API Response Handling:
   ```dart
   // Add this validation before PassKit call
   if (response.headers['content-type'] != 'application/vnd.apple.pkpass') {
     throw Exception('Invalid response content type');
   }
   
   final bytes = response.bodyBytes;
   if (bytes.length < 100) {  // Passes are typically > 1KB
     throw Exception('Response too small to be valid pass');
   }
   ```
*/