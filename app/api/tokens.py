# app/api/tokens.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import require_staff
from app.models import NFCTokenRequest, NFCToken, APIResponse
from app.services.token_service import token_service
from app.services.member_service import member_service
from app.database import get_db
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/api/tokens", tags=["tokens"])


@router.post("/generate", response_model=NFCToken)
async def generate_token(
    request: NFCTokenRequest,
    db: Session = Depends(get_db),
    current_user = Depends(require_staff)
):
    # member check
    if not member_service.is_member_active(db, request.member_id):
        member = member_service.get_member_by_id(db, request.member_id)
        if not member:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Member {request.member_id} is not active (status: {member.status})"
        )
    try:
        return token_service.generate_token(db, request)  # contains optional encrypted_payload
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating token: {e}")


# @router.get("/{token}/validate")
# async def validate_token(
#     token: str,
#     db: Session = Depends(get_db)
# ):
#     nfc_token = token_service.get_token(db, token)
#     if not nfc_token:
#         raise HTTPException(status_code=404, detail="Token not found")
#     is_valid = token_service.is_token_valid(db, token)
#     return APIResponse(
#         success=True,
#         message=f"Token is {'valid' if is_valid else 'invalid/expired'}",
#         data={
#             "token": token,
#             "is_valid": is_valid,
#             "member_id": nfc_token.member_id,
#             "created_at": nfc_token.created_at.isoformat(),
#             "expires_at": nfc_token.expires_at.isoformat() if nfc_token.expires_at else None
#         }
#     )
@router.get("/{token}/validate")
async def validate_token(
    token: str,
    db: Session = Depends(get_db)
):
    
    nfc_token = token_service.get_token(db, token)
    if not nfc_token:
        raise HTTPException(status_code=404, detail="Token not found")
    
    is_valid = token_service.is_token_valid(db, token)
    
    # Get member info for display
    member = member_service.get_member_by_id(db, nfc_token.member_id)
    member_name = member.name if member else "Unknown Member"
    
    status_color = "#10B981" if is_valid else "#EF4444"
    status_text = "Valid" if is_valid else "Invalid/Expired"
    icon = "✅" if is_valid else "❌"
    
    # Format dates
    issue_date = nfc_token.created_at.strftime('%B %d, %Y at %I:%M %p')
    expire_date = nfc_token.expires_at.strftime('%B %d, %Y at %I:%M %p') if nfc_token.expires_at else "Never"
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Token Validation</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
            }}
            .container {{
                background: white;
                border-radius: 20px;
                padding: 40px 30px;
                text-align: center;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                max-width: 400px;
                width: 100%;
            }}
            .icon {{
                font-size: 4rem;
                margin-bottom: 20px;
            }}
            .status {{
                color: {status_color};
                font-size: 2rem;
                font-weight: bold;
                margin-bottom: 15px;
            }}
            .member {{
                color: #374151;
                font-size: 1.2rem;
                margin-bottom: 10px;
            }}
            .date-info {{
                color: #6B7280;
                font-size: 0.9rem;
                margin: 10px 0;
                padding: 8px;
                background: #F9FAFB;
                border-radius: 8px;
            }}
            .badge {{
                background: {status_color};
                color: white;
                padding: 8px 16px;
                border-radius: 20px;
                font-size: 0.9rem;
                font-weight: 500;
                display: inline-block;
                margin-top: 15px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="icon">{icon}</div>
            <div class="status">Token {status_text}</div>
            <div class="member">{member_name}</div>
            <div class="badge">Member ID: {nfc_token.member_id}</div>
            <div class="date-info">
                <strong>Issued:</strong> {issue_date}
            </div>
            <div class="date-info">
                <strong>Expires:</strong> {expire_date}
            </div>
        </div>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content)


@router.get("/member/{member_id}")
async def get_member_tokens(
    member_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_staff)
):
    member = member_service.get_member_by_id(db, member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    tokens = token_service.get_tokens_for_member(db, member_id)
    return APIResponse(
        success=True,
        message=f"Found {len(tokens)} tokens for member {member_id}",
        data={
            "member_id": member_id,
            "tokens": [
                {
                    "token": t.token,
                    "created_at": t.created_at.isoformat(),
                    "expires_at": t.expires_at.isoformat() if t.expires_at else None,
                    "is_valid": token_service.is_token_valid(db, t.token)
                } for t in tokens
            ]
        }
    )


@router.delete("/{token}/revoke")
async def revoke_token(
    token: str,
    db: Session = Depends(get_db),
    current_user = Depends(require_staff)
):
    if not token_service.revoke_token(db, token):
        raise HTTPException(status_code=404, detail="Token not found")
    return APIResponse(
        success=True,
        message=f"Token {token} has been revoked",
        data={"token": token, "revoked": True}
    )


@router.post("/cleanup")
async def cleanup_expired_tokens(
    db: Session = Depends(get_db),
    current_user = Depends(require_staff)
):
    count = token_service.cleanup_expired_tokens(db)
    return APIResponse(
        success=True,
        message=f"Cleaned up {count} expired tokens",
        data={"expired_tokens_removed": count}
    )
