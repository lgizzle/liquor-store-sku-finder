#!/usr/bin/env python3
"""
Production-ready Cheers SKU Finder Application
Includes all performance and security improvements
"""

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv not installed, skip .env loading
    pass

from web_app_with_auth import app
from utils import logger
import os
import sys

def create_required_directories():
    """Ensure required directories exist"""
    directories = ['logs', 'images', 'static/images']
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            logger.info(f"Created directory: {directory}")

def validate_environment():
    """Validate required environment variables"""
    required_vars = ['GO_UPC_API_KEY']
    optional_vars = ['GMAIL_USERNAME', 'GMAIL_APP_PASSWORD', 'BASE_URL']
    
    missing = []
    for var in required_vars:
        if not os.environ.get(var):
            missing.append(var)
    
    if missing:
        logger.error(f"Missing required environment variables: {missing}")
        print(f"❌ Missing required environment variables: {missing}")
        print("Please set these before starting the application.")
        return False
    
    # Check optional vars and warn
    missing_optional = [var for var in optional_vars if not os.environ.get(var)]
    if missing_optional:
        logger.warning(f"Optional environment variables not set: {missing_optional}")
        print(f"⚠️ Optional environment variables not set: {missing_optional}")
        print("Some features (like password reset) may not work.")
    
    return True

if __name__ == "__main__":
    # Validate environment
    if not validate_environment():
        sys.exit(1)
    
    # Create directories
    create_required_directories()
    
    # Get configuration
    port = int(os.environ.get("PORT", 5001))
    debug = os.environ.get("FLASK_ENV") == "development"
    
    logger.info(f"Starting Cheers SKU Finder on port {port}")
    
    if debug:
        logger.info("Running in development mode")
        app.run(debug=True, host="0.0.0.0", port=port)
    else:
        logger.info("Running in production mode")
        # For production, use a proper WSGI server like Gunicorn
        app.run(debug=False, host="0.0.0.0", port=port)
