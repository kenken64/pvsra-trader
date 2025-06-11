#!/bin/bash

# Trading Analytics Web Dashboard Launcher for Linux/macOS
# Make executable with: chmod +x start_web_analytics.sh

echo "🚀 Starting Trading Analytics Web Dashboard..."
echo "📊 Dashboard URL: http://localhost:5000"
echo "💡 Press Ctrl+C to stop the server"
echo "============================================================"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo "❌ Error: Python is not installed or not in PATH"
        echo "Please install Python 3.7+ and try again"
        exit 1
    else
        PYTHON_CMD="python"
    fi
else
    PYTHON_CMD="python3"
fi

# Check if web_analytics.py exists
if [ ! -f "web_analytics.py" ]; then
    echo "❌ Error: web_analytics.py not found in current directory"
    echo "Please run this script from the binance-scalping-bot directory"
    exit 1
fi

# Check if required packages are installed
echo "🔍 Checking dependencies..."
$PYTHON_CMD -c "import flask, pymongo, pandas" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  Warning: Some dependencies might be missing"
    echo "Installing required packages..."
    pip3 install flask pymongo pandas python-dotenv
fi

echo "✅ Starting web server..."
echo ""

# Start the web analytics dashboard
$PYTHON_CMD web_analytics.py

# Keep terminal open on exit (equivalent to pause in Windows)
echo ""
echo "Dashboard stopped. Press any key to exit..."
read -n 1 -s
