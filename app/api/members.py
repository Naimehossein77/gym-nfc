from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.dependencies import require_staff, require_admin, require_self_or_staff, require_member
from app.models import (
    Member, MemberCreate, MemberUpdate, MemberSearchRequest,
    MemberSearchResponse, APIResponse
)
from app.services.member_service import member_service
from app.database import get_db, User
from app.core.security import get_password_hash

router = APIRouter(prefix="/api/members", tags=["members"])


@router.post("/", response_model=Member, status_code=status.HTTP_201_CREATED)
async def create_member(
    member_data: MemberCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_staff),
):
    """
    Create a new gym member (staff/admin only)
    """
    try:
        member = member_service.create_member(db, member_data)
        return member
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating member: {str(e)}",
        )


@router.get("/", response_model=list[Member])
async def get_all_members(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user=Depends(require_staff),
):
    """
    Get all members with pagination (staff/admin only)
    """
    try:
        members = member_service.get_all_members(db, skip=skip, limit=limit)
        return members
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving members: {str(e)}",
        )


@router.post("/search", response_model=MemberSearchResponse)
async def search_members(
    request: MemberSearchRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_staff),
):
    """
    Search for members (staff/admin only)
    """
    try:
        result = member_service.search_members(db, request)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching members: {str(e)}",
        )


@router.get("/me", response_model=Member)
async def get_current_member(
    db: Session = Depends(get_db),
    current_user=Depends(require_member),
):
    """
    Get the current logged-in member's details
    """
    member = member_service.get_member_by_id(db, current_user.member_id)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found",
        )
    return member


@router.get("/{member_id}", response_model=Member)
async def get_member(
    member_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_self_or_staff),  # member can view self; staff/admin can view any
):
    member = member_service.get_member_by_id(db, member_id)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found",
        )
    return member


@router.put("/{member_id}", response_model=Member)
async def update_member(
    member_id: int,
    member_data: MemberUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_staff),
):
    """
    Update a member (staff/admin only)
    """
    try:
        member = member_service.update_member(db, member_id, member_data)
        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Member not found",
            )
        return member
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating member: {str(e)}",
        )


@router.delete("/{member_id}", response_model=APIResponse)
async def delete_member(
    member_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    """
    Soft delete a member (admin only)
    """
    try:
        success = member_service.delete_member(db, member_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Member not found",
            )

        return APIResponse(
            success=True,
            message=f"Member {member_id} has been deleted",
            data={"member_id": member_id, "deleted": True},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting member: {str(e)}",
        )


@router.get("/{member_id}/status", response_model=APIResponse)
async def get_member_status(
    member_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_self_or_staff),  # member can view self; staff/admin can view any
):
    member = member_service.get_member_by_id(db, member_id)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found",
        )

    is_active = member_service.is_member_active(db, member_id)
    return APIResponse(
        success=True,
        message=f"Member {member_id} is {'active' if is_active else 'inactive'}",
        data={
            "member_id": member_id,
            "is_active": is_active,
            "status": member.status,
        },
    )


class MemberCredentialDTO(BaseModel):
    username: str
    password: str


@router.post("/{member_id}/credentials", dependencies=[Depends(require_staff)])
def set_member_credentials(
    member_id: int,
    dto: MemberCredentialDTO,
    db: Session = Depends(get_db),
):
    """
    Set or update login credentials for a member (staff/admin only)
    """
    member = member_service.get_member_by_id(db, member_id)
    if not member or member.status != "active":
        raise HTTPException(status_code=404, detail="Member not found or not active")

    # unique username check
    exist = db.query(User).filter(User.username == dto.username).first()
    if exist:
        raise HTTPException(status_code=400, detail="Username already taken")

    # create or update user for member
    u = db.query(User).filter(User.member_id == member_id).first()
    if not u:
        u = User(
            username=dto.username,
            email=member.email,
            role="member",
            member_id=member_id,
            is_active=True,
            password_hash=get_password_hash(dto.password),
        )
        db.add(u)
    else:
        u.username = dto.username
        u.password_hash = get_password_hash(dto.password)
        u.is_active = True

    db.commit()
    return {"success": True, "message": "Member credentials set"}
