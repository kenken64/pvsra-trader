@echo off
echo 🚀 Starting Merged PVSRA + Analytics Dashboard
echo ============================================
echo.
echo 📊 Dashboard URL: http://localhost:5000
echo 💡 Press Ctrl+C to stop the server
echo.

cd /d "%~dp0"
python web_analytics.py

pause
