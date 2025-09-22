from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.dependencies import get_staff_user, get_admin_user
from app.models import (
    Member, MemberCreate, MemberUpdate, MemberSearchRequest, 
    MemberSearchResponse, APIResponse
)
from app.services.member_service import member_service
from app.database import get_db

router = APIRouter(prefix="/api/members", tags=["members"])


@router.post("/", response_model=Member)
async def create_member(
    member_data: MemberCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_staff_user)
):
    """
    Create a new gym member
    
    Requires staff or admin privileges.
    
    - **name**: Full name of the member
    - **email**: Email address (must be unique)
    - **phone**: Phone number (optional)
    - **membership_type**: Type of membership (Basic, Premium, Student, etc.)
    - **status**: Member status (active, suspended, etc.)
    """
    try:
        member = member_service.create_member(db, member_data)
        return member
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating member: {str(e)}"
        )


@router.get("/", response_model=list[Member])
async def get_all_members(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_staff_user)
):
    """
    Get all members with pagination
    
    Requires staff or admin privileges.
    
    - **skip**: Number of records to skip (default: 0)
    - **limit**: Maximum number of records to return (default: 100)
    """
    try:
        members = member_service.get_all_members(db, skip=skip, limit=limit)
        return members
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving members: {str(e)}"
        )


@router.post("/search", response_model=MemberSearchResponse)
async def search_members(
    request: MemberSearchRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_staff_user)
):
    """
    Search for gym members by name, email, phone, or ID
    
    Requires staff or admin privileges.
    
    - **query**: Search query (name, email, phone, or member ID)
    - **limit**: Maximum number of results to return (default: 10)
    - **offset**: Number of results to skip for pagination (default: 0)
    """
    try:
        result = member_service.search_members(db, request)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching members: {str(e)}"
        )


@router.get("/{member_id}", response_model=Member)
async def get_member(
    member_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_staff_user)
):
    """
    Get a specific member by ID
    
    Requires staff or admin privileges.
    """
    member = member_service.get_member_by_id(db, member_id)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found"
        )
    
    return member


@router.put("/{member_id}", response_model=Member)
async def update_member(
    member_id: int,
    member_data: MemberUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_staff_user)
):
    """
    Update a member's information
    
    Requires staff or admin privileges.
    
    - **name**: Full name of the member (optional)
    - **email**: Email address (optional, must be unique)
    - **phone**: Phone number (optional)
    - **membership_type**: Type of membership (optional)
    - **status**: Member status (optional)
    """
    try:
        member = member_service.update_member(db, member_id, member_data)
        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Member not found"
            )
        return member
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating member: {str(e)}"
        )


@router.delete("/{member_id}")
async def delete_member(
    member_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_admin_user)  # Only admins can delete
):
    """
    Delete a member (soft delete)
    
    Requires admin privileges.
    
    This performs a soft delete by setting the member status to 'deleted'.
    """
    try:
        success = member_service.delete_member(db, member_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Member not found"
            )
        
        return APIResponse(
            success=True,
            message=f"Member {member_id} has been deleted",
            data={"member_id": member_id, "deleted": True}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting member: {str(e)}"
        )


@router.get("/{member_id}/status")
async def get_member_status(
    member_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_staff_user)
):
    """
    Check if a member is active
    
    Requires staff or admin privileges.
    """
    member = member_service.get_member_by_id(db, member_id)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found"
        )
    
    is_active = member_service.is_member_active(db, member_id)
    
    return APIResponse(
        success=True,
        message=f"Member {member_id} is {'active' if is_active else 'inactive'}",
        data={
            "member_id": member_id,
            "is_active": is_active,
            "status": member.status
        }
    )