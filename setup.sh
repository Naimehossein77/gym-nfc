#!/bin/bash

# Gym NFC Management System Setup Script

echo "🏋️ Setting up Gym NFC Management System..."

# Check if Python 3.8+ is installed
python3 --version
if [ $? -ne 0 ]; then
    echo "❌ Python 3.8+ is required. Please install Python first."
    exit 1
fi

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv gym-nfc-env

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source gym-nfc-env/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Copy environment file
if [ ! -f .env ]; then
    echo "⚙️ Environment file created. Please review and update .env with your settings."
else
    echo "⚙️ Environment file already exists."
fi

echo "✅ Setup complete!"
echo ""
echo "📖 Next steps:"
echo "1. Activate the virtual environment: source gym-nfc-env/bin/activate"
echo "2. Review and update the .env file with your settings"
echo "3. Connect your ACS ACR122U NFC reader via USB"
echo "4. Run the application: python main.py"
echo "5. Access the API docs at: http://localhost:8000/docs"
echo ""
echo "🔐 Default login credentials:"
echo "   Admin - username: admin, password: admin123"
echo "   Staff - username: frontdesk, password: frontdesk123"
echo ""
echo "⚠️ Remember to change default passwords in production!"