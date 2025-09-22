from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.security import verify_token, get_user
from app.models import TokenData

# Security scheme for JWT token
security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Dependency to get the current authenticated user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = credentials.credentials
    token_data = verify_token(token, credentials_exception)
    user = get_user(username=token_data.username)
    
    if user is None:
        raise credentials_exception
    
    return user


async def get_admin_user(current_user: dict = Depends(get_current_user)) -> dict:
    """Dependency to ensure the current user is an admin"""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user


async def get_staff_user(current_user: dict = Depends(get_current_user)) -> dict:
    """Dependency to ensure the current user is staff or admin"""
    if current_user.get("role") not in ["admin", "staff"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Staff privileges required"
        )
    return current_user