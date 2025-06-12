#!/usr/bin/env python3
"""
Enhanced Binance Futures Scalping Bot with PVSRA Integration and Market Orders
Combines scalping strategies with PVSRA signals and supports both simulation and live trading.
"""

import os
import json
import time
import hmac
import hashlib
import requests
from datetime import datetime, timezone, timedelta
import logging
from collections import deque
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from typing import Dict, List, Optional

# Try to load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Loaded environment variables from .env file")
except ImportError:
    print("⚠️ python-dotenv not installed. Using system environment variables.")
    print("Install with: pip install python-dotenv")

# Import PVSRA modules
try:
    from binance_futures_pvsra import BinanceFuturesPVSRA
    PVSRA_AVAILABLE = True
    print("✅ PVSRA modules imported successfully")
except ImportError as e:
    PVSRA_AVAILABLE = False
    print(f"⚠️ PVSRA modules not available: {e}")
    print("PVSRA features will be disabled")

# Configure logging
log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(level=getattr(logging, log_level), 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedBinanceFuturesBot:
    """
    Enhanced Binance Futures Bot with PVSRA Integration and Market Orders
    Combines traditional scalping with advanced technical analysis signals
    """
    
    def __init__(self):
        # Load configuration from environment variables
        self.api_key = os.getenv('BINANCE_API_KEY')
        self.api_secret = os.getenv('BINANCE_API_SECRET')
        self.symbol = os.getenv('SYMBOL', 'SUIUSDT')
        self.test_mode = os.getenv('TEST_MODE', 'True').lower() == 'true'
        
        # Trading execution mode
        self.enable_live_trading = os.getenv('ENABLE_LIVE_TRADING', 'False').lower() == 'true'
        
        # Validate required credentials
        if not self.api_key or not self.api_secret:
            raise ValueError("❌ BINANCE_API_KEY and BINANCE_API_SECRET must be set in environment variables")
        
        # MongoDB configuration
        self.mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
        self.mongodb_database = os.getenv('MONGODB_DATABASE', 'trading_bot')
        self.mongodb_collection = os.getenv('MONGODB_COLLECTION', 'orders')
        self.mongo_client = None
        self.db = None
        self.collection = None
        
        # Trading parameters from environment or defaults
        self.trade_amount = float(os.getenv('TRADE_AMOUNT', '10'))
        
        # Percentage trading configuration
        self.trade_amount_percentage = os.getenv('TRADE_AMOUNT_PERCENTAGE')
        self.use_percentage_trading = False
        
        # Validate percentage trading configuration
        if self.trade_amount_percentage:
            try:
                self.trade_amount_percentage = float(self.trade_amount_percentage)
                if 0.1 <= self.trade_amount_percentage <= 100:
                    self.use_percentage_trading = True
                    logger.info(f"✅ Percentage-based trading enabled: {self.trade_amount_percentage}% of available balance")
                else:
                    logger.warning(f"⚠️ Invalid TRADE_AMOUNT_PERCENTAGE ({self.trade_amount_percentage}%). Must be 0.1-100%. Using fixed amount.")
                    self.trade_amount_percentage = None
            except ValueError:
                logger.warning(f"⚠️ Invalid TRADE_AMOUNT_PERCENTAGE format. Using fixed amount.")
                self.trade_amount_percentage = None
        
        self.leverage = int(os.getenv('LEVERAGE', '5'))
        self.profit_threshold = float(os.getenv('PROFIT_THRESHOLD', '0.002'))
        self.stop_loss_threshold = float(os.getenv('STOP_LOSS_THRESHOLD', '0.001'))
        self.min_price_change = float(os.getenv('MIN_PRICE_CHANGE', '0.0003'))
        
        # PVSRA Configuration
        self.use_pvsra = os.getenv('USE_PVSRA', 'True').lower() == 'true' and PVSRA_AVAILABLE
        self.pvsra_weight = float(os.getenv('PVSRA_WEIGHT', '0.7'))
        self.require_pvsra_confirmation = os.getenv('REQUIRE_PVSRA_CONFIRMATION', 'False').lower() == 'true'
        
        # Bot settings
        self.price_update_interval = int(os.getenv('PRICE_UPDATE_INTERVAL', '2'))
        self.trade_cooldown = int(os.getenv('TRADE_COOLDOWN', '5'))  # Reduced from 30 to 5 seconds
        self.allow_multiple_positions = os.getenv('ALLOW_MULTIPLE_POSITIONS', 'False').lower() == 'true'
        
        # Bot state
        self.current_price = 0
        self.position_size = 0
        self.entry_price = 0
        self.price_history = deque(maxlen=50)
        self.last_trade_time = 0
        self.bot_session_id = f"bot_{int(time.time())}"
        
        # PVSRA state
        self.last_pvsra_signal = None
        self.pvsra_signal_time = 0
        self.pvsra_signals_history = deque(maxlen=20)
        
        # URLs
        self.base_url = "https://testnet.binancefuture.com" if self.test_mode else "https://fapi.binance.com"
        
        # Initialize
        self.running = False
        self.symbol_info = None
        
        # Setup MongoDB connection
        self._setup_mongodb()
        
        # Initialize PVSRA if available
        self._setup_pvsra()
        
        # Log configuration
        self._log_configuration()

    def _setup_mongodb(self):
        """Setup MongoDB connection with error handling"""
        try:
            self.mongo_client = MongoClient(self.mongodb_uri, serverSelectionTimeoutMS=5000)
            self.mongo_client.server_info()  # Test connection
            self.db = self.mongo_client[self.mongodb_database]
            self.collection = self.db[self.mongodb_collection]
            logger.info("✅ MongoDB connected successfully")
        except ConnectionFailure:
            logger.warning("⚠️ MongoDB connection failed. Continuing without database logging.")
            self.mongo_client = None
            self.db = None
            self.collection = None
        except Exception as e:
            logger.warning(f"⚠️ MongoDB setup error: {e}. Continuing without database logging.")
            self.mongo_client = None
            self.db = None
            self.collection = None

    def _setup_pvsra(self):
        """Initialize PVSRA if available"""
        if self.use_pvsra and PVSRA_AVAILABLE:
            try:
                self.pvsra = BinanceFuturesPVSRA(
                    self.api_key, 
                    self.api_secret, 
                    self.test_mode
                )
                # Register PVSRA callback
                self.pvsra.add_alert_callback(self.on_pvsra_signal)
                logger.info("✅ PVSRA initialized successfully")
            except Exception as e:
                logger.error(f"❌ Failed to initialize PVSRA: {e}")
                self.use_pvsra = False
                self.pvsra = None
        else:
            self.pvsra = None
            logger.info("ℹ️ PVSRA disabled or not available")

    def _log_configuration(self):
        """Log current configuration"""
        logger.info("🤖 Enhanced Bot Configuration:")
        logger.info(f"   Symbol: {self.symbol}")
        logger.info(f"   Test Mode: {self.test_mode}")
        logger.info(f"   🔥 Live Trading: {'ENABLED' if self.enable_live_trading else 'SIMULATION MODE'}")
        
        # Trading mode
        if self.use_percentage_trading:
            logger.info(f"   Trading Mode: Percentage-based ({self.trade_amount_percentage}% of available balance)")
        else:
            logger.info(f"   Trading Mode: Fixed amount ({self.trade_amount} USDT per trade)")
        
        logger.info(f"   Leverage: {self.leverage}x")
        logger.info(f"   Profit Threshold: {self.profit_threshold*100:.2f}%")
        logger.info(f"   Stop Loss Threshold: {self.stop_loss_threshold*100:.2f}%")
        
        # PVSRA configuration
        if self.use_pvsra:
            logger.info(f"   🎯 PVSRA Integration: Enabled (Weight: {self.pvsra_weight:.1f})")
            logger.info(f"   🎯 PVSRA Confirmation Required: {self.require_pvsra_confirmation}")
        else:
            logger.info(f"   🎯 PVSRA Integration: Disabled")
        
        logger.info(f"   Price Update Interval: {self.price_update_interval}s")
        logger.info(f"   Trade Cooldown: {self.trade_cooldown}s")
        logger.info(f"   🔒 Multiple Positions: {'ALLOWED' if self.allow_multiple_positions else 'BLOCKED'}")
        logger.info(f"   Base URL: {self.base_url}")

    def generate_signature(self, query_string):
        """Generate HMAC SHA256 signature for API requests"""
        return hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def get_server_time(self):
        """Get Binance server time to avoid timestamp issues"""
        try:
            response = requests.get(f"{self.base_url}/fapi/v1/time", timeout=10)
            if response.status_code == 200:
                return response.json()['serverTime']
            else:
                logger.warning(f"Failed to get server time, using local time. Status: {response.status_code}")
                return int(time.time() * 1000)
        except Exception as e:
            logger.warning(f"Error getting server time: {e}. Using local time.")
            return int(time.time() * 1000)
    
    def get_current_price(self):
        """Get current price via REST API"""
        try:
            response = requests.get(
                f"{self.base_url}/fapi/v1/ticker/price?symbol={self.symbol}", 
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return float(data['price'])
            else:
                logger.error(f"Failed to get price: {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error getting price: {e}")
            return None

    def get_account_balance(self):
        """Get futures account balance (supports both USDT and USDC)"""
        try:
            timestamp = self.get_server_time()
            query_string = f"timestamp={timestamp}"
            signature = self.generate_signature(query_string)
            
            headers = {'X-MBX-APIKEY': self.api_key}
            
            response = requests.get(
                f"{self.base_url}/fapi/v2/balance",
                params={'timestamp': timestamp, 'signature': signature},
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                balances = response.json()
                
                # First try USDT
                for balance in balances:
                    if balance['asset'] == 'USDT':
                        usdt_balance = float(balance['availableBalance'])
                        if usdt_balance > 0:
                            logger.info(f"💰 Using USDT balance: {usdt_balance:.2f}")
                            return usdt_balance
                
                # If no USDT, try USDC
                for balance in balances:
                    if balance['asset'] == 'USDC':
                        usdc_balance = float(balance['availableBalance'])
                        if usdc_balance > 0:
                            logger.info(f"💰 Using USDC balance: {usdc_balance:.2f}")
                            return usdc_balance
                
                logger.warning("⚠️ No USDT or USDC balance found")
                return 0
            else:
                logger.error(f"❌ Failed to get balance: {response.text}")
                return 0
                
        except Exception as e:
            logger.error(f"Error getting balance: {e}")
            return 0

    def place_market_order(self, side: str, quantity: float) -> Dict:
        """
        Place a market order for futures trading
        
        Args:
            side: 'BUY' or 'SELL'
            quantity: Position size to trade
            
        Returns:
            Dict with order result
        """
        try:
            timestamp = self.get_server_time()
            
            # Prepare order parameters
            params = {
                'symbol': self.symbol,
                'side': side,
                'type': 'MARKET',
                'quantity': str(quantity),
                'timestamp': timestamp
            }
            
            # Create query string for signature
            query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
            signature = self.generate_signature(query_string)
            params['signature'] = signature
            
            headers = {'X-MBX-APIKEY': self.api_key}
            
            # Place the order
            response = requests.post(
                f"{self.base_url}/fapi/v1/order",
                params=params,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                order_result = response.json()
                logger.info(f"✅ Market order executed: {side} {quantity} {self.symbol}")
                logger.info(f"   Order ID: {order_result.get('orderId')}")
                logger.info(f"   Status: {order_result.get('status')}")
                
                # Log to MongoDB
                self._log_to_mongodb({
                    'type': 'order_execution',
                    'order_id': order_result.get('orderId'),
                    'symbol': self.symbol,
                    'side': side,
                    'quantity': quantity,
                    'order_type': 'MARKET',
                    'status': order_result.get('status'),
                    'timestamp': datetime.now(timezone.utc),
                    'session_id': self.bot_session_id,
                    'raw_response': order_result
                })
                
                return {
                    'success': True,
                    'order_id': order_result.get('orderId'),
                    'status': order_result.get('status'),
                    'message': f"Market order executed: {side} {quantity}"
                }
            else:
                error_msg = f"Failed to place order: {response.text}"
                logger.error(f"❌ {error_msg}")
                return {
                    'success': False,
                    'error': error_msg,
                    'message': f"Order failed: {side} {quantity}"
                }
                
        except Exception as e:
            error_msg = f"Error placing market order: {e}"
            logger.error(f"❌ {error_msg}")
            return {
                'success': False,
                'error': str(e),
                'message': f"Order error: {side} {quantity}"
            }

    def calculate_position_size(self, price):
        """Calculate position size for futures trading with percentage support"""
        try:
            # Get available balance
            available_balance = self.get_account_balance()
            if available_balance <= 0:
                logger.error("❌ No available balance")
                return 0
            
            # Calculate base trade amount based on mode
            if self.use_percentage_trading:
                base_trade_amount = available_balance * (self.trade_amount_percentage / 100)
                logger.info(f"💰 Using {self.trade_amount_percentage}% of {available_balance:.2f} = {base_trade_amount:.2f}")
            else:
                base_trade_amount = min(self.trade_amount, available_balance * 0.9)
                logger.info(f"💰 Using fixed amount: {base_trade_amount:.2f}")
            
            # Apply leverage to get position value
            position_value = base_trade_amount * self.leverage
            
            # Calculate quantity
            raw_quantity = position_value / price
            
            # Apply SUIUSDC precision requirements
            step_size = 0.1
            min_qty = 0.1
            min_notional = 5.0
            
            # Round to step size
            quantity = round(raw_quantity / step_size) * step_size
            
            # Ensure minimum quantity
            if quantity < min_qty:
                quantity = min_qty
            
            # Check minimum notional value
            notional_value = quantity * price
            if notional_value < min_notional:
                # Adjust quantity to meet minimum notional
                quantity = min_notional / price
                quantity = round(quantity / step_size) * step_size
            
            logger.info(f"📊 Position calculation:")
            logger.info(f"   Trade Amount: {base_trade_amount:.2f}")
            logger.info(f"   Position Value: {position_value:.2f} (with {self.leverage}x leverage)")
            logger.info(f"   Final Quantity: {quantity:.1f}")
            logger.info(f"   Notional Value: {notional_value:.2f} (min: {min_notional})")
            
            return quantity
            
        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return 0

    def _log_to_mongodb(self, data):
        """Log data to MongoDB with error handling"""
        if self.collection is None:
            return None
        
        try:
            # Add trading mode and PVSRA information
            if self.use_percentage_trading:
                data["trading_mode"] = "percentage"
                data["trading_mode_value"] = self.trade_amount_percentage
            else:
                data["trading_mode"] = "fixed"
                data["trading_mode_value"] = self.trade_amount
            
            data["pvsra_enabled"] = self.use_pvsra
            data["live_trading_enabled"] = self.enable_live_trading
            if self.use_pvsra and self.last_pvsra_signal:
                data["latest_pvsra_signal"] = self.last_pvsra_signal
            
            result = self.collection.insert_one(data)
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Error logging to MongoDB: {e}")
            return None

    def should_enter_trade(self, action: str) -> Dict:
        """
        Enhanced trade entry evaluation with basic checks
        
        Args:
            action: 'BUY' or 'SELL'
            
        Returns:
            Dict with trade decision
        """
        # Basic checks
        if time.time() - self.last_trade_time < self.trade_cooldown:
            return {
                'should_trade': False,
                'reason': 'Trade cooldown active',
                'confidence': 0.0
            }
        
        if len(self.price_history) < 5:
            return {
                'should_trade': False,
                'reason': 'Insufficient price history',
                'confidence': 0.0
            }
        
        # Simple price momentum check
        recent_prices = list(self.price_history)[-5:]
        price_change = (recent_prices[-1] - recent_prices[0]) / recent_prices[0]
        
        confidence = 0.6
        if action == 'BUY' and price_change > self.min_price_change:
            confidence = 0.8
        elif action == 'SELL' and price_change < -self.min_price_change:
            confidence = 0.8
        elif abs(price_change) < self.min_price_change:
            return {
                'should_trade': False,
                'reason': 'Price change too small',
                'confidence': 0.0
            }
        
        return {
            'should_trade': True,
            'confidence': confidence,
            'reason': f"Price momentum signal: {price_change*100:.3f}%",
            'price_change': price_change
        }

    def start(self):
        """Start the enhanced trading bot"""
        logger.info("🚀 Starting Enhanced Futures Bot...")
        
        # Check initial balance
        balance = self.get_account_balance()
        logger.info(f"💰 Primary trading balance: {balance:.2f}")
        
        if self.use_percentage_trading:
            trade_amount = balance * (self.trade_amount_percentage / 100)
            logger.info(f"📊 Current trade amount: {trade_amount:.2f} ({self.trade_amount_percentage}% of balance)")
        else:
            if balance < self.trade_amount:
                logger.warning(f"⚠️ Low balance! Available: {balance}, Required: {self.trade_amount}")
        
        self.running = True
        logger.info("✅ Enhanced bot started successfully!")

if __name__ == "__main__":
    try:
        bot = EnhancedBinanceFuturesBot()
        bot.start()
        
        # Main trading loop
        try:
            logger.info("🔄 Starting main trading loop...")
            
            while True:
                try:
                    # Get current price
                    current_price = bot.get_current_price()
                    if current_price is None:
                        logger.warning("⚠️ Failed to get current price, retrying...")
                        time.sleep(5)
                        continue
                    
                    bot.current_price = current_price
                    bot.price_history.append(current_price)
                    
                    # Look for trading opportunities
                    if len(bot.price_history) >= 5:
                        # Simple price momentum analysis
                        recent_prices = list(bot.price_history)[-5:]
                        price_change = (recent_prices[-1] - recent_prices[0]) / recent_prices[0]
                        
                        # Determine potential action
                        potential_action = None
                        if price_change > bot.min_price_change:
                            potential_action = "BUY"
                        elif price_change < -bot.min_price_change:
                            potential_action = "SELL"
                            
                        if potential_action:
                            # Evaluate trade
                            trade_decision = bot.should_enter_trade(potential_action)
                            
                            if trade_decision['should_trade']:
                                # ASCII Art for BUY/SELL signals
                                if potential_action == "BUY":
                                    print("\n" + "="*60)
                                    print("██████╗ ██╗   ██╗██╗   ██╗")
                                    print("██╔══██╗██║   ██║╚██╗ ██╔╝")
                                    print("██████╔╝██║   ██║ ╚████╔╝ ")
                                    print("██╔══██╗██║   ██║  ╚██╔╝  ")
                                    print("██████╔╝╚██████╔╝   ██║   ")
                                    print("╚═════╝  ╚═════╝    ╚═╝   ")
                                    print("🟢 LONG SIGNAL DETECTED 🟢")
                                    print("="*60 + "\n")
                                else:  # SELL
                                    print("\n" + "="*60)
                                    print("███████╗███████╗██╗     ██╗     ")
                                    print("██╔════╝██╔════╝██║     ██║     ")
                                    print("███████╗█████╗  ██║     ██║     ")
                                    print("╚════██║██╔══╝  ██║     ██║     ")
                                    print("███████║███████╗███████╗███████╗")
                                    print("╚══════╝╚══════╝╚══════╝╚══════╝")
                                    print("🔴 SHORT SIGNAL DETECTED 🔴")
                                    print("="*60 + "\n")
                                
                                logger.info(f"🚀 Trade Signal: {potential_action}")
                                logger.info(f"   Confidence: {trade_decision['confidence']:.2f}")
                                logger.info(f"   Reason: {trade_decision['reason']}")
                                logger.info(f"   Price Change: {price_change*100:.3f}%")
                                
                                # Calculate position size
                                position_size = bot.calculate_position_size(current_price)
                                if position_size > 0:
                                    if bot.enable_live_trading:
                                        # Execute live market order
                                        logger.info(f"🔥 EXECUTING LIVE TRADE: {potential_action} {position_size} {bot.symbol} @ ${current_price:.4f}")
                                        order_result = bot.place_market_order(potential_action, position_size)
                                        
                                        if order_result['success']:
                                            logger.info(f"✅ {order_result['message']}")
                                        else:
                                            logger.error(f"❌ {order_result['message']}")
                                    else:
                                        # Simulation mode
                                        logger.info(f"💰 Would execute: {potential_action} {position_size} {bot.symbol} @ ${current_price:.4f}")
                                        logger.info("📝 Note: This is a simulation - no actual trades executed")
                                    
                                    # Update last trade time to respect cooldown
                                    bot.last_trade_time = time.time()
                                else:
                                    logger.warning("⚠️ Failed to calculate position size")
                            else:
                                logger.debug(f"❌ Trade rejected: {trade_decision['reason']}")
                    
                    # Sleep before next iteration
                    time.sleep(bot.price_update_interval)
                    
                except Exception as e:
                    logger.error(f"Error in trading loop: {e}")
                    time.sleep(5)
                    
        except KeyboardInterrupt:
            logger.info("👋 Stopping bot...")
        
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        logger.info("💡 Please check your .env file or environment variables")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
