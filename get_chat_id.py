#!/usr/bin/env python3
"""
Get your Telegram Chat ID
This script will help you find your numeric chat ID
"""

import os
import requests
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

def get_chat_id():
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not bot_token:
        print("❌ TELEGRAM_BOT_TOKEN not found in .env file")
        return
    
    print("🔍 Getting recent messages from your bot...")
    print("📱 Make sure you've sent a message to your bot recently!")
    print()
    
    try:
        url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('ok') and data.get('result'):
                print("✅ Found recent messages:")
                print()
                
                for update in data['result'][-5:]:  # Show last 5 messages
                    if 'message' in update:
                        message = update['message']
                        chat = message['chat']
                        
                        print(f"📨 Message from: {chat.get('first_name', 'Unknown')}")
                        print(f"👤 Username: @{chat.get('username', 'no-username')}")
                        print(f"🆔 Chat ID: {chat['id']}")
                        print(f"📝 Message: {message.get('text', 'No text')}")
                        print("-" * 40)
                        
                        # If this matches your username, show the correct ID
                        if chat.get('username') == 'kenken64':
                            print(f"🎯 FOUND YOUR CHAT ID: {chat['id']}")
                            print(f"✏️  Update your .env file with:")
                            print(f"TELEGRAM_CHAT_ID={chat['id']}")
                            print()
                
                if not data['result']:
                    print("❌ No recent messages found")
                    print("📱 Send a message to your bot (@Dogshiitbot) and run this script again")
                    
            else:
                print(f"❌ API Error: {data}")
                
        else:
            print(f"❌ HTTP Error {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🤖 Telegram Chat ID Finder")
    print("=" * 30)
    get_chat_id()
