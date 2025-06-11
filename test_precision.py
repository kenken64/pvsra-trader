#!/usr/bin/env python3
"""
Quick test script to check SUIUSDT precision and fix the bot
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

# Configuration
base_url = "https://testnet.binancefuture.com"  # Use testnet
symbol = "SUIUSDT"

def get_symbol_info():
    """Get symbol information for precision and filters"""
    try:
        response = requests.get(f"{base_url}/fapi/v1/exchangeInfo", timeout=10)
        data = response.json()
        
        for symbol_data in data['symbols']:
            if symbol_data['symbol'] == symbol:
                return symbol_data
        
        print(f"❌ Symbol {symbol} not found")
        return None
        
    except Exception as e:
        print(f"Error getting symbol info: {e}")
        return None

def analyze_precision(symbol_info):
    """Analyze precision requirements for the symbol"""
    if not symbol_info:
        return
    
    print(f"📏 PRECISION ANALYSIS FOR {symbol}")
    print("=" * 50)
    
    for filter_info in symbol_info['filters']:
        filter_type = filter_info['filterType']
        
        if filter_type == 'LOT_SIZE':
            step_size = float(filter_info['stepSize'])
            min_qty = float(filter_info['minQty'])
            max_qty = float(filter_info['maxQty'])
            
            print(f"LOT_SIZE Filter:")
            print(f"  Min Quantity: {min_qty}")
            print(f"  Max Quantity: {max_qty}")
            print(f"  Step Size: {step_size}")
            
            # Calculate precision
            if step_size >= 1:
                precision = 0
            else:
                step_str = f"{step_size:.10f}".rstrip('0')
                if '.' in step_str:
                    precision = len(step_str.split('.')[-1])
                else:
                    precision = 0
            
            print(f"  Required Precision: {precision} decimal places")
            
        elif filter_type == 'MIN_NOTIONAL':
            notional = float(filter_info['notional'])
            print(f"MIN_NOTIONAL Filter:")
            print(f"  Min Notional: {notional} USDT")
            
        elif filter_type == 'PRICE_FILTER':
            min_price = float(filter_info['minPrice'])
            max_price = float(filter_info['maxPrice'])
            tick_size = float(filter_info['tickSize'])
            
            print(f"PRICE_FILTER:")
            print(f"  Min Price: {min_price}")
            print(f"  Max Price: {max_price}")
            print(f"  Tick Size: {tick_size}")

def test_quantity_calculation():
    """Test quantity calculation with proper precision"""
    print(f"\n🧮 QUANTITY CALCULATION TEST")
    print("=" * 50)
    
    # Example values
    price = 4.5800  # Example SUIUSDT price
    trade_amount = 10.0  # USDT
    leverage = 5
    
    # Calculate raw quantity
    position_value = trade_amount * leverage
    raw_quantity = position_value / price
    
    print(f"Trade Amount: {trade_amount} USDT")
    print(f"Leverage: {leverage}x")
    print(f"Current Price: {price}")
    print(f"Position Value: {position_value} USDT")
    print(f"Raw Quantity: {raw_quantity}")
    
    # Get symbol info for precision
    symbol_info = get_symbol_info()
    if symbol_info:
        for filter_info in symbol_info['filters']:
            if filter_info['filterType'] == 'LOT_SIZE':
                step_size = float(filter_info['stepSize'])
                min_qty = float(filter_info['minQty'])
                
                # Round to step size
                rounded_quantity = round(raw_quantity / step_size) * step_size
                
                # Calculate precision
                if step_size >= 1:
                    precision = 0
                else:
                    step_str = f"{step_size:.10f}".rstrip('0')
                    if '.' in step_str:
                        precision = len(step_str.split('.')[-1])
                    else:
                        precision = 0
                
                # Final quantity
                final_quantity = round(rounded_quantity, precision)
                final_quantity = max(final_quantity, min_qty)
                
                print(f"\nPrecision Calculation:")
                print(f"  Step Size: {step_size}")
                print(f"  Min Quantity: {min_qty}")
                print(f"  Precision: {precision} decimal places")
                print(f"  Rounded Quantity: {rounded_quantity}")
                print(f"  Final Quantity: {final_quantity}")
                
                return final_quantity
    
    return None

if __name__ == "__main__":
    # Get symbol information
    symbol_info = get_symbol_info()
    
    if symbol_info:
        # Analyze precision requirements
        analyze_precision(symbol_info)
        
        # Test quantity calculation
        test_quantity_calculation()
    else:
        print("Failed to get symbol information")
