from flask import Flask, render_template, jsonify, send_file, request
from analytics import TradingAnalytics
import os
from datetime import datetime
import json
import threading
import time
import pandas as pd

# Import PVSRA modules
try:
    from binance_futures_pvsra import BinanceFuturesPVSRA
    PVSRA_AVAILABLE = True
    print("✅ PVSRA modules imported successfully")
except ImportError as e:
    PVSRA_AVAILABLE = False
    print(f"⚠️ PVSRA modules not available: {e}")
    print("PVSRA features will be disabled")

app = Flask(__name__)

# Global analytics instance
analytics = TradingAnalytics()

# Global PVSRA instance
pvsra = None
pvsra_alerts = []
MAX_ALERTS = 50

def initialize_pvsra():
    """Initialize PVSRA if available"""
    global pvsra
    if PVSRA_AVAILABLE:
        try:
            # Try to get API keys from environment
            api_key = os.getenv('BINANCE_API_KEY')
            api_secret = os.getenv('BINANCE_API_SECRET')
            test_mode = os.getenv('TEST_MODE', 'True').lower() == 'true'
            
            if api_key and api_secret:
                pvsra = BinanceFuturesPVSRA(api_key, api_secret, test_mode)
                pvsra.add_alert_callback(store_pvsra_alert)
                print("✅ PVSRA initialized successfully")
            else:
                print("⚠️ PVSRA API keys not found in environment")
        except Exception as e:
            print(f"❌ Failed to initialize PVSRA: {e}")
    else:
        print("ℹ️ PVSRA not available")

def store_pvsra_alert(symbol: str, alert: dict):
    """Store PVSRA alerts in memory"""
    global pvsra_alerts
    pvsra_alerts.append({
        'timestamp': datetime.now(),
        'symbol': symbol,
        **alert
    })
    
    # Keep only last MAX_ALERTS
    if len(pvsra_alerts) > MAX_ALERTS:
        pvsra_alerts = pvsra_alerts[-MAX_ALERTS:]

# Initialize PVSRA on startup
initialize_pvsra()

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/analytics')
def get_analytics():
    """API endpoint to get analytics data"""
    try:
        # Get data from analytics
        orders = analytics.get_trading_orders(days=7)
        positions = analytics.get_position_changes(days=7)
        closures = analytics.get_trade_closures(days=7)
        exit_analysis = analytics.analyze_exit_performance()
        
        # Recent orders for last 24 hours
        recent_orders = analytics.get_trading_orders(days=1)
        
        # Prepare response data
        data = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'summary': {
                'total_orders': len(orders),
                'position_changes': len(positions),
                'trade_closures': len(closures),
                'recent_orders_24h': len(recent_orders)
            },
            'orders': {
                'buy_orders': len([o for o in orders if o['order_data']['side'] == 'BUY']),
                'sell_orders': len([o for o in orders if o['order_data']['side'] == 'SELL'])
            },
            'exit_analysis': exit_analysis,
            'recent_trades': [],
            'last_order': None
        }
        
        # Add recent trade closures
        if closures:
            for closure in closures[-5:]:  # Last 5 trades
                data['recent_trades'].append({
                    'exit_reason': closure['exit_reason'],
                    'position_type': closure['position_type'],
                    'profit_pct': closure['profit_pct'],
                    'entry_price': closure['entry_price'],
                    'exit_price': closure['exit_price'],
                    'duration_minutes': closure.get('trade_duration_minutes', 0),
                    'timestamp': closure['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
                })
        
        # Add last order info
        if recent_orders:
            last_order = recent_orders[-1]
            data['last_order'] = {
                'side': last_order['order_data']['side'],
                'quantity': last_order['order_data']['quantity'],
                'price': last_order['current_price'],
                'timestamp': last_order['timestamp'].strftime('%Y-%m-%d %H:%M:%S UTC')
            }
          # Prepare chart data
        chart_data = prepare_chart_data(orders, closures)
        data['charts'] = chart_data
        
        # Add PVSRA data if available
        if pvsra:
            data['pvsra'] = {
                'available': True,
                'recent_alerts': len(pvsra_alerts),
                'latest_alert': None
            }
            
            if pvsra_alerts:
                latest_alert = pvsra_alerts[-1]
                data['pvsra']['latest_alert'] = {
                    'symbol': latest_alert['symbol'],
                    'alert': latest_alert.get('alert', ''),
                    'timestamp': latest_alert['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
                }
        else:
            data['pvsra'] = {'available': False}
        
        return jsonify(data)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def prepare_chart_data(orders, closures):
    """Prepare data for charts"""
    charts = {
        'order_timeline': {
            'labels': [],
            'buy_data': [],
            'sell_data': [],
            'price_data': []
        },
        'profit_loss': {
            'labels': [],
            'profit_data': [],
            'colors': []
        },
        'order_distribution': {
            'labels': ['BUY Orders', 'SELL Orders'],
            'data': [
                len([o for o in orders if o['order_data']['side'] == 'BUY']),
                len([o for o in orders if o['order_data']['side'] == 'SELL'])
            ]
        }
    }
    
    # Order timeline chart
    if orders:
        for order in orders[-20:]:  # Last 20 orders
            timestamp = order['timestamp'].strftime('%m/%d %H:%M')
            charts['order_timeline']['labels'].append(timestamp)
            charts['order_timeline']['price_data'].append(order['current_price'])
            
            if order['order_data']['side'] == 'BUY':
                charts['order_timeline']['buy_data'].append(order['current_price'])
                charts['order_timeline']['sell_data'].append(None)
            else:
                charts['order_timeline']['sell_data'].append(order['current_price'])
                charts['order_timeline']['buy_data'].append(None)
    
    # Profit/Loss chart
    if closures:
        for closure in closures[-10:]:  # Last 10 trades
            charts['profit_loss']['labels'].append(
                closure['timestamp'].strftime('%m/%d %H:%M')
            )
            charts['profit_loss']['profit_data'].append(closure['profit_pct'])
            
            # Color based on profit/loss
            color = '#4CAF50' if closure['profit_pct'] > 0 else '#F44336'
            charts['profit_loss']['colors'].append(color)
    
    return charts

@app.route('/api/export/orders')
def export_orders():
    """Export orders to CSV"""
    try:
        filename = f"orders_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df = analytics.export_to_csv(filename)
        return send_file(filename, as_attachment=True)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/export/trades')
def export_trades():
    """Export trade closures to CSV"""
    try:
        filename = f"trades_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df = analytics.export_trade_closures_to_csv(filename)
        return send_file(filename, as_attachment=True)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'mongodb_connected': analytics.collection is not None,
        'pvsra_available': pvsra is not None
    })

