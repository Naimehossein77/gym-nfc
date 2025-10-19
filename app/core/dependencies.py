# app/core/dependencies.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from app.core.security import decode_token
from app.database import SessionLocal, User
from sqlalchemy.orm import joinedload

security = HTTPBearer()

def _get_user_by_id(user_id: int):
    db = SessionLocal()
    try:
            return (
          db.query(User)
             .options(joinedload(User.member))
             .filter(User.id == user_id)
             .first()
      )
    finally:
        db.close()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    token = credentials.credentials
    try:
        payload = decode_token(token)
        uid = int(payload.get("uid", 0))
        if not uid:
            raise ValueError("Invalid token payload")
        user = _get_user_by_id(uid)
        if not user or not user.is_active:
            raise ValueError("User inactive or not found")
        return user
    except (JWTError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")

async def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admins only")
    return user

async def require_staff(user: User = Depends(get_current_user)) -> User:
    if user.role not in ("admin", "staff"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Staff only")
    return user

async def require_member(user: User = Depends(get_current_user)) -> User:
    if user.role != "member":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Members only")
    return user
