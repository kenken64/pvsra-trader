# 🐧 Cross-Platform Analytics Dashboard

This directory contains scripts to start the Trading Analytics Web Dashboard on different operating systems.

## 🚀 Quick Start

### Windows
```cmd
start_web_analytics.bat
```

### Linux/macOS (Simple)
```bash
chmod +x start_web_analytics.sh
./start_web_analytics.sh
```

### Linux/macOS (Advanced)
```bash
chmod +x launch_web_analytics.sh
./launch_web_analytics.sh
```

## 📋 Available Scripts

### 🪟 Windows
- **`start_web_analytics.bat`** - Simple Windows batch file
- **`start_merged_dashboard.bat`** - Merged PVSRA + Analytics Dashboard (Windows)
- **`start_merged_dashboard.ps1`** - Merged PVSRA + Analytics Dashboard (PowerShell)
- **`launch_dashboard.py`** - Python launcher with auto-browser opening

### 🐧 Linux/macOS
- **`start_web_analytics.sh`** - Simple shell script equivalent to Windows batch
- **`start_merged_dashboard.sh`** - Merged PVSRA + Analytics Dashboard (Advanced Linux)
- **`start_merged_dashboard_simple.sh`** - Merged PVSRA + Analytics Dashboard (Simple Linux)
- **`launch_web_analytics.sh`** - Advanced launcher with extra features

## 🎯 Merged Dashboard (PVSRA + Analytics)

### 🪟 **Windows (Batch)**
```cmd
start_merged_dashboard.bat
```

### 🪟 **Windows (PowerShell)**
```powershell
.\start_merged_dashboard.ps1

# With options
.\start_merged_dashboard.ps1 -Port 8080
.\start_merged_dashboard.ps1 -NoBrowser
.\start_merged_dashboard.ps1 -Port 3000 -NoBrowser
```

### 🐧 **Linux/macOS (Advanced)**
```bash
chmod +x start_merged_dashboard.sh
./start_merged_dashboard.sh

# With options
./start_merged_dashboard.sh --port 8080
./start_merged_dashboard.sh --no-browser
./start_merged_dashboard.sh --port 3000 --no-browser
```

### 🐧 **Linux/macOS (Simple)**
```bash
chmod +x start_merged_dashboard_simple.sh
./start_merged_dashboard_simple.sh
```

## ⚙️ Advanced Linux/macOS Launcher Features

### 🔧 **Original Analytics Launcher (`launch_web_analytics.sh`)**
```bash
./launch_web_analytics.sh [options]

Options:
  --no-browser    Don't automatically open browser
  --port PORT     Use custom port (default: 5000)
  --help          Show help message
```

### 🎯 **Merged Dashboard Launcher (`start_merged_dashboard.sh`)**
Enhanced version with PVSRA + Analytics integration:

```bash
./start_merged_dashboard.sh [options]

Options:
  --port PORT     Use custom port (default: 5000)
  --no-browser    Don't automatically open browser
  --help          Show help message
```

### ✨ **Enhanced Features (Merged Dashboard)**
- **🎨 Colored terminal output** for better readability
- **🔍 Automatic dependency checking** and installation
- **🌐 Port availability verification** with informative error messages
- **🐍 Python version detection** (supports both `python` and `python3`)
- **🔧 Cross-platform browser detection** (xdg-open, gnome-open, open, firefox, chrome)
- **📱 Network IP display** for mobile device access
- **🛡️ Graceful shutdown** handling with cleanup
- **⚠️ Enhanced error messages** with helpful suggestions
- **📦 Smart dependency installation** if packages are missing

### 📱 **Usage Examples**
```bash
# Start with default settings (port 5000, auto-open browser)
./start_merged_dashboard.sh

# Start on custom port
./start_merged_dashboard.sh --port 8080

# Start without opening browser automatically
./start_merged_dashboard.sh --no-browser

# Custom port + no browser
./start_merged_dashboard.sh --port 3000 --no-browser

# Simple version (no options)
./start_merged_dashboard_simple.sh
```

## 🔄 Script Comparison

### **All Merged Dashboard Scripts Comparison**

| Feature | Windows Batch | Windows PowerShell | Linux Simple | Linux Advanced |
|---------|---------------|-------------------|--------------|----------------|
| **File** | `.bat` | `.ps1` | `_simple.sh` | `.sh` |
| **Basic Startup** | ✅ | ✅ | ✅ | ✅ |
| **Colored Output** | ❌ | ✅ | ❌ | ✅ |
| **Custom Port** | ❌ | ✅ | ❌ | ✅ |
| **Auto Browser** | ❌ | ✅ | ❌ | ✅ |
| **Dependency Check** | ❌ | ✅ | ❌ | ✅ |
| **Error Handling** | Basic | Advanced | Basic | Advanced |
| **Help System** | ❌ | ✅ | ❌ | ✅ |
| **Port Validation** | ❌ | ✅ | ❌ | ✅ |
| **Network IP Display** | ❌ | ✅ | ❌ | ✅ |
| **Cross-platform** | Windows | Windows | Linux/macOS | Linux/macOS |

