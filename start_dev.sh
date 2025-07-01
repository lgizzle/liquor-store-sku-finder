#!/bin/bash

# Development Start Script for Cheers Liquor Mart SKU Finder
# This script ensures the virtual environment is activated and starts the Flask app

set -e  # Exit on any error

echo "🍺 Starting Cheers Liquor Mart SKU Finder (Development Mode)..."

# Check if we're in the right directory
if [ ! -f "web_app_with_auth.py" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Running setup first..."
    ./setup_dev.sh
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Set development environment
export FLASK_ENV=development
export FLASK_DEBUG=1

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️ Warning: .env file not found. Some features may not work."
fi

echo "🚀 Starting Flask development server..."
echo "📍 Local URL: http://127.0.0.1:5001"
echo "🛑 Press Ctrl+C to stop the server"
echo ""

# Start the Flask app
python3 web_app_with_auth.py
