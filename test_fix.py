#!/usr/bin/env python3
"""
Test the precision fix for SUIUSDT orders
"""
import os
import sys
import importlib.util
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Test the precision calculation function
def test_precision_fix():
    print("🧪 TESTING PRECISION FIX FOR SUIUSDT")
    print("=" * 50)
    
    # Example values from SUIUSDT
    price = 4.58  # Current price
    step_size = 0.1  # From our analysis
    min_qty = 0.1
    min_notional = 5.0  # USDT
    
    # Test cases
    test_cases = [
        {"trade_amount": 10.0, "leverage": 5},
        {"trade_amount": 10.0, "leverage": 10},
        {"trade_amount": 5.0, "leverage": 20},
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}:")
        print(f"  Trade Amount: {case['trade_amount']} USDT")
        print(f"  Leverage: {case['leverage']}x")
        print(f"  Price: {price}")
        
        # Calculate position
        position_value = case['trade_amount'] * case['leverage']
        raw_quantity = position_value / price        # Apply precision fix
        quantity = round(raw_quantity / step_size) * step_size
        quantity = round(quantity, 1)  # 1 decimal place for step_size 0.1
        quantity = max(quantity, min_qty)
        
        # Check notional value
        notional_value = quantity * price
        if notional_value < min_notional:
            # Increase quantity to meet minimum notional
            required_quantity = min_notional / price
            quantity = round(required_quantity / step_size) * step_size
            quantity = round(quantity, 1)
            quantity = max(quantity, min_qty)
            notional_value = quantity * price
        
        # Debug the precision check
        remainder = quantity % step_size
        
        print(f"  Raw Quantity: {raw_quantity:.4f}")
        print(f"  Final Quantity: {quantity}")
        print(f"  Notional Value: {notional_value:.2f} USDT")
        print(f"  Remainder: {remainder:.10f}")
        print(f"  Meets Min Notional: {'✅' if notional_value >= min_notional else '❌'}")
        print(f"  Precision Compliant: {'✅' if abs(remainder) < 0.0001 else '❌'}")

if __name__ == "__main__":
    test_precision_fix()
