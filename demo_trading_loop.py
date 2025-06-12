#!/usr/bin/env python3
"""
Bot Trading Loop Demonstration
This script shows how the bot continuously monitors for trading signals
"""

import os
import sys
import time
from datetime import datetime
import logging

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot import BinanceFuturesScalpingBot

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def demonstrate_trading_loop():
    """Demonstrate how the bot's trading loop works"""
    
    print("🔄 Bot Trading Loop Demonstration")
    print("=" * 50)
    
    try:
        # Initialize bot
        print("1. Initializing bot...")
        bot = BinanceFuturesScalpingBot()
        
        print(f"\n⚙️ Bot Configuration:")
        print(f"   Symbol: {bot.symbol}")
        print(f"   Price Update Interval: {bot.price_update_interval} seconds")
        print(f"   Trade Cooldown: {bot.trade_cooldown} seconds")
        print(f"   PVSRA Enabled: {bot.use_pvsra}")
        
        # Simulate the trading loop for demonstration
        print(f"\n🔄 Starting Trading Loop Simulation...")
        print("   (This will run for 30 seconds to show the loop behavior)")
        print("   Press Ctrl+C to stop early")
        
        # Add some mock price data
        mock_prices = [1.50, 1.51, 1.52, 1.53, 1.54, 1.55]
        bot.price_history.extend(mock_prices)
        
        bot.running = True
        loop_count = 0
        max_loops = 15  # Run for about 30 seconds (15 * 2s)
        
        print(f"\n📊 Loop Activity:")
        print("-" * 40)
        
        start_time = time.time()
        
        while bot.running and loop_count < max_loops:
            loop_count += 1
            current_time = datetime.now().strftime("%H:%M:%S")
            
            print(f"\n🔍 Loop #{loop_count} at {current_time}")
            
            try:
                # This is what the bot does every cycle:
                
                # 1. Get current price (simulated)
                simulated_price = 1.50 + (loop_count * 0.001)  # Simulate slight price movement
                print(f"   📈 Current Price: ${simulated_price:.4f}")
                
                # 2. Add to price history
                bot.price_history.append(simulated_price)
                
                # 3. Analyze market conditions
                if len(bot.price_history) >= 10:
                    market_analysis = bot.analyze_market_conditions()
                    
                    if market_analysis.get('status') != 'error':
                        traditional = market_analysis.get('traditional_analysis', {})
                        sentiment = market_analysis.get('overall_sentiment', 'NEUTRAL')
                        
                        print(f"   🧠 Market Analysis:")
                        print(f"      Signal: {traditional.get('signal', 'N/A')}")
                        print(f"      Strength: {traditional.get('strength', 0):.1f}%")
                        print(f"      Sentiment: {sentiment}")
                        
                        # 4. Check for trade signals
                        if sentiment in ['BUY', 'STRONG_BUY']:
                            trade_decision = bot.should_execute_trade('BUY', traditional.get('strength', 0) / 100)
                            print(f"   🟢 BUY Signal: Execute={trade_decision.get('execute')} | Confidence={trade_decision.get('confidence', 0):.2f}")
                        elif sentiment in ['SELL', 'STRONG_SELL']:
                            trade_decision = bot.should_execute_trade('SELL', traditional.get('strength', 0) / 100)
                            print(f"   🔴 SELL Signal: Execute={trade_decision.get('execute')} | Confidence={trade_decision.get('confidence', 0):.2f}")
                        else:
                            print(f"   ⚪ No Trading Signal (Neutral market)")
                        
                        # 5. Check cooldown status
                        time_since_last_trade = time.time() - bot.last_trade_time
                        if time_since_last_trade < bot.trade_cooldown:
                            remaining_cooldown = bot.trade_cooldown - time_since_last_trade
                            print(f"   ⏰ Trade Cooldown: {remaining_cooldown:.1f}s remaining")
                        else:
                            print(f"   ✅ Ready for Trading (No cooldown)")
                    else:
                        print(f"   ❌ Market analysis error: {market_analysis.get('message')}")
                else:
                    print(f"   📊 Collecting price data... ({len(bot.price_history)}/10)")
                
                # 6. Wait for next cycle (like the real bot does)
                print(f"   💤 Sleeping for {bot.price_update_interval} seconds...")
                time.sleep(bot.price_update_interval)
                
            except KeyboardInterrupt:
                print(f"\n🛑 Loop interrupted by user")
                break
            except Exception as e:
                print(f"   ❌ Error in loop: {e}")
        
        end_time = time.time()
        elapsed = end_time - start_time
        
        print(f"\n📊 Loop Summary:")
        print(f"   Loops Completed: {loop_count}")
        print(f"   Total Runtime: {elapsed:.1f} seconds")
        print(f"   Average Loop Time: {elapsed/loop_count:.1f} seconds")
        
        print(f"\n✅ Trading Loop Demonstration Complete!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Demonstration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def show_loop_explanation():
    """Explain how the bot trading loop works"""
    
    print(f"\n📖 How the Bot Trading Loop Works")
    print("=" * 40)
    
    print(f"\n🔄 **Continuous Loop Process:**")
    print(f"   1. 📊 Fetch current market price")
    print(f"   2. 📈 Update price history")
    print(f"   3. 🧠 Analyze market conditions:")
    print(f"      - Traditional price/momentum analysis")
    print(f"      - PVSRA analysis (if enabled)")
    print(f"      - Combine signals for overall sentiment")
    print(f"   4. 🎯 Evaluate trading signals:")
    print(f"      - BUY signals: Look for upward momentum")
    print(f"      - SELL signals: Look for downward momentum")
    print(f"      - Apply confidence thresholds")
    print(f"   5. ⚖️ Make trade decisions:")
    print(f"      - Check cooldown period")
    print(f"      - Validate signal strength")
    print(f"      - Execute trades if conditions met")
    print(f"   6. 💤 Sleep for configured interval")
    print(f"   7. 🔁 Repeat indefinitely")
    
    print(f"\n⚙️ **Key Parameters:**")
    print(f"   - **Loop Interval**: 2 seconds (configurable)")
    print(f"   - **Trade Cooldown**: 30 seconds between trades")
    print(f"   - **Signal Threshold**: 60% confidence minimum")
    print(f"   - **Price History**: Last 50 prices for analysis")
    
    print(f"\n🎯 **Signal Detection:**")
    print(f"   - **Traditional**: Price change & momentum analysis")
    print(f"   - **PVSRA**: Volume, support/resistance analysis")
    print(f"   - **Combined**: Weighted signal combination")
    
    print(f"\n🛡️ **Risk Management:**")
    print(f"   - Cooldown prevents over-trading")
    print(f"   - Confidence scoring filters weak signals")
    print(f"   - Position sizing based on available balance")
    print(f"   - Stop-loss and take-profit thresholds")

if __name__ == "__main__":
    print("🤖 Enhanced Bot Trading Loop Analysis")
    print("====================================")
    
    # Show explanation first
    show_loop_explanation()
    
    # Ask user if they want to see live demonstration
    print(f"\n❓ Would you like to see a live demonstration?")
    print("   This will show the actual loop behavior for 30 seconds.")
    
    try:
        response = input("   Run demonstration? (y/n): ").lower().strip()
        
        if response in ['y', 'yes']:
            success = demonstrate_trading_loop()
            
            if success:
                print(f"\n🎯 **Summary**: The bot runs in a continuous loop,")
                print(f"   checking for trading signals every {os.getenv('PRICE_UPDATE_INTERVAL', '2')} seconds")
                print(f"   and executing trades when conditions are met!")
        else:
            print(f"\n👍 Demonstration skipped. The bot loop explanation above")
            print(f"   shows exactly how it works in continuous operation.")
            
    except KeyboardInterrupt:
        print(f"\n👋 Demonstration cancelled by user")
    except Exception as e:
        print(f"\n⚠️ Input error: {e}")
    
    print(f"\n🚀 To start the actual bot trading loop:")
    print(f"   python bot.py")
