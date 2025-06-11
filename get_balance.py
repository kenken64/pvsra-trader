import requests
import hmac
import hashlib
import time
import os
from urllib.parse import urlencode
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class BinanceAPI:
    def __init__(self, api_key, api_secret):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://api.binance.com"
    
    def get_server_time(self):
        """Get Binance server time to avoid timestamp issues"""
        try:
            response = requests.get(f"{self.base_url}/api/v3/time", timeout=10)
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
    
    def get_account_info(self):
        """Get account information including all balances"""
        endpoint = "/api/v3/account"
        timestamp = self.get_server_time()  # Use server time instead
        
        # Prepare query parameters
        params = {
            'timestamp': timestamp,
            'recvWindow': 5000  # Optional: request validity window
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
            raise Exception(f"API request failed: {response.status_code} - {response.text}")
    
    def get_usdc_balance(self):
        """Get specifically USDC balance"""
        try:
            account_info = self.get_account_info()
            
            # Find USDC balance from the balances array
            for balance in account_info['balances']:
                if balance['asset'] == 'USDC':
                    return {
                        'asset': 'USDC',
                        'free': float(balance['free']),      # Available balance
                        'locked': float(balance['locked']),  # Locked in orders
                        'total': float(balance['free']) + float(balance['locked'])
                    }
            
            # If USDC not found, return zero balance
            return {
                'asset': 'USDC',
                'free': 0.0,
                'locked': 0.0,
                'total': 0.0
            }
            
        except Exception as e:
            print(f"Error getting USDC balance: {e}")
            return None
    
    def get_usdt_balance(self):
        """Get specifically USDT balance (for futures trading)"""
        try:
            account_info = self.get_account_info()
            
            # Find USDT balance from the balances array
            for balance in account_info['balances']:
                if balance['asset'] == 'USDT':
                    return {
                        'asset': 'USDT',
                        'free': float(balance['free']),      # Available balance
                        'locked': float(balance['locked']),  # Locked in orders
                        'total': float(balance['free']) + float(balance['locked'])
                    }
            
            # If USDT not found, return zero balance
            return {
                'asset': 'USDT',
                'free': 0.0,
                'locked': 0.0,
                'total': 0.0
            }
            
        except Exception as e:
            print(f"Error getting USDT balance: {e}")
            return None
    
    def get_balance_for_asset(self, asset):
        """Get balance for any asset"""
        try:
            account_info = self.get_account_info()
            
            # Find balance for the specified asset
            for balance in account_info['balances']:
                if balance['asset'] == asset:
                    return {
                        'asset': asset,
                        'free': float(balance['free']),      # Available balance
                        'locked': float(balance['locked']),  # Locked in orders
                        'total': float(balance['free']) + float(balance['locked'])
                    }
            
            # If asset not found, return zero balance
            return {
                'asset': asset,
                'free': 0.0,
                'locked': 0.0,
                'total': 0.0
            }
            
        except Exception as e:
            print(f"Error getting {asset} balance: {e}")
            return None

# Example usage
def main():
    # Load API credentials from environment variables
    API_KEY = os.getenv('BINANCE_API_KEY')
    API_SECRET = os.getenv('BINANCE_API_SECRET')
    
    # Check if credentials are loaded
    if not API_KEY or not API_SECRET:
        raise ValueError("Please set BINANCE_API_KEY and BINANCE_API_SECRET in your .env file")
      # Initialize Binance API client
    binance = BinanceAPI(API_KEY, API_SECRET)
    
    try:
        print("Checking Binance Spot Balances...\n")
        
        # Get USDC balance
        usdc_balance = binance.get_usdc_balance()
        if usdc_balance:
            print("USDC Balance:")
            print(f"  Available: {usdc_balance['free']:.6f} USDC")
            print(f"  Locked: {usdc_balance['locked']:.6f} USDC")
            print(f"  Total: {usdc_balance['total']:.6f} USDC")
        else:
            print("Failed to retrieve USDC balance")
        
        print()  # Empty line
        
        # Get USDT balance
        usdt_balance = binance.get_usdt_balance()
        if usdt_balance:
            print("USDT Balance:")
            print(f"  Available: {usdt_balance['free']:.6f} USDT")
            print(f"  Locked: {usdt_balance['locked']:.6f} USDT")
            print(f"  Total: {usdt_balance['total']:.6f} USDT")
        else:
            print("Failed to retrieve USDT balance")
        
        print()  # Empty line
        
        # Check for any non-zero balances
        account_info = binance.get_account_info()
        non_zero_balances = []
        for balance in account_info['balances']:
            total = float(balance['free']) + float(balance['locked'])
            if total > 0:
                non_zero_balances.append({
                    'asset': balance['asset'],
                    'free': float(balance['free']),
                    'locked': float(balance['locked']),
                    'total': total
                })
        
        if non_zero_balances:
            print("All Non-Zero Balances:")
            for bal in non_zero_balances:
                print(f"  {bal['asset']}: {bal['total']:.6f} (Available: {bal['free']:.6f}, Locked: {bal['locked']:.6f})")
        else:
            print("No non-zero balances found")
        
        # Get USDT balance
        usdt_balance = binance.get_usdt_balance()
        
        if usdt_balance:
            print("\nUSDT Balance:")
            print(f"Available: {usdt_balance['free']:.6f} USDT")
            print(f"Locked: {usdt_balance['locked']:.6f} USDT")
            print(f"Total: {usdt_balance['total']:.6f} USDT")
        else:
            print("Failed to retrieve USDT balance")
        
        # Example: Get balance for a different asset (e.g., BTC)
        asset_balance = binance.get_balance_for_asset('BTC')
        
        if asset_balance:
            print("\nBTC Balance:")
            print(f"Available: {asset_balance['free']:.6f} BTC")
            print(f"Locked: {asset_balance['locked']:.6f} BTC")
            print(f"Total: {asset_balance['total']:.6f} BTC")
        else:
            print("Failed to retrieve BTC balance")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()

