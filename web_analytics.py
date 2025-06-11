from flask import Flask, render_template, jsonify, send_file
from analytics import TradingAnalytics
import os
from datetime import datetime
import json
import threading
import time

app = Flask(__name__)

# Global analytics instance
analytics = TradingAnalytics()

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
        'mongodb_connected': analytics.collection is not None
    })

if __name__ == '__main__':
    print("🚀 Starting Trading Analytics Web Dashboard...")
    print("📊 Dashboard will be available at: http://localhost:5000")
    print("💡 Press Ctrl+C to stop the server")
    print("=" * 60)
    
    # Run Flask app
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
