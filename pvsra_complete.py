#!/usr/bin/env python3
"""
Complete PVSRA Binance Futures Trading Example
This script demonstrates best practices for using the PVSRA indicator
with Binance Futures including error handling, logging, and risk management.
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd
from dotenv import load_dotenv
import time

# Import our PVSRA modules
from binance_futures_pvsra import BinanceFuturesPVSRA, PVSRATradingBot
from pvsra_dashboard import PVSRAQuickAnalysis


class PVSRATradingSystem:
    """
    Complete trading system using PVSRA signals
    Includes risk management, position tracking, and performance monitoring
    """
    
    def __init__(self, config_file: str = "config.json"):
        # Load configuration
        self.config = self.load_config(config_file)
        
        # Setup logging
        self.setup_logging()
        
        # Load API credentials
        load_dotenv()
        self.api_key = os.getenv('BINANCE_API_KEY')
        self.api_secret = os.getenv('BINANCE_API_SECRET')
        self.testnet = os.getenv('BINANCE_TESTNET', 'true').lower() == 'true'
        
        if not self.api_key or not self.api_secret:
            self.logger.error("API credentials not found in environment variables")
            sys.exit(1)
        
        # Initialize PVSRA
        try:
            self.pvsra = BinanceFuturesPVSRA(
                self.api_key, 
                self.api_secret, 
                self.testnet
            )
            self.logger.info(f"PVSRA initialized (testnet={self.testnet})")
        except Exception as e:
            self.logger.error(f"Failed to initialize PVSRA: {e}")
            sys.exit(1)
        
        # Trading state
        self.active_positions = {}
        self.trade_history = []
        self.performance_metrics = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_pnl': 0.0,
            'max_drawdown': 0.0
        }
        
        # Register callbacks
        self.pvsra.add_alert_callback(self.on_pvsra_alert)
        self.pvsra.add_trade_callback(self.on_trade_executed)
    
    def load_config(self, config_file: str) -> Dict:
        """Load configuration from JSON file"""
        default_config = {
            "trading": {
                "symbols": ["BTCUSDT", "ETHUSDT"],
                "intervals": ["5m", "15m"],
                "max_positions": 2,
                "risk_per_trade": 0.01,
                "stop_loss_pct": 0.02,
                "take_profit_pct": 0.04,
                "use_trailing_stop": True,
                "trailing_stop_pct": 0.01
            },
            "filters": {
                "min_volume_ratio": 2.0,
                "require_trend_confirmation": True,
                "trend_ma_period": 20,
                "min_spread_pct": 0.001
            },
            "notifications": {
                "telegram_enabled": False,
                "telegram_token": "",
                "telegram_chat_id": "",
                "discord_webhook": ""
            }
        }
        
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                loaded_config = json.load(f)
                # Merge with defaults
                for key in default_config:
                    if key in loaded_config:
                        default_config[key].update(loaded_config[key])
        else:
            # Save default config
            with open(config_file, 'w') as f:
                json.dump(default_config, f, indent=4)
        
        return default_config
    
    def setup_logging(self):
        """Setup logging configuration"""
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        # Create logs directory
        os.makedirs('logs', exist_ok=True)
        
        # File handler
        file_handler = logging.FileHandler(
            f'logs/pvsra_trading_{datetime.now().strftime("%Y%m%d")}.log'
        )
        file_handler.setFormatter(logging.Formatter(log_format))
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(log_format))
        
        # Setup logger
        self.logger = logging.getLogger('PVSRATrading')
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def on_pvsra_alert(self, symbol: str, alert: Dict):
        """Handle PVSRA alerts with filtering and validation"""
        self.logger.info(f"Alert received for {symbol}: {alert['alert']}")
        
        # Check if we should trade this alert
        if not self.should_trade_alert(symbol, alert):
            return
        
        # Determine trade direction
        if 'Bull' in alert['alert'] and alert['condition'] == 'climax':
            self.evaluate_long_entry(symbol, alert)
        elif 'Bear' in alert['alert'] and alert['condition'] == 'climax':
            self.evaluate_short_entry(symbol, alert)
    
    def should_trade_alert(self, symbol: str, alert: Dict) -> bool:
        """Apply filters to determine if alert should be traded"""
        # Check if symbol is in watchlist
        if symbol not in self.config['trading']['symbols']:
            return False
        
        # Check max positions
        if len(self.active_positions) >= self.config['trading']['max_positions']:
            self.logger.info(f"Max positions reached ({self.config['trading']['max_positions']})")
            return False
        
        # Check if already have position in this symbol
        if symbol in self.active_positions:
            self.logger.info(f"Already have position in {symbol}")
            return False
        
        # Only trade climax conditions
        if alert['condition'] != 'climax':
            return False
        
        return True
    
    def evaluate_long_entry(self, symbol: str, alert: Dict):
        """Evaluate and execute long entry"""
        try:
            # Get additional market data for confirmation
            df = self.pvsra.get_futures_klines(symbol, '5m', 50)
            if df.empty:
                return
            
            # Apply trend filter if enabled
            if self.config['filters']['require_trend_confirmation']:
                ma_period = self.config['filters']['trend_ma_period']
                current_price = alert['price']
                ma_value = df['close'].rolling(ma_period).mean().iloc[-1]
                
                if current_price < ma_value:
                    self.logger.info(f"Long entry rejected: price below MA{ma_period}")
                    return
            
            # Check spread
            spread_pct = (df['high'].iloc[-1] - df['low'].iloc[-1]) / df['close'].iloc[-1]
            if spread_pct < self.config['filters']['min_spread_pct']:
                self.logger.info(f"Long entry rejected: spread too small ({spread_pct:.4f})")
                return
            
            # Calculate position size
            position_size = self.calculate_position_size(symbol, alert['price'])
            
            if position_size > 0:
                # Place order
                self.open_long_position(symbol, position_size, alert)
                
        except Exception as e:
            self.logger.error(f"Error evaluating long entry: {e}")
    
    def evaluate_short_entry(self, symbol: str, alert: Dict):
        """Evaluate and execute short entry"""
        try:
            # Get additional market data for confirmation
            df = self.pvsra.get_futures_klines(symbol, '5m', 50)
            if df.empty:
                return
            
            # Apply trend filter if enabled
            if self.config['filters']['require_trend_confirmation']:
                ma_period = self.config['filters']['trend_ma_period']
                current_price = alert['price']
                ma_value = df['close'].rolling(ma_period).mean().iloc[-1]
                
                if current_price > ma_value:
                    self.logger.info(f"Short entry rejected: price above MA{ma_period}")
                    return
            
            # Check spread
            spread_pct = (df['high'].iloc[-1] - df['low'].iloc[-1]) / df['close'].iloc[-1]
            if spread_pct < self.config['filters']['min_spread_pct']:
                self.logger.info(f"Short entry rejected: spread too small ({spread_pct:.4f})")
                return
            
            # Calculate position size
            position_size = self.calculate_position_size(symbol, alert['price'])
            
            if position_size > 0:
                # Place order
                self.open_short_position(symbol, position_size, alert)
                
        except Exception as e:
            self.logger.error(f"Error evaluating short entry: {e}")
    
    def calculate_position_size(self, symbol: str, entry_price: float) -> float:
        """Calculate position size based on risk management rules"""
        try:
            # Get account balance
            balance = self.pvsra.get_balance()
            
            # Calculate risk amount
            risk_amount = balance * self.config['trading']['risk_per_trade']
            
            # Calculate stop distance
            stop_distance = entry_price * self.config['trading']['stop_loss_pct']
            
            # Calculate position size
            position_size = risk_amount / stop_distance
            
            # Get symbol info for precision (simplified)
            # In production, fetch from exchange info
            precision = 3
            position_size = round(position_size, precision)
            
            # Validate minimum order size
            min_order_value = 10  # USDT
            if position_size * entry_price < min_order_value:
                self.logger.warning(f"Position size too small: ${position_size * entry_price:.2f}")
                return 0
            
            return position_size
            
        except Exception as e:
            self.logger.error(f"Error calculating position size: {e}")
            return 0
    
    def open_long_position(self, symbol: str, size: float, alert: Dict):
        """Open a long position with risk management"""
        try:
            entry_price = alert['price']
            
            # Place market order
            order = self.pvsra.place_market_order(symbol, 'BUY', size)
            
            if order:
                # Calculate stop loss and take profit
                stop_price = entry_price * (1 - self.config['trading']['stop_loss_pct'])
                tp_price = entry_price * (1 + self.config['trading']['take_profit_pct'])
                
                # Set stop loss
                self.pvsra.set_stop_loss(symbol, 'BUY', stop_price, size)
                
                # Set take profit
                self.pvsra.place_limit_order(symbol, 'SELL', size, tp_price)
                
                # Record position
                self.active_positions[symbol] = {
                    'side': 'LONG',
                    'entry_price': entry_price,
                    'size': size,
                    'stop_loss': stop_price,
                    'take_profit': tp_price,
                    'entry_time': datetime.now(),
                    'alert': alert
                }
                
                self.logger.info(
                    f"LONG position opened: {symbol} "
                    f"Size: {size} @ ${entry_price:.2f} "
                    f"SL: ${stop_price:.2f} TP: ${tp_price:.2f}"
                )
                
                # Send notification
                self.send_notification(
                    f"📈 LONG {symbol}\n"
                    f"Entry: ${entry_price:.2f}\n"
                    f"Size: {size}\n"
                    f"Stop: ${stop_price:.2f}\n"
                    f"Target: ${tp_price:.2f}"
                )
                
        except Exception as e:
            self.logger.error(f"Error opening long position: {e}")
    
    def open_short_position(self, symbol: str, size: float, alert: Dict):
        """Open a short position with risk management"""
        try:
            entry_price = alert['price']
            
            # Place market order
            order = self.pvsra.place_market_order(symbol, 'SELL', size)
            
            if order:
                # Calculate stop loss and take profit
                stop_price = entry_price * (1 + self.config['trading']['stop_loss_pct'])
                tp_price = entry_price * (1 - self.config['trading']['take_profit_pct'])
                
                # Set stop loss
                self.pvsra.set_stop_loss(symbol, 'SELL', stop_price, size)
                
                # Set take profit
                self.pvsra.place_limit_order(symbol, 'BUY', size, tp_price)
                
                # Record position
                self.active_positions[symbol] = {
                    'side': 'SHORT',
                    'entry_price': entry_price,
                    'size': size,
                    'stop_loss': stop_price,
                    'take_profit': tp_price,
                    'entry_time': datetime.now(),
                    'alert': alert
                }
                
                self.logger.info(
                    f"SHORT position opened: {symbol} "
                    f"Size: {size} @ ${entry_price:.2f} "
                    f"SL: ${stop_price:.2f} TP: ${tp_price:.2f}"
                )
                
                # Send notification
                self.send_notification(
                    f"📉 SHORT {symbol}\n"
                    f"Entry: ${entry_price:.2f}\n"
                    f"Size: {size}\n"
                    f"Stop: ${stop_price:.2f}\n"
                    f"Target: ${tp_price:.2f}"
                )
                
        except Exception as e:
            self.logger.error(f"Error opening short position: {e}")
    
    def on_trade_executed(self, order: Dict):
        """Handle trade execution callback"""
        self.logger.info(f"Trade executed: {order}")
        self.performance_metrics['total_trades'] += 1
    
    def update_positions(self):
        """Update and manage open positions"""
        for symbol, position in list(self.active_positions.items()):
            try:
                # Get current position from exchange
                current_pos = self.pvsra.get_position(symbol)
                
                if not current_pos or float(current_pos.get('positionAmt', 0)) == 0:
                    # Position closed
                    self.close_position_tracking(symbol, current_pos)
                else:
                    # Update trailing stop if enabled
                    if self.config['trading']['use_trailing_stop']:
                        self.update_trailing_stop(symbol, position, current_pos)
                
            except Exception as e:
                self.logger.error(f"Error updating position {symbol}: {e}")
    
    def update_trailing_stop(self, symbol: str, position: Dict, current_pos: Dict):
        """Update trailing stop loss"""
        try:
            current_price = float(current_pos['markPrice'])
            trailing_pct = self.config['trading']['trailing_stop_pct']
            
            if position['side'] == 'LONG':
                # For long positions, move stop up
                new_stop = current_price * (1 - trailing_pct)
                if new_stop > position['stop_loss']:
                    self.pvsra.set_stop_loss(symbol, 'BUY', new_stop, position['size'])
                    position['stop_loss'] = new_stop
                    self.logger.info(f"Trailing stop updated for {symbol}: ${new_stop:.2f}")
            
            else:  # SHORT
                # For short positions, move stop down
                new_stop = current_price * (1 + trailing_pct)
                if new_stop < position['stop_loss']:
                    self.pvsra.set_stop_loss(symbol, 'SELL', new_stop, position['size'])
                    position['stop_loss'] = new_stop
                    self.logger.info(f"Trailing stop updated for {symbol}: ${new_stop:.2f}")
                    
        except Exception as e:
            self.logger.error(f"Error updating trailing stop: {e}")
    
    def close_position_tracking(self, symbol: str, final_pos: Dict):
        """Close position tracking and calculate PnL"""
        if symbol in self.active_positions:
            position = self.active_positions[symbol]
            
            # Calculate PnL
            if final_pos and 'realizedPnl' in final_pos:
                pnl = float(final_pos['realizedPnl'])
            else:
                # Estimate PnL
                pnl = 0
            
            # Update metrics
            self.performance_metrics['total_pnl'] += pnl
            if pnl > 0:
                self.performance_metrics['winning_trades'] += 1
            else:
                self.performance_metrics['losing_trades'] += 1
            
            # Record trade
            self.trade_history.append({
                'symbol': symbol,
                'side': position['side'],
                'entry_price': position['entry_price'],
                'entry_time': position['entry_time'],
                'exit_time': datetime.now(),
                'pnl': pnl,
                'size': position['size']
            })
            
            # Remove from active positions
            del self.active_positions[symbol]
            
            self.logger.info(f"Position closed: {symbol} PnL: ${pnl:.2f}")
            self.send_notification(f"Position closed: {symbol}\nPnL: ${pnl:.2f}")
    
    def send_notification(self, message: str):
        """Send notifications via configured channels"""
        # Implement Telegram/Discord notifications here
        pass
    
    def get_performance_report(self) -> Dict:
        """Generate performance report"""
        total_trades = self.performance_metrics['total_trades']
        
        if total_trades > 0:
            win_rate = (self.performance_metrics['winning_trades'] / total_trades) * 100
            avg_pnl = self.performance_metrics['total_pnl'] / total_trades
        else:
            win_rate = 0
            avg_pnl = 0
        
        return {
            'total_trades': total_trades,
            'winning_trades': self.performance_metrics['winning_trades'],
            'losing_trades': self.performance_metrics['losing_trades'],
            'win_rate': f"{win_rate:.1f}%",
            'total_pnl': f"${self.performance_metrics['total_pnl']:.2f}",
            'average_pnl': f"${avg_pnl:.2f}",
            'active_positions': len(self.active_positions)
        }
    
    def run(self):
        """Main trading loop"""
        self.logger.info("Starting PVSRA Trading System")
        self.logger.info(f"Monitoring symbols: {self.config['trading']['symbols']}")
        
        # Start real-time monitoring for all symbols
        for symbol in self.config['trading']['symbols']:
            for interval in self.config['trading']['intervals']:
                self.pvsra.start_realtime_analysis(symbol, interval)
                self.logger.info(f"Started monitoring {symbol} on {interval}")
        
        # Main loop
        try:
            while True:
                # Update positions
                self.update_positions()
                
                # Log performance every hour
                if datetime.now().minute == 0:
                    report = self.get_performance_report()
                    self.logger.info(f"Performance Report: {report}")
                
                # Sleep
                time.sleep(30)
                
        except KeyboardInterrupt:
            self.logger.info("Shutting down trading system...")
            self.shutdown()
    
    def shutdown(self):
        """Gracefully shutdown the trading system"""
        # Close all WebSocket connections
        for symbol, ws in self.pvsra.ws_connections.items():
            ws.close()
        
        # Log final performance
        report = self.get_performance_report()
        self.logger.info(f"Final Performance Report: {report}")
        
        # Save trade history
        if self.trade_history:
            df = pd.DataFrame(self.trade_history)
            filename = f"trade_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            df.to_csv(filename, index=False)
            self.logger.info(f"Trade history saved to {filename}")


def main():
    """Main entry point"""
    # Create config file if it doesn't exist
    if not os.path.exists('config.json'):
        print("Creating default config.json...")
        system = PVSRATradingSystem()
        print("Please edit config.json and add your API credentials to .env file")
        return
    
    # Check for .env file
    if not os.path.exists('.env'):
        print("Please create a .env file with your Binance API credentials:")
        print("BINANCE_API_KEY=your_api_key")
        print("BINANCE_API_SECRET=your_api_secret")
        print("BINANCE_TESTNET=true")
        return
    
    # Initialize and run trading system
    system = PVSRATradingSystem()
    
    # Display initial status
    account = system.pvsra.get_account_info()
    if account:
        balance = system.pvsra.get_balance()
        print(f"Account Balance: ${balance:.2f} USDT")
        print(f"Testnet Mode: {system.testnet}")
    
    # Run system
    system.run()


if __name__ == "__main__":
    main()