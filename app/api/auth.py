# app/api/auth.py
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from app.core.config import settings
from app.core.security import authenticate_user, create_access_token
from app.database import SessionLocal, User

router = APIRouter(prefix="/api/auth", tags=["authentication"])

def _issue_token(user: User):
    access_token_expires = timedelta(minutes=settings.jwt_access_token_expire_minutes)
    token = create_access_token(
        data={"sub": user.username, "role": user.role, "uid": user.id},
        expires_delta=access_token_expires
    )
    return {"access_token": token, "token_type": "bearer", "role": user.role}

@router.post("/admin/login")
async def admin_login(form: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form.username, form.password)
    if not user or user.role not in ("admin", "staff"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin/staff credentials")
    return _issue_token(user)

@router.post("/member/login")
async def member_login(form: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form.username, form.password)
    if not user or user.role != "member":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid member credentials")
    # ঐচ্ছিক: member status check (active)
    if not user.member or user.member.status != "active":
        raise HTTPException(status_code=403, detail=f"Member is {user.member.status if user.member else 'missing'}")
    return _issue_token(user)
