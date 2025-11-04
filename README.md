# 🏋️ Gym NFC Management System

A secure command-line tool and backend API for gym software that allows front desk staff to assign NFC access cards to members by writing unique tokens to physical cards using the ACS ACR122U NFC reader.

## 🚀 Features

- **Member Search API**: Search for gym members by name, email, phone, or ID
- **Token Generation**: Generate secure, unique tokens for NFC cards
- **NFC Card Writing**: Write tokens to physical NFC cards using ACS ACR122U reader
- **Apple Wallet Integration**: Generate .pkpass files for iOS Wallet app NFC access
- **JWT Authentication**: Secure all endpoints with JWT-based authentication
- **Cross-Platform Support**: Works on Windows, macOS, and Linux
- **Synchronous NFC Operations**: Handles blocking NFC communication properly
- **Comprehensive API Documentation**: Auto-generated OpenAPI docs

## 📋 Requirements

### Hardware
- **ACS ACR122U NFC Reader** (connected via USB)
- Compatible NFC cards (NTAG213, NTAG215, NTAG216, or MIFARE Classic)

### Software
- **Python 3.8+**
- **USB Drivers**: 
  - On Windows: May require libusb drivers instead of default ACS drivers
  - On macOS/Linux: Usually works with default drivers

## 🛠️ Installation

### Automated Setup

#### On macOS/Linux:
```bash
chmod +x setup.sh
./setup.sh
```

#### On Windows:
```cmd
setup.bat
```

### Manual Setup

1. **Clone/Download the project**
```bash
git clone <repository-url>
cd gym-nfc
```

2. **Create virtual environment**
```bash
python3 -m venv gym-nfc-env
source gym-nfc-env/bin/activate  # On Windows: gym-nfc-env\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment**
```bash
cp .env.example .env  # Edit .env with your settings
```

## ⚙️ Configuration

Edit the `.env` file to configure your system:

```env
# JWT Security (CHANGE IN PRODUCTION!)
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Application Settings
APP_NAME=Gym NFC Management System
APP_VERSION=1.0.0
DEBUG=true

# NFC Reader Settings
NFC_READER_TIMEOUT=30
NFC_WRITE_TIMEOUT=10
```

⚠️ **Security Note**: Always change the default JWT secret key and passwords in production!

## 🏃‍♂️ Running the Application

1. **Activate virtual environment**
```bash
source gym-nfc-env/bin/activate  # On Windows: gym-nfc-env\Scripts\activate
```

2. **Connect NFC Reader**
   - Connect your ACS ACR122U reader via USB
   - Ensure drivers are properly installed

3. **Start the server**
```bash
python main.py
```

4. **Access API Documentation**
   - Open your browser to `http://localhost:8000/docs`
   - Interactive API documentation with Swagger UI

## 🔐 Authentication

The system uses JWT (JSON Web Token) authentication to secure all endpoints.

### Default Credentials
- **Admin**: `username: admin`, `password: admin123`
- **Staff**: `username: frontdesk`, `password: frontdesk123`

### Getting Access Token

1. **POST** `/api/auth/login`
```json
{
  "username": "admin",
  "password": "admin123"
}
```

2. **Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

3. **Use token in subsequent requests**:
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## 📡 API Endpoints

### Authentication
- `POST /api/auth/login` - Login and get JWT token

### Members
- `POST /api/members/search` - Search members by query
- `GET /api/members/{member_id}` - Get specific member
- `GET /api/members/{member_id}/status` - Check member status

### Tokens
- `POST /api/tokens/generate` - Generate NFC token for member
- `GET /api/tokens/{token}/validate` - Validate token
- `GET /api/tokens/member/{member_id}` - Get all tokens for member
- `DELETE /api/tokens/{token}/revoke` - Revoke token

### NFC Operations
- `POST /api/nfc/write` - Write token to NFC card (blocking operation)
- `GET /api/nfc/read` - Read data from NFC card
- `GET /api/nfc/status` - Check NFC reader status

### Apple Wallet
- `POST /api/pass/sign` - Generate signed .pkpass file for iOS Wallet
- `GET /api/pass/certificates/status` - Check certificate status

## 🎯 Usage Workflow

### 1. Search for Member
```bash
curl -X POST "http://localhost:8000/api/members/search" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "John Doe", "limit": 10}'
```

### 2. Generate Token
```bash
curl -X POST "http://localhost:8000/api/tokens/generate" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"member_id": 1, "expires_in_days": 365}'
```

### 3. Write Token to NFC Card
```bash
curl -X POST "http://localhost:8000/api/nfc/write" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"token": "GENERATED_TOKEN_HERE", "member_id": 1}'
```

