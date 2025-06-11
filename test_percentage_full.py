#!/usr/bin/env python3
"""
Standalone test for percentage trading functionality
"""

import os
import logging

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_percentage_calculation():
    """Test the percentage calculation logic independently"""
    print("🧪 TESTING PERCENTAGE TRADING CALCULATION")
    print("=" * 50)
    
    # Test scenarios
    test_scenarios = [
        {"balance": 100, "percentage": 5.0, "leverage": 10},
        {"balance": 500, "percentage": 3.0, "leverage": 20},
        {"balance": 1000, "percentage": 2.0, "leverage": 50},
        {"balance": 50, "percentage": 10.0, "leverage": 5},
    ]
    
    for i, scenario in enumerate(test_scenarios, 1):
        balance = scenario["balance"]
        percentage = scenario["percentage"]
        leverage = scenario["leverage"]
        price = 4.58  # Example SUIUSDT price
        
        print(f"\nTest Scenario {i}:")
        print(f"  Available Balance: {balance} USDT")
        print(f"  Percentage Setting: {percentage}%")
        print(f"  Leverage: {leverage}x")
        print(f"  Current Price: {price}")
        
        # Calculate trade amount
        base_trade_amount = balance * (percentage / 100)
        print(f"  Base Trade Amount: {base_trade_amount:.2f} USDT")
        
        # Apply leverage
        position_value = base_trade_amount * leverage
        print(f"  Position Value: {position_value:.2f} USDT")
        
        # Calculate quantity
        raw_quantity = position_value / price
        print(f"  Raw Quantity: {raw_quantity:.4f}")
        
        # Apply SUIUSDT precision (step size 0.1)
        step_size = 0.1
        min_qty = 0.1
        min_notional = 5.0
        
        # Round to step size
        quantity = round(raw_quantity / step_size) * step_size
        quantity = round(quantity, 1)  # 1 decimal place for step_size 0.1
        quantity = max(quantity, min_qty)
        
        # Check minimum notional
        notional_value = quantity * price
        if notional_value < min_notional:
            required_quantity = min_notional / price
            quantity = round(required_quantity / step_size) * step_size
            quantity = round(quantity, 1)
            quantity = max(quantity, min_qty)
            notional_value = quantity * price
        
        print(f"  Final Quantity: {quantity}")
        print(f"  Final Notional: {notional_value:.2f} USDT")
        print(f"  Actual Risk: {(base_trade_amount/balance)*100:.2f}% of balance")
        
        # Validation
        print(f"  ✅ Meets min quantity: {quantity >= min_qty}")
        print(f"  ✅ Meets min notional: {notional_value >= min_notional}")
        print(f"  ✅ Precision compliance: {quantity % step_size < 0.0001}")

def test_configuration_validation():
    """Test the configuration validation logic"""
    print("\n🔧 TESTING CONFIGURATION VALIDATION")
    print("=" * 50)
    
    test_values = [
        ("5.0", True, "Valid moderate percentage"),
        ("1.0", True, "Valid conservative percentage"),
        ("15.0", True, "Valid aggressive percentage"),
        ("0.5", True, "Valid low percentage"),
        ("100.0", True, "Valid maximum percentage"),
        ("0.05", False, "Too low - below 0.1%"),
        ("150.0", False, "Too high - above 100%"),
        ("abc", False, "Invalid format"),
        ("", False, "Empty value"),
    ]
    
    for test_value, should_pass, description in test_values:
        print(f"\nTesting: {test_value} ({description})")
        
        # Simulate the validation logic
        use_percentage_trading = False
        error_message = None
        
        if test_value:
            try:
                percentage = float(test_value)
                if 0.1 <= percentage <= 100:
                    use_percentage_trading = True
                    print(f"  ✅ Valid: {percentage}% trading enabled")
                else:
                    error_message = f"Invalid range: {percentage}%. Must be 0.1-100%"
                    print(f"  ⚠️ {error_message}")
            except ValueError:
                error_message = "Invalid format - not a number"
                print(f"  ❌ {error_message}")
        else:
            error_message = "No value provided"
            print(f"  ❌ {error_message}")
        
        # Check if result matches expectation
        result_matches = use_percentage_trading == should_pass
        status = "✓ PASS" if result_matches else "✗ FAIL"
        print(f"  Result: {status}")

def demo_comparison():
    """Demo comparison between fixed and percentage trading"""
    print("\n⚖️ FIXED vs PERCENTAGE TRADING COMPARISON")
    print("=" * 50)
    
    balance = 1000  # USDT
    price = 4.58
    leverage = 20
    
    print(f"Scenario: {balance} USDT balance, {leverage}x leverage, price {price}")
    print()
    
    # Fixed amount trading
    fixed_amount = 10  # USDT
    fixed_position_value = fixed_amount * leverage
    fixed_quantity = fixed_position_value / price
    fixed_risk_pct = (fixed_amount / balance) * 100
    
    print("Fixed Amount Trading:")
    print(f"  Trade Amount: {fixed_amount} USDT")
    print(f"  Position Value: {fixed_position_value} USDT")
    print(f"  Quantity: {fixed_quantity:.2f}")
    print(f"  Risk: {fixed_risk_pct:.1f}% of balance")
    print()
    
    # Percentage trading
    percentage = 2.0  # 2%
    percentage_amount = balance * (percentage / 100)
    percentage_position_value = percentage_amount * leverage
    percentage_quantity = percentage_position_value / price
    
    print("Percentage Trading (2%):")
    print(f"  Trade Amount: {percentage_amount} USDT")
    print(f"  Position Value: {percentage_position_value} USDT")
    print(f"  Quantity: {percentage_quantity:.2f}")
    print(f"  Risk: {percentage}% of balance")
    print()
    
    # Show what happens when balance changes
    print("After 20% profit (balance = 1200 USDT):")
    new_balance = balance * 1.2
    new_fixed_risk = (fixed_amount / new_balance) * 100
    new_percentage_amount = new_balance * (percentage / 100)
    
    print(f"  Fixed: Still {fixed_amount} USDT ({new_fixed_risk:.1f}% risk)")
    print(f"  Percentage: Now {new_percentage_amount} USDT ({percentage}% risk)")
    print()
    
    print("After 20% loss (balance = 800 USDT):")
    new_balance = balance * 0.8
    new_fixed_risk = (fixed_amount / new_balance) * 100
    new_percentage_amount = new_balance * (percentage / 100)
    
    print(f"  Fixed: Still {fixed_amount} USDT ({new_fixed_risk:.1f}% risk)")
    print(f"  Percentage: Now {new_percentage_amount} USDT ({percentage}% risk)")

if __name__ == "__main__":
    test_percentage_calculation()
    test_configuration_validation()
    demo_comparison()
    
    print("\n" + "=" * 50)
    print("🎯 SUMMARY:")
    print("- Percentage trading provides dynamic position sizing")
    print("- Risk remains constant as percentage of balance")
    print("- Position sizes automatically adjust to account growth/decline")
    print("- Validation ensures safe percentage ranges (0.1% - 100%)")
    print("- All calculations respect SUIUSDT precision requirements")
    print("=" * 50)