### **Simple vs Advanced Merged Dashboard Scripts**

| Feature | Simple | Advanced |
|---------|---------|-----------|
| **Basic Startup** | ✅ | ✅ |
| **Colored Output** | ❌ | ✅ |
| **Custom Port** | ❌ | ✅ |
| **Auto Browser** | ❌ | ✅ |
| **Dependency Check** | ❌ | ✅ |
| **Error Handling** | Basic | Advanced |
| **Help System** | ❌ | ✅ |
| **Port Validation** | ❌ | ✅ |
| **Network IP Display** | ❌ | ✅ |
| **File Size** | ~500 bytes | ~8KB |

### **Which One to Use?**
- **🚀 Windows Batch** (`start_merged_dashboard.bat`): Simple, works on all Windows versions
- **⚡ Windows PowerShell** (`start_merged_dashboard.ps1`): Advanced features with error handling
- **🐧 Linux Simple** (`start_merged_dashboard_simple.sh`): Quick start, minimal features
- **🌟 Linux Advanced** (`start_merged_dashboard.sh`): Full-featured with all enhancements

### **Recommendations by Use Case**
- **👤 Casual Use**: Use the simple versions (`.bat` or `_simple.sh`)
- **👨‍💻 Development**: Use advanced versions (`.ps1` or `.sh`) for better debugging
- **🏢 Production**: Use advanced versions for better error handling and monitoring
- **📱 Mobile Access**: Use advanced versions to get network IP display

### ✨ **Advanced Features**
- **Automatic dependency checking** and installation
- **Port availability checking** with automatic fallback
- **Cross-platform browser detection** (Linux/macOS)
- **Colored terminal output** for better readability
- **Error handling** with informative messages
- **Graceful shutdown** handling
- **Python version detection**

## 🔧 Manual Setup (if needed)

### 1. Make Scripts Executable (Linux/macOS)
```bash
chmod +x *.sh
```

### 2. Install Dependencies
```bash
# Python 3.7+
pip install flask pymongo pandas python-dotenv

# Or using requirements.txt
pip install -r requirements.txt
```

### 3. Set Environment Variables
Create a `.env` file with your MongoDB settings:
```env
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DATABASE=trading_bot
MONGODB_COLLECTION=orders
```

## 🌐 Access Dashboard

Once started, access your dashboard at:
- **Default**: http://localhost:5000
- **Custom Port**: http://localhost:[PORT]
- **Network Access**: http://[your-ip]:[PORT]

## 🐛 Troubleshooting

### Script Won't Execute (Linux/macOS)
```bash
# Make sure script is executable
chmod +x start_web_analytics.sh
chmod +x launch_web_analytics.sh

# Check line endings (convert from Windows if needed)
dos2unix *.sh
```

### Port Already in Use
```bash
# Use custom port
./launch_web_analytics.sh --port 8080

# Or check what's using the port
lsof -i :5000
```

### Dependencies Missing
```bash
# Install all requirements
pip install -r requirements.txt

# Or manually install
pip install flask pymongo pandas python-dotenv
```

### Python Not Found
```bash
# Check Python installation
python3 --version
python --version

# Install Python 3.7+ if missing
# Ubuntu/Debian: sudo apt install python3 python3-pip
# CentOS/RHEL: sudo yum install python3 python3-pip
# macOS: brew install python3
```

## 📊 Platform-Specific Notes

### 🪟 **Windows**
- Use **PowerShell** or **Command Prompt**
- `.bat` files work out of the box
- Python launcher automatically detects Python installation

### 🐧 **Linux**
- Requires **bash shell**
- Scripts auto-detect package managers
- Browser detection for **GNOME**, **KDE**, and others
- Supports **xdg-open**, **gnome-open**, **firefox**, **chromium**

### 🍎 **macOS**
- Uses **bash shell** (default on older macOS) or **zsh** (newer macOS)
- Automatic browser opening with **`open`** command
- Homebrew package detection

## 🚀 Performance Tips

1. **Keep dashboard open** in a browser tab for continuous monitoring
2. **Use network access** to monitor from mobile devices
3. **Bookmark** the dashboard URL for quick access
4. **Export data regularly** using the web interface
5. **Monitor resource usage** if running on limited hardware

## 🔐 Security Considerations

- Dashboard runs on **localhost** by default (secure)
- For **network access**, ensure firewall allows the port
- Consider **authentication** for production environments
- Use **HTTPS** in production deployments

Perfect for cross-platform monitoring of your trading bot! 🚀📊
