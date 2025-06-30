#!/usr/bin/env python3
"""
Setup script for SKU Picture Finder
"""

import subprocess
import sys
import os
from pathlib import Path


def install_requirements():
    """Install required packages"""
    print("📦 Installing required packages...")

    requirements_files = ["requirements.txt", "web_requirements.txt"]

    for req_file in requirements_files:
        if os.path.exists(req_file):
            print(f"Installing packages from {req_file}...")
            try:
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", "-r", req_file]
                )
                print(f"✅ Successfully installed packages from {req_file}")
            except subprocess.CalledProcessError as e:
                print(f"❌ Failed to install packages from {req_file}: {e}")
        else:
            print(f"⚠️  {req_file} not found, skipping...")


def setup_directories():
    """Create necessary directories"""
    print("📁 Setting up directories...")

    directories = ["images", "logs", "exports"]

    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created directory: {directory}")


def setup_env_file():
    """Setup environment file"""
    print("⚙️  Setting up environment file...")

    if not os.path.exists(".env"):
        if os.path.exists(".env.example"):
            import shutil

            shutil.copy(".env.example", ".env")
            print("✅ Created .env file from .env.example")
            print("📝 Please edit .env file with your API keys if you have them")
        else:
            print("❌ .env.example not found")
    else:
        print("✅ .env file already exists")


def test_installation():
    """Test if the installation works"""
    print("🧪 Testing installation...")

    try:
        from sku_finder import SKUPictureFinder

        finder = SKUPictureFinder()
        print("✅ SKU Picture Finder imported successfully")

        # Test with a simple search (won't download anything)
        print("🔍 Testing basic functionality...")
        test_results = finder._search_open_food_facts("123456789012")
        print("✅ Basic functionality test passed")

    except Exception as e:
        print(f"❌ Installation test failed: {e}")
        return False

    return True


def main():
    print("🚀 SKU Picture Finder Setup")
    print("=" * 40)

    # Check Python version
    if sys.version_info < (3, 7):
        print("❌ Python 3.7+ is required")
        sys.exit(1)

    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")

    # Setup steps
    setup_directories()
    install_requirements()
    setup_env_file()

    # Test installation
    if test_installation():
        print("\n🎉 Setup completed successfully!")
        print("\nNext steps:")
        print("1. Edit .env file with your API keys (optional)")
        print("2. Run: python example_usage.py")
        print("3. Or start web interface: python web_app.py")
        print("4. Or use command line: python sku_finder.py --sku 12345")
    else:
        print("\n❌ Setup completed with errors. Please check the installation.")


if __name__ == "__main__":
    main()
