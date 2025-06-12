#!/bin/bash
# Linux equivalent of start_merged_dashboard.bat
# Starts the Merged PVSRA + Analytics Dashboard

# Color definitions for better output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Default settings
PORT=5000
OPEN_BROWSER=true
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Function to print colored output
print_header() {
    echo -e "${CYAN}🚀 Starting Merged PVSRA + Analytics Dashboard${NC}"
    echo -e "${BLUE}============================================${NC}"
    echo ""
    echo -e "${GREEN}📊 Dashboard URL: http://localhost:${PORT}${NC}"
    echo -e "${YELLOW}💡 Press Ctrl+C to stop the server${NC}"
    echo ""
}

# Function to check if port is available
check_port() {
    if command -v lsof &> /dev/null; then
        if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
            echo -e "${RED}❌ Port $PORT is already in use${NC}"
            echo -e "${YELLOW}💡 Try using a different port with: $0 --port <port_number>${NC}"
            return 1
        fi
    elif command -v netstat &> /dev/null; then
        if netstat -ln 2>/dev/null | grep ":$PORT " >/dev/null; then
            echo -e "${RED}❌ Port $PORT is already in use${NC}"
            echo -e "${YELLOW}💡 Try using a different port with: $0 --port <port_number>${NC}"
            return 1
        fi
    fi
    return 0
}

# Function to check Python installation
check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        # Check if it's Python 3
        PYTHON_VERSION=$(python -c 'import sys; print(sys.version_info[0])')
        if [ "$PYTHON_VERSION" -eq 3 ]; then
            PYTHON_CMD="python"
        else
            echo -e "${RED}❌ Python 3 is required but not found${NC}"
            echo -e "${YELLOW}💡 Please install Python 3.7+ and try again${NC}"
            exit 1
        fi
    else
        echo -e "${RED}❌ Python is not installed or not in PATH${NC}"
        echo -e "${YELLOW}💡 Please install Python 3.7+ and try again${NC}"
        exit 1
    fi
}

# Function to check dependencies
check_dependencies() {
    echo -e "${BLUE}🔍 Checking dependencies...${NC}"
    
    if ! $PYTHON_CMD -c "import flask, pymongo, pandas" 2>/dev/null; then
        echo -e "${YELLOW}⚠️ Missing dependencies detected${NC}"
        echo -e "${CYAN}📦 Installing required packages...${NC}"
        
        $PYTHON_CMD -m pip install flask pymongo pandas python-dotenv requests
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✅ Dependencies installed successfully${NC}"
        else
            echo -e "${RED}❌ Failed to install dependencies${NC}"
            echo -e "${YELLOW}💡 Please run: pip install flask pymongo pandas python-dotenv requests${NC}"
            exit 1
        fi
    else
        echo -e "${GREEN}✅ All dependencies are available${NC}"
    fi
}

# Function to open browser
open_browser() {
    if [ "$OPEN_BROWSER" = true ]; then
        echo -e "${CYAN}🌐 Opening browser...${NC}"
        
        # Wait a moment for the server to start
        sleep 2
        
        # Try different browser opening methods
        if command -v xdg-open &> /dev/null; then
            xdg-open "http://localhost:$PORT" 2>/dev/null &
        elif command -v gnome-open &> /dev/null; then
            gnome-open "http://localhost:$PORT" 2>/dev/null &
        elif command -v open &> /dev/null; then
            # macOS
            open "http://localhost:$PORT" 2>/dev/null &
        elif command -v firefox &> /dev/null; then
            firefox "http://localhost:$PORT" 2>/dev/null &
        elif command -v chromium-browser &> /dev/null; then
            chromium-browser "http://localhost:$PORT" 2>/dev/null &
        elif command -v google-chrome &> /dev/null; then
            google-chrome "http://localhost:$PORT" 2>/dev/null &
        else
            echo -e "${YELLOW}⚠️ Could not auto-open browser${NC}"
            echo -e "${CYAN}💡 Please manually open: http://localhost:$PORT${NC}"
        fi
    fi
}

# Function to show usage
show_usage() {
    echo -e "${WHITE}Usage: $0 [options]${NC}"
    echo ""
    echo -e "${CYAN}Options:${NC}"
    echo -e "  ${GREEN}--port PORT${NC}       Use custom port (default: 5000)"
    echo -e "  ${GREEN}--no-browser${NC}      Don't automatically open browser"
    echo -e "  ${GREEN}--help${NC}            Show this help message"
    echo ""
    echo -e "${CYAN}Examples:${NC}"
    echo -e "  ${YELLOW}$0${NC}                           # Start with default settings"
    echo -e "  ${YELLOW}$0 --port 8080${NC}              # Start on port 8080"
    echo -e "  ${YELLOW}$0 --no-browser${NC}             # Start without opening browser"
    echo -e "  ${YELLOW}$0 --port 3000 --no-browser${NC} # Custom port, no browser"
}

# Function to handle cleanup on exit
cleanup() {
    echo ""
    echo -e "${CYAN}🛑 Shutting down dashboard...${NC}"
    echo -e "${GREEN}✅ Dashboard stopped${NC}"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --port)
            PORT="$2"
            if ! [[ "$PORT" =~ ^[0-9]+$ ]] || [ "$PORT" -lt 1 ] || [ "$PORT" -gt 65535 ]; then
                echo -e "${RED}❌ Invalid port number: $PORT${NC}"
                echo -e "${YELLOW}💡 Port must be between 1 and 65535${NC}"
                exit 1
            fi
            shift 2
            ;;
        --no-browser)
            OPEN_BROWSER=false
            shift
            ;;
        --help|-h)
            show_usage
            exit 0
            ;;
        *)
            echo -e "${RED}❌ Unknown option: $1${NC}"
            show_usage
            exit 1
            ;;
    esac
done

# Main execution
main() {
    print_header
    
    # Change to script directory
    cd "$SCRIPT_DIR" || {
        echo -e "${RED}❌ Failed to change to script directory${NC}"
        exit 1
    }
    
    # Check if web_analytics.py exists
    if [ ! -f "web_analytics.py" ]; then
        echo -e "${RED}❌ web_analytics.py not found in current directory${NC}"
        echo -e "${YELLOW}💡 Please run this script from the binance-scalping-bot directory${NC}"
        exit 1
    fi
    
    # Perform checks
    check_python
    check_port || exit 1
    check_dependencies
    
    echo -e "${BLUE}🚀 Starting dashboard server...${NC}"
    echo ""
    
    # Open browser in background if requested
    if [ "$OPEN_BROWSER" = true ]; then
        (sleep 3 && open_browser) &
    fi
    
    # Set environment variable for Flask port if different from default
    if [ "$PORT" != "5000" ]; then
        export FLASK_RUN_PORT=$PORT
    fi
    
    # Start the dashboard
    echo -e "${GREEN}✅ Dashboard is starting...${NC}"
    echo -e "${CYAN}🌐 Access URL: http://localhost:$PORT${NC}"
    echo -e "${PURPLE}📱 Network access: http://$(hostname -I | awk '{print $1}'):$PORT${NC}"
    echo ""
    
    # Run the Python dashboard
    $PYTHON_CMD web_analytics.py
}

# Run main function
main "$@"
