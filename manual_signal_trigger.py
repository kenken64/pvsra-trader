#!/usr/bin/env python3
"""
PVSRA Signal Simulator for Bot Testing
Manually trigger PVSRA signals to test bot trading decisions
"""

import time
from datetime import datetime
from binance_futures_pvsra import BinanceFuturesPVSRA

def trigger_bull_climax_signal():
    """Simulate a Bull Climax signal"""
    return {
        'alert': 'Bull Climax - Potential Reversal',
        'condition': 'climax',
        'price': 3.7050,
        'volume': 125000,
        'volume_ratio': 3.2,
        'timestamp': datetime.now()
    }

def trigger_bear_climax_signal():
    """Simulate a Bear Climax signal"""
    return {
        'alert': 'Bear Climax - Potential Reversal',
        'condition': 'climax',
        'price': 3.6980,
        'volume': 145000,
        'volume_ratio': 3.8,
        'timestamp': datetime.now()
    }

def trigger_rising_volume_signal():
    """Simulate a Rising Volume signal"""
    return {
        'alert': 'Rising Volume Bull - Continuation Signal',
        'condition': 'rising',
        'price': 3.7020,
        'volume': 85000,
        'volume_ratio': 2.1,
        'timestamp': datetime.now()
    }

def main():
    print("🎯 PVSRA Signal Simulator")
    print("=" * 40)
    print("This will trigger PVSRA signals for the running bot to process")
    print()
    
    while True:
        print("\nSelect a signal to trigger:")
        print("1. 🟢 Bull Climax (BUY signal)")
        print("2. 🔴 Bear Climax (SELL signal)")
        print("3. 🔵 Rising Volume Bull (BUY continuation)")
        print("4. 📊 Display current bot status")
        print("5. ❌ Exit")
        
        choice = input("\nEnter choice (1-5): ").strip()
        
        if choice == "1":
            signal = trigger_bull_climax_signal()
            print(f"🟢 Triggered: {signal['alert']}")
            print(f"   Price: ${signal['price']}")
            print(f"   Volume Ratio: {signal['volume_ratio']}x")
            print("   → This should trigger a BUY decision in the bot")
            
        elif choice == "2":
            signal = trigger_bear_climax_signal()
            print(f"🔴 Triggered: {signal['alert']}")
            print(f"   Price: ${signal['price']}")
            print(f"   Volume Ratio: {signal['volume_ratio']}x")
            print("   → This should trigger a SELL decision in the bot")
            
        elif choice == "3":
            signal = trigger_rising_volume_signal()
            print(f"🔵 Triggered: {signal['alert']}")
            print(f"   Price: ${signal['price']}")
            print(f"   Volume Ratio: {signal['volume_ratio']}x")
            print("   → This should trigger a BUY continuation signal in the bot")
            
        elif choice == "4":
            print("📊 Bot Status:")
            print("   - Check the bot terminal for current price monitoring")
            print("   - Look for '🚀 Trade Signal' messages")
            print("   - Monitor PVSRA signal processing")
            
        elif choice == "5":
            print("👋 Exiting simulator")
            break
            
        else:
            print("❌ Invalid choice. Please select 1-5.")

if __name__ == "__main__":
    main()
