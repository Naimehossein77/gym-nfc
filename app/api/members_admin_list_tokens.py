# app/api/members_admin_list_tokens.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List, Optional
from datetime import datetime, timezone

from app.core.dependencies import require_admin
from app.database import get_db, User, Token  # <- adjust if your models live elsewhere
from pydantic import BaseModel

router = APIRouter(prefix="/api/members/admin", tags=["members-admin"])

class MemberWithTokenOut(BaseModel):
    member_id: int
    username: str
    token: Optional[str] = None  # None হলে বুঝবেন এখনো token generate হয়নি / valid নেই

class MemberWithTokenOut(BaseModel):
    member_id: int
    username: str
    token: Optional[str] = None  # None হলে বুঝবেন এখনো token generate হয়নি / valid নেই
    token_issued_at: Optional[datetime] = None
    token_expires_at: Optional[datetime] = None

@router.get(
    "/members-with-tokens",
    response_model=List[MemberWithTokenOut],
    dependencies=[Depends(require_admin)],
    status_code=status.HTTP_200_OK,
)
def list_members_with_latest_token(
    db: Session = Depends(get_db),
    only_active_users: bool = Query(True, description="শুধু active user নেবো"),
    only_unexpired_tokens: bool = Query(True, description="expired token বাদ"),
    only_unrevoked_tokens: bool = Query(True, description="revoked token বাদ"),
    limit: int = Query(10000, ge=1, le=20000),
):
    """
    Admin-only:
    প্রতিটা member-এর সর্বশেষ valid token তুলে আনে।
    রিটার্ন: member_id, username, token, token_issued_at, token_expires_at
    """
    try:
        now = datetime.now(timezone.utc)

        # Base user query: শুধু role='member' আর member_id আছে এমন user
        uq = db.query(User).filter(User.role == "member", User.member_id.isnot(None))
        if only_active_users:
            uq = uq.filter(User.is_active.is_(True))
        uq = uq.order_by(User.id.asc()).limit(limit).subquery()

        # Token validity condition
        token_filters = []
        if only_unexpired_tokens:
            token_filters.append((Token.expires_at.is_(None)) | (Token.expires_at > now))
        if only_unrevoked_tokens and hasattr(Token, "revoked"):
            token_filters.append((Token.revoked.is_(False)) | (Token.revoked.is_(None)))

        token_where = and_(*token_filters) if token_filters else True

        # প্রতি member_id-এর সর্বশেষ (max created_at) টোকেন খুঁজতে subquery
        latest_token_sq = (
            db.query(
                Token.member_id.label("m_id"),
                func.max(Token.created_at).label("max_created"),
            )
            .filter(Token.member_id.isnot(None))
            .filter(token_where)
            .group_by(Token.member_id)
            .subquery()
        )

        # join users -> latest per-member token created_at -> actual token row to get token string
        q = (
            db.query(
                uq.c.member_id.label("member_id"),
                uq.c.username.label("username"),
                Token.token.label("token"),
                Token.created_at.label("token_issued_at"),
                Token.expires_at.label("token_expires_at"),
            )
            .outerjoin(
                latest_token_sq,
                latest_token_sq.c.m_id == uq.c.member_id,
            )
            .outerjoin(
                Token,
                and_(
                    Token.member_id == latest_token_sq.c.m_id,
                    Token.created_at == latest_token_sq.c.max_created,
                ),
            )
        )

        rows = q.all()
        return [
            MemberWithTokenOut(
                member_id=r.member_id,
                username=r.username,
                token=r.token,
                token_issued_at=r.token_issued_at,
                token_expires_at=r.token_expires_at
            )
            for r in rows
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing members with tokens: {e}")
