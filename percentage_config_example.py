#!/usr/bin/env python3
"""
Configuration examples for percentage-based trading
"""

def show_percentage_config_examples():
    print("💰 PERCENTAGE TRADING CONFIGURATION EXAMPLES")
    print("=" * 60)
    
    print("\n📋 Configuration Options:")
    print("You can configure the bot to use either:")
    print("1. Fixed USDT amount per trade")
    print("2. Percentage of available balance per trade")
    
    print("\n🔧 Environment Variables (.env file):")
    print()
    
    print("# Option 1: Fixed Amount Trading (Default)")
    print("TRADE_AMOUNT=10                    # Use exactly 10 USDT per trade")
    print("# TRADE_AMOUNT_PERCENTAGE=         # Leave this commented out")
    print()
    
    print("# Option 2: Percentage-Based Trading")
    print("# TRADE_AMOUNT=10                  # Comment this out")
    print("TRADE_AMOUNT_PERCENTAGE=5.0        # Use 5% of available balance")
    print()
    
    print("📊 Percentage Trading Examples:")
    print()
    
    examples = [
        {"balance": 100, "percentage": 5.0, "leverage": 10},
        {"balance": 500, "percentage": 3.0, "leverage": 20},
        {"balance": 1000, "percentage": 2.0, "leverage": 50},
        {"balance": 50, "percentage": 10.0, "leverage": 5},
    ]
    
    for i, example in enumerate(examples, 1):
        balance = example["balance"]
        percentage = example["percentage"]
        leverage = example["leverage"]
        
        trade_amount = balance * (percentage / 100)
        position_value = trade_amount * leverage
        
        print(f"Example {i}:")
        print(f"  Available Balance: {balance} USDT")
        print(f"  Percentage Setting: {percentage}%")
        print(f"  Trade Amount: {trade_amount:.2f} USDT")
        print(f"  Leverage: {leverage}x")
        print(f"  Total Position Value: {position_value:.2f} USDT")
        print(f"  Risk per Trade: {percentage}% of account")
        print()
    
    print("⚠️ IMPORTANT CONSIDERATIONS:")
    print()
    print("1. Percentage Range: 0.1% to 100%")
    print("   - Too low (<0.1%): May not meet minimum notional requirements")
    print("   - Too high (>20%): High risk per trade")
    print()
    print("2. Recommended Percentages:")
    print("   - Conservative: 1-3% per trade")
    print("   - Moderate: 3-7% per trade") 
    print("   - Aggressive: 7-15% per trade")
    print("   - Very Aggressive: 15%+ per trade")
    print()
    print("3. With Leverage Considerations:")
    print("   - 2% with 50x leverage = 100% of balance position")
    print("   - 1% with 25x leverage = 25% of balance position")
    print("   - 5% with 10x leverage = 50% of balance position")
    print()
    print("4. Dynamic Balance Adjustment:")
    print("   - Trade amounts automatically adjust as balance changes")
    print("   - Profits increase future trade sizes")
    print("   - Losses decrease future trade sizes")

def show_risk_management():
    print("\n🛡️ RISK MANAGEMENT WITH PERCENTAGE TRADING")
    print("=" * 60)
    
    print("\n📈 Scenario Analysis:")
    
    scenarios = [
        {"name": "Conservative Scalper", "percentage": 2.0, "leverage": 10, "balance": 1000},
        {"name": "Moderate Trader", "percentage": 5.0, "leverage": 20, "balance": 500},
        {"name": "Aggressive Scalper", "percentage": 10.0, "leverage": 50, "balance": 200},
    ]
    
    for scenario in scenarios:
        name = scenario["name"]
        percentage = scenario["percentage"]
        leverage = scenario["leverage"]
        balance = scenario["balance"]
        
        trade_amount = balance * (percentage / 100)
        position_value = trade_amount * leverage
        
        # Calculate potential outcomes
        profit_2pct = position_value * 0.002  # 0.2% price move
        loss_1pct = position_value * 0.001    # 0.1% price move
        
        print(f"\n{name}:")
        print(f"  Starting Balance: {balance} USDT")
        print(f"  Risk per Trade: {percentage}% ({trade_amount:.2f} USDT)")
        print(f"  Position Size: {position_value:.2f} USDT ({leverage}x leverage)")
        print(f"  Potential Profit (0.2% move): +{profit_2pct:.2f} USDT")
        print(f"  Potential Loss (0.1% move): -{loss_1pct:.2f} USDT")
        print(f"  Max Daily Trades: ~20-30 (with cooldowns)")

if __name__ == "__main__":
    show_percentage_config_examples()
    show_risk_management()
    
    print("\n" + "=" * 60)
    print("📚 FOR MORE INFORMATION:")
    print("- Check the bot logs for actual trade amounts used")
    print("- Monitor your balance in the web dashboard")
    print("- Start with conservative percentages (1-3%)")
    print("- Test thoroughly in TEST_MODE before live trading")
    print("=" * 60)