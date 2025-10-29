# Simple script to install Python 3.11 and set up environment
#!/bin/bash

echo "🐍 Setting up Python 3.11 for Gym NFC..."

cd /root/gym-nfc

# Check if Python 3.11 is available
if ! command -v python3.11 &> /dev/null; then
    echo "📦 Installing Python 3.11..."
    sudo apt update
    sudo apt install -y software-properties-common
    sudo add-apt-repository -y ppa:deadsnakes/ppa
    sudo apt update
    sudo apt install -y python3.11 python3.11-venv python3.11-dev
fi

echo "🗑️  Removing old virtual environment..."
rm -rf gym-nfc-env

echo "🔨 Creating new virtual environment with Python 3.11..."
python3.11 -m venv gym-nfc-env
source gym-nfc-env/bin/activate

echo "📦 Installing dependencies..."
pip install --upgrade pip setuptools wheel
pip install -r requirements-ubuntu.txt

echo ""
echo "✅ Setup complete!"
echo ""
echo "🚀 To start the application:"
echo "   cd /root/gym-nfc"
echo "   source gym-nfc-env/bin/activate"
echo "   python main.py"