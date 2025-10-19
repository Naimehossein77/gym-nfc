# app/services/token_service.py
import json, secrets, string
from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session
from cryptography.fernet import Fernet
from app.models import NFCToken, NFCTokenRequest
from app.database import Token as DBToken
from app.core.config import settings

class TokenService:
    def __init__(self) -> None:
        pass

    def _get_fernet(self) -> Optional[Fernet]:
        key = settings.fernet_key
        if not key:
            return None
        try:
            return Fernet(key.encode() if isinstance(key, str) else key)
        except Exception:
            return None

    def generate_token(self, db: Session, request: NFCTokenRequest) -> NFCToken:
        token = self._generate_secure_token()
        expires_at = datetime.utcnow() + timedelta(days=request.expires_in_days) if request.expires_in_days else None

        rec = DBToken(token=token, member_id=request.member_id, expires_at=expires_at, is_active=True)
        db.add(rec); db.commit(); db.refresh(rec)

        # 🔐 build encrypted payload if possible
        encrypted = None
        f = self._get_fernet()
        if f:
            payload = {"t": token, "mid": request.member_id, "exp": int(expires_at.timestamp()) if expires_at else None}
            encrypted = f.encrypt(json.dumps(payload).encode()).decode()

        # ➜ কনস্ট্রাক্টরেই ফিল্ড বসিয়ে দিচ্ছি
        return NFCToken(
            token=token,
            member_id=request.member_id,
            created_at=rec.created_at,
            expires_at=expires_at,
            encrypted_payload=encrypted
        )

    def get_token(self, db: Session, token: str) -> Optional[NFCToken]:
        rec = db.query(DBToken).filter(DBToken.token == token, DBToken.is_active == True).first()
        if not rec: return None
        return NFCToken(token=rec.token, member_id=rec.member_id, created_at=rec.created_at, expires_at=rec.expires_at)

    def is_token_valid(self, db: Session, token: str) -> bool:
        rec = db.query(DBToken).filter(DBToken.token == token, DBToken.is_active == True).first()
        if not rec: return False
        if rec.expires_at and rec.expires_at < datetime.utcnow(): return False
        return True

    def get_tokens_for_member(self, db: Session, member_id: int) -> List[NFCToken]:
        rows = db.query(DBToken).filter(DBToken.member_id == member_id, DBToken.is_active == True).all()
        return [NFCToken(token=r.token, member_id=r.member_id, created_at=r.created_at, expires_at=r.expires_at) for r in rows]

    def revoke_token(self, db: Session, token: str) -> bool:
        rec = db.query(DBToken).filter(DBToken.token == token, DBToken.is_active == True).first()
        if not rec: return False
        rec.is_active = False; rec.updated_at = datetime.utcnow(); db.commit(); return True

    def cleanup_expired_tokens(self, db: Session) -> int:
        now = datetime.utcnow()
        rows = db.query(DBToken).filter(DBToken.expires_at != None, DBToken.expires_at < now, DBToken.is_active == True).all()  # noqa: E711
        for r in rows: r.is_active = False; r.updated_at = now
        db.commit(); return len(rows)

    def _generate_secure_token(self, length: int = 32) -> str:
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))

token_service = TokenService()
