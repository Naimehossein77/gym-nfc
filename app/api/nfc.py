# app/api/nfc.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from cryptography.fernet import Fernet, InvalidToken
import json, time

from app.core.dependencies import require_staff
from app.models import NFCWriteRequest, NFCWriteResponse, APIResponse
from app.services.nfc_service import nfc_service
from app.services.token_service import token_service
from app.services.member_service import member_service
from app.database import get_db
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/nfc", tags=["nfc"])


# ----------- existing write/read/status routes (unchanged) -----------

@router.post("/write", response_model=NFCWriteResponse)
async def write_token_to_card(
    request: NFCWriteRequest,
    db: Session = Depends(get_db),
    current_user = Depends(require_staff)
):
    nfc_token = token_service.get_token(db, request.token)
    if not nfc_token:
        raise HTTPException(status_code=404, detail="Token not found")

    if not token_service.is_token_valid(db, request.token):
        raise HTTPException(status_code=400, detail="Token is invalid or expired")

    if nfc_token.member_id != request.member_id:
        raise HTTPException(status_code=400, detail="Token does not belong to the specified member")

    if not member_service.is_member_active(db, request.member_id):
        member = member_service.get_member_by_id(db, request.member_id)
        if not member:
            raise HTTPException(status_code=404, detail="Member not found")
        raise HTTPException(status_code=400, detail=f"Member {request.member_id} is not active (status: {member.status})")

    try:
        logger.info(f"Starting NFC write operation for member {request.member_id}")
        result = nfc_service.write_token_to_card(request.token, request.member_id)
        if result["success"]:
            logger.info(f"Wrote token to card {result['card_id']}")
            return NFCWriteResponse(
                success=True,
                message=result["message"],
                card_id=result["card_id"],
                token_written=result["token_written"]
            )
        raise HTTPException(status_code=400, detail=result["message"])
    except Exception as e:
        logger.error(f"NFC write error: {e}")
        raise HTTPException(status_code=500, detail=f"NFC operation failed: {e}")


@router.get("/read")
async def read_card_data(current_user = Depends(require_staff)):
    try:
        logger.info("Starting NFC read operation")
        result = nfc_service.read_card_data()
        if result["success"]:
            return APIResponse(success=True, message=result["message"], data=result["data"])
        raise HTTPException(status_code=400, detail=result["message"])
    except Exception as e:
        logger.error(f"NFC read error: {e}")
        raise HTTPException(status_code=500, detail=f"NFC read operation failed: {e}")


@router.get("/status")
async def get_nfc_status(current_user = Depends(require_staff)):
    try:
        if nfc_service.initialize_reader():
            return APIResponse(
                success=True,
                message="NFC reader is connected and operational",
                data={"status": "connected", "reader_type": "ACS ACR122U", "timeout": nfc_service.timeout}
            )
        return APIResponse(
            success=False,
            message="NFC reader is not connected or not operational",
            data={"status": "disconnected", "reader_type": "ACS ACR122U", "timeout": nfc_service.timeout}
        )
    except Exception as e:
        logger.error(f"NFC status error: {e}")
        raise HTTPException(status_code=500, detail=f"Error checking NFC reader status: {e}")


# ----------- NEW: encrypted payload validate (no hardware needed) -----------

class NFCValidateDTO(BaseModel):
    encrypted_payload: str

@router.post("/validate")
async def validate_encrypted_payload(
    dto: NFCValidateDTO,
    db: Session = Depends(get_db),
    current_user = Depends(require_staff)
):
    if not settings.fernet_key:
        raise HTTPException(status_code=400, detail="Server not configured with FERNET_KEY")

    try:
        f = Fernet(settings.fernet_key.encode() if isinstance(settings.fernet_key, str) else settings.fernet_key)
        data = json.loads(f.decrypt(dto.encrypted_payload.encode()).decode())
        token_str = data.get("t"); mid = data.get("mid"); exp = data.get("exp")

        if not token_str or not mid:
            raise HTTPException(status_code=400, detail="Invalid payload")
        if exp is not None and time.time() > float(exp):
            return APIResponse(success=False, message="Token expired", data={"valid": False, "reason": "expired"})

        # DB check
        nfc_token = token_service.get_token(db, token_str)
        if not nfc_token or nfc_token.member_id != mid:
            return APIResponse(success=False, message="Token not found or mismatched", data={"valid": False, "reason": "not_found"})

        if not token_service.is_token_valid(db, token_str):
            return APIResponse(success=False, message="Token invalid/expired", data={"valid": False, "reason": "invalid"})

        return APIResponse(success=True, message="Token valid", data={"valid": True, "member_id": mid})

    except InvalidToken:
        raise HTTPException(status_code=400, detail="Bad encrypted payload")