**Important**: The NFC write operation is **synchronous and blocking**. The API will wait up to 30 seconds for an NFC card to be placed on the reader.

## 🔧 NFC Reader Setup

### Windows Setup
1. **Install libusb drivers** (recommended for nfcpy):
   - Download Zadig from https://zadig.akeo.ie/
   - Connect your ACR122U reader
   - Run Zadig as administrator
   - Select your ACR122U device
   - Choose "libusb-win32" driver
   - Click "Replace Driver"

2. **Alternative**: Use default ACS drivers (may require additional configuration)

### macOS Setup
1. Install via Homebrew (if using):
```bash
brew install libusb
```

2. The reader should work with default drivers

### Linux Setup
1. Install libusb development libraries:
```bash
# Ubuntu/Debian
sudo apt-get install libusb-1.0-0-dev

# CentOS/RHEL
sudo yum install libusb1-devel
```

2. Add user to appropriate groups:
```bash
sudo usermod -a -G dialout $USER
```

## 🐛 Troubleshooting

### NFC Reader Issues

**Problem**: "NFC reader not found" or connection errors
**Solutions**:
1. Check USB connection
2. Verify drivers are installed correctly
3. Try different USB port
4. Check device permissions (Linux)
5. Restart the application

**Problem**: "Permission denied" errors (Linux)
**Solution**:
```bash
sudo usermod -a -G dialout $USER
# Log out and log back in
```

**Problem**: Reader detection issues (Windows)
**Solution**:
1. Install libusb drivers using Zadig
2. Or install official ACS drivers from ACS website

### Token Writing Issues

**Problem**: "No card detected within timeout"
**Solutions**:
1. Ensure card is placed properly on reader
2. Use compatible NFC cards (NTAG213/215/216, MIFARE Classic)
3. Increase timeout in `.env` file
4. Try different cards

**Problem**: "Card does not support NDEF"
**Solutions**:
1. Use NDEF-compatible cards (NTAG series recommended)
2. The system will attempt to format compatible cards automatically

### API Issues

**Problem**: 401 Unauthorized errors
**Solution**:
1. Ensure you're using valid JWT token
2. Check token expiration
3. Use correct Authorization header format

**Problem**: 403 Forbidden errors
**Solution**:
1. Check user role permissions
2. Admin endpoints require admin role
3. Staff endpoints accept both admin and staff roles

## 🏗️ Project Structure

```
gym-nfc/
├── app/
│   ├── api/           # API endpoint definitions
│   │   ├── auth.py    # Authentication endpoints
│   │   ├── members.py # Member management endpoints
│   │   ├── tokens.py  # Token management endpoints
│   │   └── nfc.py     # NFC operations endpoints
│   ├── core/          # Core functionality
│   │   ├── config.py  # Application configuration
│   │   ├── security.py# Security utilities (JWT, hashing)
│   │   └── dependencies.py # FastAPI dependencies
│   ├── models/        # Pydantic models
│   │   └── __init__.py# Data models and schemas
│   └── services/      # Business logic services
│       ├── member_service.py  # Member operations
│       ├── token_service.py   # Token operations
│       └── nfc_service.py     # NFC hardware interface
├── main.py           # FastAPI application entry point
├── requirements.txt  # Python dependencies
├── .env             # Environment configuration
├── setup.sh         # Linux/macOS setup script
├── setup.bat        # Windows setup script
└── README.md        # This file
```

## 🔒 Security Considerations

### Production Deployment

1. **Change Default Credentials**: Update default usernames and passwords
2. **Secure JWT Secret**: Use a strong, randomly generated JWT secret key
3. **HTTPS**: Deploy behind HTTPS in production
4. **CORS**: Configure CORS properly for your frontend domain
5. **Database**: Replace mock data with proper database
6. **Logging**: Implement proper logging and monitoring
7. **Rate Limiting**: Add rate limiting for API endpoints

### Token Security

- Tokens are generated using cryptographically secure random functions
- Tokens can have expiration dates
- Tokens can be revoked individually
- All token operations require authentication

## 🚀 Deployment

### Development
```bash
python main.py
```

### Production (using Gunicorn)
```bash
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UnicornWorker --bind 0.0.0.0:8000
```

### Docker (Optional)
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 📚 API Documentation

Once the server is running, comprehensive API documentation is available at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📞 Support

For support and questions:
1. Check the troubleshooting section above
2. Review the API documentation at `/docs`
3. For Apple Wallet integration, see `WALLET_API.md`
4. Check the logs for error details
5. Ensure NFC reader is properly connected and configured

## 🔄 Version History

- **v1.0.0**: Initial release with core NFC functionality
  - Member search API
  - Token generation and management
  - NFC card writing with ACS ACR122U
  - JWT authentication
  - Cross-platform support