# app/core/dependencies.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from sqlalchemy.orm import joinedload

from app.core.security import decode_token
from app.database import SessionLocal, User

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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )

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

# NEW: allow admins/staff to access any member; members can only access their own member_id
async def require_self_or_staff(
    member_id: int,  # pulled from path param automatically
    user: User = Depends(get_current_user)
) -> User:
    # Admin/Staff: full access
    if user.role in ("admin", "staff"):
        return user
    # Member: only their own record
    if user.role == "member" and getattr(user, "member_id", None) == member_id:
        return user
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

# Optional helper: self or admin (useful for sensitive updates)
async def require_self_or_admin(
    member_id: int,
    user: User = Depends(get_current_user)
) -> User:
    if user.role == "admin":
        return user
    if user.role == "member" and getattr(user, "member_id", None) == member_id:
        return user
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
