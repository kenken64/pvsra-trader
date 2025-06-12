import requests
import time
from datetime import datetime, timezone
import json
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, DuplicateKeyError
import logging

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BinanceFundingTracker:
    def __init__(self, mongodb_uri=None, db_name=None, collection_name=None):
        self.base_url = "https://fapi.binance.com"
        
        # Load configuration from environment variables with fallbacks
        self.mongodb_uri = mongodb_uri or os.getenv('MONGODB_URI', 'mongodb://localhost:27017')
        self.db_name = db_name or os.getenv('MONGODB_DATABASE', 'test')
        self.collection_name = collection_name or os.getenv('MONGODB_COLLECTION_FUNDINGRATE', 'funding_rates')
        
        # Log configuration (hide password for security)
        safe_uri = self.mongodb_uri.split('@')[1] if '@' in self.mongodb_uri else self.mongodb_uri
        logger.info(f"MongoDB Config - URI: ***@{safe_uri}, DB: {self.db_name}, Collection: {self.collection_name}")
        
        self.client = None
        self.db = None
        self.collection = None
        self.connect_to_mongodb()
        
    def connect_to_mongodb(self):
        """Connect to MongoDB"""
        try:
            self.client = MongoClient(self.mongodb_uri, serverSelectionTimeoutMS=5000)
            # Test connection
            self.client.admin.command('ping')
            self.db = self.client[self.db_name]
            self.collection = self.db[self.collection_name]
            
            # Create indexes for better performance
            self.collection.create_index([("symbol", 1), ("timestamp", 1)], unique=True)
            self.collection.create_index([("date", 1)])
            self.collection.create_index([("symbol", 1)])
            
            logger.info(f"Connected to MongoDB: {self.db_name}.{self.collection_name}")
            
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    def get_available_symbols(self):
        """Get list of available futures symbols from Binance"""
        try:
            url = f"{self.base_url}/fapi/v1/exchangeInfo"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            symbols = []
            for symbol_info in data['symbols']:
                if symbol_info['status'] == 'TRADING':
                    symbols.append({
                        'symbol': symbol_info['symbol'],
                        'baseAsset': symbol_info['baseAsset'],
                        'quoteAsset': symbol_info['quoteAsset'],
                        'contractType': symbol_info.get('contractType', 'PERPETUAL')
                    })
            
            logger.info(f"Found {len(symbols)} active trading symbols")
            return symbols
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching available symbols: {e}")
            return []
    
    def find_symbol_variations(self, base_asset="SUI"):
        """Find all variations of a symbol (e.g., SUIUSDT, SUIUSDC, etc.)"""
        symbols = self.get_available_symbols()
        variations = [s for s in symbols if s['baseAsset'] == base_asset.upper()]
        
        logger.info(f"Found {len(variations)} variations for {base_asset}:")
        for var in variations:
            logger.info(f"  {var['symbol']} ({var['baseAsset']}/{var['quoteAsset']})")
        
        return variations
    
    def validate_symbol(self, symbol):
        """Validate if a symbol exists and is tradeable"""
        try:
            url = f"{self.base_url}/fapi/v1/exchangeInfo"
            params = {"symbol": symbol}
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 400:
                logger.error(f"Symbol {symbol} does not exist on Binance Futures")
                return False
            
            response.raise_for_status()
            data = response.json()
            
            if 'symbols' in data and len(data['symbols']) > 0:
                symbol_info = data['symbols'][0]
                if symbol_info['status'] == 'TRADING':
                    logger.info(f"Symbol {symbol} is valid and trading")
                    return True
                else:
                    logger.warning(f"Symbol {symbol} exists but status is: {symbol_info['status']}")
                    return False
            else:
                logger.error(f"Symbol {symbol} not found")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error validating symbol {symbol}: {e}")
            return False
    
    def get_funding_rate(self, symbol="SUIUSDT"):
        """Get the latest funding rate for a symbol"""
        try:
            url = f"{self.base_url}/fapi/v1/fundingRate"
            params = {"symbol": symbol, "limit": 1}
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 400:
                logger.error(f"Invalid symbol: {symbol}")
                return None
            elif response.status_code == 403:
                logger.error(f"Access forbidden for symbol: {symbol}")
                return None
            
            response.raise_for_status()
            data = response.json()
            
            if data and len(data) > 0:
                funding_data = data[0]
                return {
                    "symbol": funding_data["symbol"],
                    "funding_rate": float(funding_data["fundingRate"]),
                    "funding_time": int(funding_data["fundingTime"]),
                    "mark_price": float(funding_data.get("markPrice", 0))
                }
            else:
                logger.error(f"No funding rate data found for {symbol}")
                return None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching funding rate for {symbol}: {e}")
            return None
    
    def calculate_next_funding_time(self, last_funding_time_ms):
        """Calculate next funding time (funding happens every 8 hours at 00:00, 08:00, 16:00 UTC)"""
        # Funding times in UTC: 00:00, 08:00, 16:00 (every 8 hours)
        funding_hours = [0, 8, 16]
        
        last_funding_dt = datetime.fromtimestamp(last_funding_time_ms / 1000, tz=timezone.utc)
        current_dt = datetime.now(timezone.utc)
        
        # Find next funding hour
        current_hour = current_dt.hour
        next_funding_hour = None
        
        for hour in funding_hours:
            if hour > current_hour:
                next_funding_hour = hour
                break
        
        # If no funding hour found today, use first hour of next day
        if next_funding_hour is None:
            next_funding_hour = funding_hours[0]
            next_funding_dt = current_dt.replace(hour=next_funding_hour, minute=0, second=0, microsecond=0)
            next_funding_dt = next_funding_dt.replace(day=next_funding_dt.day + 1)
        else:
            next_funding_dt = current_dt.replace(hour=next_funding_hour, minute=0, second=0, microsecond=0)
        
        return int(next_funding_dt.timestamp() * 1000)
    
    def calculate_countdown(self, next_funding_time_ms):
        """Calculate countdown to next funding time"""
        current_time_ms = int(time.time() * 1000)
        time_diff_ms = next_funding_time_ms - current_time_ms
        
        if time_diff_ms <= 0:
            return 0, "00:00:00"
        
        time_diff_seconds = time_diff_ms // 1000
        hours = time_diff_seconds // 3600
        minutes = (time_diff_seconds % 3600) // 60
        seconds = time_diff_seconds % 60
        
        return time_diff_seconds, f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    def get_funding_info(self, symbol="SUIUSDT"):
        """Get comprehensive funding information for a symbol"""
        try:
            # Get latest funding rate
            funding_data = self.get_funding_rate(symbol)
            if not funding_data:
                return None
            
            # Calculate next funding time
            next_funding_time = self.calculate_next_funding_time(funding_data["funding_time"])
            current_time = int(time.time() * 1000)
            
            return {
                "symbol": funding_data["symbol"],
                "funding_rate": funding_data["funding_rate"],
                "last_funding_time": funding_data["funding_time"],
                "next_funding_time": next_funding_time,
                "current_time": current_time,
                "mark_price": funding_data["mark_price"]
            }
            
        except Exception as e:
            logger.error(f"Error getting funding info for {symbol}: {e}")
            return None
    
    def prepare_document(self, symbol, funding_info):
        """Prepare document for MongoDB storage"""
        if not funding_info:
            return None
            
        current_timestamp = datetime.now(timezone.utc)
        countdown_seconds, countdown_formatted = self.calculate_countdown(funding_info["next_funding_time"])
        
        next_funding_dt = datetime.fromtimestamp(
            funding_info["next_funding_time"] / 1000, 
            tz=timezone.utc
        )
        
        last_funding_dt = datetime.fromtimestamp(
            funding_info["last_funding_time"] / 1000, 
            tz=timezone.utc
        )
        
        document = {
            "symbol": funding_info["symbol"],
            "timestamp": current_timestamp,
            "date": current_timestamp.strftime("%Y-%m-%d"),
            "funding_rate": funding_info["funding_rate"],
            "funding_rate_percentage": funding_info["funding_rate"] * 100,
            "last_funding_time": last_funding_dt,
            "next_funding_time": next_funding_dt,
            "countdown_seconds": countdown_seconds,
            "countdown_formatted": countdown_formatted,
            "mark_price": funding_info.get("mark_price", 0),
            "created_at": current_timestamp
        }
        
        return document
    
    def store_funding_data(self, symbol="SUIUSDT"):
        """Store single funding data point to MongoDB"""
        try:
            funding_info = self.get_funding_info(symbol)
            if not funding_info:
                logger.warning(f"No funding info received for {symbol}")
                return False
                
            document = self.prepare_document(symbol, funding_info)
            if not document:
                logger.warning(f"Could not prepare document for {symbol}")
                return False
            
            # Insert document (will skip if duplicate due to unique index)
            try:
                result = self.collection.insert_one(document)
                logger.info(f"Stored funding data for {symbol}: Rate {document['funding_rate_percentage']:.4f}%, Countdown: {document['countdown_formatted']}")
                return True
                
            except DuplicateKeyError:
                # Update existing document instead
                self.collection.update_one(
                    {"symbol": symbol, "timestamp": document["timestamp"]},
                    {"$set": document}
                )
                logger.info(f"Updated funding data for {symbol}")
                return True
                
        except Exception as e:
            logger.error(f"Error storing funding data for {symbol}: {e}")
            return False
    
    def store_multiple_symbols(self, symbols=None):
        """Store funding data for multiple symbols"""
        if symbols is None:
            symbols = ["SUIUSDT", "BTCUSDT", "ETHUSDT", "ADAUSDT", "SOLUSDT"]
        
        success_count = 0
        for symbol in symbols:
            if self.store_funding_data(symbol):
                success_count += 1
            time.sleep(0.1)  # Small delay to avoid rate limiting
            
        logger.info(f"Successfully stored data for {success_count}/{len(symbols)} symbols")
        return success_count
    
    def continuous_monitoring(self, symbols=None, interval_seconds=60):
        """Continuously monitor and store funding data"""
        if symbols is None:
            symbols = ["SUIUSDT"]
            
        logger.info(f"Starting continuous monitoring for {symbols}")
        logger.info(f"Update interval: {interval_seconds} seconds")
        logger.info("Press Ctrl+C to stop")
        
        try:
            while True:
                start_time = time.time()
                
                # Store data for all symbols
                success_count = self.store_multiple_symbols(symbols)
                
                # Display current status
                current_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
                print(f"\r[{current_time}] Stored data for {success_count}/{len(symbols)} symbols", 
                      end="", flush=True)
                
                # Wait for next interval
                elapsed = time.time() - start_time
                sleep_time = max(0, interval_seconds - elapsed)
                time.sleep(sleep_time)
                
        except KeyboardInterrupt:
            print("\nStopping continuous monitoring...")
            logger.info("Monitoring stopped by user")
        except Exception as e:
            logger.error(f"Error in continuous monitoring: {e}")
            raise
    
    def get_today_data(self, symbol="SUIUSDT", date=None):
        """Retrieve stored data for today or specific date"""
        if date is None:
            date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            
        try:
            cursor = self.collection.find(
                {"symbol": symbol, "date": date}
            ).sort("timestamp", 1)
            
            data = list(cursor)
            logger.info(f"Retrieved {len(data)} records for {symbol} on {date}")
            return data
            
        except Exception as e:
            logger.error(f"Error retrieving data: {e}")
            return []
    
    def get_statistics(self, symbol="SUIUSDT", date=None):
        """Get funding rate statistics for a symbol on a specific date"""
        if date is None:
            date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            
        try:
            pipeline = [
                {"$match": {"symbol": symbol, "date": date}},
                {"$group": {
                    "_id": "$symbol",
                    "count": {"$sum": 1},
                    "avg_funding_rate": {"$avg": "$funding_rate_percentage"},
                    "min_funding_rate": {"$min": "$funding_rate_percentage"},
                    "max_funding_rate": {"$max": "$funding_rate_percentage"},
                    "first_recorded": {"$min": "$timestamp"},
                    "last_recorded": {"$max": "$timestamp"}
                }}
            ]
            
            result = list(self.collection.aggregate(pipeline))
            return result[0] if result else None
            
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return None
    
    def get_funding_summary(self, symbol="SUIUSDT"):
        """Get comprehensive funding information summary"""
        funding_info = self.get_funding_info(symbol)
        if not funding_info:
            return None
        
        countdown_seconds, countdown_formatted = self.calculate_countdown(funding_info["next_funding_time"])
        
        summary = {
            "symbol": funding_info["symbol"],
            "current_funding_rate": f"{funding_info['funding_rate'] * 100:.4f}%",
            "next_funding_countdown": countdown_formatted,
            "next_funding_time": datetime.fromtimestamp(
                funding_info["next_funding_time"] / 1000, tz=timezone.utc
            ).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "last_funding_time": datetime.fromtimestamp(
                funding_info["last_funding_time"] / 1000, tz=timezone.utc
            ).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "mark_price": funding_info.get("mark_price", 0)
        }
        
        return summary
    
    def display_current_status(self, symbols=None):
        """Display current funding status for symbols"""
        if symbols is None:
            symbols = ["SUIUSDT", "BTCUSDT", "ETHUSDT"]
        
        print(f"\n{'Symbol':<10} {'Rate %':<10} {'Countdown':<12} {'Next Funding (UTC)':<20}")
        print("-" * 55)
        
        for symbol in symbols:
            summary = self.get_funding_summary(symbol)
            if summary:
                print(f"{symbol:<10} {summary['current_funding_rate']:<10} "
                      f"{summary['next_funding_countdown']:<12} "
                      f"{summary['next_funding_time']:<20}")
            else:
                print(f"{symbol:<10} {'ERROR':<10} {'ERROR':<12} {'ERROR':<20}")
    
    def close_connection(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")

# Usage examples and main execution
if __name__ == "__main__":
    # Initialize tracker with MongoDB connection from environment variables
    tracker = BinanceFundingTracker()
    
    try:
        # Find available SUI symbols first
        print("=== Finding Available SUI Symbols ===")
        sui_variations = tracker.find_symbol_variations("SUI")
        
        if sui_variations:
            preferred_symbol = sui_variations[0]['symbol']
            print(f"Using {preferred_symbol} for examples")
        else:
            print("No SUI symbols found, using BTCUSDT")
            preferred_symbol = "BTCUSDT"
        
        # Display current funding status
        print(f"\n=== Current Funding Status ===")
        tracker.display_current_status([preferred_symbol, "BTCUSDT", "ETHUSDT"])
        
        # Get detailed summary
        print(f"\n=== Detailed Summary for {preferred_symbol} ===")
        summary = tracker.get_funding_summary(preferred_symbol)
        if summary:
            for key, value in summary.items():
                print(f"{key.replace('_', ' ').title()}: {value}")
        
        # Store current data
        print(f"\n=== Storing Data ===")
        success = tracker.store_funding_data(preferred_symbol)
        print(f"Data stored successfully: {success}")
        
        # Show today's statistics
        print(f"\n=== Today's Statistics for {preferred_symbol} ===")
        stats = tracker.get_statistics(preferred_symbol)
        if stats:
            print(f"Records today: {stats['count']}")
            print(f"Average rate: {stats['avg_funding_rate']:.4f}%")
            print(f"Min rate: {stats['min_funding_rate']:.4f}%")
            print(f"Max rate: {stats['max_funding_rate']:.4f}%")
        
        print(f"\n=== Ready for Continuous Monitoring ===")
        print("To start continuous monitoring, uncomment the line below:")
        print(f"# tracker.continuous_monitoring(['{preferred_symbol}'], interval_seconds=30)")
        
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
    finally:
        tracker.close_connection()

# Simple function to start monitoring immediately
def start_funding_monitor(symbols=None, interval=60):
    """Start monitoring funding rates immediately"""
    if symbols is None:
        symbols = ["SUIUSDT"]
    
    tracker = BinanceFundingTracker()
    
    try:
        print(f"Starting monitoring for: {symbols}")
        tracker.continuous_monitoring(symbols, interval)
    except KeyboardInterrupt:
        print("\nMonitoring stopped")
    finally:
        tracker.close_connection()

# Uncomment to start monitoring immediately:
start_funding_monitor(["SUIUSDT"], interval=30)