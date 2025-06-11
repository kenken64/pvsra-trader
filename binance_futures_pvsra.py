import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import asyncio
import json
from typing import Dict, List, Optional, Callable
import logging
from decimal import Decimal
import websocket
import threading
import time

# Binance API imports
from binance.client import Client
from binance.enums import *
from binance.exceptions import BinanceAPIException
import binance.websockets as bws

# Import the PVSRA class (assuming it's in pvsra.py)
from pvsra import PVSRA


class BinanceFuturesPVSRA:
    """
    PVSRA integration for Binance Futures trading
    Provides real-time analysis, alerts, and automated trading capabilities
    """
    
    def __init__(self, api_key: str, api_secret: str, testnet: bool = False):
        """
        Initialize Binance Futures PVSRA
        
        Parameters:
        - api_key: Binance API key
        - api_secret: Binance API secret
        - testnet: Use testnet if True (recommended for testing)
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        
        # Initialize Binance client
        if testnet:
            self.client = Client(api_key, api_secret, testnet=True)
            self.ws_base = "wss://stream.binancefuture.com"
        else:
            self.client = Client(api_key, api_secret)
            self.ws_base = "wss://fstream.binance.com"
        
        # Initialize PVSRA analyzer
        self.pvsra = PVSRA(lookback_period=10, climax_multiplier=2.0, rising_multiplier=1.5)
        
        # Storage for real-time data
        self.klines_data = {}
        self.current_positions = {}
        self.active_orders = {}
        
        # WebSocket connections
        self.ws_connections = {}
        
        # Callbacks
        self.alert_callbacks = []
        self.trade_callbacks = []
        
        # Logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
    def get_futures_klines(self, symbol: str, interval: str, limit: int = 100) -> pd.DataFrame:
        """
        Fetch historical klines data from Binance Futures
        
        Parameters:
        - symbol: Trading pair (e.g., 'BTCUSDT')
        - interval: Kline interval (e.g., '1m', '5m', '1h')
        - limit: Number of klines to fetch
        
        Returns:
        - DataFrame with OHLCV data
        """
        try:
            klines = self.client.futures_klines(
                symbol=symbol,
                interval=interval,
                limit=limit
            )
            
            # Convert to DataFrame
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                'taker_buy_quote', 'ignore'
            ])
            
            # Convert types
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            # Convert to float
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = df[col].astype(float)
            
            # Keep only OHLCV
            df = df[['open', 'high', 'low', 'close', 'volume']]
            
            return df
            
        except BinanceAPIException as e:
            self.logger.error(f"Error fetching klines: {e}")
            return pd.DataFrame()
    
    def analyze_symbol(self, symbol: str, interval: str = '5m', limit: int = 100) -> pd.DataFrame:
        """
        Analyze a symbol using PVSRA
        
        Parameters:
        - symbol: Trading pair
        - interval: Timeframe
        - limit: Number of bars to analyze
        
        Returns:
        - DataFrame with PVSRA analysis
        """
        # Fetch data
        df = self.get_futures_klines(symbol, interval, limit)
        
        if df.empty:
            return df
        
        # Apply PVSRA analysis
        result = self.pvsra.calculate(df)
        
        # Check for alerts in the latest bars
        alerts = self.pvsra.get_alerts(result.tail(5))
        if alerts:
            for alert in alerts:
                self._trigger_alert(symbol, alert)
        
        return result
    
    def start_realtime_analysis(self, symbol: str, interval: str = '1m'):
        """
        Start real-time PVSRA analysis using WebSocket
        
        Parameters:
        - symbol: Trading pair
        - interval: Kline interval
        """
        # Initialize storage for this symbol
        if symbol not in self.klines_data:
            # Fetch initial historical data
            self.klines_data[symbol] = self.get_futures_klines(symbol, interval, 100)
        
        # WebSocket endpoint
        stream_name = f"{symbol.lower()}@kline_{interval}"
        ws_endpoint = f"{self.ws_base}/ws/{stream_name}"
        
        def on_message(ws, message):
            self._process_kline_message(symbol, message)
        
        def on_error(ws, error):
            self.logger.error(f"WebSocket error for {symbol}: {error}")
        
        def on_close(ws):
            self.logger.info(f"WebSocket closed for {symbol}")
        
        def on_open(ws):
            self.logger.info(f"WebSocket opened for {symbol}")
        
        # Create WebSocket connection
        ws = websocket.WebSocketApp(
            ws_endpoint,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
            on_open=on_open
        )
        
        # Store connection
        self.ws_connections[symbol] = ws
        
        # Run in separate thread
        ws_thread = threading.Thread(target=ws.run_forever)
        ws_thread.daemon = True
        ws_thread.start()
        
        self.logger.info(f"Started real-time analysis for {symbol}")
    
    def _process_kline_message(self, symbol: str, message: str):
        """Process incoming kline data from WebSocket"""
        try:
            data = json.loads(message)
            kline = data['k']
            
            # Create new row
            new_row = pd.DataFrame({
                'open': [float(kline['o'])],
                'high': [float(kline['h'])],
                'low': [float(kline['l'])],
                'close': [float(kline['c'])],
                'volume': [float(kline['v'])]
            }, index=[pd.to_datetime(kline['t'], unit='ms')])
            
            # Update or append to existing data
            if kline['x']:  # Kline closed
                self.klines_data[symbol] = pd.concat([
                    self.klines_data[symbol][:-1], 
                    new_row
                ])
                
                # Keep only last 200 bars
                if len(self.klines_data[symbol]) > 200:
                    self.klines_data[symbol] = self.klines_data[symbol].tail(200)
                
                # Run PVSRA analysis
                result = self.pvsra.calculate(self.klines_data[symbol])
                
                # Check latest bar for alerts
                latest = result.iloc[-1]
                if latest['alert']:
                    alert_info = {
                        'symbol': symbol,
                        'timestamp': result.index[-1],
                        'alert': latest['alert'],
                        'price': latest['close'],
                        'volume': latest['volume'],
                        'condition': latest['condition']
                    }
                    self._trigger_alert(symbol, alert_info)
            else:
                # Update current bar
                self.klines_data[symbol].iloc[-1] = new_row.iloc[0]
                
        except Exception as e:
            self.logger.error(f"Error processing kline message: {e}")
    
    def _trigger_alert(self, symbol: str, alert: Dict):
        """Trigger alert callbacks"""
        self.logger.info(f"ALERT {symbol}: {alert['alert']} at ${alert['price']}")
        
        for callback in self.alert_callbacks:
            try:
                callback(symbol, alert)
            except Exception as e:
                self.logger.error(f"Error in alert callback: {e}")
    
    def add_alert_callback(self, callback: Callable):
        """Add callback function for alerts"""
        self.alert_callbacks.append(callback)
    
    def add_trade_callback(self, callback: Callable):
        """Add callback function for trades"""
        self.trade_callbacks.append(callback)
    
    # Trading functions
    def get_account_info(self) -> Dict:
        """Get futures account information"""
        try:
            return self.client.futures_account()
        except Exception as e:
            self.logger.error(f"Error getting account info: {e}")
            return {}
    
    def get_balance(self, asset: str = 'USDT') -> float:
        """Get available balance for an asset"""
        account = self.get_account_info()
        for balance in account.get('assets', []):
            if balance['asset'] == asset:
                return float(balance['availableBalance'])
        return 0.0
    
    def get_position(self, symbol: str) -> Dict:
        """Get current position for a symbol"""
        try:
            positions = self.client.futures_position_information(symbol=symbol)
            return positions[0] if positions else {}
        except Exception as e:
            self.logger.error(f"Error getting position: {e}")
            return {}
    
    def place_market_order(self, symbol: str, side: str, quantity: float) -> Dict:
        """
        Place a market order
        
        Parameters:
        - symbol: Trading pair
        - side: 'BUY' or 'SELL'
        - quantity: Order quantity
        
        Returns:
        - Order response
        """
        try:
            order = self.client.futures_create_order(
                symbol=symbol,
                side=side,
                type=ORDER_TYPE_MARKET,
                quantity=quantity
            )
            
            self.logger.info(f"Market order placed: {side} {quantity} {symbol}")
            
            # Trigger trade callback
            for callback in self.trade_callbacks:
                callback(order)
            
            return order
            
        except BinanceAPIException as e:
            self.logger.error(f"Error placing order: {e}")
            return {}
    
    def place_limit_order(self, symbol: str, side: str, quantity: float, price: float) -> Dict:
        """Place a limit order"""
        try:
            order = self.client.futures_create_order(
                symbol=symbol,
                side=side,
                type=ORDER_TYPE_LIMIT,
                timeInForce=TIME_IN_FORCE_GTC,
                quantity=quantity,
                price=price
            )
            
            self.logger.info(f"Limit order placed: {side} {quantity} {symbol} @ {price}")
            return order
            
        except BinanceAPIException as e:
            self.logger.error(f"Error placing limit order: {e}")
            return {}
    
    def set_stop_loss(self, symbol: str, side: str, stop_price: float, quantity: float) -> Dict:
        """Set a stop loss order"""
        try:
            # For stop loss, side is opposite of position
            stop_side = SIDE_SELL if side == SIDE_BUY else SIDE_BUY
            
            order = self.client.futures_create_order(
                symbol=symbol,
                side=stop_side,
                type=ORDER_TYPE_STOP_MARKET,
                stopPrice=stop_price,
                quantity=quantity,
                reduceOnly=True
            )
            
            self.logger.info(f"Stop loss set for {symbol} at {stop_price}")
            return order
            
        except BinanceAPIException as e:
            self.logger.error(f"Error setting stop loss: {e}")
            return {}
    
    def close_position(self, symbol: str) -> Dict:
        """Close all positions for a symbol"""
        position = self.get_position(symbol)
        
        if position and float(position.get('positionAmt', 0)) != 0:
            quantity = abs(float(position['positionAmt']))
            side = SIDE_SELL if float(position['positionAmt']) > 0 else SIDE_BUY
            
            return self.place_market_order(symbol, side, quantity)
        
        return {}


class PVSRATradingBot:
    """
    Automated trading bot using PVSRA signals
    """
    
    def __init__(self, binance_pvsra: BinanceFuturesPVSRA, config: Dict):
        """
        Initialize trading bot
        
        Parameters:
        - binance_pvsra: BinanceFuturesPVSRA instance
        - config: Trading configuration
        """
        self.pvsra = binance_pvsra
        self.config = config
        self.active_trades = {}
        
        # Register callbacks
        self.pvsra.add_alert_callback(self.on_pvsra_alert)
        
    def on_pvsra_alert(self, symbol: str, alert: Dict):
        """Handle PVSRA alerts"""
        # Check if we should trade this alert
        if not self.should_trade(symbol, alert):
            return
        
        # Execute trade based on alert
        if 'Bull' in alert['alert'] and alert['condition'] == 'climax':
            self.open_long_position(symbol, alert)
        elif 'Bear' in alert['alert'] and alert['condition'] == 'climax':
            self.open_short_position(symbol, alert)
    
    def should_trade(self, symbol: str, alert: Dict) -> bool:
        """Determine if we should trade based on alert"""
        # Check if symbol is in our watchlist
        if symbol not in self.config.get('symbols', []):
            return False
        
        # Check if we already have a position
        if symbol in self.active_trades:
            return False
        
        # Check if it's a climax condition
        if alert['condition'] != 'climax':
            return False
        
        # Additional filters can be added here
        return True
    
    def open_long_position(self, symbol: str, alert: Dict):
        """Open a long position"""
        try:
            # Calculate position size
            balance = self.pvsra.get_balance()
            risk_amount = balance * self.config.get('risk_per_trade', 0.01)
            
            # Get current price
            current_price = alert['price']
            
            # Calculate quantity
            quantity = risk_amount / current_price
            quantity = round(quantity, self.get_quantity_precision(symbol))
            
            # Place order
            order = self.pvsra.place_market_order(symbol, SIDE_BUY, quantity)
            
            if order:
                # Set stop loss
                stop_price = current_price * (1 - self.config.get('stop_loss_pct', 0.02))
                self.pvsra.set_stop_loss(symbol, SIDE_BUY, stop_price, quantity)
                
                # Record trade
                self.active_trades[symbol] = {
                    'side': 'LONG',
                    'entry_price': current_price,
                    'quantity': quantity,
                    'stop_loss': stop_price,
                    'alert': alert
                }
                
                self.pvsra.logger.info(f"Opened LONG position for {symbol}")
                
        except Exception as e:
            self.pvsra.logger.error(f"Error opening long position: {e}")
    
    def open_short_position(self, symbol: str, alert: Dict):
        """Open a short position"""
        try:
            # Calculate position size
            balance = self.pvsra.get_balance()
            risk_amount = balance * self.config.get('risk_per_trade', 0.01)
            
            # Get current price
            current_price = alert['price']
            
            # Calculate quantity
            quantity = risk_amount / current_price
            quantity = round(quantity, self.get_quantity_precision(symbol))
            
            # Place order
            order = self.pvsra.place_market_order(symbol, SIDE_SELL, quantity)
            
            if order:
                # Set stop loss
                stop_price = current_price * (1 + self.config.get('stop_loss_pct', 0.02))
                self.pvsra.set_stop_loss(symbol, SIDE_SELL, stop_price, quantity)
                
                # Record trade
                self.active_trades[symbol] = {
                    'side': 'SHORT',
                    'entry_price': current_price,
                    'quantity': quantity,
                    'stop_loss': stop_price,
                    'alert': alert
                }
                
                self.pvsra.logger.info(f"Opened SHORT position for {symbol}")
                
        except Exception as e:
            self.pvsra.logger.error(f"Error opening short position: {e}")
    
    def get_quantity_precision(self, symbol: str) -> int:
        """Get quantity precision for a symbol"""
        # This should be fetched from exchange info
        # Simplified version
        return 3
    
    def run(self, symbols: List[str], interval: str = '5m'):
        """Start the trading bot"""
        self.pvsra.logger.info(f"Starting PVSRA Trading Bot for {symbols}")
        
        # Start real-time analysis for each symbol
        for symbol in symbols:
            self.pvsra.start_realtime_analysis(symbol, interval)
        
        # Keep running
        try:
            while True:
                time.sleep(60)  # Check every minute
                self.check_positions()
        except KeyboardInterrupt:
            self.pvsra.logger.info("Stopping trading bot...")
    
    def check_positions(self):
        """Check and manage open positions"""
        for symbol, trade in list(self.active_trades.items()):
            position = self.pvsra.get_position(symbol)
            
            if position and float(position.get('positionAmt', 0)) == 0:
                # Position closed
                del self.active_trades[symbol]
                self.pvsra.logger.info(f"Position closed for {symbol}")


# Example usage
if __name__ == "__main__":
    # Configuration
    API_KEY = "your_api_key"
    API_SECRET = "your_api_secret"
    
    # Trading bot configuration
    bot_config = {
        'symbols': ['BTCUSDT', 'ETHUSDT'],
        'risk_per_trade': 0.01,  # 1% risk per trade
        'stop_loss_pct': 0.02,   # 2% stop loss
        'take_profit_pct': 0.04  # 4% take profit
    }
    
    # Initialize PVSRA for Binance Futures
    binance_pvsra = BinanceFuturesPVSRA(API_KEY, API_SECRET, testnet=True)
    
    # Example 1: Simple analysis
    print("=== BTCUSDT Analysis ===")
    result = binance_pvsra.analyze_symbol('BTCUSDT', '1h', 50)
    
    if not result.empty:
        # Get statistics
        stats = binance_pvsra.pvsra.get_statistics(result)
        print(f"Climax bars: {stats['climax_bars']} ({stats['climax_percentage']:.1f}%)")
        print(f"Rising bars: {stats['rising_bars']} ({stats['rising_percentage']:.1f}%)")
        
        # Show recent alerts
        alerts = binance_pvsra.pvsra.get_alerts(result.tail(10))
        if alerts:
            print("\nRecent Alerts:")
            for alert in alerts:
                print(f"{alert['timestamp']}: {alert['alert']} at ${alert['price']:.2f}")
    
    # Example 2: Real-time monitoring with custom alerts
    def custom_alert_handler(symbol, alert):
        print(f"\n🚨 CUSTOM ALERT for {symbol}:")
        print(f"   {alert['alert']} at ${alert['price']:.2f}")
        print(f"   Volume: {alert['volume']:,.0f}")
        
        # Send notification, log to file, etc.
    
    binance_pvsra.add_alert_callback(custom_alert_handler)
    
    # Start real-time analysis
    binance_pvsra.start_realtime_analysis('BTCUSDT', '1m')
    
    # Example 3: Automated trading bot
    # trading_bot = PVSRATradingBot(binance_pvsra, bot_config)
    # trading_bot.run(['BTCUSDT', 'ETHUSDT'], '5m')