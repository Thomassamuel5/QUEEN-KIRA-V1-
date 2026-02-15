#!/usr/bin/env python3
"""
Kira V1 - Main Launcher
Checks dependencies and starts the bot
"""

import sys
import subprocess
import importlib.util
import os

# Required packages
REQUIRED_PACKAGES = [
    'telethon',
    'requests'
]

KIRA_ASCII = '''
╦  ╔═╗╦═╗╦═╗
║  ╠═╣╠╦╝╠╦╝
╩═╝╩ ╩╩╚═╩╚═ V1
Created by Thomas Samuel
Multi-File Structure with AI & Auto-Typing
'''

def check_package(package_name):
    """Check if a Python package is installed"""
    return importlib.util.find_spec(package_name) is not None

def install_packages():
    """Install missing packages"""
    print("📦 Installing required packages...")
    missing_packages = [pkg for pkg in REQUIRED_PACKAGES if not check_package(pkg)]
    
    if missing_packages:
        for package in missing_packages:
            print(f"Installing {package}...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                print(f"✅ {package} installed successfully")
            except subprocess.CalledProcessError:
                print(f"❌ Failed to install {package}")
                return False
    else:
        print("✅ All packages already installed")
    return True

def check_files():
    """Check if all required files exist"""
    required_files = ['bot.py', 'ai_module.py', 'chat_manager.py', 'utils.py']
    missing_files = []
    
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print("❌ Missing required files:")
        for file in missing_files:
            print(f"   - {file}")
        print("\nPlease ensure all files are in the same directory.")
        return False
    return True

def main():
    """Main entry point"""
    print(KIRA_ASCII)
    print("Kira V1 Multi-File Edition")
    print("=" * 50)
    
    # Check Python version
    if sys.version_info < (3, 7):
        print("❌ Python 3.7 or higher is required!")
        sys.exit(1)
    
    print(f"✅ Python version: {sys.version_info.major}.{sys.version_info.minor}")
    
    # Check and install dependencies
    if not install_packages():
        print("\n❌ Failed to install some packages. Please install manually:")
        print("pip install telethon requests")
        sys.exit(1)
    
    # Check files
    if not check_files():
        sys.exit(1)
    
    print("✅ All dependencies satisfied!")
    print("=" * 50)
    
    # Import and run bot
    try:
        from bot import run_bot
        run_bot()
    except ImportError as e:
        print(f"❌ Failed to import bot modules: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n👋 Kira V1 stopped gracefully!")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
