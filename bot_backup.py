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

# Try to load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Loaded environment variables from .env file")
except ImportError:
    print("⚠️ python-dotenv not installed. Using system environment variables.")
    print("Install with: pip install python-dotenv")

# Configure logging
log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(level=getattr(logging, log_level), 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BinanceFuturesScalpingBot:
    def __init__(self):
        # Load configuration from environment variables
        self.api_key = os.getenv('BINANCE_API_KEY')
        self.api_secret = os.getenv('BINANCE_API_SECRET')
        self.symbol = os.getenv('SYMBOL', 'SUIUSDT')
        self.test_mode = os.getenv('TEST_MODE', 'True').lower() == 'true'
        
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
        
        # NEW: Percentage trading configuration
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
        
        # Bot settings
        self.price_update_interval = int(os.getenv('PRICE_UPDATE_INTERVAL', '2'))
        self.trade_cooldown = int(os.getenv('TRADE_COOLDOWN', '30'))
        
        # Bot state
        self.current_price = 0
        self.position_size = 0
        self.entry_price = 0
        self.price_history = deque(maxlen=50)
        self.last_trade_time = 0
        self.bot_session_id = f"bot_{int(time.time())}"  # Unique session ID
        
        # URLs
        self.base_url = "https://testnet.binancefuture.com" if self.test_mode else "https://fapi.binance.com"
        
        # Initialize
        self.running = False
        self.symbol_info = None
        
        # Setup MongoDB connection
        self._setup_mongodb()
        
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

    def _log_configuration(self):
        """Log current configuration"""
        logger.info("🤖 Bot Configuration:")
        logger.info(f"   Symbol: {self.symbol}")
        logger.info(f"   Test Mode: {self.test_mode}")
        
        # NEW: Show trading mode
        if self.use_percentage_trading:
            logger.info(f"   Trading Mode: Percentage-based ({self.trade_amount_percentage}% of available balance)")
        else:
            logger.info(f"   Trading Mode: Fixed amount ({self.trade_amount} USDT per trade)")
        
        logger.info(f"   Leverage: {self.leverage}x")
        logger.info(f"   Profit Threshold: {self.profit_threshold*100:.2f}%")
        logger.info(f"   Stop Loss Threshold: {self.stop_loss_threshold*100:.2f}%")
        logger.info(f"   Price Update Interval: {self.price_update_interval}s")
        logger.info(f"   Trade Cooldown: {self.trade_cooldown}s")
        logger.info(f"   Base URL: {self.base_url}")

    def generate_signature(self, query_string):
        """Generate HMAC SHA256 signature for API requests"""
        return hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def get_server_time(self):
        """Get Binance server time"""
        try:
            response = requests.get(f"{self.base_url}/fapi/v1/time", timeout=10)
            return response.json()['serverTime']
        except Exception as e:
            logger.error(f"Error getting server time: {e}")
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
        """Get futures account balance"""
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
                for balance in balances:
                    if balance['asset'] == 'USDT':
                        return float(balance['availableBalance'])
                return 0
            else:
                logger.error(f"❌ Failed to get balance: {response.text}")
                return 0
                
        except Exception as e:
            logger.error(f"Error getting balance: {e}")
            return 0

    def calculate_position_size(self, price):
        """Calculate position size for futures trading with percentage support"""
        try:
            # Get available balance
            available_balance = self.get_account_balance()
            if available_balance <= 0:
                logger.error("❌ No available balance")
                return 0
            
            # NEW: Calculate base trade amount based on mode
            if self.use_percentage_trading:
                base_trade_amount = available_balance * (self.trade_amount_percentage / 100)
                logger.info(f"💰 Using {self.trade_amount_percentage}% of {available_balance:.2f} USDT = {base_trade_amount:.2f} USDT")
            else:
                base_trade_amount = min(self.trade_amount, available_balance * 0.9)
                logger.info(f"💰 Using fixed amount: {base_trade_amount:.2f} USDT")
            
            # Apply leverage to get position value
            position_value = base_trade_amount * self.leverage
            
            # Calculate quantity
            raw_quantity = position_value / price
            
            # Apply SUIUSDT precision requirements
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
            logger.info(f"   Trade Amount: {base_trade_amount:.2f} USDT")
            logger.info(f"   Position Value: {position_value:.2f} USDT (with {self.leverage}x leverage)")
            logger.info(f"   Raw Quantity: {raw_quantity:.4f}")
            logger.info(f"   Final Quantity: {quantity:.1f} (step size: {step_size})")
            logger.info(f"   Notional Value: {notional_value:.2f} USDT (min: {min_notional})")
            
            return quantity
            
        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return 0

    def _log_to_mongodb(self, data):
        """Log data to MongoDB with error handling"""
        if self.collection is None:
            return None
        
        try:
            # Add trading mode information
            if self.use_percentage_trading:
                data["trading_mode"] = "percentage"
                data["trading_mode_value"] = self.trade_amount_percentage
            else:
                data["trading_mode"] = "fixed"
                data["trading_mode_value"] = self.trade_amount
            
            result = self.collection.insert_one(data)
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Error logging to MongoDB: {e}")
            return None

    def start(self):
        """Start the trading bot"""
        logger.info("🚀 Starting Futures Scalping Bot...")
        
        # Check initial balance and log trading mode
        balance = self.get_account_balance()
        logger.info(f"💰 Available USDT balance: {balance:.2f}")
        
        if self.use_percentage_trading:
            trade_amount = balance * (self.trade_amount_percentage / 100)
            logger.info(f"📊 Current trade amount: {trade_amount:.2f} USDT ({self.trade_amount_percentage}% of balance)")
        else:
            if balance < self.trade_amount:
                logger.warning(f"⚠️ Low balance! Available: {balance}, Required: {self.trade_amount}")
        
        self.running = True
        logger.info("✅ Bot started successfully with percentage trading support!")

if __name__ == "__main__":
    try:
        bot = BinanceFuturesScalpingBot()
        bot.start()
        
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        logger.info("💡 Please check your .env file or environment variables")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
