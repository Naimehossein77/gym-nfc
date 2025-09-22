from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.dependencies import get_staff_user
from app.models import NFCTokenRequest, NFCToken, APIResponse
from app.services.token_service import token_service
from app.services.member_service import member_service
from app.database import get_db

router = APIRouter(prefix="/api/tokens", tags=["tokens"])


@router.post("/generate", response_model=NFCToken)
async def generate_token(
    request: NFCTokenRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_staff_user)
):
    """
    Generate a new NFC token for a member
    
    Requires staff or admin privileges.
    
    - **member_id**: ID of the member to generate token for
    - **expires_in_days**: Optional expiration in days (if not provided, token doesn't expire)
    """
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
        token = token_service.generate_token(db, request)
        return token
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating token: {str(e)}"
        )


@router.get("/{token}/validate")
async def validate_token(
    token: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_staff_user)
):
    """
    Validate an NFC token
    
    Requires staff or admin privileges.
    """
    nfc_token = token_service.get_token(db, token)
    if not nfc_token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Token not found"
        )
    
    is_valid = token_service.is_token_valid(db, token)
    
    return APIResponse(
        success=True,
        message=f"Token is {'valid' if is_valid else 'invalid/expired'}",
        data={
            "token": token,
            "is_valid": is_valid,
            "member_id": nfc_token.member_id,
            "created_at": nfc_token.created_at.isoformat(),
            "expires_at": nfc_token.expires_at.isoformat() if nfc_token.expires_at else None
        }
    )


@router.get("/member/{member_id}")
async def get_member_tokens(
    member_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_staff_user)
):
    """
    Get all tokens for a specific member
    
    Requires staff or admin privileges.
    """
    # Verify member exists
    member = member_service.get_member_by_id(db, member_id)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found"
        )
    
    tokens = token_service.get_tokens_for_member(db, member_id)
    
    return APIResponse(
        success=True,
        message=f"Found {len(tokens)} tokens for member {member_id}",
        data={
            "member_id": member_id,
            "tokens": [
                {
                    "token": token.token,
                    "created_at": token.created_at.isoformat(),
                    "expires_at": token.expires_at.isoformat() if token.expires_at else None,
                    "is_valid": token_service.is_token_valid(db, token.token)
                }
                for token in tokens
            ]
        }
    )


@router.delete("/{token}/revoke")
async def revoke_token(
    token: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_staff_user)
):
    """
    Revoke an NFC token
    
    Requires staff or admin privileges.
    """
    success = token_service.revoke_token(db, token)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Token not found"
        )
    
    return APIResponse(
        success=True,
        message=f"Token {token} has been revoked",
        data={"token": token, "revoked": True}
    )


@router.post("/cleanup")
async def cleanup_expired_tokens(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_staff_user)
):
    """
    Clean up expired tokens
    
    Requires staff or admin privileges.
    """
    try:
        count = token_service.cleanup_expired_tokens(db)
        return APIResponse(
            success=True,
            message=f"Cleaned up {count} expired tokens",
            data={"expired_tokens_removed": count}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error cleaning up tokens: {str(e)}"
        )