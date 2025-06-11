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
        
    def _log_configuration(self):
        """Log current bot configuration"""
        logger.info("🤖 Bot Configuration:")
        logger.info(f"   Symbol: {self.symbol}")
        logger.info(f"   Test Mode: {self.test_mode}")
        logger.info(f"   Trade Amount: {self.trade_amount} USDT")
        logger.info(f"   Leverage: {self.leverage}x")
        logger.info(f"   Profit Target: {self.profit_threshold*100:.2f}%")
        logger.info(f"   Stop Loss: {self.stop_loss_threshold*100:.2f}%")
        logger.info(f"   Price Update Interval: {self.price_update_interval}s")
        logger.info(f"   Trade Cooldown: {self.trade_cooldown}s")
        logger.info(f"   Session ID: {self.bot_session_id}")
    
    def _setup_mongodb(self):
        """Setup MongoDB connection and create indexes"""
        try:
            self.mongo_client = MongoClient(
                self.mongodb_uri,
                serverSelectionTimeoutMS=5000,  # 5 second timeout
                connectTimeoutMS=5000
            )
            
            # Test connection
            self.mongo_client.admin.command('ismaster')
            
            self.db = self.mongo_client[self.mongodb_database]
            self.collection = self.db[self.mongodb_collection]
            
            # Create indexes for better query performance
            self.collection.create_index([("timestamp", -1)])  # Most recent first
            self.collection.create_index([("symbol", 1), ("timestamp", -1)])
            self.collection.create_index([("session_id", 1), ("timestamp", -1)])
            self.collection.create_index([("order_type", 1), ("timestamp", -1)])
            
            logger.info(f"✅ Connected to MongoDB: {self.mongodb_database}.{self.mongodb_collection}")
            
            # Log bot startup
            self._log_to_mongodb({
                "type": "bot_startup",
                "message": "Trading bot started",
                "configuration": {
                    "symbol": self.symbol,
                    "test_mode": self.test_mode,
                    "trade_amount": self.trade_amount,
                    "leverage": self.leverage,
                    "profit_threshold": self.profit_threshold,
                    "stop_loss_threshold": self.stop_loss_threshold
                }            })
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.warning(f"⚠️ MongoDB connection failed: {e}")
            logger.warning("📝 Orders will not be logged to database")
            self.mongo_client = None
        except Exception as e:
            logger.error(f"❌ MongoDB setup error: {e}")
            self.mongo_client = None
    
    def _log_to_mongodb(self, log_data):
        """Log data to MongoDB with error handling"""
        if self.mongo_client is None or self.collection is None:
            return False
        
        try:
            # Add standard fields to all logs
            log_entry = {
                "timestamp": datetime.now(timezone.utc),
                "session_id": self.bot_session_id,
                "symbol": self.symbol,
                "test_mode": self.test_mode,
                **log_data
            }
            
            result = self.collection.insert_one(log_entry)
            return result.inserted_id
            
        except Exception as e:
            logger.error(f"❌ Failed to log to MongoDB: {e}")
            return False
    
    def _log_order_to_mongodb(self, order_data, binance_response=None, error=None):
        """Log trading order to MongoDB"""
        log_entry = {
            "type": "trading_order",
            "order_data": order_data,
            "current_price": self.current_price,
            "success": binance_response is not None,
        }
        
        if binance_response:
            log_entry["binance_response"] = binance_response
            log_entry["order_id"] = binance_response.get("orderId")
            log_entry["client_order_id"] = binance_response.get("clientOrderId")
            
        if error:
            log_entry["error"] = str(error)
        
        return self._log_to_mongodb(log_entry)
    
    def _log_trade_close(self, exit_info, order_response=None):
        """Log detailed trade closure information to MongoDB"""
        trade_close_data = {
            "type": "trade_close",
            "exit_reason": exit_info["exit_reason"],
            "position_type": exit_info["position_type"],
            "entry_price": exit_info["entry_price"],
            "exit_price": exit_info["current_price"],
            "profit_pct": exit_info["profit_pct"],
            "unrealized_pnl": exit_info["unrealized_pnl"],
            "position_amt": exit_info["position_amt"],
            "position_value": exit_info["position_value"],
            "trigger_threshold": exit_info["trigger_threshold"],
            "timestamp": datetime.now(timezone.utc)
        }
        
        if order_response:
            trade_close_data["close_order_id"] = order_response.get("orderId")
            trade_close_data["close_client_order_id"] = order_response.get("clientOrderId")
        
        # Determine if this was a winning or losing trade
        trade_close_data["trade_result"] = "PROFIT" if exit_info["profit_pct"] > 0 else "LOSS"
        
        # Calculate trade duration if we have position history
        try:
            # Find the most recent position open for this symbol
            recent_position_open = self.collection.find_one(
                {
                    "type": "position_change",
                    "action": {"$in": ["OPEN_LONG", "OPEN_SHORT"]},
                    "symbol": self.symbol,
                    "session_id": self.bot_session_id
                },
                sort=[("timestamp", -1)]
            )
            
            if recent_position_open:
                trade_duration = datetime.now(timezone.utc) - recent_position_open["timestamp"]
                trade_close_data["trade_duration_seconds"] = trade_duration.total_seconds()
                trade_close_data["trade_duration_minutes"] = trade_duration.total_seconds() / 60
                trade_close_data["position_opened_at"] = recent_position_open["timestamp"]
        except Exception as e:
            logger.warning(f"Could not calculate trade duration: {e}")
        
        # Log the trade closure
        log_id = self._log_to_mongodb(trade_close_data)
        
        # Log summary for console
        profit_emoji = "💰" if exit_info["profit_pct"] > 0 else "📉"
        reason_emoji = "🎯" if exit_info["exit_reason"] == "TAKE_PROFIT" else "🛑"
        
        logger.info(f"{reason_emoji} {exit_info['exit_reason']} triggered")
        logger.info(f"{profit_emoji} {exit_info['position_type']} position closed: {exit_info['profit_pct']:.2f}% profit/loss")
        logger.info(f"💵 Entry: {exit_info['entry_price']:.4f} → Exit: {exit_info['current_price']:.4f}")
        
        if log_id:
            logger.info(f"📝 Trade closure logged to MongoDB (ID: {log_id})")
        
        return log_id
    
    def _log_position_change(self, action, position_before, position_after, reason="", additional_data=None):
        """Log position changes to MongoDB"""
        log_data = {
            "type": "position_change",
            "action": action,
            "position_before": position_before,
            "position_after": position_after,
            "reason": reason,
            "current_price": self.current_price        }
        
        if additional_data:
            log_data.update(additional_data)
        
        return self._log_to_mongodb(log_data)
    
    def get_trading_stats_from_db(self, days=7):
        """Get trading statistics from MongoDB"""
        if self.collection is None:
            return None
        
        try:
            from_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            pipeline = [
                {
                    "$match": {
                        "timestamp": {"$gte": from_date},
                        "type": "trading_order",
                        "success": True
                    }
                },
                {
                    "$group": {
                        "_id": "$order_data.side",
                        "count": {"$sum": 1},
                        "total_quantity": {"$sum": "$order_data.quantity"}
                    }
                }
            ]
            
            stats = list(self.collection.aggregate(pipeline))
            return stats
            
        except Exception as e:
            logger.error(f"Error getting trading stats: {e}")
            return None
        
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
      def get_symbol_info(self):
        """Get symbol information for precision and filters"""
        try:
            response = requests.get(f"{self.base_url}/fapi/v1/exchangeInfo", timeout=10)
            data = response.json()
            
            for symbol_data in data['symbols']:
                if symbol_data['symbol'] == self.symbol:
                    self.symbol_info = symbol_data
                    logger.info(f"✅ Symbol info loaded for {self.symbol}")
                    
                    # Display trading rules for debugging
                    self.get_symbol_trading_rules()
                    
                    return symbol_data
            
            logger.error(f"❌ Symbol {self.symbol} not found")
            return None
            
        except Exception as e:
            logger.error(f"Error getting symbol info: {e}")
            return None
    
    def set_leverage(self):
        """Set leverage for the symbol"""
        try:
            timestamp = self.get_server_time()
            
            params = {
                'symbol': self.symbol,
                'leverage': self.leverage,
                'timestamp': timestamp
            }
            
            query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
            signature = self.generate_signature(query_string)
            
            headers = {'X-MBX-APIKEY': self.api_key}
            
            response = requests.post(
                f"{self.base_url}/fapi/v1/leverage",
                params=params,
                headers=headers,
                data={'signature': signature},
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Leverage set to {self.leverage}x for {self.symbol}")
                return True
            else:
                logger.error(f"❌ Failed to set leverage: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error setting leverage: {e}")
            return False
    
    def set_margin_type(self, margin_type="ISOLATED"):
        """Set margin type (ISOLATED or CROSSED)"""
        try:
            timestamp = self.get_server_time()
            
            params = {
                'symbol': self.symbol,
                'marginType': margin_type,
                'timestamp': timestamp
            }
            
            query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
            signature = self.generate_signature(query_string)
            
            headers = {'X-MBX-APIKEY': self.api_key}
            
            response = requests.post(
                f"{self.base_url}/fapi/v1/marginType",
                params=params,
                headers=headers,
                data={'signature': signature},
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Margin type set to {margin_type} for {self.symbol}")
                return True
            else:
                logger.warning(f"⚠️ Margin type change: {response.text}")
                return True  # Often fails if already set, which is okay
                
        except Exception as e:
            logger.error(f"Error setting margin type: {e}")
            return False
    
    def place_futures_order(self, side, quantity, order_type="MARKET", price=None):
        """Place futures order on Binance with MongoDB logging"""
        try:
            timestamp = self.get_server_time()
            
            params = {
                'symbol': self.symbol,
                'side': side,
                'type': order_type,
                'quantity': abs(quantity),
                'timestamp': timestamp
            }
            
            if order_type == "LIMIT":
                params['price'] = price
                params['timeInForce'] = 'GTC'
            
            # Log order attempt to MongoDB
            order_data = {
                "side": side,
                "quantity": abs(quantity),
                "order_type": order_type,
                "price": price,
                "symbol": self.symbol
            }
            
            query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
            signature = self.generate_signature(query_string)
            
            headers = {'X-MBX-APIKEY': self.api_key}
            
            response = requests.post(
                f"{self.base_url}/fapi/v1/order",
                params=params,
                headers=headers,
                data={'signature': signature},
                timeout=10
            )
            
            if response.status_code == 200:
                binance_response = response.json()
                
                # Log successful order to MongoDB
                self._log_order_to_mongodb(order_data, binance_response)
                
                logger.info(f"✅ Order successful: {side} {quantity} {self.symbol} at {self.current_price}")
                logger.info(f"📋 Order ID: {binance_response.get('orderId', 'N/A')}")
                
                return binance_response
            else:
                error_msg = response.text
                
                # Log failed order to MongoDB
                self._log_order_to_mongodb(order_data, error=error_msg)
                
                logger.error(f"❌ Order failed: {error_msg}")
                return None
                
        except Exception as e:
            # Log exception to MongoDB
            self._log_order_to_mongodb(order_data, error=str(e))
            logger.error(f"Error placing order: {e}")
            return None
    
    def get_position_info(self):
        """Get current position information"""
        try:
            timestamp = self.get_server_time()
            query_string = f"timestamp={timestamp}"
            signature = self.generate_signature(query_string)
            
            headers = {'X-MBX-APIKEY': self.api_key}
            
            response = requests.get(
                f"{self.base_url}/fapi/v2/positionRisk",
                params={'timestamp': timestamp, 'signature': signature},
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                positions = response.json()
                for pos in positions:
                    if pos['symbol'] == self.symbol:
                        return pos
                return None
            else:
                logger.error(f"❌ Failed to get position: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting position: {e}")
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
        """Calculate position size for futures trading with proper precision handling"""
        try:
            available_balance = self.get_account_balance()
            
            # Use a portion of available balance with leverage
            max_position_value = min(self.trade_amount, available_balance * 0.1) * self.leverage
            quantity = max_position_value / price
            
            # Apply symbol precision constraints
            if self.symbol_info:
                step_size = None
                min_qty = None
                max_qty = None
                
                for filter_info in self.symbol_info['filters']:
                    if filter_info['filterType'] == 'LOT_SIZE':
                        step_size = float(filter_info['stepSize'])
                        min_qty = float(filter_info['minQty'])
                        max_qty = float(filter_info['maxQty'])
                        break
                
                if step_size:
                    # Calculate precision from step size
                    if step_size >= 1:
                        precision = 0
                    else:
                        precision = len(str(step_size).split('.')[-1].rstrip('0'))
                    
                    # Round quantity to step size
                    quantity = round(quantity / step_size) * step_size
                    
                    # Round to appropriate decimal places
                    quantity = round(quantity, precision)
                    
                    # Ensure minimum quantity requirement
                    if min_qty and quantity < min_qty:
                        quantity = min_qty
                    
                    # Ensure maximum quantity requirement
                    if max_qty and quantity > max_qty:
                        quantity = max_qty
                    
                    logger.debug(f"Position size calculation: {quantity} (step: {step_size}, min: {min_qty}, precision: {precision})")
            
            # Final fallback minimum
            return max(quantity, 0.001)
            
        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return 0
    
    def analyze_price_movement(self):
        """Analyze recent price movements for scalping signals"""
        if len(self.price_history) < 20:
            return None
        
        recent_prices = list(self.price_history)[-20:]
        
        # Calculate short-term momentum
        short_momentum = (recent_prices[-1] - recent_prices[-5]) / recent_prices[-5]
        medium_momentum = (recent_prices[-1] - recent_prices[-10]) / recent_prices[-10]
        
        # Simple momentum strategy with confirmation
        if short_momentum > self.min_price_change and medium_momentum > 0:
            return "BUY"  # Strong upward momentum
        elif short_momentum < -self.min_price_change and medium_momentum < 0:
            return "SELL"  # Strong downward momentum
        
        return None
    
    def check_exit_conditions(self):
        """Check if we should exit current position with detailed logging"""
        position = self.get_position_info()
        if not position or float(position['positionAmt']) == 0:
            self.position_size = 0
            return False, None
        
        position_amt = float(position['positionAmt'])
        entry_price = float(position['entryPrice'])
        unrealized_pnl = float(position['unRealizedPnl'])
        
        exit_info = {
            "position_amt": position_amt,
            "entry_price": entry_price,
            "current_price": self.current_price,
            "unrealized_pnl": unrealized_pnl,
            "position_value": abs(position_amt * self.current_price)
        }
        
        if position_amt > 0:  # Long position
            profit_pct = (self.current_price - entry_price) / entry_price
            exit_info["profit_pct"] = profit_pct * 100
            exit_info["position_type"] = "LONG"
            
            if profit_pct >= self.profit_threshold:
                exit_info["exit_reason"] = "TAKE_PROFIT"
                exit_info["trigger_threshold"] = self.profit_threshold * 100
                logger.info(f"🎯 Take profit triggered for LONG: {profit_pct*100:.2f}% (Target: {self.profit_threshold*100:.2f}%)")
                return True, exit_info
            elif profit_pct <= -self.stop_loss_threshold:
                exit_info["exit_reason"] = "STOP_LOSS"
                exit_info["trigger_threshold"] = -self.stop_loss_threshold * 100
                logger.info(f"🛑 Stop loss triggered for LONG: {profit_pct*100:.2f}% (Stop: {-self.stop_loss_threshold*100:.2f}%)")
                return True, exit_info
                
        elif position_amt < 0:  # Short position
            profit_pct = (entry_price - self.current_price) / entry_price
            exit_info["profit_pct"] = profit_pct * 100
            exit_info["position_type"] = "SHORT"
            
            if profit_pct >= self.profit_threshold:
                exit_info["exit_reason"] = "TAKE_PROFIT"
                exit_info["trigger_threshold"] = self.profit_threshold * 100
                logger.info(f"🎯 Take profit triggered for SHORT: {profit_pct*100:.2f}% (Target: {self.profit_threshold*100:.2f}%)")
                return True, exit_info
            elif profit_pct <= -self.stop_loss_threshold:
                exit_info["exit_reason"] = "STOP_LOSS"
                exit_info["trigger_threshold"] = -self.stop_loss_threshold * 100
                logger.info(f"🛑 Stop loss triggered for SHORT: {profit_pct*100:.2f}% (Stop: {-self.stop_loss_threshold*100:.2f}%)")
                return True, exit_info
        
        return False, None
    
    def execute_trade(self, action):
        """Execute buy or sell trade with enhanced MongoDB logging"""
        current_time = time.time()
        
        # Check cooldown
        if current_time - self.last_trade_time < self.trade_cooldown:
            return
        
        try:
            # Get current position
            position = self.get_position_info()
            current_position = float(position['positionAmt']) if position else 0
            position_before = current_position
            
            if action == "BUY" and current_position == 0:
                # Open long position
                quantity = self.calculate_position_size(self.current_price)
                if quantity > 0:
                    order = self.place_futures_order("BUY", quantity)
                    if order:
                        logger.info(f"📈 LONG position opened: {quantity} at {self.current_price}")
                        self.last_trade_time = current_time
                        
                        # Log position change with entry details
                        self._log_position_change(
                            action="OPEN_LONG",
                            position_before=position_before,
                            position_after=quantity,
                            reason="Signal: BUY momentum detected",
                            additional_data={
                                "entry_price": self.current_price,
                                "target_profit_price": self.current_price * (1 + self.profit_threshold),
                                "stop_loss_price": self.current_price * (1 - self.stop_loss_threshold),
                                "position_value": quantity * self.current_price,
                                "leverage_used": self.leverage
                            }
                        )
            
            elif action == "SELL" and current_position == 0:
                # Open short position
                quantity = self.calculate_position_size(self.current_price)
                if quantity > 0:
                    order = self.place_futures_order("SELL", quantity)
                    if order:
                        logger.info(f"📉 SHORT position opened: {quantity} at {self.current_price}")
                        self.last_trade_time = current_time
                        
                        # Log position change with entry details
                        self._log_position_change(
                            action="OPEN_SHORT",
                            position_before=position_before,
                            position_after=-quantity,
                            reason="Signal: SELL momentum detected",
                            additional_data={
                                "entry_price": self.current_price,
                                "target_profit_price": self.current_price * (1 - self.profit_threshold),
                                "stop_loss_price": self.current_price * (1 + self.stop_loss_threshold),
                                "position_value": quantity * self.current_price,
                                "leverage_used": self.leverage
                            }
                        )
            
            elif current_position != 0:
                # Check exit conditions with detailed information
                should_exit, exit_info = self.check_exit_conditions()
                
                if should_exit and exit_info:
                    # Close position based on type
                    if current_position > 0:
                        # Close long position
                        order = self.place_futures_order("SELL", abs(current_position))
                        action_type = "CLOSE_LONG"
                    elif current_position < 0:
                        # Close short position
                        order = self.place_futures_order("BUY", abs(current_position))
                        action_type = "CLOSE_SHORT"
                    
                    if order:
                        # Log detailed trade closure
                        self._log_trade_close(exit_info, order)
                        
                        # Log basic position change
                        self._log_position_change(
                            action=action_type,
                            position_before=current_position,
                            position_after=0,
                            reason=f"{exit_info['exit_reason']}: {exit_info['profit_pct']:.2f}% {exit_info['position_type']}",
                            additional_data={
                                "profit_loss_pct": exit_info["profit_pct"],
                                "exit_trigger": exit_info["exit_reason"],
                                "unrealized_pnl": exit_info["unrealized_pnl"]
                            }
                        )
                        
                        self.last_trade_time = current_time
        
        except Exception as e:
            logger.error(f"Error executing trade: {e}")
            # Log error to MongoDB with context
            self._log_to_mongodb({
                "type": "error",
                "function": "execute_trade",
                "error": str(e),
                "action": action,
                "current_price": self.current_price,
                "current_position": current_position if 'current_position' in locals() else None
            })
    
    def update_price_and_trade(self):
        """Update price and check for trading opportunities"""
        try:
            # Get current price
            new_price = self.get_current_price()
            if new_price:
                self.current_price = new_price
                self.price_history.append(self.current_price)
                
                # Analyze and potentially trade
                signal = self.analyze_price_movement()
                if signal:
                    self.execute_trade(signal)
                
                # Check exit conditions for existing positions
                self.execute_trade(None) # This will check exit conditions
                
        except Exception as e:
            logger.error(f"Error updating price: {e}")
    
    def start(self):
        """Start the trading bot"""
        logger.info("🚀 Starting Futures Scalping Bot...")
        
        # Initialize futures settings
        if not self.get_symbol_info():
            logger.error("❌ Failed to get symbol info")
            return
        
        if not self.set_margin_type("ISOLATED"):
            logger.error("❌ Failed to set margin type")
            return
        
        if not self.set_leverage():
            logger.error("❌ Failed to set leverage")
            return
        
        # Check initial balance
        balance = self.get_account_balance()
        logger.info(f"💰 Available USDT balance: {balance:.2f}")
        
        if balance < self.trade_amount:
            logger.warning(f"⚠️ Low balance! Available: {balance}, Required: {self.trade_amount}")
        
        self.running = True
        
        # Main trading loop
        try:
            iteration = 0
            while self.running:
                self.update_price_and_trade()
                
                # Log status every 25 iterations
                iteration += 1
                if iteration % 25 == 0:
                    position = self.get_position_info()
                    pos_size = float(position['positionAmt']) if position else 0
                    logger.info(f"💹 Price: {self.current_price:.4f}, Position: {pos_size:.3f}")
                
                time.sleep(self.price_update_interval)
                
        except KeyboardInterrupt:
            logger.info("⏹️ Stopping bot...")
            self.stop()
    
    def stop(self):
        """Stop the trading bot with cleanup and final logging"""
        self.running = False
        
        # Close any open positions before stopping
        try:
            position = self.get_position_info()
            if position and float(position['positionAmt']) != 0:
                logger.info("🔒 Closing open position before stopping...")
                pos_amt = float(position['positionAmt'])
                
                if pos_amt > 0:
                    self.place_futures_order("SELL", abs(pos_amt))
                    self._log_position_change(
                        action="FORCE_CLOSE_LONG",
                        position_before=pos_amt,
                        position_after=0,
                        reason="Bot shutdown - force close position"
                    )
                elif pos_amt < 0:
                    self.place_futures_order("BUY", abs(pos_amt))
                    self._log_position_change(
                        action="FORCE_CLOSE_SHORT",
                        position_before=pos_amt,
                        position_after=0,
                        reason="Bot shutdown - force close position"
                    )
        except Exception as e:
            logger.error(f"Error closing position: {e}")
        
        # Log bot shutdown
        self._log_to_mongodb({
            "type": "bot_shutdown",
            "message": "Trading bot stopped",
            "final_price": self.current_price,
            "total_price_updates": len(self.price_history)
        })
          # Get and log session statistics
        if self.collection is not None:
            try:
                stats = self.get_trading_stats_from_db(days=1)
                if stats:
                    logger.info("📊 Today's Trading Statistics:")
                    for stat in stats:
                        logger.info(f"   {stat['_id']}: {stat['count']} orders, {stat['total_quantity']:.3f} total quantity")
            except Exception as e:
                logger.error(f"Error getting final stats: {e}")
          # Close MongoDB connection
        if self.mongo_client is not None:
            try:
                self.mongo_client.close()
                logger.info("🔌 MongoDB connection closed")
            except Exception as e:
                logger.error(f"Error closing MongoDB: {e}")
        
        logger.info("✅ Bot stopped")

    def get_symbol_trading_rules(self):
        """Get and display symbol trading rules for debugging"""
        if not self.symbol_info:
            logger.warning("Symbol info not loaded")
            return None
        
        rules = {}
        for filter_info in self.symbol_info['filters']:
            filter_type = filter_info['filterType']
            
            if filter_type == 'LOT_SIZE':
                rules['lot_size'] = {
                    'minQty': float(filter_info['minQty']),
                    'maxQty': float(filter_info['maxQty']),
                    'stepSize': float(filter_info['stepSize'])
                }
            elif filter_type == 'MIN_NOTIONAL':
                rules['min_notional'] = float(filter_info['notional'])
            elif filter_type == 'PRICE_FILTER':
                rules['price_filter'] = {
                    'minPrice': float(filter_info['minPrice']),
                    'maxPrice': float(filter_info['maxPrice']),
                    'tickSize': float(filter_info['tickSize'])
                }
        
        logger.info(f"📏 Trading rules for {self.symbol}:")
        if 'lot_size' in rules:
            logger.info(f"   Quantity - Min: {rules['lot_size']['minQty']}, Max: {rules['lot_size']['maxQty']}, Step: {rules['lot_size']['stepSize']}")
        if 'min_notional' in rules:
            logger.info(f"   Min Notional: {rules['min_notional']}")
        if 'price_filter' in rules:
            logger.info(f"   Price - Min: {rules['price_filter']['minPrice']}, Max: {rules['price_filter']['maxPrice']}, Tick: {rules['price_filter']['tickSize']}")
        
        return rules

# Example usage
if __name__ == "__main__":
    try:
        # Initialize bot with environment variables
        bot = BinanceFuturesScalpingBot()
        
        # Start trading
        bot.start()
        
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        logger.info("💡 Please check your .env file or environment variables")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")