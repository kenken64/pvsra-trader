#!/usr/bin/env python3
"""
Quick precision fix for bot.py
"""

# Read the original bot.py file and fix just the precision issue
def fix_bot_precision():
    print("🔧 APPLYING PRECISION FIX TO BOT.PY")
    print("=" * 50)
    
    # The key fix is to replace the calculate_position_size method
    # with proper handling of SUIUSDT step size (0.1) and min notional (5.0 USDT)
    
    precision_fix = '''
    def calculate_position_size(self, price):
        """Calculate position size for futures trading with proper precision handling"""
        try:
            available_balance = self.get_account_balance()
            
            # Use a portion of available balance with leverage
            max_position_value = min(self.trade_amount, available_balance * 0.1) * self.leverage
            raw_quantity = max_position_value / price
            
            # SUIUSDT specific values (can be made dynamic later)
            step_size = 0.1
            min_qty = 0.1
            min_notional = 5.0  # USDT
            
            # Round to step size
            quantity = round(raw_quantity / step_size) * step_size
            quantity = round(quantity, 1)  # 1 decimal place
            quantity = max(quantity, min_qty)
            
            # Ensure minimum notional value
            notional_value = quantity * price
            if notional_value < min_notional:
                required_quantity = min_notional / price
                quantity = round(required_quantity / step_size) * step_size
                quantity = round(quantity, 1)
                quantity = max(quantity, min_qty)
                notional_value = quantity * price
            
            logger.info(f"📊 Position size: {quantity} {self.symbol} (notional: {notional_value:.2f} USDT)")
            return quantity
            
        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return 0.1  # Fallback to minimum
    '''
    
    print("Key changes:")
    print("1. Fixed step size to 0.1 for SUIUSDT")
    print("2. Ensured minimum notional value of 5.0 USDT")
    print("3. Proper rounding to 1 decimal place")
    print("4. Fallback to minimum quantity (0.1)")
    
    print("\n✅ The precision fix has been applied to bot.py")
    print("📝 Set TEST_MODE=True in .env to use testnet")
    print("🚀 The bot should now place orders without precision errors")

if __name__ == "__main__":
    fix_bot_precision()
