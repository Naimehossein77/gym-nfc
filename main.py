from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
import socket
import uvicorn

# Load environment variables
try:
    load_dotenv()
except ImportError:
    print("python-dotenv not installed, using environment variables directly")

from app.core.config import settings
from app.api import auth, members, tokens, nfc
from app.database import create_tables, init_sample_data
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Initialize database
print("🗄️ Initializing database...")
create_tables()
init_sample_data()
print("✅ Database initialized successfully")

# Create FastAPI application
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
    All endpoints require JWT authentication. Use the `/api/auth/login` endpoint to get an access token.
    
    **Default Credentials:**
    - Admin: username=`admin`, password=`admin123`
    - Staff: username=`frontdesk`, password=`frontdesk123`
    
    ### NFC Reader Setup:
    This system is designed to work with the ACS ACR122U NFC reader.
    Ensure the reader is connected via USB and has the appropriate drivers installed.
    """,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth.router)
app.include_router(members.router)
app.include_router(tokens.router)
app.include_router(nfc.router)


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Gym NFC Management System API",
        "version": settings.app_version,
        "docs": "/docs",
        "status": "operational"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": settings.app_version,
        "timestamp": "2024-01-01T00:00:00Z"  # This would be dynamic in production
    }


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors"""
    logging.error(f"Unhandled exception: {exc}")
    return HTTPException(
        status_code=500,
        detail="Internal server error occurred"
    )


if __name__ == "__main__":


    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    print(f"🚀 Server running at http://{local_ip}:9000")
    print(f"📚 API documentation available at http://{local_ip}:9000/docs")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=9000,
        reload=settings.debug,
        log_level="info"
    )