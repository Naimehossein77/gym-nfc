import secrets
import string
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from app.models import NFCToken, NFCTokenRequest
from app.database import Token as DBToken


class TokenService:
    """Service for managing NFC tokens with database operations"""
    
    def __init__(self):
        pass
    
    def generate_token(self, db: Session, request: NFCTokenRequest) -> NFCToken:
        """
        Generate a new NFC token for a member
        
        Args:
            db: Database session
            request: Token generation request
            
        Returns:
            Generated NFCToken
        """
        # Generate a secure random token
        token = self._generate_secure_token()
        
        # Calculate expiration date
        expires_at = None
        if request.expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=request.expires_in_days)
        
        # Create database token
        db_token = DBToken(
            token=token,
            member_id=request.member_id,
            expires_at=expires_at
        )
        
        db.add(db_token)
        db.commit()
        db.refresh(db_token)
        
        # Create NFCToken object
        nfc_token = NFCToken(
            token=token,
            member_id=request.member_id,
            created_at=db_token.created_at,
            expires_at=expires_at
        )
        
        return nfc_token
    
    def get_token(self, db: Session, token: str) -> Optional[NFCToken]:
        """
        Get token details by token string
        
        Args:
            db: Database session
            token: The token string
            
        Returns:
            NFCToken if found, None otherwise
        """
        db_token = db.query(DBToken).filter(
            DBToken.token == token,
            DBToken.is_active == True
        ).first()
        
        if db_token:
            return NFCToken(
                token=db_token.token,
                member_id=db_token.member_id,
                created_at=db_token.created_at,
                expires_at=db_token.expires_at
            )
        return None
    
    def is_token_valid(self, db: Session, token: str) -> bool:
        """
        Check if a token is valid and not expired
        
        Args:
            db: Database session
            token: The token string
            
        Returns:
            True if token is valid and not expired, False otherwise
        """
        db_token = db.query(DBToken).filter(
            DBToken.token == token,
            DBToken.is_active == True
        ).first()
        
        if not db_token:
            return False
        
        # Check if token is expired
        if db_token.expires_at and db_token.expires_at < datetime.utcnow():
            return False
        
        return True
    
    def get_tokens_for_member(self, db: Session, member_id: int) -> List[NFCToken]:
        """
        Get all tokens for a specific member
        
        Args:
            db: Database session
            member_id: The member's ID
            
        Returns:
            List of NFCTokens for the member
        """
        db_tokens = db.query(DBToken).filter(
            DBToken.member_id == member_id,
            DBToken.is_active == True
        ).all()
        
        return [
            NFCToken(
                token=db_token.token,
                member_id=db_token.member_id,
                created_at=db_token.created_at,
                expires_at=db_token.expires_at
            )
            for db_token in db_tokens
        ]
    
    def revoke_token(self, db: Session, token: str) -> bool:
        """
        Revoke a token by setting it as inactive
        
        Args:
            db: Database session
            token: The token string to revoke
            
        Returns:
            True if token was found and revoked, False otherwise
        """
        db_token = db.query(DBToken).filter(
            DBToken.token == token,
            DBToken.is_active == True
        ).first()
        
        if db_token:
            db_token.is_active = False
            db_token.updated_at = datetime.utcnow()
            db.commit()
            return True
        return False
    
    def cleanup_expired_tokens(self, db: Session) -> int:
        """
        Remove expired tokens from storage
        
        Args:
            db: Database session
            
        Returns:
            Number of tokens deactivated
        """
        now = datetime.utcnow()
        expired_tokens = db.query(DBToken).filter(
            DBToken.expires_at < now,
            DBToken.is_active == True
        ).all()
        
        count = 0
        for token in expired_tokens:
            token.is_active = False
            token.updated_at = now
            count += 1
        
        db.commit()
        return count
    
    def _generate_secure_token(self, length: int = 32) -> str:
        """
        Generate a secure random token
        
        Args:
            length: Length of the token to generate
            
        Returns:
            Secure random token string
        """
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))


# Global token service instance
token_service = TokenService()