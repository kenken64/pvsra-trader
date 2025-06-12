#!/usr/bin/env python3
"""
Telegram Bot Test Script
Test your Telegram bot configuration before running the full trading bot
"""

import os
import sys
import requests
from dotenv import load_dotenv
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class TelegramTester:
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
    def test_configuration(self):
        """Test if Telegram bot configuration is valid"""
        logger.info("🔍 Testing Telegram Bot Configuration...")
        
        if not self.bot_token:
            logger.error("❌ TELEGRAM_BOT_TOKEN not found in .env file")
            return False
        
        if not self.chat_id:
            logger.error("❌ TELEGRAM_CHAT_ID not found in .env file")
            return False
            
        logger.info(f"✅ Bot Token: {self.bot_token[:10]}...{self.bot_token[-10:]}")
        logger.info(f"✅ Chat ID: {self.chat_id}")
        return True
    
    def test_bot_api(self):
        """Test if the bot token is valid"""
        logger.info("🤖 Testing Bot API Connection...")
        
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/getMe"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                bot_info = response.json()
                if bot_info.get('ok'):
                    bot_name = bot_info['result']['username']
                    logger.info(f"✅ Bot API Connection Successful! Bot: @{bot_name}")
                    return True
                else:
                    logger.error(f"❌ Bot API Error: {bot_info}")
                    return False
            else:
                logger.error(f"❌ HTTP Error {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Exception testing bot API: {e}")
            return False
    
    def send_test_message(self):
        """Send a test message to verify chat connection"""
        logger.info("📨 Sending Test Message...")
        
        test_message = """🧪 **Telegram Bot Test** 🧪

✅ Your Telegram bot is working correctly!

This is a test message from your trading bot configuration.

🤖 **Bot Status:** Connected
📱 **Chat Connection:** Successful
⏰ **Test Time:** Now

Your bot is ready to send trading notifications! 🚀"""

        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            payload = {
                'chat_id': self.chat_id,
                'text': test_message,
                'parse_mode': 'Markdown'
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                logger.info("✅ Test message sent successfully!")
                logger.info("📱 Check your Telegram chat for the test message")
                return True
            else:
                logger.error(f"❌ Failed to send message: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Exception sending test message: {e}")
            return False
    
    def run_full_test(self):
        """Run all tests"""
        logger.info("🚀 Starting Telegram Bot Full Test...")
        logger.info("=" * 50)
        
        # Test 1: Configuration
        if not self.test_configuration():
            logger.error("💥 Configuration test failed. Please check your .env file.")
            return False
        
        logger.info("-" * 30)
        
        # Test 2: Bot API
        if not self.test_bot_api():
            logger.error("💥 Bot API test failed. Please check your bot token.")
            return False
            
        logger.info("-" * 30)
        
        # Test 3: Send Message
        if not self.send_test_message():
            logger.error("💥 Message test failed. Please check your chat ID.")
            return False
        
        logger.info("=" * 50)
        logger.info("🎉 ALL TESTS PASSED! Your Telegram bot is ready!")
        logger.info("📱 You should have received a test message in Telegram")
        logger.info("🚀 You can now run your trading bot with Telegram notifications enabled")
        return True

def print_setup_instructions():
    """Print setup instructions if configuration is missing"""
    print("""
🤖 TELEGRAM BOT SETUP REQUIRED

To use Telegram notifications, you need to:

1️⃣ CREATE A TELEGRAM BOT:
   • Open Telegram and search for @BotFather
   • Send /newbot and follow the instructions
   • Copy the bot token (looks like: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz)

2️⃣ GET YOUR CHAT ID:
   • Search for @userinfobot on Telegram
   • Start a chat - it will send you your Chat ID

3️⃣ UPDATE YOUR .env FILE:
   Add these lines to your .env file:
   
   TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
   TELEGRAM_CHAT_ID=123456789

4️⃣ RUN THIS TEST AGAIN:
   python test_telegram.py

📖 For detailed instructions, see: TELEGRAM_SETUP_GUIDE.md
""")

if __name__ == "__main__":
    try:
        tester = TelegramTester()
        
        # Check if configuration exists
        if not tester.bot_token or not tester.chat_id:
            print_setup_instructions()
            sys.exit(1)
        
        # Run the full test
        success = tester.run_full_test()
        
        if success:
            sys.exit(0)
        else:
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Test cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)
