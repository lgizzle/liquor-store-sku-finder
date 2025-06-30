import os
from pathlib import Path

def setup_directories():
    """Create necessary directories for the application"""
    directories = ['images', 'templates']
    
    for dir_name in directories:
        Path(dir_name).mkdir(exist_ok=True)
        print(f"Ensured directory exists: {dir_name}")

if __name__ == "__main__":
    setup_directories()
