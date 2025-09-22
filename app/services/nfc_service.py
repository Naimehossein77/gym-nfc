import threading
import time
import os
from typing import Optional, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class NFCService:
    """Service for handling NFC card operations with ACS ACR122U reader"""
    
    def __init__(self, timeout: int = 30):
        self.timeout = int(os.getenv('NFC_TIMEOUT', timeout))
        self._clf = None
        self._lock = threading.Lock()
        self._nfc_available = None
        self._force_simulation = os.getenv('FORCE_NFC_SIMULATION', 'false').lower() == 'true'
    
    def _check_nfc_availability(self) -> bool:
        """Check if nfcpy library is available and working"""
        if self._force_simulation:
            logger.info("NFC simulation mode forced by environment variable")
            self._nfc_available = False
            return False
            
        if self._nfc_available is not None:
            return self._nfc_available
        
        try:
            # Try to import nfc, but catch any import errors from dependencies
            import nfc
            logger.info("NFC library loaded successfully - hardware mode available")
            self._nfc_available = True
            return True
        except ImportError as e:
            if "message_decoder" in str(e):
                logger.warning("NFC library dependency issue detected (ndef message_decoder)")
                logger.warning("This is a known compatibility issue between nfcpy and newer ndef versions")
                logger.warning("See NFC_README.md for solutions or use simulation mode")
            else:
                logger.warning(f"NFC library not available: {e}")
            logger.info("NFC operations will run in simulation mode")
            self._nfc_available = False
            return False
        except Exception as e:
            # Catch any other errors that might occur during import
            logger.warning(f"NFC library import error: {e}")
            logger.info("NFC operations will run in simulation mode")
            self._nfc_available = False
            return False
    
    def initialize_reader(self) -> bool:
        """Initialize the NFC reader connection"""
        if not self._check_nfc_availability():
            logger.info("NFC reader initialized in simulation mode")
            return True
        
        try:
            import nfc
            # Try to connect to the ACS ACR122U reader
            # This will automatically detect USB readers
            self._clf = nfc.ContactlessFrontend('usb')
            if self._clf:
                logger.info("NFC reader initialized successfully")
                return True
            else:
                logger.error("Failed to initialize NFC reader")
                return False
        except Exception as e:
            logger.error(f"Error initializing NFC reader: {e}")
            return False
    
    def close_reader(self) -> None:
        """Close the NFC reader connection"""
        if self._clf:
            self._clf.close()
            self._clf = None
            logger.info("NFC reader connection closed")
    
    def wait_for_card(self) -> Optional[Any]:
        """Wait for an NFC card to be placed on the reader"""
        if not self._check_nfc_availability():
            # Simulation mode
            logger.info("Simulating card detection (no NFC hardware)")
            time.sleep(2)  # Simulate waiting
            return {"simulated": True, "identifier": b'\x04\x12\x34\x56\x78\x90\x12'}
        
        if not self._clf:
            if not self.initialize_reader():
                return None
        
        try:
            import nfc
            start_time = time.time()
            logger.info("Waiting for NFC card...")
            # Wait for a tag to be presented
            tag = self._clf.connect(rdwr={
                'on-connect': lambda tag: False  # Return False to keep the connection open
            }, terminate=lambda: time.time() - start_time > self.timeout)
            
            if tag:
                logger.info(f"Card detected: {tag}")
                return tag
            else:
                logger.warning("No card detected within timeout period")
                return None
                
        except Exception as e:
            logger.error(f"Error waiting for card: {e}")
            return None
    
    def write_token_to_card(self, token: str, member_id: int) -> Dict[str, Any]:
        """
        Write a token to an NFC card
        
        Args:
            token: The token string to write
            member_id: The member ID associated with the token
            
        Returns:
            Dict containing success status, message, and card details
        """
        with self._lock:
            try:
                if not self._check_nfc_availability():
                    # Simulation mode
                    logger.info(f"🎭 Running in simulation mode - member {member_id}")
                    logger.info("💡 No physical NFC card needed - simulating card write")
                    time.sleep(3)  # Simulate writing time
                    card_id = f"SIM{member_id:04d}"
                    logger.info(f"✅ Simulated successful write to card {card_id}")
                    return {
                        "success": True,
                        "message": f"Token successfully written to simulated card {card_id} (simulation mode)",
                        "card_id": card_id,
                        "token_written": token
                    }
                
                # Real NFC hardware mode
                start_time = time.time()
                tag = None
                
                logger.info("Please place an NFC card on the reader...")
                
                if not self._clf:
                    if not self.initialize_reader():
                        return {
                            "success": False,
                            "message": "Failed to initialize NFC reader",
                            "card_id": None,
                            "token_written": None
                        }
                
                import nfc
                
                # Wait for card with timeout
                def on_connect(tag):
                    return False  # Keep connection open
                
                def terminate():
                    return time.time() - start_time > self.timeout
                
                tag = self._clf.connect(rdwr={'on-connect': on_connect}, terminate=terminate)
                
                if not tag:
                    return {
                        "success": False,
                        "message": f"No NFC card detected within {self.timeout} seconds",
                        "card_id": None,
                        "token_written": None
                    }
                
                # Get card ID
                card_id = tag.identifier.hex().upper()
                logger.info(f"Writing to card ID: {card_id}")
                
                # Prepare data to write
                # Format: TOKEN|MEMBER_ID|TIMESTAMP
                timestamp = datetime.now().isoformat()
                data_to_write = f"{token}|{member_id}|{timestamp}"
                
                # Write data to NDEF record
                if hasattr(tag, 'ndef') and tag.ndef:
                    # Create simple text record without using ndef library
                    # We'll write the data directly to the tag
                    try:
                        # Clear existing records
                        tag.ndef.records = []
                        
                        # Create a simple text record manually
                        # NDEF Text Record format: [flags][lang_len][lang][text]
                        payload = bytes([0x02, 0x65, 0x6E]) + data_to_write.encode('utf-8')  # UTF-8, "en", text
                        record = nfc.ndef.Record('T', '', payload)
                        tag.ndef.records = [record]
                        
                        logger.info(f"Successfully wrote token to card {card_id}")
                        return {
                            "success": True,
                            "message": f"Token successfully written to card {card_id}",
                            "card_id": card_id,
                            "token_written": token
                        }
                    except Exception as write_error:
                        logger.error(f"Failed to write NDEF data: {write_error}")
                        return {
                            "success": False,
                            "message": f"Failed to write data to card: {write_error}",
                            "card_id": card_id,
                            "token_written": None
                        }
                else:
                    # Try to format the card for NDEF if not already formatted
                    try:
                        tag.format()
                        # Try writing again after formatting
                        payload = bytes([0x02, 0x65, 0x6E]) + data_to_write.encode('utf-8')
                        record = nfc.ndef.Record('T', '', payload)
                        tag.ndef.records = [record]
                        
                        logger.info(f"Formatted and wrote token to card {card_id}")
                        return {
                            "success": True,
                            "message": f"Card formatted and token written to card {card_id}",
                            "card_id": card_id,
                            "token_written": token
                        }
                    except Exception as format_error:
                        logger.error(f"Failed to format card: {format_error}")
                        return {
                            "success": False,
                            "message": f"Card does not support NDEF and formatting failed: {format_error}",
                            "card_id": card_id,
                            "token_written": None
                        }
                        
            except Exception as e:
                logger.error(f"Error writing to NFC card: {e}")
                return {
                    "success": False,
                    "message": f"Error writing to card: {str(e)}",
                    "card_id": None,
                    "token_written": None
                }
    
    def read_card_data(self) -> Dict[str, Any]:
        """
        Read data from an NFC card
        
        Returns:
            Dict containing card data and status
        """
        with self._lock:
            try:
                if not self._check_nfc_availability():
                    # Simulation mode
                    logger.info("🎭 Running in simulation mode - simulating card read")
                    logger.info("💡 No physical NFC card needed - returning simulated data")
                    time.sleep(2)  # Simulate reading time
                    return {
                        "success": True,
                        "message": "Successfully read data from simulated card SIM0001 (simulation mode)",
                        "data": {
                            "card_id": "SIM0001",
                            "content": "SIMULATED_TOKEN|1|2024-01-01T12:00:00",
                            "records_count": 1
                        }
                    }
                
                # Real NFC hardware mode
                start_time = time.time()
                
                if not self._clf:
                    if not self.initialize_reader():
                        return {
                            "success": False,
                            "message": "Failed to initialize NFC reader",
                            "data": None
                        }
                
                import nfc
                
                logger.info("Please place an NFC card on the reader to read...")
                
                def on_connect(tag):
                    return False
                
                def terminate():
                    return time.time() - start_time > self.timeout
                
                tag = self._clf.connect(rdwr={'on-connect': on_connect}, terminate=terminate)
                
                if not tag:
                    return {
                        "success": False,
                        "message": f"No NFC card detected within {self.timeout} seconds",
                        "data": None
                    }
                
                card_id = tag.identifier.hex().upper()
                
                if hasattr(tag, 'ndef') and tag.ndef and tag.ndef.records:
                    # Read NDEF records without using ndef library
                    data = ""
                    for record in tag.ndef.records:
                        if record.type == 'T':  # Text record
                            # Extract text from NDEF text record
                            payload = record.data
                            if len(payload) > 3:
                                # Skip the flags, lang length, and language code
                                lang_len = payload[0] & 0x3F
                                text_start = 1 + lang_len
                                if text_start < len(payload):
                                    data += payload[text_start:].decode('utf-8', errors='ignore')
                    
                    return {
                        "success": True,
                        "message": f"Successfully read data from card {card_id}",
                        "data": {
                            "card_id": card_id,
                            "content": data,
                            "records_count": len(tag.ndef.records)
                        }
                    }
                else:
                    return {
                        "success": True,
                        "message": f"Card {card_id} detected but no NDEF data found",
                        "data": {
                            "card_id": card_id,
                            "content": None,
                            "records_count": 0
                        }
                    }
                    
            except Exception as e:
                logger.error(f"Error reading NFC card: {e}")
                return {
                    "success": False,
                    "message": f"Error reading card: {str(e)}",
                    "data": None
                }


# Global NFC service instance
nfc_service = NFCService()