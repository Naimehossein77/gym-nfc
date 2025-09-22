from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from app.core.security import authenticate_user, create_access_token
from app.core.config import settings
from app.models import Token

router = APIRouter(prefix="/api/auth", tags=["authentication"])


@router.post("/login", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Login endpoint to get JWT access token
    
    Use credentials:
    - Username: admin, Password: admin123 (admin role)
    - Username: frontdesk, Password: frontdesk123 (staff role)
    """
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.jwt_access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}