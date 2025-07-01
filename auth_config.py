# Simple Authentication Configuration

import os

class AuthConfig:
    # Email settings for password reset
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('GMAIL_USERNAME', 'your-email@gmail.com')  # SET THIS
    MAIL_PASSWORD = os.environ.get('GMAIL_APP_PASSWORD', 'your-app-password')  # SET THIS
    
    # Secret key for sessions
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
    
    # Database
    DATABASE_PATH = 'users.db'
    
    # App settings
    APP_NAME = 'Cheers SKU Finder'
    FROM_EMAIL = MAIL_USERNAME
