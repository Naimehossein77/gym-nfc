# main.py
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
from dotenv import load_dotenv
import logging
from datetime import datetime

# Load environment variables
try:
    load_dotenv()
except ImportError:
    print("python-dotenv not installed, using environment variables directly")

from app.core.config import settings
from app.api import auth, members, tokens, nfc
from app.database import create_tables, init_sample_data, SessionLocal, User
from app.core.security import get_password_hash

# ---------------------------
# Logging
# ---------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# ---------------------------
# Bootstrap default users
# ---------------------------
def bootstrap_users():
    """Create default admin/staff users from .env if missing (dev convenience)."""
    db = SessionLocal()
    try:
        def ensure_user(username: str, password: str, role: str, email: str | None = None):
            if not username or not password or not role:
                return
            u = db.query(User).filter(User.username == username).first()
            if not u:
                db.add(User(
                    username=username,
                    email=email,
                    password_hash=get_password_hash(password),
                    role=role,
                    is_active=True
                ))
                db.commit()

        ensure_user(
            os.getenv("ADMIN_USERNAME", "admin"),
            os.getenv("ADMIN_PASSWORD", "admin123"),
            "admin",
            "admin@example.com"
        )
        ensure_user(
            os.getenv("STAFF_USERNAME", "frontdesk"),
            os.getenv("STAFF_PASSWORD", "frontdesk123"),
            "staff",
            "frontdesk@example.com"
        )
    finally:
        db.close()

# ---------------------------
# DB init
# ---------------------------
print("🗄️ Initializing database...")
create_tables()
init_sample_data()
bootstrap_users()
print("✅ Database initialized successfully")

# ---------------------------
# FastAPI App
# ---------------------------
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
    ## Gym NFC Management System API

    A secure backend API for managing NFC card assignments in gym software.

    ### Features:
    - **Member Search**: Search for gym members by name, email, phone, or ID
    - **Token Generation**: Generate secure tokens for NFC cards
    - **NFC Card Writing**: Write tokens to physical NFC cards using ACS ACR122U reader
    - **JWT Authentication**: Secure all endpoints with JWT-based authentication

    ### Authentication:
    All endpoints require JWT authentication.
    Use **`/api/auth/admin/login`** (admin/staff) or **`/api/auth/member/login`** (members) to get an access token.

    **Default Credentials (dev only):**
    - Admin: username=`admin`, password=`admin123`
    - Staff: username=`frontdesk`, password=`frontdesk123`
    """,
    docs_url="/docs",
    redoc_url="/redoc"
)

# ---------------------------
# CORS
# ---------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------
# Routers
# ---------------------------
app.include_router(auth.router)
app.include_router(members.router)
app.include_router(tokens.router)
app.include_router(nfc.router)

# ---------------------------
# Health & Root
# ---------------------------
@app.get("/")
async def root():
    return {
        "message": "Gym NFC Management System API",
        "version": settings.app_version,
        "docs": "/docs",
        "status": "operational"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": settings.app_version,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

# ---------------------------
# Global exception handler
# ---------------------------
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logging.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error occurred"}
    )

# ---------------------------
# Dev server entrypoint
# ---------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info"
    )
