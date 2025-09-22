from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models import Member, MemberCreate, MemberUpdate, MemberSearchRequest, MemberSearchResponse
from app.database import Member as DBMember


class MemberService:
    """Service for managing gym members with database operations"""
    
    def __init__(self):
        pass
    
    def create_member(self, db: Session, member_data: MemberCreate) -> Member:
        """
        Create a new member in the database
        
        Args:
            db: Database session
            member_data: Member creation data
            
        Returns:
            Created Member object
        """
        # Check if email already exists
        existing_member = db.query(DBMember).filter(DBMember.email == member_data.email).first()
        if existing_member:
            raise ValueError(f"Member with email {member_data.email} already exists")
        
        # Create new member
        db_member = DBMember(
            name=member_data.name,
            email=member_data.email,
            phone=member_data.phone,
            membership_type=member_data.membership_type,
            status=member_data.status
        )
        
        db.add(db_member)
        db.commit()
        db.refresh(db_member)
        
        return self._db_member_to_pydantic(db_member)
    
    def update_member(self, db: Session, member_id: int, member_data: MemberUpdate) -> Optional[Member]:
        """
        Update an existing member
        
        Args:
            db: Database session
            member_id: Member ID to update
            member_data: Member update data
            
        Returns:
            Updated Member object or None if not found
        """
        db_member = db.query(DBMember).filter(DBMember.id == member_id).first()
        if not db_member:
            return None
        
        # Update fields
        update_data = member_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_member, field, value)
        
        db_member.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_member)
        
        return self._db_member_to_pydantic(db_member)
    
    def delete_member(self, db: Session, member_id: int) -> bool:
        """
        Delete a member (soft delete by setting status to 'deleted')
        
        Args:
            db: Database session
            member_id: Member ID to delete
            
        Returns:
            True if deleted, False if not found
        """
        db_member = db.query(DBMember).filter(DBMember.id == member_id).first()
        if not db_member:
            return False
        
        db_member.status = "deleted"
        db_member.updated_at = datetime.utcnow()
        db.commit()
        
        return True
    
    def search_members(self, db: Session, request) -> MemberSearchResponse:
        """
        Search for members based on query string
        
        Args:
            db: Database session
            request: Search request parameters (MemberSearchRequest) or string query
            
        Returns:
            MemberSearchResponse with matching members
        """
        # Handle both string queries and MemberSearchRequest objects
        if isinstance(request, str):
            query = request.lower().strip()
            offset = 0
            limit = 100  # Default limit for string queries
        else:
            query = request.query.lower().strip()
            offset = request.offset
            limit = request.limit
        
        # Build search query
        search_query = db.query(DBMember).filter(DBMember.status != "deleted")
        
        if query:
            if query.isdigit():
                # Search by ID if query is numeric
                search_query = search_query.filter(DBMember.id == int(query))
            else:
                # Search in name, email, and phone
                search_query = search_query.filter(
                    or_(
                        DBMember.name.ilike(f"%{query}%"),
                        DBMember.email.ilike(f"%{query}%"),
                        DBMember.phone.ilike(f"%{query}%") if query else False
                    )
                )
        
        # Get total count
        total = search_query.count()
        
        # Apply pagination
        members_query = search_query.offset(offset).limit(limit)
        db_members = members_query.all()
        
        # Convert to Pydantic models
        members = [self._db_member_to_pydantic(db_member) for db_member in db_members]
        
        return MemberSearchResponse(
            members=members,
            total=total,
            limit=limit,
            offset=offset
        )
    
    def get_member_by_id(self, db: Session, member_id: int) -> Optional[Member]:
        """
        Get a member by their ID
        
        Args:
            db: Database session
            member_id: The member's ID
            
        Returns:
            Member object if found, None otherwise
        """
        db_member = db.query(DBMember).filter(
            DBMember.id == member_id,
            DBMember.status != "deleted"
        ).first()
        
        if db_member:
            return self._db_member_to_pydantic(db_member)
        return None
    
    def get_member_by_email(self, db: Session, email: str) -> Optional[Member]:
        """
        Get a member by their email
        
        Args:
            db: Database session
            email: The member's email
            
        Returns:
            Member object if found, None otherwise
        """
        db_member = db.query(DBMember).filter(
            DBMember.email == email,
            DBMember.status != "deleted"
        ).first()
        
        if db_member:
            return self._db_member_to_pydantic(db_member)
        return None
    
    def is_member_active(self, db: Session, member_id: int) -> bool:
        """
        Check if a member is active
        
        Args:
            db: Database session
            member_id: The member's ID
            
        Returns:
            True if member exists and is active, False otherwise
        """
        db_member = db.query(DBMember).filter(DBMember.id == member_id).first()
        return db_member is not None and db_member.status == "active"
    
    def get_all_members(self, db: Session, skip: int = 0, limit: int = 100) -> List[Member]:
        """
        Get all members with pagination
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of Member objects
        """
        db_members = db.query(DBMember).filter(
            DBMember.status != "deleted"
        ).offset(skip).limit(limit).all()
        
        return [self._db_member_to_pydantic(db_member) for db_member in db_members]
    
    def _db_member_to_pydantic(self, db_member: DBMember) -> Member:
        """Convert database member to Pydantic model"""
        return Member(
            id=db_member.id,
            name=db_member.name,
            email=db_member.email,
            phone=db_member.phone,
            membership_type=db_member.membership_type,
            status=db_member.status,
            created_at=db_member.created_at,
            updated_at=db_member.updated_at
        )


# Global member service instance
member_service = MemberService()