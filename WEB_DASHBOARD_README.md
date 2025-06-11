# 📊 Trading Analytics Web Dashboard

A beautiful, real-time web dashboard for monitoring your Binance futures scalping bot performance.

## ✨ Features

### 🔴 Live Monitoring
- **Real-time updates** every 10 seconds
- **Live statistics** for orders, trades, and performance
- **Auto-refresh** with loading indicators
- **Responsive design** that works on desktop and mobile

### 📈 Advanced Analytics
- **Trading Timeline Chart** - Visual representation of buy/sell orders over time
- **Order Distribution** - Pie chart showing BUY vs SELL order ratios
- **Profit/Loss Analysis** - Bar chart of recent trade performance
- **Exit Strategy Performance** - Comprehensive analysis of take profit vs stop loss

### 📊 Key Metrics
- **Total Orders** (7-day summary)
- **Trade Closures** with detailed breakdown
- **Win Rate** percentage
- **Risk/Reward Ratio** calculation
- **Average Trade Duration**
- **Net Profit/Loss** tracking

### 💾 Export Capabilities
- **CSV Export** for orders and trades
- **One-click downloads** with timestamped filenames
- **Comprehensive data** including all trade details

### 🎨 Modern UI
- **Glass-morphism design** with beautiful gradients
- **Responsive Bootstrap layout**
- **Interactive charts** using Chart.js
- **Real-time status indicators**
- **Professional color scheme**

## 🚀 Quick Start

### Option 1: Direct Python Launch
```bash
python web_analytics.py
```

### Option 2: Auto-launch with Browser
```bash
python launch_dashboard.py
```

### Option 3: Windows Batch File
```bash
start_web_analytics.bat
```

## 📱 Access Dashboard

Once started, access your dashboard at:
- **Local Access**: http://localhost:5000
- **Network Access**: http://[your-ip]:5000

## 📋 Dashboard Sections

### 1. **Header Status**
- Live connection status
- Last update timestamp
- Auto-refresh indicator

### 2. **Statistics Cards**
- Total Orders (7-day)
- Trade Closures
- BUY Orders count
- SELL Orders count

### 3. **Interactive Charts**
- **Timeline Chart**: Price movements with buy/sell markers
- **Distribution Chart**: Order type breakdown
- **Performance Chart**: Recent trade profit/loss

### 4. **Recent Trades Panel**
- Last 5 trade closures
- Profit/loss indicators
- Entry/exit prices
- Trade duration

### 5. **Performance Metrics**
- Win rate percentage
- Net profit/loss
- Average trade duration
- Risk/reward ratio

### 6. **Export Controls**
- Export orders to CSV
- Export trades to CSV
- Timestamped filenames

## 🔧 API Endpoints

### GET /
Main dashboard page

### GET /api/analytics
Returns complete analytics data in JSON format

### GET /api/export/orders
Downloads orders CSV file

### GET /api/export/trades
Downloads trades CSV file

### GET /health
Health check endpoint

## 📊 Data Sources

The dashboard connects to your MongoDB database using the same configuration as your trading bot:

- **MongoDB URI**: From MONGODB_URI environment variable
- **Database**: From MONGODB_DATABASE environment variable  
- **Collection**: From MONGODB_COLLECTION environment variable

## 🔄 Auto-Refresh

The dashboard automatically refreshes every **10 seconds** as requested, providing:
- Live data updates
- Real-time chart refreshes
- Updated statistics
- Fresh trade information

## 🛠 Technical Details

### Built With
- **Flask** - Python web framework
- **Chart.js** - Interactive charts
- **Bootstrap 5** - Responsive UI framework
- **Font Awesome** - Professional icons
- **MongoDB** - Data persistence

### Browser Compatibility
- Chrome/Edge (recommended)
- Firefox
- Safari
- Mobile browsers

## 🔒 Security Notes

- Dashboard runs on localhost by default
- For network access, ensure your firewall allows port 5000
- In production, consider using HTTPS and authentication

## 🚨 Troubleshooting

### Dashboard Won't Start
1. Check if port 5000 is available
2. Verify MongoDB connection
3. Ensure Flask is installed: `pip install flask`

### No Data Showing
1. Verify bot is running and creating database entries
2. Check MongoDB connection settings
3. Ensure TEST_MODE is properly configured

### Charts Not Loading
1. Check browser console for JavaScript errors
2. Ensure internet connection for CDN resources
3. Try refreshing the page

## 💡 Tips

1. **Bookmark** http://localhost:5000 for quick access
2. **Leave dashboard open** for continuous monitoring
3. **Export data regularly** for backup and analysis
4. **Use network access** to monitor from mobile devices
5. **Check health endpoint** to verify system status

## 🔄 Integration

The web dashboard uses the same `TradingAnalytics` class as the terminal version, ensuring:
- **Consistent data** across interfaces
- **No performance impact** on trading bot
- **Same MongoDB collections**
- **Identical calculations**

Perfect for monitoring your trading bot's performance with a professional, real-time web interface! 📈✨
