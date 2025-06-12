#!/bin/bash
# Simple Linux equivalent of start_merged_dashboard.bat

echo "🚀 Starting Merged PVSRA + Analytics Dashboard"
echo "============================================"
echo ""
echo "📊 Dashboard URL: http://localhost:5000"
echo "💡 Press Ctrl+C to stop the server"
echo ""

# Change to script directory
cd "$(dirname "$0")"

# Check if Python 3 is available
if command -v python3 &> /dev/null; then
    python3 web_analytics.py
elif command -v python &> /dev/null; then
    python web_analytics.py
else
    echo "❌ Python not found. Please install Python 3.7+"
    exit 1
fi
