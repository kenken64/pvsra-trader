# PowerShell equivalent of start_merged_dashboard.bat
# Enhanced version with error handling and options

param(
    [int]$Port = 5000,
    [switch]$NoBrowser,
    [switch]$Help
)

# Color functions
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

function Write-Header {
    Write-ColorOutput Cyan "🚀 Starting Merged PVSRA + Analytics Dashboard"
    Write-ColorOutput Blue "============================================"
    Write-Output ""
    Write-ColorOutput Green "📊 Dashboard URL: http://localhost:$Port"
    Write-ColorOutput Yellow "💡 Press Ctrl+C to stop the server"
    Write-Output ""
}

function Show-Usage {
    Write-ColorOutput White "Usage: .\start_merged_dashboard.ps1 [options]"
    Write-Output ""
    Write-ColorOutput Cyan "Options:"
    Write-ColorOutput Green "  -Port <number>     Use custom port (default: 5000)"
    Write-ColorOutput Green "  -NoBrowser         Don't automatically open browser"
    Write-ColorOutput Green "  -Help              Show this help message"
    Write-Output ""
    Write-ColorOutput Cyan "Examples:"
    Write-ColorOutput Yellow "  .\start_merged_dashboard.ps1"
    Write-ColorOutput Yellow "  .\start_merged_dashboard.ps1 -Port 8080"
    Write-ColorOutput Yellow "  .\start_merged_dashboard.ps1 -NoBrowser"
    Write-ColorOutput Yellow "  .\start_merged_dashboard.ps1 -Port 3000 -NoBrowser"
}

function Test-Port {
    param([int]$PortNumber)
    
    try {
        $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Any, $PortNumber)
        $listener.Start()
        $listener.Stop()
        return $true
    }
    catch {
        Write-ColorOutput Red "❌ Port $PortNumber is already in use"
        Write-ColorOutput Yellow "💡 Try using a different port with: -Port <port_number>"
        return $false
    }
}

function Test-Python {
    $pythonCmd = $null
    
    if (Get-Command python3 -ErrorAction SilentlyContinue) {
        $pythonCmd = "python3"
    }
    elseif (Get-Command python -ErrorAction SilentlyContinue) {
        $version = python -c "import sys; print(sys.version_info[0])" 2>$null
        if ($version -eq "3") {
            $pythonCmd = "python"
        }
    }
    
    if (-not $pythonCmd) {
        Write-ColorOutput Red "❌ Python 3 is required but not found"
        Write-ColorOutput Yellow "💡 Please install Python 3.7+ and try again"
        exit 1
    }
    
    return $pythonCmd
}

function Test-Dependencies {
    param([string]$PythonCmd)
    
    Write-ColorOutput Blue "🔍 Checking dependencies..."
    
    $result = & $PythonCmd -c "import flask, pymongo, pandas" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-ColorOutput Yellow "⚠️ Missing dependencies detected"
        Write-ColorOutput Cyan "📦 Installing required packages..."
        
        & $PythonCmd -m pip install flask pymongo pandas python-dotenv requests
        
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput Green "✅ Dependencies installed successfully"
        }
        else {
            Write-ColorOutput Red "❌ Failed to install dependencies"
            Write-ColorOutput Yellow "💡 Please run: pip install flask pymongo pandas python-dotenv requests"
            exit 1
        }
    }
    else {
        Write-ColorOutput Green "✅ All dependencies are available"
    }
}

function Open-Browser {
    if (-not $NoBrowser) {
        Write-ColorOutput Cyan "🌐 Opening browser..."
        Start-Sleep -Seconds 2
        Start-Process "http://localhost:$Port"
    }
}

# Show help if requested
if ($Help) {
    Show-Usage
    exit 0
}

# Validate port
if ($Port -lt 1 -or $Port -gt 65535) {
    Write-ColorOutput Red "❌ Invalid port number: $Port"
    Write-ColorOutput Yellow "💡 Port must be between 1 and 65535"
    exit 1
}

# Main execution
try {
    Write-Header
    
    # Change to script directory
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    Set-Location $scriptDir
    
    # Check if web_analytics.py exists
    if (-not (Test-Path "web_analytics.py")) {
        Write-ColorOutput Red "❌ web_analytics.py not found in current directory"
        Write-ColorOutput Yellow "💡 Please run this script from the binance-scalping-bot directory"
        exit 1
    }
    
    # Perform checks
    $pythonCmd = Test-Python
    if (-not (Test-Port $Port)) { exit 1 }
    Test-Dependencies $pythonCmd
    
    Write-ColorOutput Blue "🚀 Starting dashboard server..."
    Write-Output ""
    
    # Open browser in background if requested
    if (-not $NoBrowser) {
        Start-Job -ScriptBlock { Start-Sleep 3; Start-Process "http://localhost:$using:Port" } | Out-Null
    }
    
    # Set environment variable for Flask port if different from default
    if ($Port -ne 5000) {
        $env:FLASK_RUN_PORT = $Port
    }
    
    # Start the dashboard
    Write-ColorOutput Green "✅ Dashboard is starting..."
    Write-ColorOutput Cyan "🌐 Access URL: http://localhost:$Port"
    
    # Get network IP for mobile access
    $networkIP = (Get-NetIPAddress -AddressFamily IPv4 -InterfaceAlias (Get-NetAdapter | Where-Object Status -eq "Up").Name | Where-Object { $_.IPAddress -notlike "127.*" } | Select-Object -First 1).IPAddress
    if ($networkIP) {
        Write-ColorOutput Magenta "📱 Network access: http://$networkIP`:$Port"
    }
    Write-Output ""
    
    # Run the Python dashboard
    & $pythonCmd web_analytics.py
}
catch {
    Write-ColorOutput Red "❌ An error occurred: $($_.Exception.Message)"
    exit 1
}
finally {
    Write-Output ""
    Write-ColorOutput Cyan "🛑 Shutting down dashboard..."
    Write-ColorOutput Green "✅ Dashboard stopped"
}
