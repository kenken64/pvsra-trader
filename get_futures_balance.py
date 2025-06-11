import requests
import hmac
import hashlib
import time
import os
from urllib.parse import urlencode
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class BinanceFuturesAPI:
    def __init__(self, api_key, api_secret):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://fapi.binance.com"  # Futures API base URL
    
    def get_server_time(self):
        """Get Binance server time to avoid timestamp issues"""
        try:
            response = requests.get(f"{self.base_url}/fapi/v1/time", timeout=10)
            if response.status_code == 200:
                return response.json()['serverTime']
            else:
                return int(time.time() * 1000)
        except Exception:
            return int(time.time() * 1000)
    
    def _generate_signature(self, query_string):
        """Generate signature for authenticated requests"""
        return hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def get_futures_account_info(self):
        """Get futures account information"""
        endpoint = "/fapi/v2/account"
        timestamp = self.get_server_time()
        
        # Prepare query parameters
        params = {
            'timestamp': timestamp,
            'recvWindow': 5000
        }
        
        # Create query string and signature
        query_string = urlencode(params)
        signature = self._generate_signature(query_string)
        
        # Add signature to parameters
        params['signature'] = signature
        
        # Set headers
        headers = {
            'X-MBX-APIKEY': self.api_key
        }
        
        # Make request
        url = f"{self.base_url}{endpoint}"
        response = requests.get(url, params=params, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Futures API request failed: {response.status_code} - {response.text}")
    
    def get_futures_balance(self):
        """Get futures account balance"""
        endpoint = "/fapi/v2/balance"
        timestamp = self.get_server_time()
        
        # Prepare query parameters
        params = {
            'timestamp': timestamp,
            'recvWindow': 5000
        }
        
        # Create query string and signature
        query_string = urlencode(params)
        signature = self._generate_signature(query_string)
        
        # Add signature to parameters
        params['signature'] = signature
        
        # Set headers
        headers = {
            'X-MBX-APIKEY': self.api_key
        }
        
        # Make request
        url = f"{self.base_url}{endpoint}"
        response = requests.get(url, params=params, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Futures balance API request failed: {response.status_code} - {response.text}")
    
    def get_usdt_futures_balance(self):
        """Get specifically USDT balance from futures account"""
        try:
            balances = self.get_futures_balance()
            
            # Find USDT balance from the balances array
            for balance in balances:
                if balance['asset'] == 'USDT':
                    return {
                        'asset': 'USDT',
                        'balance': float(balance['balance']),                    # Total balance
                        'availableBalance': float(balance['availableBalance']), # Available for trading
                        'crossWalletBalance': float(balance['crossWalletBalance']),
                        'crossUnPnl': float(balance['crossUnPnl']),
                        'maxWithdrawAmount': float(balance['maxWithdrawAmount'])
                    }
            
            # If USDT not found, return zero balance
            return {
                'asset': 'USDT',
                'balance': 0.0,
                'availableBalance': 0.0,
                'crossWalletBalance': 0.0,
                'crossUnPnl': 0.0,
                'maxWithdrawAmount': 0.0
            }
            
        except Exception as e:
            print(f"Error getting USDT futures balance: {e}")
            return None
    
    def get_positions(self):
        """Get current futures positions"""
        endpoint = "/fapi/v2/positionRisk"
        timestamp = self.get_server_time()
        
        # Prepare query parameters
        params = {
            'timestamp': timestamp,
            'recvWindow': 5000
        }
        
        # Create query string and signature
        query_string = urlencode(params)
        signature = self._generate_signature(query_string)
        
        # Add signature to parameters
        params['signature'] = signature
        
        # Set headers
        headers = {
            'X-MBX-APIKEY': self.api_key
        }
        
        # Make request
        url = f"{self.base_url}{endpoint}"
        response = requests.get(url, params=params, headers=headers)
        
        if response.status_code == 200:
            positions = response.json()
            # Filter out zero positions
            active_positions = [pos for pos in positions if float(pos['positionAmt']) != 0]
            return active_positions
        else:
            raise Exception(f"Positions API request failed: {response.status_code} - {response.text}")

def main():
    # Load API credentials from environment variables
    API_KEY = os.getenv('BINANCE_API_KEY')
    API_SECRET = os.getenv('BINANCE_API_SECRET')
    
    # Check if credentials are loaded
    if not API_KEY or not API_SECRET:
        raise ValueError("Please set BINANCE_API_KEY and BINANCE_API_SECRET in your .env file")
    
    # Initialize Binance Futures API client
    binance_futures = BinanceFuturesAPI(API_KEY, API_SECRET)
    
    try:
        print("Checking Binance Futures Account...\n")
        
        # Get USDT futures balance
        usdt_balance = binance_futures.get_usdt_futures_balance()
        if usdt_balance:
            print("USDT Futures Balance:")
            print(f"  Total Balance: {usdt_balance['balance']:.6f} USDT")
            print(f"  Available for Trading: {usdt_balance['availableBalance']:.6f} USDT")
            print(f"  Cross Wallet Balance: {usdt_balance['crossWalletBalance']:.6f} USDT")
            print(f"  Unrealized PnL: {usdt_balance['crossUnPnl']:.6f} USDT")
            print(f"  Max Withdraw Amount: {usdt_balance['maxWithdrawAmount']:.6f} USDT")
        else:
            print("Failed to retrieve USDT futures balance")
        
        print()  # Empty line
        
        # Get all balances
        all_balances = binance_futures.get_futures_balance()
        non_zero_balances = [bal for bal in all_balances if float(bal['balance']) > 0]
        
        if non_zero_balances:
            print("All Non-Zero Futures Balances:")
            for bal in non_zero_balances:
                print(f"  {bal['asset']}: {float(bal['balance']):.6f} (Available: {float(bal['availableBalance']):.6f})")
        else:
            print("No non-zero futures balances found")
        
        print()  # Empty line
        
        # Get active positions
        positions = binance_futures.get_positions()
        if positions:
            print("Active Futures Positions:")
            for pos in positions:
                side = "LONG" if float(pos['positionAmt']) > 0 else "SHORT"
                print(f"  {pos['symbol']}: {side} {abs(float(pos['positionAmt'])):.6f}")
                print(f"    Entry Price: {float(pos['entryPrice']):.6f}")
                print(f"    Mark Price: {float(pos['markPrice']):.6f}")
                print(f"    Unrealized PnL: {float(pos['unRealizedProfit']):.6f} USDT")
                print(f"    Percentage: {float(pos['percentage']):.2f}%")
                print()
        else:
            print("No active positions found")
        
        # Get account info for additional details
        account_info = binance_futures.get_futures_account_info()
        print("Account Summary:")
        print(f"  Total Wallet Balance: {float(account_info['totalWalletBalance']):.6f} USDT")
        print(f"  Total Unrealized Profit: {float(account_info['totalUnrealizedProfit']):.6f} USDT")
        print(f"  Total Margin Balance: {float(account_info['totalMarginBalance']):.6f} USDT")
        print(f"  Total Position Initial Margin: {float(account_info['totalPositionInitialMargin']):.6f} USDT")
        print(f"  Total Open Order Initial Margin: {float(account_info['totalOpenOrderInitialMargin']):.6f} USDT")
        print(f"  Available Balance: {float(account_info['availableBalance']):.6f} USDT")
        print(f"  Max Withdraw Amount: {float(account_info['maxWithdrawAmount']):.6f} USDT")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
