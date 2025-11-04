# Gym NFC Management System - AI Assistant Guide

## Project Overview
This is a **FastAPI-based gym management system** that enables front desk staff to assign NFC access cards to members using physical ACS ACR122U NFC readers. The system bridges gym software with hardware NFC operations through secure token generation and card writing.

## Key Architecture Components

### 🔧 Core Services Pattern
- **Service Layer**: Business logic in `app/services/` (member_service, token_service, nfc_service)  
- **API Layer**: REST endpoints in `app/api/` with JWT authentication
- **Hardware Abstraction**: `nfc_service.py` handles both real hardware and simulation mode
- **Database**: SQLAlchemy with SQLite, relationships: Member → User, Member → Token, Member → NFCCard

### 🎯 Critical NFC Workflow
1. Search member via `/api/members/search` (fuzzy search by name/email/phone/ID)
2. Generate secure token via `/api/tokens/generate` with optional expiration
3. **Blocking NFC write** via `/api/nfc/write` - waits up to 30s for card placement
4. Validation via `/api/nfc/validate` using encrypted payloads

### 🔐 Authentication & Security
- **JWT tokens** for API access (default: admin/admin123, frontdesk/frontdesk123)
- **Role-based access**: `require_staff` decorator allows both admin and staff roles
- **Token encryption**: Fernet encryption for NFC payloads when `FERNET_KEY` is set
- **Database relationships**: Proper FK constraints with CASCADE deletes

## Development Patterns

### 🏗️ Service Dependencies
```python
# Services depend on each other through dependency injection
from app.services.token_service import token_service
from app.services.member_service import member_service
```

### 📡 NFC Simulation Mode
- **Automatic fallback**: If nfcpy unavailable or `FORCE_NFC_SIMULATION=true`
- **Simulation responses**: Predictable card IDs like `SIM0001`, 2-3 second delays
- **Hardware vs Sim**: Check `nfc_service._check_nfc_availability()` logic

### 🗄️ Database Patterns
- **Single file**: `app/database.py` contains all models and session management
- **Initialization**: `create_tables()`, `init_sample_data()`, `ensure_admin_user()` called from main.py
- **Session handling**: `get_db()` dependency for request-scoped sessions

### 🎮 CLI Tool Integration
- **Standalone client**: `cli.py` provides interactive and command-line interfaces
- **Testing workflow**: Use `python cli.py interactive` for full workflow testing
- **Direct API calls**: Handles authentication and provides member search → token gen → NFC write flow

## Key Files for Understanding

### Core Entry Points
- **main.py**: FastAPI app setup, CORS, router registration, startup database init
- **app/core/config.py**: Environment-based settings with .env loading
- **app/database.py**: SQLAlchemy models, relationships, and initialization

### Critical Services
- **app/services/nfc_service.py**: Hardware abstraction with simulation fallback
- **app/api/nfc.py**: NFC endpoints including encrypted payload validation
- **cli.py**: Command-line client demonstrating complete workflows

## Environment Configuration

### Required .env Variables
```bash
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-in-production
FERNET_KEY=base64-encoded-32-byte-key  # For NFC payload encryption
FORCE_NFC_SIMULATION=true             # Force simulation mode
NFC_READER_TIMEOUT=30                 # Card detection timeout
```

## Hardware Dependencies
- **ACS ACR122U NFC Reader**: USB-connected, requires libusb drivers on Windows
- **Compatible Cards**: NTAG213/215/216, MIFARE Classic with NDEF support
- **Driver Issues**: Windows may need Zadig tool to install libusb drivers

## Testing & Development
- **Start server**: `python main.py` (runs on port 8001, displays all network interfaces)
- **API docs**: Auto-generated at `/docs` and `/redoc`
- **CLI testing**: `python cli.py interactive` for complete workflow simulation
- **Mock data**: 5 sample members created automatically on first run

## Common Gotchas
- **Blocking NFC operations**: `/api/nfc/write` and `/api/nfc/read` are synchronous and block for up to 30 seconds
- **Simulation vs Hardware**: Check logs for "simulation mode" vs "hardware mode" indicators  
- **Token validation**: Always verify token belongs to correct member_id before NFC operations
- **Database relationships**: Member deletion cascades to tokens and cards via `ondelete="CASCADE"`
- **CORS settings**: Currently open (`allow_origins=["*"]`) - restrict in production

## Extending the System
- **New endpoints**: Follow pattern in `app/api/` with proper authentication decorators
- **Service methods**: Add to appropriate service in `app/services/` for business logic
- **Database changes**: Modify models in `app/database.py`, handle migrations manually
- **NFC customization**: Extend `NFCService` class for different hardware or protocols