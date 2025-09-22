from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from app.core.dependencies import get_staff_user
from app.models import NFCWriteRequest, NFCWriteResponse, APIResponse
from app.services.nfc_service import nfc_service
from app.services.token_service import token_service
from app.services.member_service import member_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/nfc", tags=["nfc"])


from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from app.core.dependencies import get_staff_user
from app.models import NFCWriteRequest, NFCWriteResponse, APIResponse
from app.services.nfc_service import nfc_service
from app.services.token_service import token_service
from app.services.member_service import member_service
from app.database import get_db
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/nfc", tags=["nfc"])


@router.post("/write", response_model=NFCWriteResponse)
async def write_token_to_card(
    request: NFCWriteRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_staff_user)
):
    """
    Write a token to an NFC card
    
    This endpoint handles the physical writing of a token to an NFC card.
    It will wait for a card to be placed on the reader (blocking operation).
    
    Requires staff or admin privileges.
    
    - **token**: The token string to write to the card
    - **member_id**: The member ID associated with the token
    
    Instructions:
    1. Call this endpoint with the token and member_id
    2. Place an NFC card on the ACS ACR122U reader within 30 seconds
    3. The token will be written to the card automatically
    4. Remove the card once writing is complete
    """
    # Validate token exists and is valid
    nfc_token = token_service.get_token(db, request.token)
    if not nfc_token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Token not found"
        )
    
    if not token_service.is_token_valid(db, request.token):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token is invalid or expired"
        )
    
    # Verify token belongs to the specified member
    if nfc_token.member_id != request.member_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token does not belong to the specified member"
        )
    
    # Verify member exists and is active
    if not member_service.is_member_active(db, request.member_id):
        member = member_service.get_member_by_id(db, request.member_id)
        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Member not found"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Member {request.member_id} is not active (status: {member.status})"
            )
    
    try:
        # This is a synchronous, blocking operation
        # The frontend should show a "waiting for card" message
        logger.info(f"Starting NFC write operation for member {request.member_id}")
        
        result = nfc_service.write_token_to_card(request.token, request.member_id)
        
        if result["success"]:
            logger.info(f"Successfully wrote token to card {result['card_id']}")
            return NFCWriteResponse(
                success=True,
                message=result["message"],
                card_id=result["card_id"],
                token_written=result["token_written"]
            )
        else:
            logger.error(f"Failed to write token: {result['message']}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )
            
    except Exception as e:
        logger.error(f"Error in NFC write operation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"NFC operation failed: {str(e)}"
        )


@router.get("/read")
async def read_card_data(
    current_user: dict = Depends(get_staff_user)
):
    """
    Read data from an NFC card
    
    This endpoint reads data from an NFC card placed on the reader.
    Useful for debugging and verifying card contents.
    
    Requires staff or admin privileges.
    
    Instructions:
    1. Call this endpoint
    2. Place an NFC card on the ACS ACR122U reader within 30 seconds
    3. The card data will be read and returned
    """
    try:
        logger.info("Starting NFC read operation")
        
        result = nfc_service.read_card_data()
        
        if result["success"]:
            logger.info(f"Successfully read card data")
            return APIResponse(
                success=True,
                message=result["message"],
                data=result["data"]
            )
        else:
            logger.error(f"Failed to read card: {result['message']}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )
            
    except Exception as e:
        logger.error(f"Error in NFC read operation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"NFC read operation failed: {str(e)}"
        )


@router.get("/status")
async def get_nfc_status(
    current_user: dict = Depends(get_staff_user)
):
    """
    Get NFC reader status
    
    Check if the NFC reader is connected and operational.
    
    Requires staff or admin privileges.
    """
    try:
        # Try to initialize the reader to check status
        if nfc_service.initialize_reader():
            return APIResponse(
                success=True,
                message="NFC reader is connected and operational",
                data={
                    "status": "connected",
                    "reader_type": "ACS ACR122U",
                    "timeout": nfc_service.timeout
                }
            )
        else:
            return APIResponse(
                success=False,
                message="NFC reader is not connected or not operational",
                data={
                    "status": "disconnected",
                    "reader_type": "ACS ACR122U",
                    "timeout": nfc_service.timeout
                }
            )
    except Exception as e:
        logger.error(f"Error checking NFC status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error checking NFC reader status: {str(e)}"
        )