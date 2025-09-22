from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

# Database URL - using SQLite for local development
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./gym_nfc.db")

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


class Member(Base):
    """Database model for gym members"""
    __tablename__ = "members"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    phone = Column(String(20), nullable=True)
    membership_type = Column(String(50), default="Basic")
    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class NFCCard(Base):
    """Database model for NFC cards"""
    __tablename__ = "nfc_cards"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    card_id = Column(String(50), unique=True, nullable=False, index=True)
    token = Column(String(100), nullable=False, index=True)
    member_id = Column(Integer, nullable=False, index=True)
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Token(Base):
    """Database model for tokens"""
    __tablename__ = "tokens"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    token = Column(String(100), unique=True, nullable=False, index=True)
    member_id = Column(Integer, nullable=False, index=True)
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_sample_data():
    """Initialize database with sample data"""
    db = SessionLocal()
    try:
        # Check if we already have data
        existing_members = db.query(Member).count()
        if existing_members > 0:
            return
        
        # Create sample members
        sample_members = [
            Member(
                name="John Doe",
                email="john.doe@email.com",
                phone="555-1234",
                membership_type="Premium",
                status="active"
            ),
            Member(
                name="Jane Smith",
                email="jane.smith@email.com",
                phone="555-5678",
                membership_type="Basic",
                status="active"
            ),
            Member(
                name="Bob Johnson",
                email="bob.johnson@email.com",
                phone="555-9012",
                membership_type="Premium",
                status="active"
            ),
            Member(
                name="Alice Brown",
                email="alice.brown@email.com",
                phone="555-3456",
                membership_type="Student",
                status="active"
            ),
            Member(
                name="Charlie Wilson",
                email="charlie.wilson@email.com",
                phone="555-7890",
                membership_type="Basic",
                status="suspended"
            )
        ]
        
        for member in sample_members:
            db.add(member)
        
        db.commit()
        print("✅ Sample data initialized successfully")
        
    except Exception as e:
        print(f"❌ Error initializing sample data: {e}")
        db.rollback()
    finally:
        db.close()