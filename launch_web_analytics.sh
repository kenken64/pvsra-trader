#!/bin/bash

# Advanced Trading Analytics Web Dashboard Launcher
# Features: Auto-browser opening, dependency checking, error handling
# Usage: ./launch_web_analytics.sh [options]
# Options:
#   --no-browser    Don't automatically open browser
#   --port PORT     Use custom port (default: 5000)
#   --help          Show this help message

set -e  # Exit on any error

# Default values
PORT=5000
OPEN_BROWSER=true
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show help
show_help() {
    echo "Trading Analytics Web Dashboard Launcher"
    echo ""
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  --no-browser    Don't automatically open browser"
    echo "  --port PORT     Use custom port (default: 5000)"
    echo "  --help          Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                          # Start with default settings"
    echo "  $0 --port 8080             # Start on port 8080"
    echo "  $0 --no-browser             # Start without opening browser"
    echo "  $0 --port 3000 --no-browser # Custom port, no browser"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --no-browser)
            OPEN_BROWSER=false
            shift
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Header
echo "=================================================================="
echo "🚀 Trading Analytics Web Dashboard Launcher"
echo "=================================================================="
print_status "Dashboard URL: http://localhost:$PORT"
print_status "Press Ctrl+C to stop the server"
echo "=================================================================="

# Change to script directory
cd "$SCRIPT_DIR"

# Check if Python is available
print_status "Checking Python installation..."
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
    PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
else
    print_error "Python is not installed or not in PATH"
    print_error "Please install Python 3.7+ and try again"
    exit 1
fi

print_success "Found Python $PYTHON_VERSION"

# Check if web_analytics.py exists
if [ ! -f "web_analytics.py" ]; then
    print_error "web_analytics.py not found in current directory"
    print_error "Please run this script from the binance-scalping-bot directory"
    exit 1
fi

# Check if required packages are installed
print_status "Checking dependencies..."
MISSING_PACKAGES=()

check_package() {
    $PYTHON_CMD -c "import $1" 2>/dev/null || MISSING_PACKAGES+=("$2")
}

check_package "flask" "flask"
check_package "pymongo" "pymongo"
check_package "pandas" "pandas"
check_package "dotenv" "python-dotenv"

if [ ${#MISSING_PACKAGES[@]} -gt 0 ]; then
    print_warning "Missing packages: ${MISSING_PACKAGES[*]}"
    print_status "Installing missing packages..."
    
    if command -v pip3 &> /dev/null; then
        pip3 install "${MISSING_PACKAGES[@]}"
    elif command -v pip &> /dev/null; then
        pip install "${MISSING_PACKAGES[@]}"
    else
        print_error "pip is not available. Please install the missing packages manually:"
        print_error "pip install ${MISSING_PACKAGES[*]}"
        exit 1
    fi
    
    print_success "Dependencies installed successfully"
else
    print_success "All dependencies are available"
fi

# Check if port is available
print_status "Checking if port $PORT is available..."
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    print_warning "Port $PORT is already in use"
    print_status "Finding alternative port..."
    for alt_port in {5001..5010}; do
        if ! lsof -Pi :$alt_port -sTCP:LISTEN -t >/dev/null 2>&1; then
            PORT=$alt_port
            print_success "Using alternative port: $PORT"
            break
        fi
    done
    
    if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        print_error "No available ports found in range 5000-5010"
        exit 1
    fi
fi

# Function to open browser
open_browser() {
    sleep 3  # Wait for server to start
    local url="http://localhost:$PORT"
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        open "$url"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        if command -v xdg-open &> /dev/null; then
            xdg-open "$url"
        elif command -v gnome-open &> /dev/null; then
            gnome-open "$url"
        elif command -v firefox &> /dev/null; then
            firefox "$url"
        elif command -v chromium-browser &> /dev/null; then
            chromium-browser "$url"
        else
            print_warning "Could not find a suitable browser to open $url"
        fi
    else
        print_warning "Unsupported OS type: $OSTYPE"
    fi
}

# Set environment variable for custom port
export FLASK_PORT=$PORT

# Start browser in background if requested
if [ "$OPEN_BROWSER" = true ]; then
    print_status "Browser will open automatically in 3 seconds..."
    open_browser &
fi

# Trap SIGINT (Ctrl+C) for graceful shutdown
trap 'echo -e "\n\n🛑 Dashboard stopped by user"; exit 0' SIGINT

print_success "Starting web server on port $PORT..."
echo ""

# Modify web_analytics.py to use custom port if needed
if [ $PORT -ne 5000 ]; then
    # Create temporary version with custom port
    sed "s/port=5000/port=$PORT/g" web_analytics.py > /tmp/web_analytics_custom.py
    $PYTHON_CMD /tmp/web_analytics_custom.py
    rm -f /tmp/web_analytics_custom.py
else
    # Use original file
    $PYTHON_CMD web_analytics.py
fi

echo ""
print_status "Dashboard stopped. Press any key to exit..."
read -n 1 -s
