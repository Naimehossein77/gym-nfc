@echo off
REM Gym NFC Management System Setup Script for Windows

echo 🏋️ Setting up Gym NFC Management System...

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python 3.8+ is required. Please install Python first.
    exit /b 1
)

REM Create virtual environment
echo 📦 Creating virtual environment...
python -m venv gym-nfc-env

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call gym-nfc-env\Scripts\activate.bat

REM Upgrade pip
echo ⬆️ Upgrading pip...
pip install --upgrade pip

REM Install dependencies
echo 📥 Installing dependencies...
pip install -r requirements.txt

REM Check environment file
if not exist .env (
    echo ⚙️ Environment file created. Please review and update .env with your settings.
) else (
    echo ⚙️ Environment file already exists.
)

echo ✅ Setup complete!
echo.
echo 📖 Next steps:
echo 1. Activate the virtual environment: gym-nfc-env\Scripts\activate.bat
echo 2. Review and update the .env file with your settings
echo 3. Connect your ACS ACR122U NFC reader via USB
echo 4. Install libusb drivers for the NFC reader if needed
echo 5. Run the application: python main.py
echo 6. Access the API docs at: http://localhost:8000/docs
echo.
echo 🔐 Default login credentials:
echo    Admin - username: admin, password: admin123
echo    Staff - username: frontdesk, password: frontdesk123
echo.
echo ⚠️ Remember to change default passwords in production!

pause