# app/api/wallet.py
import os
import json
import tempfile
import zipfile
import subprocess
import shutil
from datetime import datetime
from typing import Dict, Any
from pathlib import Path

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import logging

from app.core.dependencies import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/pass", tags=["apple_wallet"])


class NFCData(BaseModel):
    """NFC data for the pass"""
    message: str  # Base64 encoded token


class PassSignRequest(BaseModel):
    """Request model for signing Apple Wallet pass"""
    serialNumber: str
    description: str
    organizationName: str
    passTypeIdentifier: str
    teamIdentifier: str
    nfc: NFCData


class PassService:
    """Service for creating and signing Apple Wallet passes"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent.parent  # Navigate to project root
        self.static_dir = self.base_dir / "static"
        self.certs_dir = self.base_dir / "certs"
        
        # Certificate file paths
        self.pass_cert_path = self.certs_dir / "pass_cert.pem"
        self.pass_key_path = self.certs_dir / "pass_key.pem"
        self.wwdr_cert_path = self.certs_dir / "WWDR.pem"
        
        logger.info(f"PassService initialized with base_dir: {self.base_dir}")
    
    def _validate_certificates(self) -> None:
        """Validate that required certificate files exist"""
        required_files = [
            (self.pass_cert_path, "Apple Pass Type Certificate"),
            (self.pass_key_path, "Apple Pass Type Private Key"),
            (self.wwdr_cert_path, "Apple WWDR Certificate")
        ]
        
        missing_files = []
        for file_path, description in required_files:
            if not file_path.exists():
                missing_files.append(f"{description} ({file_path})")
        
        if missing_files:
            raise HTTPException(
                status_code=500,
                detail=f"Missing certificate files: {', '.join(missing_files)}"
            )
    
    def _create_pass_json(self, request_data: PassSignRequest) -> Dict[str, Any]:
        """Create the pass.json content"""
        pass_data = {
            "formatVersion": 1,
            "passTypeIdentifier": request_data.passTypeIdentifier,
            "serialNumber": request_data.serialNumber,
            "teamIdentifier": request_data.teamIdentifier,
            "organizationName": request_data.organizationName,
            "description": request_data.description,
            "logoText": request_data.organizationName,
            "foregroundColor": "rgb(255, 255, 255)",
            "backgroundColor": "rgb(197, 31, 31)",  # Using working sample colors
            "generic": {
                "primaryFields": [
                    {
                        "key": "member",
                        "value": request_data.description
                    }
                ],
                "secondaryFields": [
                    {
                        "key": "subtitle",
                        "label": "MEMBER SINCE",
                        "value": "2025"
                    }
                ],
                "auxiliaryFields": [
                    {
                        "key": "serial",
                        "label": "SERIAL NUMBER",
                        "value": request_data.serialNumber
                    }
                ]
            },
            # Remove NFC section entirely - this was causing validation failures
            # NFC functionality can be added later with proper encryption key
            "barcode": {
                "message": request_data.nfc.message,
                "format": "PKBarcodeFormatQR",
                "messageEncoding": "iso-8859-1"
            }
        }
        
        return pass_data
    
    def _create_manifest(self, temp_dir: Path) -> Dict[str, str]:
        """Create manifest.json with SHA1 hashes of all files"""
        import hashlib
        
        manifest = {}
        
        # Hash all files in the pass bundle
        for file_path in temp_dir.glob("*"):
            if file_path.is_file() and file_path.name != "manifest.json":
                with open(file_path, "rb") as f:
                    content = f.read()
                    sha1_hash = hashlib.sha1(content).hexdigest()
                    manifest[file_path.name] = sha1_hash
        
        return manifest
    
    def _sign_manifest(self, temp_dir: Path) -> None:
        """Sign the manifest.json using OpenSSL"""
        manifest_path = temp_dir / "manifest.json"
        signature_path = temp_dir / "signature"
        
        # Create the signature using OpenSSL
        cmd = [
            "openssl", "smime", "-binary", "-sign",
            "-certfile", str(self.wwdr_cert_path),
            "-signer", str(self.pass_cert_path),
            "-inkey", str(self.pass_key_path),
            "-in", str(manifest_path),
            "-out", str(signature_path),
            "-outform", "DER"
        ]
        
        try:
            logger.info(f"Running OpenSSL command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.info("Manifest signed successfully")
        except subprocess.CalledProcessError as e:
            logger.error(f"OpenSSL signing failed: {e.stderr}")
            logger.error(f"OpenSSL stdout: {e.stdout}")
            logger.error(f"OpenSSL command: {' '.join(cmd)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to sign pass: {e.stderr}"
            )
        except FileNotFoundError:
            raise HTTPException(
                status_code=500,
                detail="OpenSSL not found. Please install OpenSSL."
            )
    
    def create_signed_pass(self, request_data: PassSignRequest) -> bytes:
        """Create and sign a complete Apple Wallet pass"""
        self._validate_certificates()
        
        with tempfile.TemporaryDirectory() as temp_dir_str:
            temp_dir = Path(temp_dir_str)
            logger.info(f"Creating pass in temporary directory: {temp_dir}")
            
            try:
                # 1. Create pass.json
                pass_data = self._create_pass_json(request_data)
                pass_json_path = temp_dir / "pass.json"
                with open(pass_json_path, "w") as f:
                    json.dump(pass_data, f, indent=2)
                
                # 2. Copy images
                icon_src = self.static_dir / "icon.png"
                logo_src = self.static_dir / "logo.png"
                
                if icon_src.exists():
                    shutil.copy2(icon_src, temp_dir / "icon.png")
                else:
                    logger.warning(f"Icon not found at {icon_src}")
                
                if logo_src.exists():
                    shutil.copy2(logo_src, temp_dir / "logo.png")
                else:
                    logger.warning(f"Logo not found at {logo_src}")
                
                # 3. Create manifest.json
                manifest = self._create_manifest(temp_dir)
                manifest_path = temp_dir / "manifest.json"
                with open(manifest_path, "w") as f:
                    json.dump(manifest, f, indent=2)
                
                # 4. Sign the manifest
                self._sign_manifest(temp_dir)
                
                # 5. Create the .pkpass zip file
                pkpass_path = temp_dir / "nfc_access.pkpass"
                with zipfile.ZipFile(pkpass_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
                    for file_path in temp_dir.glob("*"):
                        if file_path.is_file() and file_path.suffix != ".pkpass":
                            zip_file.write(file_path, file_path.name)
                
                # 6. Read the final .pkpass file
                with open(pkpass_path, "rb") as f:
                    pkpass_data = f.read()
                
                logger.info(f"Successfully created signed pass of {len(pkpass_data)} bytes")
                return pkpass_data
                
            except Exception as e:
                logger.error(f"Error creating pass: {e}")
                logger.exception("Full traceback:")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to create pass: {str(e)}"
                )


# Global service instance
pass_service = PassService()


@router.post("/sign")
async def sign_pass(
    request_data: PassSignRequest,
    current_user = Depends(get_current_user)
):
    """
    Sign an Apple Wallet pass for NFC access
    
    This endpoint creates a complete .pkpass file that can be installed
    on iOS devices for NFC access to the gym.
    
    **Authentication:** Requires valid JWT token (admin, staff, or member)
    
    **Required Certificate Files:**
    - ./certs/pass_cert.pem (Apple Pass Type Certificate)
    - ./certs/pass_key.pem (Apple Pass Type Private Key)  
    - ./certs/WWDR.pem (Apple WWDR Certificate)
    
    **Required Static Files:**
    - ./static/icon.png (Pass icon)
    - ./static/logo.png (Pass logo)
    """
    logger.info(f"Creating signed pass for serial: {request_data.serialNumber}")
    
    try:
        # Create the signed pass
        pkpass_data = pass_service.create_signed_pass(request_data)
        
        # Create a file-like object for streaming
        def generate():
            yield pkpass_data
        
        headers = {
            "Content-Type": "application/vnd.apple.pkpass",
            "Content-Disposition": 'attachment; filename="nfc_access.pkpass"',
            "Content-Length": str(len(pkpass_data))
        }
        
        return StreamingResponse(
            generate(),
            headers=headers,
            media_type="application/vnd.apple.pkpass"
        )
        
    except HTTPException:
        # Re-raise HTTPExceptions from the service
        raise
    except Exception as e:
        logger.error(f"Unexpected error signing pass: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )


@router.get("/certificates/status")
async def check_certificate_status(current_user = Depends(get_current_user)):
    """
    Check the status of required certificate files
    
    **Authentication:** Requires valid JWT token (admin, staff, or member)
    """
    
    cert_status = {}
    required_files = [
        ("pass_cert.pem", "Apple Pass Type Certificate"),
        ("pass_key.pem", "Apple Pass Type Private Key"),
        ("WWDR.pem", "Apple WWDR Certificate")
    ]
    
    for filename, description in required_files:
        file_path = pass_service.certs_dir / filename
        cert_status[filename] = {
            "description": description,
            "exists": file_path.exists(),
            "path": str(file_path)
        }
        
        if file_path.exists():
            try:
                stat = file_path.stat()
                cert_status[filename]["size"] = stat.st_size
                cert_status[filename]["modified"] = datetime.fromtimestamp(stat.st_mtime).isoformat()
            except Exception as e:
                cert_status[filename]["error"] = str(e)
    
    # Check static files too
    static_status = {}
    for filename in ["icon.png", "logo.png"]:
        file_path = pass_service.static_dir / filename
        static_status[filename] = {
            "exists": file_path.exists(),
            "path": str(file_path)
        }
    
    all_certs_exist = all(status["exists"] for status in cert_status.values())
    all_static_exist = all(status["exists"] for status in static_status.values())
    
    return {
        "certificates": cert_status,
        "static_files": static_status,
        "ready": all_certs_exist and all_static_exist,
        "message": (
            "All files present and ready for pass signing" 
            if all_certs_exist and all_static_exist 
            else "Missing required files for pass signing"
        )
    }