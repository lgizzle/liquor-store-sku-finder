#!/bin/bash

# Development Setup Script for Cheers Liquor Mart SKU Finder
# This script sets up a virtual environment and installs dependencies

set -e  # Exit on any error

echo "🍺 Setting up Cheers Liquor Mart SKU Finder Development Environment..."

# Check if we're in the right directory
if [ ! -f "web_app_with_auth.py" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "📦 Virtual environment already exists"
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️ Warning: .env file not found. Please create one with your API keys."
    echo "📝 Example .env file:"
    echo "GO_UPC_API_KEY=your_api_key_here"
    echo "GMAIL_USERNAME=your_email@gmail.com"
    echo "GMAIL_APP_PASSWORD=your_app_password"
    echo "FLASK_ENV=development"
else
    echo "✅ .env file found"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "To start the development server:"
echo "1. Activate the virtual environment: source venv/bin/activate"
echo "2. Run the app: python3 web_app_with_auth.py"
echo ""
echo "Or use the start script: ./start_dev.sh"
