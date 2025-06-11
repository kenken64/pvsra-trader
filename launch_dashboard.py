#!/usr/bin/env python3
"""
Quick launcher for the Trading Analytics Web Dashboard
"""

import subprocess
import sys
import webbrowser
import time
import threading

def open_browser():
    """Open browser after a short delay"""
    time.sleep(2)  # Wait for server to start
    webbrowser.open('http://localhost:5000')

def main():
    print("🚀 Starting Trading Analytics Web Dashboard...")
    print("📊 Dashboard will open automatically at: http://localhost:5000")
    print("💡 Press Ctrl+C to stop the server")
    print("=" * 60)
    
    # Start browser in background
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    try:
        # Start Flask app
        subprocess.run([sys.executable, 'web_analytics.py'])
    except KeyboardInterrupt:
        print("\n🛑 Dashboard stopped by user")
    except Exception as e:
        print(f"❌ Error starting dashboard: {e}")

if __name__ == '__main__':
    main()
