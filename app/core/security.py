from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from app.core.config import settings
from app.models import TokenData

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt


def verify_token(token: str, credentials_exception: HTTPException) -> TokenData:
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
        return token_data
    except JWTError:
        raise credentials_exception


# Mock user database for demo purposes
# In production, this would be replaced with a proper database
FAKE_USERS_DB = {
    "admin": {
        "username": "admin",
        "hashed_password": get_password_hash("admin123"),  # Change this in production!
        "role": "admin"
    },
    "frontdesk": {
        "username": "frontdesk", 
        "hashed_password": get_password_hash("frontdesk123"),  # Change this in production!
        "role": "staff"
    }
}


def authenticate_user(username: str, password: str) -> Optional[dict]:
    """Authenticate a user with username and password"""
    user = FAKE_USERS_DB.get(username)
    if not user:
        return None
    if not verify_password(password, user["hashed_password"]):
        return None
    return user


def get_user(username: str) -> Optional[dict]:
    """Get user by username"""
    return FAKE_USERS_DB.get(username)