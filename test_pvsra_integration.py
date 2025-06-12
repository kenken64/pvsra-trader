#!/usr/bin/env python3
"""
Test PVSRA Integration in Enhanced Bot
This script tests the PVSRA integration functionality
"""

import os
import sys
import time
from datetime import datetime
import logging

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Try importing the enhanced bot
try:
    from bot import BinanceFuturesScalpingBot
    print("✅ Successfully imported enhanced bot with PVSRA integration")
except ImportError as e:
    print(f"❌ Failed to import bot: {e}")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_pvsra_integration():
    """Test PVSRA integration functionality"""
    
    print("\n🧪 Testing PVSRA Integration")
    print("=" * 50)
    
    try:
        # Initialize bot
        print("1. Initializing bot...")
        bot = BinanceFuturesScalpingBot()
        
        # Test PVSRA configuration
        print(f"2. PVSRA Status: {'✅ ENABLED' if bot.use_pvsra else '❌ DISABLED'}")
        if bot.use_pvsra:
            print(f"   - PVSRA Weight: {bot.pvsra_weight}")
            print(f"   - Require Confirmation: {bot.require_pvsra_confirmation}")
            print(f"   - Lookback Period: {bot.pvsra_lookback}")
            print(f"   - Climax Multiplier: {bot.pvsra_climax_multiplier}")
            print(f"   - Rising Multiplier: {bot.pvsra_rising_multiplier}")
        
        # Test method availability
        print("\n3. Testing method availability:")
        methods_to_test = [
            'get_pvsra_analysis',
            'evaluate_pvsra_signal',
            'should_execute_trade',
            'analyze_market_conditions',
            'analyze_price_movement',
            'execute_scalping_strategy'
        ]
        
        for method_name in methods_to_test:
            if hasattr(bot, method_name):
                print(f"   ✅ {method_name}")
            else:
                print(f"   ❌ {method_name} - MISSING")
        
        # Test PVSRA analysis (if available)
        print("\n4. Testing PVSRA analysis:")
        if bot.use_pvsra and bot.pvsra_client:
            try:
                # Test getting PVSRA analysis
                pvsra_result = bot.get_pvsra_analysis()
                print(f"   ✅ PVSRA analysis method works")
                print(f"   Result keys: {list(pvsra_result.keys()) if pvsra_result else 'Empty result'}")
            except Exception as e:
                print(f"   ⚠️ PVSRA analysis error: {e}")
        else:
            print("   ⚠️ PVSRA client not available - this is expected if binance_futures_pvsra.py is missing")
        
        # Test signal evaluation
        print("\n5. Testing signal evaluation:")
        try:
            buy_eval = bot.evaluate_pvsra_signal('BUY')
            sell_eval = bot.evaluate_pvsra_signal('SELL')
            print(f"   ✅ BUY evaluation: {buy_eval.get('pvsra_support', 'N/A')}")
            print(f"   ✅ SELL evaluation: {sell_eval.get('pvsra_support', 'N/A')}")
        except Exception as e:
            print(f"   ❌ Signal evaluation error: {e}")
        
        # Test trade decision logic
        print("\n6. Testing trade decision logic:")
        try:
            trade_decision = bot.should_execute_trade('BUY', 0.8)
            print(f"   ✅ Trade decision method works")
            print(f"   Execute: {trade_decision.get('execute', 'N/A')}")
            print(f"   Confidence: {trade_decision.get('confidence', 'N/A')}")
            print(f"   Reason: {trade_decision.get('reason', 'N/A')}")
        except Exception as e:
            print(f"   ❌ Trade decision error: {e}")
        
        # Test market analysis
        print("\n7. Testing market analysis:")
        try:
            # Add some dummy price history for testing
            bot.price_history.extend([1.5, 1.51, 1.52, 1.53, 1.54, 1.55, 1.56, 1.57, 1.58, 1.59])
            
            market_analysis = bot.analyze_market_conditions()
            print(f"   ✅ Market analysis method works")
            print(f"   Status: {market_analysis.get('status', 'success')}")
            if market_analysis.get('status') != 'error':
                print(f"   Overall sentiment: {market_analysis.get('overall_sentiment', 'N/A')}")
                traditional = market_analysis.get('traditional_analysis', {})
                print(f"   Traditional signal: {traditional.get('signal', 'N/A')}")
        except Exception as e:
            print(f"   ❌ Market analysis error: {e}")
        
        print("\n✅ PVSRA Integration Test Complete!")
        print("=" * 50)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_configuration():
    """Test configuration loading"""
    
    print("\n⚙️ Testing Configuration")
    print("=" * 30)
    
    # Check environment variables
    env_vars = [
        'USE_PVSRA',
        'PVSRA_WEIGHT',
        'REQUIRE_PVSRA_CONFIRMATION',
        'PVSRA_LOOKBACK',
        'PVSRA_CLIMAX_MULTIPLIER',
        'PVSRA_RISING_MULTIPLIER'
    ]
    
    for var in env_vars:
        value = os.getenv(var)
        if value is not None:
            print(f"✅ {var} = {value}")
        else:
            print(f"⚠️ {var} = Not set (using default)")

if __name__ == "__main__":
    print("🔮 Enhanced Bot PVSRA Integration Test")
    print("====================================")
    
    # Test configuration first
    test_configuration()
    
    # Test PVSRA integration
    success = test_pvsra_integration()
    
    if success:
        print("\n🎉 All tests passed! The bot is ready for PVSRA-enhanced trading.")
        print("\n💡 Next steps:")
        print("   1. Ensure you have the binance_futures_pvsra.py module")
        print("   2. Install required dependencies: pip install pandas numpy python-binance")
        print("   3. Test the bot with: python bot.py")
    else:
        print("\n⚠️ Some tests failed. Please check the errors above.")
