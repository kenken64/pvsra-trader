import os
import pandas as pd
from pymongo import MongoClient
from datetime import datetime, timezone, timedelta
import matplotlib.pyplot as plt
import seaborn as sns

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

class TradingAnalytics:
    def __init__(self):
        self.mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
        self.mongodb_database = os.getenv('MONGODB_DATABASE', 'trading_bot')
        self.mongodb_collection = os.getenv('MONGODB_COLLECTION', 'orders')
        
        self.client = MongoClient(self.mongodb_uri)
        self.db = self.client[self.mongodb_database]
        self.collection = self.db[self.mongodb_collection]
    
    def get_trading_orders(self, days=7):
        """Get all trading orders from the last N days"""
        from_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        orders = list(self.collection.find({
            "timestamp": {"$gte": from_date},
            "type": "trading_order",
            "success": True
        }).sort("timestamp", 1))
        
        return orders
    
    def get_position_changes(self, days=7):
        """Get all position changes from the last N days"""
        from_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        positions = list(self.collection.find({
            "timestamp": {"$gte": from_date},
            "type": "position_change"
        }).sort("timestamp", 1))
        
        return positions
    
    def get_trade_closures(self, days=7):
        """Get detailed trade closure data from the last N days"""
        from_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        closures = list(self.collection.find({
            "timestamp": {"$gte": from_date},
            "type": "trade_close"
        }).sort("timestamp", 1))
        
        return closures
    
    def analyze_exit_performance(self):
        """Analyze performance of profit taking vs stop loss exits"""
        closures = self.get_trade_closures(days=30)
        
        if not closures:
            return None
        
        profit_takes = [c for c in closures if c['exit_reason'] == 'TAKE_PROFIT']
        stop_losses = [c for c in closures if c['exit_reason'] == 'STOP_LOSS']
        
        analysis = {
            'total_trades': len(closures),
            'profit_takes': {
                'count': len(profit_takes),
                'percentage': len(profit_takes) / len(closures) * 100 if closures else 0,
                'avg_profit': sum(c['profit_pct'] for c in profit_takes) / len(profit_takes) if profit_takes else 0,
                'total_profit': sum(c['profit_pct'] for c in profit_takes)
            },
            'stop_losses': {
                'count': len(stop_losses),
                'percentage': len(stop_losses) / len(closures) * 100 if closures else 0,
                'avg_loss': sum(c['profit_pct'] for c in stop_losses) / len(stop_losses) if stop_losses else 0,
                'total_loss': sum(c['profit_pct'] for c in stop_losses)
            }
        }
        
        # Calculate strategy effectiveness
        if closures:
            analysis['net_profit_pct'] = sum(c['profit_pct'] for c in closures)
            analysis['avg_trade_duration'] = sum(c.get('trade_duration_minutes', 0) for c in closures) / len(closures)
            analysis['win_rate'] = len([c for c in closures if c['profit_pct'] > 0]) / len(closures) * 100
        
        return analysis
    
    def generate_report(self):
        """Generate comprehensive trading report with exit analysis"""
        print("📊 TRADING ANALYTICS REPORT")
        print("=" * 50)
        
        # Basic statistics
        orders = self.get_trading_orders(days=7)
        positions = self.get_position_changes(days=7)
        closures = self.get_trade_closures(days=7)
        
        print(f"\n📈 Last 7 Days Summary:")
        print(f"   Total Orders: {len(orders)}")
        print(f"   Position Changes: {len(positions)}")
        print(f"   Trade Closures: {len(closures)}")
        
        # Order statistics
        buy_orders = len([o for o in orders if o['order_data']['side'] == 'BUY'])
        sell_orders = len([o for o in orders if o['order_data']['side'] == 'SELL'])
        
        print(f"\n🔄 Order Breakdown:")
        print(f"   BUY Orders: {buy_orders}")
        print(f"   SELL Orders: {sell_orders}")
        
        # Exit Performance Analysis
        exit_analysis = self.analyze_exit_performance()
        if exit_analysis:
            print(f"\n🎯 Exit Strategy Performance (30 days):")
            print(f"   Total Trades Closed: {exit_analysis['total_trades']}")
            print(f"   Win Rate: {exit_analysis['win_rate']:.1f}%")
            print(f"   Net Profit/Loss: {exit_analysis['net_profit_pct']:.2f}%")
            print(f"   Avg Trade Duration: {exit_analysis['avg_trade_duration']:.1f} minutes")
            
            print(f"\n🎯 Take Profit Performance:")
            pt = exit_analysis['profit_takes']
            print(f"   Triggered: {pt['count']} times ({pt['percentage']:.1f}%)")
            print(f"   Average Profit: {pt['avg_profit']:.2f}%")
            print(f"   Total Profit: {pt['total_profit']:.2f}%")
            
            print(f"\n🛑 Stop Loss Performance:")
            sl = exit_analysis['stop_losses']
            print(f"   Triggered: {sl['count']} times ({sl['percentage']:.1f}%)")
            print(f"   Average Loss: {sl['avg_loss']:.2f}%")
            print(f"   Total Loss: {sl['total_loss']:.2f}%")
            
            # Strategy effectiveness metrics
            if pt['count'] > 0 and sl['count'] > 0:
                risk_reward_ratio = abs(pt['avg_profit'] / sl['avg_loss'])
                print(f"\n📊 Strategy Metrics:")
                print(f"   Risk/Reward Ratio: 1:{risk_reward_ratio:.2f}")
                print(f"   Profit Factor: {abs(pt['total_profit'] / sl['total_loss']) if sl['total_loss'] != 0 else 'N/A':.2f}")
        
        # Detailed trade closure analysis
        if closures:
            print(f"\n💹 Recent Trade Closures:")
            for i, closure in enumerate(closures[-5:], 1):  # Show last 5 trades
                emoji = "💰" if closure['profit_pct'] > 0 else "📉"
                reason_emoji = "🎯" if closure['exit_reason'] == 'TAKE_PROFIT' else "🛑"
                print(f"   {i}. {reason_emoji} {closure['position_type']} {closure['exit_reason']}: {closure['profit_pct']:.2f}%")
                print(f"      Entry: {closure['entry_price']:.4f} → Exit: {closure['exit_price']:.4f}")
                if 'trade_duration_minutes' in closure:
                    print(f"      Duration: {closure['trade_duration_minutes']:.1f} minutes")
        
        # Recent activity
        recent_orders = self.get_trading_orders(days=1)
        if recent_orders:
            print(f"\n🕐 Last 24 Hours:")
            print(f"   Orders: {len(recent_orders)}")
            last_order = recent_orders[-1]
            print(f"   Last Order: {last_order['order_data']['side']} {last_order['order_data']['quantity']} at {last_order['current_price']}")
            print(f"   Time: {last_order['timestamp'].strftime('%Y-%m-%d %H:%M:%S UTC')}")
        
        return {
            'orders': orders,
            'positions': positions,
            'closures': closures,
            'exit_analysis': exit_analysis
        }
    
    def export_trade_closures_to_csv(self, filename="trade_closures.csv", days=30):
        """Export detailed trade closure data to CSV"""
        closures = self.get_trade_closures(days=days)
        
        if not closures:
            print("No trade closure data found to export")
            return
        
        # Flatten the data for CSV
        csv_data = []
        for closure in closures:
            row = {
                'timestamp': closure['timestamp'],
                'symbol': closure['symbol'],
                'exit_reason': closure['exit_reason'],
                'position_type': closure['position_type'],
                'entry_price': closure['entry_price'],
                'exit_price': closure['exit_price'],
                'profit_pct': closure['profit_pct'],
                'unrealized_pnl': closure.get('unrealized_pnl', 0),
                'position_amt': closure['position_amt'],
                'position_value': closure['position_value'],
                'trigger_threshold': closure['trigger_threshold'],
                'trade_result': closure['trade_result'],
                'session_id': closure['session_id'],
                'test_mode': closure['test_mode']
            }
            
            # Add optional fields
            if 'trade_duration_minutes' in closure:
                row['trade_duration_minutes'] = closure['trade_duration_minutes']
                row['trade_duration_seconds'] = closure['trade_duration_seconds']
            
            if 'position_opened_at' in closure:
                row['position_opened_at'] = closure['position_opened_at']
            
            if 'close_order_id' in closure:
                row['close_order_id'] = closure['close_order_id']
                row['close_client_order_id'] = closure.get('close_client_order_id', '')
            
            csv_data.append(row)
        
        df = pd.DataFrame(csv_data)
        df.to_csv(filename, index=False)
        print(f"✅ Trade closure data exported to {filename}")
        print(f"📊 Exported {len(csv_data)} trade closures from last {days} days")
        return df
    
    def export_to_csv(self, filename="trading_data.csv", days=30):
        """Export trading order data to CSV"""
        orders = self.get_trading_orders(days=days)
        
        if not orders:
            print("No trading data found to export")
            return
        
        # Flatten the data for CSV
        csv_data = []
        for order in orders:
            row = {
                'timestamp': order['timestamp'],
                'symbol': order['symbol'],
                'side': order['order_data']['side'],
                'quantity': order['order_data']['quantity'],
                'price': order['current_price'],
                'order_type': order['order_data']['order_type'],
                'success': order['success'],
                'session_id': order['session_id'],
                'test_mode': order['test_mode']
            }
            
            if 'binance_response' in order:
                row['order_id'] = order['binance_response'].get('orderId', '')
                row['client_order_id'] = order['binance_response'].get('clientOrderId', '')
            
            csv_data.append(row)
        
        df = pd.DataFrame(csv_data)
        df.to_csv(filename, index=False)
        print(f"✅ Trading order data exported to {filename}")
        print(f"📊 Exported {len(csv_data)} orders from last {days} days")
        return df
    
    def plot_trading_activity(self):
        """Create plots of trading activity"""
        try:
            import matplotlib.pyplot as plt
            import matplotlib.dates as mdates
            
            orders = self.get_trading_orders(days=7)
            if not orders:
                print("No data to plot")
                return
            
            # Prepare data
            timestamps = [order['timestamp'] for order in orders]
            prices = [order['current_price'] for order in orders]
            sides = [order['order_data']['side'] for order in orders]
            
            # Create figure with subplots
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
            
            # Plot 1: Price over time with buy/sell markers
            buy_times = [t for t, s in zip(timestamps, sides) if s == 'BUY']
            buy_prices = [p for p, s in zip(prices, sides) if s == 'BUY']
            sell_times = [t for t, s in zip(timestamps, sides) if s == 'SELL']
            sell_prices = [p for p, s in zip(prices, sides) if s == 'SELL']
            
            ax1.plot(timestamps, prices, 'b-', alpha=0.5, label='Price')
            ax1.scatter(buy_times, buy_prices, color='green', marker='^', s=50, label='BUY', alpha=0.7)
            ax1.scatter(sell_times, sell_prices, color='red', marker='v', s=50, label='SELL', alpha=0.7)
            
            ax1.set_title('Trading Activity - Price and Orders')
            ax1.set_ylabel('Price (USDT)')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # Plot 2: Order frequency over time
            order_counts = {}
            for ts in timestamps:
                hour_key = ts.replace(minute=0, second=0, microsecond=0)
                order_counts[hour_key] = order_counts.get(hour_key, 0) + 1
            
            hours = list(order_counts.keys())
            counts = list(order_counts.values())
            
            ax2.bar(hours, counts, alpha=0.7, color='purple')
            ax2.set_title('Order Frequency by Hour')
            ax2.set_ylabel('Number of Orders')
            ax2.set_xlabel('Time')
            
            # Format x-axis
            ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
            ax2.xaxis.set_major_locator(mdates.HourLocator(interval=6))
            plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
            
            plt.tight_layout()
            plt.savefig('trading_activity.png', dpi=300, bbox_inches='tight')
            plt.show()
            
            print("📊 Chart saved as 'trading_activity.png'")
            
        except ImportError:
            print("⚠️ matplotlib not installed. Install with: pip install matplotlib")
        except Exception as e:
            print(f"Error creating plots: {e}")
    
    def close(self):
        """Close MongoDB connection"""
        self.client.close()

# Example usage
if __name__ == "__main__":
    analytics = TradingAnalytics()
    
    try:
        # Generate comprehensive report
        data = analytics.generate_report()
        
        print("\n" + "="*50)
        print("Additional Options:")
        print("1. Export orders to CSV: analytics.export_to_csv('my_orders.csv')")
        print("2. Export trade closures to CSV: analytics.export_trade_closures_to_csv('my_trades.csv')")
        print("3. Create plots: analytics.plot_trading_activity()")
        print("4. Exit analysis: analytics.analyze_exit_performance()")
        print("5. Access raw data: data['orders'], data['positions'], data['closures']")
        
        # Optionally export detailed trade closures
        # analytics.export_trade_closures_to_csv("detailed_trades.csv")
        
        # Optionally export basic orders
        # analytics.export_to_csv("trading_orders.csv")
        
        # Optionally create plots
        # analytics.plot_trading_activity()
        
    except Exception as e:
        print(f"Error running analytics: {e}")
    finally:
        analytics.close()