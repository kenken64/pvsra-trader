#!/usr/bin/env python3
"""
Enhanced Bot Demonstration
This script demonstrates the enhanced bot capabilities with PVSRA integration
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

def demonstrate_enhanced_features():
    """Demonstrate the enhanced bot features"""
    
    print("\n🚀 Enhanced Binance Futures Scalping Bot Demo")
    print("=" * 60)
    
    try:
        # Initialize the enhanced bot
        print("Initializing enhanced bot...")
        bot = BinanceFuturesScalpingBot()
        
        print("\n📊 Bot Configuration Summary:")
        print("-" * 40)
        print(f"Symbol: {bot.symbol}")
        print(f"Test Mode: {bot.test_mode}")
        print(f"Trading Mode: {'Percentage' if bot.use_percentage_trading else 'Fixed'}")
        
        if bot.use_percentage_trading:
            print(f"Trade Amount: {bot.trade_amount_percentage}% of balance")
        else:
            print(f"Trade Amount: {bot.trade_amount} USDT")
        
        print(f"PVSRA Analysis: {'✅ ENABLED' if bot.use_pvsra else '❌ DISABLED'}")
        print(f"Leverage: {bot.leverage}x")
        
        print("\n💰 Account Information:")
        print("-" * 30)
        
        # Get and display account balance
        balance = bot.get_account_balance()
        print(f"Available Balance: {balance:.2f} USDT")
        
        if bot.use_percentage_trading and balance > 0:
            trade_amount = balance * (bot.trade_amount_percentage / 100)
            print(f"Current Trade Amount: {trade_amount:.2f} USDT")
        
        # Display all balances
        print("\n💰 Full Account Summary:")
        bot.display_account_summary()
        
        print("\n🔮 PVSRA Features:")
        print("-" * 25)
        if bot.use_pvsra:
            print(f"✅ PVSRA Weight: {bot.pvsra_weight}")
            print(f"✅ Require Confirmation: {bot.require_pvsra_confirmation}")
            print(f"✅ Lookback Period: {bot.pvsra_lookback}")
            print(f"✅ Climax Multiplier: {bot.pvsra_climax_multiplier}")
            
            # Test PVSRA signal evaluation
            buy_signal = bot.evaluate_pvsra_signal('BUY')
            sell_signal = bot.evaluate_pvsra_signal('SELL')
            
            print(f"\n📈 Sample BUY Signal Evaluation:")
            print(f"   Support: {buy_signal.get('pvsra_support', 'N/A')}")
            print(f"   Confidence: {buy_signal.get('confidence', 'N/A')}")
            print(f"   Message: {buy_signal.get('message', 'N/A')}")
            
            print(f"\n📉 Sample SELL Signal Evaluation:")
            print(f"   Support: {sell_signal.get('pvsra_support', 'N/A')}")
            print(f"   Confidence: {sell_signal.get('confidence', 'N/A')}")
            print(f"   Message: {sell_signal.get('message', 'N/A')}")
        else:
            print("❌ PVSRA analysis is disabled")
            print("   Reason: Missing binance_futures_pvsra.py module")
            print("   Bot will use traditional price-based signals only")
        
        print("\n🔄 Trading Logic Demo:")
        print("-" * 25)
        
        # Add some sample price data
        sample_prices = [1.50, 1.51, 1.52, 1.53, 1.54, 1.55, 1.56, 1.57, 1.58, 1.59]
        bot.price_history.extend(sample_prices)
        
        # Demonstrate market analysis
        market_analysis = bot.analyze_market_conditions()
        
        if market_analysis.get('status') != 'error':
            print(f"✅ Market Analysis Working:")
            print(f"   Overall Sentiment: {market_analysis.get('overall_sentiment', 'N/A')}")
            
            traditional = market_analysis.get('traditional_analysis', {})
            print(f"   Traditional Signal: {traditional.get('signal', 'N/A')}")
            print(f"   Traditional Strength: {traditional.get('strength', 0):.1f}%")
            
            pvsra = market_analysis.get('pvsra_analysis', {})
            if pvsra:
                print(f"   PVSRA Signal: {pvsra.get('signal', 'N/A')}")
                print(f"   PVSRA Strength: {pvsra.get('strength', 0):.1f}%")
        
        # Test trade decision logic
        print(f"\n🎯 Trade Decision Demo:")
        for action in ['BUY', 'SELL']:
            decision = bot.should_execute_trade(action, 0.75)
            print(f"   {action} Decision:")
            print(f"      Execute: {decision.get('execute', 'N/A')}")
            print(f"      Confidence: {decision.get('confidence', 'N/A'):.3f}")
            print(f"      Reason: {decision.get('reason', 'N/A')}")
        
        print("\n✅ Demo Complete!")
        print("=" * 60)
        print("\n💡 Key Enhancements:")
        print("  🔮 PVSRA signal integration for sophisticated market analysis")
        print("  💰 Percentage-based trading amounts")
        print("  📊 Enhanced balance monitoring with non-zero display")
        print("  🎯 Intelligent trade decision combining multiple signals")
        print("  📈 Comprehensive market condition analysis")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def show_pvsra_setup_guide():
    """Show guide for setting up PVSRA"""
    print("\n📖 PVSRA Setup Guide")
    print("=" * 30)
    print("\nTo enable full PVSRA functionality:")
    print("1. Ensure you have the binance_futures_pvsra.py module")
    print("2. Install required dependencies:")
    print("   pip install pandas numpy python-binance websocket-client")
    print("3. Configure PVSRA settings in .env file:")
    print("   USE_PVSRA=True")
    print("   PVSRA_WEIGHT=0.7")
    print("   REQUIRE_PVSRA_CONFIRMATION=False")
    print("\n4. The bot will automatically detect and enable PVSRA features")

if __name__ == "__main__":
    print("🤖 Enhanced Binance Futures Scalping Bot")
    print("========================================")
    
    # Run demonstration
    success = demonstrate_enhanced_features()
    
    if success:
        # Show PVSRA setup guide
        show_pvsra_setup_guide()
        
        print("\n🎯 Ready to Trade!")
        print("To start the bot: python bot.py")
    else:
        print("\n⚠️ Demo encountered issues. Please check the configuration.")
