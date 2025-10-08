#!/bin/bash

# Setup script for Python virtual environment
# This script helps set up the Python environment for the web novel evaluation project

echo "🐍 Setting up Python virtual environment for web novel evaluation..."

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3 first."
    echo "   On Ubuntu/Debian: sudo apt install python3 python3-pip python3-venv"
    echo "   On macOS: brew install python3"
    echo "   On Windows: Download from https://python.org"
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"


cd $(dirname $0)/py-eval-tool
if [ $? -ne 0 ]; then
    echo "❌ Failed to change directory to py-eval-tool directory"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    if [ $? -eq 0 ]; then
        echo "✅ Virtual environment created successfully"
    else
        echo "❌ Failed to create virtual environment"
        exit 1
    fi
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
# echo "⬆️  Upgrading pip..."
# pip install --upgrade pip

# Install dependencies from requirements.txt
if [ -f "requirements.txt" ]; then
    echo "📚 Installing dependencies from requirements.txt..."
    pip install -r requirements.txt
    if [ $? -eq 0 ]; then
        echo "✅ Dependencies installed successfully"
    else
        echo "❌ Failed to install some dependencies"
        echo "   You may need to install system dependencies first:"
        echo "   On Ubuntu/Debian: sudo apt install python3-dev libxml2-dev libxslt-dev"
        exit 1
    fi
else
    echo "⚠️  No requirements.txt found, skipping dependency installation"
fi

echo ""
echo "🎉 Setup complete!"
echo ""