#!/usr/bin/env python3
"""
Simple test to add percentage trading feature to the bot
"""

import os
import logging

# Test the percentage trading logic
def test_percentage_trading():
    print("Testing percentage trading feature...")
    
    # Test cases
    test_cases = [
        ("5.0", True),   # Valid percentage
        ("10.5", True),  # Valid percentage  
        ("0.5", True),   # Valid small percentage
        ("150", False),  # Too high
        ("0.05", False), # Too low
        ("abc", False),  # Invalid format
        (None, False),   # None value
    ]
    
    for test_value, should_be_valid in test_cases:
        os.environ['TRADE_AMOUNT_PERCENTAGE'] = str(test_value) if test_value else ""
        
        trade_amount_percentage = os.getenv('TRADE_AMOUNT_PERCENTAGE')
        use_percentage_trading = False
        
        if trade_amount_percentage:
            try:
                trade_amount_percentage = float(trade_amount_percentage)
                if 0.1 <= trade_amount_percentage <= 100:
                    use_percentage_trading = True
                    print(f"✅ {test_value}: Valid percentage ({trade_amount_percentage}%)")
                else:
                    print(f"⚠️ {test_value}: Invalid range ({trade_amount_percentage}%). Must be 0.1-100%")
            except ValueError:
                print(f"❌ {test_value}: Invalid format")
        else:
            print(f"❌ {test_value}: No value set")
        
        # Verify result matches expectation
        if use_percentage_trading == should_be_valid:
            print(f"   ✓ Test passed for {test_value}")
        else:
            print(f"   ✗ Test failed for {test_value} (expected {should_be_valid}, got {use_percentage_trading})")
        print()

if __name__ == "__main__":
    test_percentage_trading()