@app.route('/api/pvsra/analyze')
def pvsra_analyze():
    """PVSRA analysis endpoint"""
    if not pvsra:
        return jsonify({'error': 'PVSRA not available'}), 503
    
    try:
        symbol = request.args.get('symbol', 'BTCUSDT')
        interval = request.args.get('interval', '5m')
        limit = int(request.args.get('limit', 100))
        
        # Get PVSRA analysis
        result = pvsra.analyze_symbol(symbol, interval, limit)
        
        if result.empty:
            return jsonify({'error': 'No data available'}), 404
        
        # Prepare chart data
        chart_data = {
            'timestamps': result.index.strftime('%Y-%m-%d %H:%M:%S').tolist(),
            'ohlcv': {
                'open': result['open'].tolist(),
                'high': result['high'].tolist(),
                'low': result['low'].tolist(),
                'close': result['close'].tolist(),
                'volume': result['volume'].tolist()
            },
            'pvsra': {
                'colors': result['candle_color'].tolist(),
                'conditions': result['condition'].tolist(),
                'is_climax': result['is_climax'].tolist(),
                'is_rising': result['is_rising'].tolist(),
                'is_bullish': result['is_bullish'].tolist(),
                'alerts': result['alert'].tolist()
            },
            'latest': {
                'price': float(result['close'].iloc[-1]),
                'condition': result['condition'].iloc[-1],
                'alert': result['alert'].iloc[-1] if result['alert'].iloc[-1] else None,
                'volume_ratio': float(result['volume'].iloc[-1] / result['avg_volume'].iloc[-1])
            }
        }
        
        return jsonify(chart_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/pvsra/alerts')
def pvsra_get_alerts():
    """Get recent PVSRA alerts"""
    try:
        alerts_data = []
        for alert in pvsra_alerts[-20:]:  # Last 20 alerts
            alerts_data.append({
                'timestamp': alert['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                'symbol': alert['symbol'],
                'alert': alert.get('alert', ''),
                'condition': alert.get('condition', ''),
                'price': alert.get('price', 0)
            })
        
        return jsonify({
            'alerts': alerts_data,
            'total_count': len(pvsra_alerts)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/pvsra/scan')
def pvsra_scan_symbols():
    """Scan multiple symbols for PVSRA patterns"""
    if not pvsra:
        return jsonify({'error': 'PVSRA not available'}), 503
    
    try:
        symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'ADAUSDT', 'DOTUSDT', 'SUIUSDC']
        interval = request.args.get('interval', '15m')
        
        scan_results = []
        
        for symbol in symbols:
            try:
                result = pvsra.analyze_symbol(symbol, interval, 20)
                if not result.empty:
                    latest = result.iloc[-1]
                    
                    scan_results.append({
                        'symbol': symbol,
                        'price': float(latest['close']),
                        'condition': latest['condition'],
                        'alert': latest['alert'] if latest['alert'] else None,
                        'is_climax': bool(latest['is_climax']),
                        'is_rising': bool(latest['is_rising']),
                        'volume_ratio': float(latest['volume'] / latest['avg_volume']),
                        'color': latest['candle_color']
                    })
            except Exception as e:
                print(f"Error scanning {symbol}: {e}")
                continue
        
        return jsonify({
            'scan_results': scan_results,
            'scan_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/pvsra/start_monitoring')
def pvsra_start_monitoring():
    """Start real-time PVSRA monitoring"""
    if not pvsra:
        return jsonify({'error': 'PVSRA not available'}), 503
    
    try:
        symbol = request.args.get('symbol', 'BTCUSDT')
        interval = request.args.get('interval', '1m')
        
        pvsra.start_realtime_analysis(symbol, interval)
        
        return jsonify({
            'message': f'Started monitoring {symbol} on {interval}',
            'symbol': symbol,
            'interval': interval
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🚀 Starting Trading Analytics Web Dashboard...")
    print("📊 Dashboard will be available at: http://localhost:5000")
    print("💡 Press Ctrl+C to stop the server")
    print("=" * 60)
    
    # Run Flask app
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
