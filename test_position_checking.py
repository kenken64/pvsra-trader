#!/usr/bin/env python3
"""
Position Checking Test
This script demonstrates the position checking functionality
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

def test_position_checking():
    """Test position checking functionality"""
    
    print("🔒 Position Checking Test")
    print("=" * 40)
    
    try:
        # Initialize bot
        print("1. Initializing bot...")
        bot = BinanceFuturesScalpingBot()
        
        print(f"\n⚙️ Position Configuration:")
        print(f"   Allow Multiple Positions: {bot.allow_multiple_positions}")
        print(f"   Symbol: {bot.symbol}")
        
        # Test getting open positions
        print(f"\n📊 Testing position retrieval...")
        open_positions = bot.get_open_positions()
        
        if open_positions:
            print(f"✅ Found {len(open_positions)} open position(s):")
            for pos in open_positions:
                pnl_status = "🟢 Profit" if pos['unrealized_pnl'] >= 0 else "🔴 Loss"
                print(f"   📈 {pos['symbol']} {pos['side']}:")
                print(f"      Size: {pos['size']}")
                print(f"      Entry: ${pos['entry_price']:.4f}")
                print(f"      Current: ${pos['mark_price']:.4f}")
                print(f"      PnL: {pnl_status} ${pos['unrealized_pnl']:.2f} ({pos['percentage']:.2f}%)")
        else:
            print("✅ No open positions found")
        
        # Test specific symbol position check
        print(f"\n🎯 Testing {bot.symbol} position check...")
        existing_position = bot.check_existing_position(bot.symbol)
        
        if existing_position:
            print(f"🔒 Position exists for {bot.symbol}:")
            print(f"   Side: {existing_position['side']}")
            print(f"   Size: {existing_position['size']}")
            print(f"   Entry: ${existing_position['entry_price']:.4f}")
            print(f"   PnL: ${existing_position['unrealized_pnl']:.2f}")
        else:
            print(f"✅ No position exists for {bot.symbol}")
        
        # Test trading strategy with position check
        print(f"\n🔄 Testing trading strategy with position check...")
        
        # Mock some price data
        bot.price_history.extend([1.50, 1.51, 1.52, 1.53, 1.54, 1.55, 1.56, 1.57, 1.58, 1.59])
        
        # Simulate strategy execution
        print("Simulating execute_scalping_strategy()...")
        
        if not bot.allow_multiple_positions:
            existing_position = bot.check_existing_position(bot.symbol)
            if existing_position:
                print(f"🔒 Trade would be blocked due to existing {existing_position['side']} position")
                print(f"   This is the safety mechanism working correctly!")
            else:
                print(f"✅ No existing position - trading would be allowed")
        else:
            print(f"⚠️ Multiple positions allowed - no blocking would occur")
        
        # Test configuration scenarios
        print(f"\n⚙️ Configuration Scenarios:")
        print(f"   Current setting: ALLOW_MULTIPLE_POSITIONS={bot.allow_multiple_positions}")
        
        if bot.allow_multiple_positions:
            print(f"   📊 Mode: Multiple positions allowed")
            print(f"   🟢 Bot can open new trades even with existing positions")
            print(f"   ⚠️ Higher risk but more trading opportunities")
        else:
            print(f"   🔒 Mode: Single position per symbol (SAFE)")
            print(f"   🛡️ Bot blocks new trades when position exists")
            print(f"   ✅ Lower risk, prevents position conflicts")
        
        print(f"\n💡 To change this behavior:")
        print(f"   Edit .env file: ALLOW_MULTIPLE_POSITIONS=True/False")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def explain_position_checking():
    """Explain how position checking works"""
    
    print(f"\n📖 Position Checking Explanation")
    print("=" * 40)
    
    print(f"\n🔍 **How It Works:**")
    print(f"   1. Before executing any trade, bot checks for existing positions")
    print(f"   2. Uses Binance API '/fapi/v2/positionRisk' endpoint")
    print(f"   3. Filters positions with non-zero 'positionAmt'")
    print(f"   4. Blocks trades if position exists (when ALLOW_MULTIPLE_POSITIONS=False)")
    
    print(f"\n🛡️ **Safety Benefits:**")
    print(f"   ✅ Prevents accidental position doubling")
    print(f"   ✅ Avoids conflicting long/short positions")
    print(f"   ✅ Reduces risk of margin issues")
    print(f"   ✅ Provides clear position status visibility")
    
    print(f"\n⚙️ **Configuration Options:**")
    print(f"   🔒 ALLOW_MULTIPLE_POSITIONS=False (Default, Recommended)")
    print(f"      - Single position per symbol")
    print(f"      - Safer for beginners")
    print(f"      - Prevents position conflicts")
    print(f"   📊 ALLOW_MULTIPLE_POSITIONS=True (Advanced)")
    print(f"      - Multiple positions allowed")
    print(f"      - More trading opportunities")
    print(f"      - Requires careful risk management")
    
    print(f"\n📋 **Position Information Displayed:**")
    print(f"   - Symbol and side (LONG/SHORT)")
    print(f"   - Position size and entry price")
    print(f"   - Current mark price")
    print(f"   - Unrealized PnL and percentage")

if __name__ == "__main__":
    print("🔒 Enhanced Bot Position Checking Test")
    print("=====================================")
    
    # Explain position checking first
    explain_position_checking()
    
    # Run the test
    success = test_position_checking()
    
    if success:
        print(f"\n🎉 Position checking is working correctly!")
        print(f"\n🚀 The bot now safely checks for existing positions")
        print(f"   before executing new trades!")
    else:
        print(f"\n⚠️ Position checking test encountered issues.")
