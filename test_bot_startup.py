#!/usr/bin/env python3
"""
Quick Bot Startup Test
Tests that the enhanced bot starts correctly
"""

import os
import sys
import time
import threading
from datetime import datetime

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot import BinanceFuturesScalpingBot

def test_bot_startup():
    """Test bot startup process"""
    
    print("🧪 Testing Enhanced Bot Startup")
    print("=" * 40)
    
    try:
        # Initialize bot
        print("1. Initializing bot...")
        bot = BinanceFuturesScalpingBot()
        
        # Test startup method (but don't run the loop)
        print("2. Testing startup display...")
        
        # Simulate startup without running the trading loop
        original_run_method = bot.run_trading_loop
        
        def mock_run_loop():
            print("   🔄 Trading loop would start here...")
            print("   ⏹️  Stopping for test purposes")
            return
        
        bot.run_trading_loop = mock_run_loop
        
        # Test start method
        bot.start()
        
        print("\n✅ Bot startup test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Bot startup test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_bot_startup()
    
    if success:
        print("\n🎉 Enhanced bot is ready for trading!")
        print("📝 Use 'python bot.py' to start full trading")
    else:
        print("\n⚠️ Bot startup issues detected")
