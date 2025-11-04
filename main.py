# app/main.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
from dotenv import load_dotenv
import socket
import uvicorn
import logging
from datetime import datetime, timezone

# Load environment variables
try:
    load_dotenv()
except ImportError:
    print("python-dotenv not installed, using environment variables directly")

from app.core.config import settings
from app.api import auth, members, tokens, nfc, wallet
from app.api import members_admin_list_tokens


from app.database import create_tables, init_sample_data, ensure_admin_user

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Initialize database (you can move these into startup event if you prefer)
print("🗄️ Initializing database...")
create_tables()
init_sample_data()
ensure_admin_user()
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

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router)
app.include_router(members.router)
app.include_router(tokens.router)
app.include_router(nfc.router)
app.include_router(wallet.router)
app.include_router(members_admin_list_tokens.router)

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
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

# Global exception handler -> JSON response
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logging.exception("Unhandled exception", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error occurred"}
    )

if __name__ == "__main__":
    # Find and display available network interfaces
    def get_available_hosts():
        hostname = socket.gethostname()
        available_hosts = ['127.0.0.1', '0.0.0.0']
        
        try:
            # Get local IP address
            local_ip = socket.gethostbyname(hostname)
            if local_ip not in available_hosts:
                available_hosts.append(local_ip)
        except:
            pass
        
        try:
            # Alternative method to get local IP
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                local_ip = s.getsockname()[0]
                if local_ip not in available_hosts:
                    available_hosts.append(local_ip)
        except:
            pass
            
        return available_hosts, hostname
    
    hosts, hostname = get_available_hosts()
    print(f"🔍 Available hosts: {hosts}")
    print(f"🏠 Hostname: {hostname}")
    
    port = 8001
    
    print(f"🚀 Server running at:")
    for host in hosts:
        if host != '0.0.0.0':
            print(f"   http://{host}:{port}")
    print(f"📚 API documentation available at http://{hosts[-1]}:{port}/docs")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=settings.debug,
        log_level="info",
    )
