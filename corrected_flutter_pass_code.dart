// Download the pass data first
final dio = Dio();
Response<dynamic> response = await dio.post(
  '${ApiService.baseUrl}api/pass/sign',
  data: {
    'serialNumber':
        userProfile['id']?.toString() ??
        'USER${DateTime.now().millisecondsSinceEpoch}',
    'description': 'NFC Access Card',
    'organizationName': 'New Life Fitness',
    'passTypeIdentifier': 'pass.com.newlife.fitness', // ✅ FIXED: Removed .nfcaccess
    'teamIdentifier': 'C4JDUP99R7',
    'nfc': {'message': 'QkFTRTY0RU5DT0RFRE1FU1NBR0U='},
  },
  options: Options(
    headers: {
      'Authorization': 'Bearer $token',
      'Content-Type': 'application/json',
    },
    responseType: ResponseType.bytes,
    validateStatus: (status) => status! < 500,
  ),
);

// Close loading dialog
Get.back();

if (response.statusCode == 200) {
  // Validate the response data before trying to add to PassKit
  if (response.data == null || response.data.isEmpty) {
    throw Exception("Received empty pass data from server");
  }

  log('✅ Received pass data: ${response.data.length} bytes');

  // Check if the data looks like a valid ZIP file (pkpass is a ZIP)
  if (response.data.length < 4) {
    throw Exception("Pass data too small to be valid");
  }

  // Check for ZIP file signature (PK)
  final zipSignature = response.data.sublist(0, 2);
  if (zipSignature[0] != 0x50 || zipSignature[1] != 0x4B) {
    log(
      '❌ Invalid file signature. Expected ZIP (PK), got: ${zipSignature.map((b) => b.toRadixString(16)).join(' ')}',
    );

    // Try to log what we actually received (first 100 bytes as string)
    try {
      final preview = String.fromCharCodes(response.data.take(100));
      log('Data preview: $preview');
    } catch (e) {
      log('Could not preview data as string: $e');
    }

    throw Exception("Server returned invalid pass data (not a ZIP file)");
  }

  // Additional debugging info
  try {
    final preview = String.fromCharCodes(response.data.take(100));
    log('Data preview: $preview');
  } catch (e) {
    log('Could not preview data as string: $e');
  }
  
  log('✅ Pass data appears to be a valid ZIP file');
  log('🔍 Pass configuration:');
  log('   Team ID: C4JDUP99R7');
  log('   Pass Type: pass.com.newlife.fitness'); // ✅ Correct value
  log('   Serial: ${userProfile['id']?.toString() ?? 'USER${DateTime.now().millisecondsSinceEpoch}'}');

  // Try to add the pass directly to Apple Wallet
  try {
    log('📱 Attempting to add pass to Apple Wallet...');
    await passKit.addPass(response.data.bytes);
    log('🎉 Pass successfully added to Apple Wallet!');
    
  } catch (passKitError) {
    log('❌ PassKit Error: $passKitError');
    log('   Error Type: ${passKitError.runtimeType}');
    
    // If it's still failing, provide detailed debugging info
    if (passKitError.toString().contains('invalid')) {
      log('🔬 PassKit rejected the pass. Possible causes:');
      log('   1. Apple Developer Portal configuration mismatch');
      log('   2. Certificate/Team ID issues');
      log('   3. Pass Type ID not matching: pass.com.newlife.fitness');
      log('   4. Device/simulator limitations (use real iOS device)');
    }
    
    rethrow; // Re-throw to handle in calling code
  }
}