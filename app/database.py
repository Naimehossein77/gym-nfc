# app/database.py
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, ForeignKey, UniqueConstraint, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./gym_nfc.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# >>> Enable FK constraints for SQLite
if "sqlite" in DATABASE_URL:
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
# <<<

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)
Base = declarative_base()


class Member(Base):
    __tablename__ = "members"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    phone = Column(String(20), nullable=True)
    membership_type = Column(String(50), default="Basic", index=True)  # indexed
    status = Column(String(20), default="active", index=True)          # indexed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="member", uselist=False, passive_deletes=True)
    tokens = relationship("Token", back_populates="member", cascade="all, delete-orphan", passive_deletes=True)
    cards = relationship("NFCCard", back_populates="member", cascade="all, delete-orphan", passive_deletes=True)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=True, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, index=True)  # 'admin' | 'staff' | 'member'
    # keep member user optional; if member is deleted, set null so admin/staff unaffected
    member_id = Column(Integer, ForeignKey("members.id", ondelete="SET NULL"), nullable=True, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    __table_args__ = (UniqueConstraint('member_id', name='uq_users_member'),)

    member = relationship("Member", back_populates="user", passive_deletes=True, lazy="joined")


class NFCCard(Base):
    __tablename__ = "nfc_cards"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    card_id = Column(String(50), unique=True, nullable=False, index=True)
    token = Column(String(255), nullable=False, index=True)
    member_id = Column(Integer, ForeignKey("members.id", ondelete="CASCADE"), nullable=False, index=True)  # FIX INDENT + CASCADE
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    member = relationship("Member", back_populates="cards", passive_deletes=True)


class Token(Base):
    __tablename__ = "tokens"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    token = Column(String(255), unique=True, nullable=False, index=True)
    member_id = Column(Integer, ForeignKey("members.id", ondelete="CASCADE"), nullable=False, index=True)  # add CASCADE
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    member = relationship("Member", back_populates="tokens", passive_deletes=True)


def create_tables():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_sample_data():
    db = SessionLocal()
    try:
        if db.query(Member).count() > 0:
            return
        sample_members = [
            Member(name="John Doe",   email="john.doe@email.com",   phone="555-1234", membership_type="Premium", status="active"),
            Member(name="Jane Smith", email="jane.smith@email.com", phone="555-5678", membership_type="Basic",   status="active"),
            Member(name="Bob Johnson", email="bob.johnson@email.com", phone="555-9012", membership_type="Premium", status="active"),
            Member(name="Alice Brown", email="alice.brown@email.com", phone="555-3456", membership_type="Student", status="active"),
            Member(name="Charlie Wilson", email="charlie.wilson@email.com", phone="555-7890", membership_type="Basic", status="suspended"),
        ]
        for m in sample_members:
            db.add(m)
        db.commit()
        print("✅ Sample data initialized successfully")
    except Exception as e:
        print(f"❌ Error initializing sample data: {e}")
        db.rollback()
    finally:
        db.close()
