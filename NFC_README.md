"""
NFC Library Compatibility Information

The gym NFC management system supports both real NFC hardware and simulation mode.

Current Status:
- NFC library (nfcpy) has a dependency conflict with the ndef library
- The nfcpy library expects 'message_decoder' from ndef, but newer ndef versions don't have it
- Simulation mode is fully functional and provides the same API

Solutions:
1. Use simulation mode (current default when NFC hardware/libraries unavailable)
2. For production with real hardware, install compatible versions:
   - nfcpy==1.0.3 (older version)
   - ndef==0.3.2 (compatible version)

Environment Variables:
- FORCE_NFC_SIMULATION=true - Force simulation mode even if hardware is available
- NFC_TIMEOUT=30 - Set NFC operation timeout in seconds

Simulation Mode Features:
- Simulates card detection and writing
- Returns realistic card IDs and data
- Same API as real hardware mode
- No physical NFC reader required

For Production:
If you have an ACS ACR122U reader and need real NFC functionality:
1. Uninstall current nfc packages: pip uninstall nfcpy ndef
2. Install compatible versions: pip install nfcpy==1.0.3 ndef==0.3.2
3. Connect your ACS ACR122U reader
4. Restart the application
"""