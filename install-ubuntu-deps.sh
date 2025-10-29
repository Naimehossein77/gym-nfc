#!/bin/bash
# Install dependencies for Gym NFC on Ubuntu Server

echo "🔧 Installing system dependencies for Gym NFC..."

# Update package list
sudo apt update

# Install Python development headers and build tools
echo "📦 Installing Python development packages..."
sudo apt install -y \
    python3-dev \
    python3-pip \
    python3-venv \
    build-essential \
    libssl-dev \
    libffi-dev \
    pkg-config

# Install Rust (required for Pydantic 2.x)
echo "🦀 Installing Rust..."
if ! command -v rustc &> /dev/null; then
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
    source "$HOME/.cargo/env"
    echo "✅ Rust installed"
else
    echo "✅ Rust already installed"
fi

echo ""
echo "✅ All system dependencies installed!"
echo ""
echo "📝 Next steps:"
echo "1. Load Rust environment: source \$HOME/.cargo/env"
echo "2. Activate virtual environment: source gym-nfc-env/bin/activate"
echo "3. Upgrade pip: pip install --upgrade pip setuptools wheel"
echo "4. Install Python packages: pip install -r requirements.txt"