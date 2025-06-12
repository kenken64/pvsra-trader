#!/usr/bin/env python3
"""
PVSRA Signal Simulator & Trade Executor
Allows manual simulation of PVSRA signals to test bot trading functionality
"""

import os
import sys
import time
import json
import requests
from datetime import datetime, timezone
from typing import Dict, List, Optional
import logging

# Try to load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Import PVSRA modules
try:
    from binance_futures_pvsra import BinanceFuturesPVSRA
    from bot_pvsra_integrated import EnhancedBinanceFuturesBot
    MODULES_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Required modules not available: {e}")
    MODULES_AVAILABLE = False

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class PVSRASignalSimulator:
    """
    Simulate PVSRA signals and trigger bot trading
    """
    
    def __init__(self):
        """Initialize the simulator"""
        if not MODULES_AVAILABLE:
            raise ImportError("Required modules not available")
        
        # Configuration
        self.api_key = os.getenv('BINANCE_API_KEY')
        self.api_secret = os.getenv('BINANCE_API_SECRET')
        self.test_mode = os.getenv('TEST_MODE', 'True').lower() == 'true'
        
        if not self.api_key or not self.api_secret:
            raise ValueError("BINANCE_API_KEY and BINANCE_API_SECRET must be set")
        
        # Initialize bot
        self.bot = None
        self.pvsra = None
        self.initialize_components()
        
        # Simulation state
        self.simulation_active = False
        self.simulated_signals = []
        
        logger.info("🎯 PVSRA Signal Simulator initialized")
    
    def initialize_components(self):
        """Initialize bot and PVSRA components"""
        try:
            # Initialize PVSRA
            self.pvsra = BinanceFuturesPVSRA(self.api_key, self.api_secret, self.test_mode)
            
            # Initialize bot
            self.bot = EnhancedBinanceFuturesBot()
            
            logger.info("✅ Components initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize components: {e}")
            raise
    
    def create_pvsra_signal(self, symbol: str, signal_type: str, price: float = None, 
                          condition: str = "climax", volume_ratio: float = 2.5) -> Dict:
        """
        Create a simulated PVSRA signal
        
        Args:
            symbol: Trading symbol (e.g., 'BTCUSDT', 'SUIUSDC')
            signal_type: 'bull_climax', 'bear_climax', 'rising_bull', 'rising_bear'
            price: Current price (if None, fetches current price)
            condition: 'climax', 'rising', or 'normal'
            volume_ratio: Volume ratio compared to average
        
        Returns:
            Simulated PVSRA signal dictionary
        """
        if price is None:
            # Get current price from Binance
            try:
                current_price = self.get_current_price(symbol)
                price = current_price
            except Exception as e:
                logger.error(f"Failed to get current price for {symbol}: {e}")
                return None
        
        # Map signal types to alerts
        signal_map = {
            'bull_climax': 'Bull Climax - Potential Reversal',
            'bear_climax': 'Bear Climax - Potential Reversal', 
            'rising_bull': 'Rising Volume Bull - Continuation Signal',
            'rising_bear': 'Rising Volume Bear - Continuation Signal'
        }
        
        alert = signal_map.get(signal_type, 'Bull Climax - Potential Reversal')
        
        # Create signal dictionary
        signal = {
            'symbol': symbol,
            'timestamp': datetime.now(timezone.utc),
            'alert': alert,
            'price': price,
            'volume': 150000,  # Simulated volume
            'condition': condition,
            'volume_ratio': volume_ratio,
            'is_climax': condition == 'climax',
            'is_rising': condition == 'rising',
            'is_bullish': 'Bull' in alert,
            'simulated': True
        }
        
        logger.info(f"📊 Created PVSRA signal: {symbol} - {alert} @ ${price:.4f}")
        return signal
    
    def get_current_price(self, symbol: str) -> float:
        """Get current price for a symbol"""
        try:
            url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
            response = requests.get(url)
            data = response.json()
            return float(data['price'])
        except Exception as e:
            logger.error(f"Error getting price for {symbol}: {e}")
            raise
    
    def trigger_signal(self, signal: Dict) -> bool:
        """
        Trigger a PVSRA signal and have the bot process it
        
        Args:
            signal: PVSRA signal dictionary
            
        Returns:
            True if signal was processed successfully
        """
        try:
            symbol = signal['symbol']
            
            # Store the signal
            self.simulated_signals.append(signal)
            
            # Send signal to bot's PVSRA callback
            if self.bot and hasattr(self.bot, 'on_pvsra_signal'):
                self.bot.on_pvsra_signal(symbol, signal)
                logger.info(f"✅ Signal sent to bot: {symbol} - {signal['alert']}")
                return True
            else:
                logger.error("❌ Bot not initialized or missing callback")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error triggering signal: {e}")
            return False
    
    def simulate_bull_climax(self, symbol: str = "BTCUSDT") -> bool:
        """Simulate a Bull Climax signal (potential buy signal)"""
        signal = self.create_pvsra_signal(symbol, 'bull_climax', condition='climax')
        if signal:
            return self.trigger_signal(signal)
        return False
    
    def simulate_bear_climax(self, symbol: str = "BTCUSDT") -> bool:
        """Simulate a Bear Climax signal (potential sell signal)"""
        signal = self.create_pvsra_signal(symbol, 'bear_climax', condition='climax')
        if signal:
            return self.trigger_signal(signal)
        return False
    
    def simulate_rising_bull(self, symbol: str = "BTCUSDT") -> bool:
        """Simulate a Rising Volume Bull signal (continuation buy signal)"""
        signal = self.create_pvsra_signal(symbol, 'rising_bull', condition='rising', volume_ratio=1.8)
        if signal:
            return self.trigger_signal(signal)
        return False
    
    def simulate_rising_bear(self, symbol: str = "BTCUSDT") -> bool:
        """Simulate a Rising Volume Bear signal (continuation sell signal)"""
        signal = self.create_pvsra_signal(symbol, 'rising_bear', condition='rising', volume_ratio=1.8)
        if signal:
            return self.trigger_signal(signal)
        return False
    
    def get_bot_status(self) -> Dict:
        """Get current bot status and position info"""
        try:
            status = {
                'running': getattr(self.bot, 'running', False),
                'current_price': getattr(self.bot, 'current_price', 0),
                'position_size': getattr(self.bot, 'position_size', 0),
                'entry_price': getattr(self.bot, 'entry_price', 0),
                'last_pvsra_signal': getattr(self.bot, 'last_pvsra_signal', None),
                'pvsra_enabled': getattr(self.bot, 'use_pvsra', False),
                'symbol': getattr(self.bot, 'symbol', 'Unknown'),
                'balance': 0
            }
            
            # Try to get account balance
            try:
                status['balance'] = self.bot.get_account_balance()
            except:
                status['balance'] = 0
            
            return status
        except Exception as e:
            logger.error(f"Error getting bot status: {e}")
            return {'error': str(e)}
    
    def get_simulation_history(self) -> List[Dict]:
        """Get history of simulated signals"""
        return self.simulated_signals[-10:]  # Last 10 signals
    
    def start_bot(self) -> bool:
        """Start the trading bot"""
        try:
            if self.bot and not getattr(self.bot, 'running', False):
                # Start bot in a separate thread to avoid blocking
                import threading
                bot_thread = threading.Thread(target=self.bot.start)
                bot_thread.daemon = True
                bot_thread.start()
                
                # Give it a moment to initialize
                time.sleep(2)
                
                logger.info("🚀 Trading bot started")
                return True
            else:
                logger.info("⚠️ Bot already running or not initialized")
                return False
        except Exception as e:
            logger.error(f"❌ Error starting bot: {e}")
            return False
    
    def stop_bot(self) -> bool:
        """Stop the trading bot"""
        try:
            if self.bot and hasattr(self.bot, 'stop'):
                self.bot.stop()
                logger.info("🛑 Trading bot stopped")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Error stopping bot: {e}")
            return False
    
    def run_interactive_mode(self):
        """Run interactive command-line interface"""
        print("\n" + "="*60)
        print("🎯 PVSRA Signal Simulator - Interactive Mode")
        print("="*60)
        
        # Start bot
        print("\n🚀 Starting trading bot...")
        self.start_bot()
        
        while True:
            print("\n📋 Available Commands:")
            print("1. Simulate Bull Climax (BUY signal)")
            print("2. Simulate Bear Climax (SELL signal)")
            print("3. Simulate Rising Bull (BUY continuation)")
            print("4. Simulate Rising Bear (SELL continuation)")
            print("5. Check Bot Status")
            print("6. View Signal History")
            print("7. Custom Signal")
            print("8. Start/Stop Bot")
            print("9. Exit")
            
            try:
                choice = input("\n🔥 Enter your choice (1-9): ").strip()
                
                if choice == '1':
                    symbol = input("Enter symbol (default: BTCUSDT): ").strip() or "BTCUSDT"
                    success = self.simulate_bull_climax(symbol.upper())
                    if success:
                        print(f"✅ Bull Climax signal sent for {symbol}")
                    else:
                        print(f"❌ Failed to send signal for {symbol}")
                
                elif choice == '2':
                    symbol = input("Enter symbol (default: BTCUSDT): ").strip() or "BTCUSDT"
                    success = self.simulate_bear_climax(symbol.upper())
                    if success:
                        print(f"✅ Bear Climax signal sent for {symbol}")
                    else:
                        print(f"❌ Failed to send signal for {symbol}")
                
                elif choice == '3':
                    symbol = input("Enter symbol (default: BTCUSDT): ").strip() or "BTCUSDT"
                    success = self.simulate_rising_bull(symbol.upper())
                    if success:
                        print(f"✅ Rising Bull signal sent for {symbol}")
                    else:
                        print(f"❌ Failed to send signal for {symbol}")
                
                elif choice == '4':
                    symbol = input("Enter symbol (default: BTCUSDT): ").strip() or "BTCUSDT"
                    success = self.simulate_rising_bear(symbol.upper())
                    if success:
                        print(f"✅ Rising Bear signal sent for {symbol}")
                    else:
                        print(f"❌ Failed to send signal for {symbol}")
                
                elif choice == '5':
                    status = self.get_bot_status()
                    print(f"\n📊 Bot Status:")
                    for key, value in status.items():
                        print(f"   {key}: {value}")
                
                elif choice == '6':
                    history = self.get_simulation_history()
                    print(f"\n📜 Signal History ({len(history)} signals):")
                    for i, signal in enumerate(history, 1):
                        print(f"   {i}. {signal['symbol']} - {signal['alert']} @ ${signal['price']:.4f}")
                
                elif choice == '7':
                    symbol = input("Enter symbol: ").strip().upper()
                    signal_type = input("Enter signal type (bull_climax/bear_climax/rising_bull/rising_bear): ").strip()
                    price_input = input("Enter price (leave empty for current): ").strip()
                    price = float(price_input) if price_input else None
                    
                    signal = self.create_pvsra_signal(symbol, signal_type, price)
                    if signal and self.trigger_signal(signal):
                        print(f"✅ Custom signal sent: {symbol} - {signal['alert']}")
                    else:
                        print("❌ Failed to send custom signal")
                
                elif choice == '8':
                    status = self.get_bot_status()
                    if status.get('running', False):
                        self.stop_bot()
                        print("🛑 Bot stopped")
                    else:
                        self.start_bot()
                        print("🚀 Bot started")
                
                elif choice == '9':
                    print("\n👋 Exiting simulator...")
                    self.stop_bot()
                    break
                
                else:
                    print("❌ Invalid choice. Please enter 1-9.")
                    
            except KeyboardInterrupt:
                print("\n\n👋 Exiting simulator...")
                self.stop_bot()
                break
            except Exception as e:
                print(f"❌ Error: {e}")


def main():
    """Main entry point"""
    try:
        simulator = PVSRASignalSimulator()
        simulator.run_interactive_mode()
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
