#!/usr/bin/env python3
"""
Install script for PVSRA Dashboard dependencies
"""

import subprocess
import sys
import os

def install_package(package):
    """Install a package using pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ Successfully installed {package}")
        return True
    except subprocess.CalledProcessError:
        print(f"❌ Failed to install {package}")
        return False

def main():
    print("🚀 Installing PVSRA Dashboard Dependencies")
    print("=" * 50)
    
    # Required packages for PVSRA functionality
    packages = [
        "python-binance",
        "plotly", 
        "pandas",
        "flask",
        "python-dotenv",
        "pymongo",
        "requests",
        "streamlit"  # In case user wants to run original pvsra_dashboard.py
    ]
    
    success_count = 0
    
    for package in packages:
        print(f"\n📦 Installing {package}...")
        if install_package(package):
            success_count += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Installation Summary:")
    print(f"   Successful: {success_count}/{len(packages)} packages")
    
    if success_count == len(packages):
        print("✅ All dependencies installed successfully!")
        print("\n🎯 Next Steps:")
        print("1. Set up your .env file with Binance API credentials")
        print("2. Run: python web_analytics.py")
        print("3. Open: http://localhost:5000")
        print("4. Navigate to the PVSRA Analysis tab")
    else:
        print("⚠️ Some packages failed to install")
        print("Try installing them manually:")
        for package in packages:
            print(f"   pip install {package}")

if __name__ == "__main__":
    main()
