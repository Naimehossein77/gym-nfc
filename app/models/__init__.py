# app/models.py
from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional, List
from datetime import datetime


# ---------------- Members ----------------
class Member(BaseModel):
    """Member model representing a gym member"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    phone: Optional[str] = None
    membership_type: str
    status: str = "active"
    created_at: datetime
    updated_at: datetime


class MemberCreate(BaseModel):
    """Model for creating a new member"""
    name: str
    email: EmailStr
    phone: Optional[str] = None
    membership_type: str = "Basic"
    status: str = "active"


class MemberUpdate(BaseModel):
    """Model for updating a member"""
    name: Optional[str] = None
    email: Optional[EmailStr] = None
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
    members: List[Member]
    total: int
    limit: int
    offset: int


# ---------------- Auth ----------------
class Token(BaseModel):
    """Token model for JWT authentication"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token data for JWT validation"""
    username: Optional[str] = None


# ---------------- NFC Tokens ----------------
class NFCToken(BaseModel):
    """NFC token model for card assignment / validation"""
    # যদি কখনো ORM অবজেক্ট সরাসরি রিটার্ন করেন, এটা রাখতে পারেন:
    # model_config = ConfigDict(from_attributes=True)

    token: str
    member_id: int
    created_at: datetime
    expires_at: Optional[datetime] = None
    encrypted_payload: Optional[str] = None  # ✅ নতুন ফিল্ড


class NFCTokenRequest(BaseModel):
    """Request model for NFC token generation"""
    member_id: int
    expires_in_days: Optional[int] = None


# ---------------- NFC I/O ----------------
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


# ---------------- Common API ----------------
class APIResponse(BaseModel):
    """Generic API response model"""
    success: bool
    message: str
    data: Optional[dict] = None
