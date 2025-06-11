"""
MongoDB Query Examples for Detailed Trade Closure Analysis

This script demonstrates how to query your MongoDB database for specific
profit taking and stop loss events to analyze your trading performance.
"""

import os
from pymongo import MongoClient
from datetime import datetime, timezone, timedelta
import pandas as pd

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# MongoDB connection
client = MongoClient(os.getenv('MONGODB_URI', 'mongodb://localhost:27017/'))
db = client[os.getenv('MONGODB_DATABASE', 'trading_bot')]
collection = db[os.getenv('MONGODB_COLLECTION', 'orders')]

def query_profit_taking_events():
    """Query all profit taking events"""
    print("🎯 PROFIT TAKING EVENTS")
    print("=" * 40)
    
    profit_takes = list(collection.find({
        "type": "trade_close",
        "exit_reason": "TAKE_PROFIT"
    }).sort("timestamp", -1))
    
    if not profit_takes:
        print("No profit taking events found")
        return
    
    total_profit = sum(trade['profit_pct'] for trade in profit_takes)
    avg_profit = total_profit / len(profit_takes)
    
    print(f"Total Profit Takes: {len(profit_takes)}")
    print(f"Average Profit: {avg_profit:.2f}%")
    print(f"Total Profit: {total_profit:.2f}%")
    print(f"Best Profit Take: {max(trade['profit_pct'] for trade in profit_takes):.2f}%")
    
    print("\nRecent Profit Takes:")
    for i, trade in enumerate(profit_takes[:5], 1):
        print(f"{i}. {trade['position_type']} - {trade['profit_pct']:.2f}% profit")
        print(f"   Entry: {trade['entry_price']:.4f} → Exit: {trade['exit_price']:.4f}")
        print(f"   Time: {trade['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
        if 'trade_duration_minutes' in trade:
            print(f"   Duration: {trade['trade_duration_minutes']:.1f} minutes")
        print()

def query_stop_loss_events():
    """Query all stop loss events"""
    print("\n🛑 STOP LOSS EVENTS")
    print("=" * 40)
    
    stop_losses = list(collection.find({
        "type": "trade_close",
        "exit_reason": "STOP_LOSS"
    }).sort("timestamp", -1))
    
    if not stop_losses:
        print("No stop loss events found")
        return
    
    total_loss = sum(trade['profit_pct'] for trade in stop_losses)
    avg_loss = total_loss / len(stop_losses)
    
    print(f"Total Stop Losses: {len(stop_losses)}")
    print(f"Average Loss: {avg_loss:.2f}%")
    print(f"Total Loss: {total_loss:.2f}%")
    print(f"Worst Stop Loss: {min(trade['profit_pct'] for trade in stop_losses):.2f}%")
    
    print("\nRecent Stop Losses:")
    for i, trade in enumerate(stop_losses[:5], 1):
        print(f"{i}. {trade['position_type']} - {trade['profit_pct']:.2f}% loss")
        print(f"   Entry: {trade['entry_price']:.4f} → Exit: {trade['exit_price']:.4f}")
        print(f"   Time: {trade['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
        if 'trade_duration_minutes' in trade:
            print(f"   Duration: {trade['trade_duration_minutes']:.1f} minutes")
        print()

def query_by_position_type(position_type="LONG"):
    """Query trades by position type (LONG or SHORT)"""
    print(f"\n📊 {position_type} POSITION ANALYSIS")
    print("=" * 40)
    
    trades = list(collection.find({
        "type": "trade_close",
        "position_type": position_type
    }).sort("timestamp", -1))
    
    if not trades:
        print(f"No {position_type} trades found")
        return
    
    profit_takes = [t for t in trades if t['exit_reason'] == 'TAKE_PROFIT']
    stop_losses = [t for t in trades if t['exit_reason'] == 'STOP_LOSS']
    
    print(f"Total {position_type} Trades: {len(trades)}")
    print(f"Profit Takes: {len(profit_takes)} ({len(profit_takes)/len(trades)*100:.1f}%)")
    print(f"Stop Losses: {len(stop_losses)} ({len(stop_losses)/len(trades)*100:.1f}%)")
    
    if trades:
        avg_profit = sum(t['profit_pct'] for t in trades) / len(trades)
        print(f"Average {position_type} Profit/Loss: {avg_profit:.2f}%")

def query_trades_by_timeframe(hours=24):
    """Query trades within a specific timeframe"""
    print(f"\n⏰ TRADES IN LAST {hours} HOURS")
    print("=" * 40)
    
    from_time = datetime.now(timezone.utc) - timedelta(hours=hours)
    
    trades = list(collection.find({
        "type": "trade_close",
        "timestamp": {"$gte": from_time}
    }).sort("timestamp", -1))
    
    if not trades:
        print(f"No trades found in last {hours} hours")
        return
    
    profit_count = len([t for t in trades if t['profit_pct'] > 0])
    loss_count = len([t for t in trades if t['profit_pct'] < 0])
    
    print(f"Total Trades: {len(trades)}")
    print(f"Profitable: {profit_count} ({profit_count/len(trades)*100:.1f}%)")
    print(f"Losing: {loss_count} ({loss_count/len(trades)*100:.1f}%)")
    
    if trades:
        total_pnl = sum(t['profit_pct'] for t in trades)
        print(f"Net P&L: {total_pnl:.2f}%")

def query_performance_metrics():
    """Calculate comprehensive performance metrics"""
    print("\n📈 PERFORMANCE METRICS")
    print("=" * 40)
    
    # Get all trade closures
    all_trades = list(collection.find({"type": "trade_close"}))
    
    if not all_trades:
        print("No trade data found")
        return
    
    # Basic metrics
    total_trades = len(all_trades)
    winning_trades = len([t for t in all_trades if t['profit_pct'] > 0])
    losing_trades = len([t for t in all_trades if t['profit_pct'] < 0])
    
    win_rate = winning_trades / total_trades * 100 if total_trades > 0 else 0
    
    # Profit/Loss metrics
    total_profit = sum(t['profit_pct'] for t in all_trades if t['profit_pct'] > 0)
    total_loss = sum(t['profit_pct'] for t in all_trades if t['profit_pct'] < 0)
    net_pnl = total_profit + total_loss
    
    avg_win = total_profit / winning_trades if winning_trades > 0 else 0
    avg_loss = total_loss / losing_trades if losing_trades > 0 else 0
    
    # Risk metrics
    profit_factor = abs(total_profit / total_loss) if total_loss != 0 else float('inf')
    risk_reward = abs(avg_win / avg_loss) if avg_loss != 0 else float('inf')
    
    print(f"Total Trades: {total_trades}")
    print(f"Win Rate: {win_rate:.1f}%")
    print(f"Net P&L: {net_pnl:.2f}%")
    print(f"Average Win: {avg_win:.2f}%")
    print(f"Average Loss: {avg_loss:.2f}%")
    print(f"Profit Factor: {profit_factor:.2f}")
    print(f"Risk/Reward Ratio: 1:{risk_reward:.2f}")
    
    # Trade duration analysis
    trades_with_duration = [t for t in all_trades if 'trade_duration_minutes' in t]
    if trades_with_duration:
        avg_duration = sum(t['trade_duration_minutes'] for t in trades_with_duration) / len(trades_with_duration)
        max_duration = max(t['trade_duration_minutes'] for t in trades_with_duration)
        min_duration = min(t['trade_duration_minutes'] for t in trades_with_duration)
        
        print(f"\nTrade Duration:")
        print(f"Average: {avg_duration:.1f} minutes")
        print(f"Shortest: {min_duration:.1f} minutes")
        print(f"Longest: {max_duration:.1f} minutes")

def export_detailed_analysis():
    """Export detailed analysis to CSV"""
    print("\n💾 EXPORTING DETAILED ANALYSIS")
    print("=" * 40)
    
    # Get all trade closures
    trades = list(collection.find({"type": "trade_close"}))
    
    if not trades:
        print("No trade data to export")
        return
    
    # Convert to DataFrame for easy analysis
    df_data = []
    for trade in trades:
        row = {
            'timestamp': trade['timestamp'],
            'exit_reason': trade['exit_reason'],
            'position_type': trade['position_type'],
            'profit_pct': trade['profit_pct'],
            'entry_price': trade['entry_price'],
            'exit_price': trade['exit_price'],
            'position_value': trade['position_value'],
            'trade_result': trade['trade_result'],
            'duration_minutes': trade.get('trade_duration_minutes', 0)
        }
        df_data.append(row)
    
    df = pd.DataFrame(df_data)
    
    # Save to CSV
    filename = f"detailed_trade_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    df.to_csv(filename, index=False)
    
    print(f"✅ Analysis exported to {filename}")
    print(f"📊 Total records: {len(df)}")
    
    # Show summary statistics
    print("\nSummary Statistics:")
    print(df.groupby('exit_reason')['profit_pct'].agg(['count', 'mean', 'sum']).round(2))

def query_live_bot_status():
    """Query live bot status and recent activity"""
    print("\n🤖 LIVE BOT STATUS")
    print("=" * 40)
    
    # Get the most recent bot session
    recent_session = collection.find_one({
        "type": "bot_startup"
    }, sort=[("timestamp", -1)])
    
    if not recent_session:
        print("No bot sessions found")
        return
    
    session_id = recent_session['session_id']
    startup_time = recent_session['timestamp']
    
    print(f"Active Session: {session_id}")
    print(f"Started: {startup_time.strftime('%Y-%m-%d %H:%M:%S')} UTC")
    
    # Calculate running time with timezone awareness
    if startup_time.tzinfo is None:
        startup_time = startup_time.replace(tzinfo=timezone.utc)
    
    running_time = (datetime.now(timezone.utc) - startup_time).total_seconds() / 60
    print(f"Running for: {running_time:.1f} minutes")
    
    # Check for recent orders (last 5 minutes)
    recent_time = datetime.now(timezone.utc) - timedelta(minutes=5)
    recent_orders = list(collection.find({
        "session_id": session_id,
        "type": "trading_order",
        "timestamp": {"$gte": recent_time}
    }).sort("timestamp", -1))
    
    if recent_orders:
        print(f"\nRecent Orders (last 5 minutes): {len(recent_orders)}")
        for order in recent_orders[:3]:
            status = "✅" if order.get('success') else "❌"
            side = order['order_data']['side']
            qty = order['order_data']['quantity']
            price = order['current_price']
            print(f"  {status} {side} {qty} at {price:.4f}")
    else:
        print("\nNo recent orders (last 5 minutes)")
    
    # Check for recent position changes
    recent_positions = list(collection.find({
        "session_id": session_id,
        "type": "position_change",
        "timestamp": {"$gte": recent_time}
    }).sort("timestamp", -1))
    
    if recent_positions:
        print(f"\nRecent Position Changes: {len(recent_positions)}")
        for pos in recent_positions[:3]:
            action = pos['action']
            reason = pos.get('reason', '')
            print(f"  📊 {action}: {reason}")

def query_current_session_stats():
    """Query statistics for the current bot session"""
    print("\n📊 CURRENT SESSION STATS")
    print("=" * 40)
    
    # Get the most recent bot session
    recent_session = collection.find_one({
        "type": "bot_startup"
    }, sort=[("timestamp", -1)])
    
    if not recent_session:
        print("No active bot sessions found")
        return
    
    session_id = recent_session['session_id']
    
    # Count orders in this session
    session_orders = list(collection.find({
        "session_id": session_id,
        "type": "trading_order",
        "success": True
    }))
    
    # Count trades in this session
    session_trades = list(collection.find({
        "session_id": session_id,
        "type": "trade_close"
    }))
    
    buy_orders = len([o for o in session_orders if o['order_data']['side'] == 'BUY'])
    sell_orders = len([o for o in session_orders if o['order_data']['side'] == 'SELL'])
    
    print(f"Session Orders: {len(session_orders)} (Buy: {buy_orders}, Sell: {sell_orders})")
    print(f"Session Trades Closed: {len(session_trades)}")
    
    if session_trades:
        profitable_trades = len([t for t in session_trades if t['profit_pct'] > 0])
        session_pnl = sum(t['profit_pct'] for t in session_trades)
        print(f"Session Win Rate: {profitable_trades}/{len(session_trades)} ({profitable_trades/len(session_trades)*100:.1f}%)")
        print(f"Session P&L: {session_pnl:.2f}%")

# Example usage
if __name__ == "__main__":
    import time
    import os
    
    # Monitoring settings
    refresh_interval = int(os.getenv('MONITOR_REFRESH_INTERVAL', '30'))  # seconds
    
    print("🔍 MONGODB TRADE CLOSURE MONITORING")
    print("=" * 50)
    print(f"📊 Refreshing every {refresh_interval} seconds")
    print("Press Ctrl+C to stop monitoring")
    print()
    
    try:
        while True:
            # Clear screen (works on both Windows and Unix)
            if os.name == 'nt':  # Windows
                os.system('cls')
            else:  # Unix/Linux/MacOS
                os.system('clear')
            
            print(f"🔍 MONGODB TRADE CLOSURE ANALYSIS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("=" * 70)
            
            try:                # Run live status functions first
                query_live_bot_status()
                query_current_session_stats()
                
                # Run all analysis functions
                query_profit_taking_events()
                query_stop_loss_events()
                query_by_position_type("LONG")
                query_by_position_type("SHORT")
                query_trades_by_timeframe(24)  # Last 24 hours
                query_performance_metrics()
                
                print(f"\n🔄 Next update in {refresh_interval} seconds... (Press Ctrl+C to stop)")
                
            except Exception as e:
                print(f"❌ Error running analysis: {e}")
                print(f"🔄 Retrying in {refresh_interval} seconds...")
            
            # Wait before next refresh
            time.sleep(refresh_interval)
            
    except KeyboardInterrupt:
        print("\n\n⏹️ Monitoring stopped by user")
        
        # Optionally export final detailed analysis
        try:
            print("\n💾 Generating final detailed analysis...")
            export_detailed_analysis()
        except Exception as e:
            print(f"Error exporting final analysis: {e}")
            
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    finally:
        client.close()
        print("🔌 MongoDB connection closed")