from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class Member(BaseModel):
    """Member model representing a gym member"""
    id: int
    name: str
    email: str
    phone: Optional[str] = None
    membership_type: str
    status: str = "active"
    created_at: datetime
    updated_at: datetime


class MemberCreate(BaseModel):
    """Model for creating a new member"""
    name: str
    email: str
    phone: Optional[str] = None
    membership_type: str = "Basic"
    status: str = "active"


class MemberUpdate(BaseModel):
    """Model for updating a member"""
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    membership_type: Optional[str] = None
    status: Optional[str] = None


class MemberSearchRequest(BaseModel):
    """Request model for member search"""
    query: str
    limit: int = 10
    offset: int = 0


class MemberSearchResponse(BaseModel):
    """Response model for member search"""
    members: list[Member]
    total: int
    limit: int
    offset: int


class Token(BaseModel):
    """Token model for JWT authentication"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token data for JWT validation"""
    username: Optional[str] = None


class NFCToken(BaseModel):
    """NFC token model for card assignment"""
    token: str
    member_id: int
    created_at: datetime
    expires_at: Optional[datetime] = None


class NFCTokenRequest(BaseModel):
    """Request model for NFC token generation"""
    member_id: int
    expires_in_days: Optional[int] = None


class NFCWriteRequest(BaseModel):
    """Request model for writing token to NFC card"""
    token: str
    member_id: int


class NFCWriteResponse(BaseModel):
    """Response model for NFC card writing"""
    success: bool
    message: str
    card_id: Optional[str] = None
    token_written: Optional[str] = None


class APIResponse(BaseModel):
    """Generic API response model"""
    success: bool
    message: str
    data: Optional[dict] = None