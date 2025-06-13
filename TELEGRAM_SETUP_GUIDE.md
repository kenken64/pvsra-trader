# 🤖 Telegram Bot Integration Guide

## 📱 Overview

Your trading bot now includes **Telegram notification support** to send you real-time alerts for:

- 🎯 **PVSRA Signal Detection** - When PVSRA patterns are identified
- 🚀 **Trade Signal Alerts** - When BUY/SELL signals are generated
- 💰 **Trade Execution Notifications** - When trades are executed (live or simulation)
- ⚠️ **Error Alerts** - When problems occur with the bot
- 🤖 **Bot Status Updates** - When the bot starts/stops

## 🔧 Setup Instructions

### Step 1: Create a Telegram Bot

1. **Open Telegram** and search for `@BotFather`
2. **Start a chat** with BotFather by clicking "START"
3. **Create a new bot** by sending: `/newbot`
4. **Choose a name** for your bot (e.g., "My Trading Bot")
5. **Choose a username** for your bot (must end in 'bot', e.g., "mytradingbot_bot")
6. **Copy the bot token** that BotFather provides (it looks like: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### Step 2: Get Your Chat ID

**Option A: Using @userinfobot**
1. Search for `@userinfobot` on Telegram
2. Start a chat and it will send you your Chat ID

**Option B: Manual method**
1. Send a message to your bot (the one you just created)
2. Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
3. Look for your Chat ID in the response

### Step 3: Configure Your Bot

1. **Open your `.env` file**
2. **Add your Telegram credentials**:
```properties
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz  # Your bot token from BotFather
TELEGRAM_CHAT_ID=123456789  # Your chat ID
```

## 📨 Message Types

### 🎯 PVSRA Signal Notifications
```
🎯 PVSRA SIGNAL DETECTED 🎯

📊 Symbol: SUIUSDC
📡 Signal: Bull Climax - Potential Reversal
💰 Price: $1.2345
🔍 Condition: climax
📈 Volume Ratio: 2.5x
⏰ Time: 2025-06-13 15:30:45 UTC

🤖 Bot will analyze this signal for trading decision...
```

### 🚀 Trade Signal Alerts
```
🟢🚀 LONG SIGNAL DETECTED 🟢🚀

📊 Symbol: SUIUSDC
💰 Price: $1.2345
🎯 Confidence: 85%
📝 Reason: PVSRA confirms BUY signal
🔍 PVSRA Signal: Bull Climax - Potential Reversal
⏰ Time: 2025-06-13 15:30:45 UTC
```

### 💰 Trade Execution Notifications
```
🔥 TRADE EXECUTED 🔥

🟢 Action: BUY
📊 Symbol: SUIUSDC
📦 Quantity: 100.0
💰 Price: $1.2345
💼 Mode: LIVE
⏰ Time: 2025-06-13 15:30:45 UTC
```

### 🤖 Bot Startup Notification
```
🤖 Trading Bot Started 🤖

📊 Symbol: SUIUSDC
💰 Mode: SIMULATION
🎯 PVSRA: Enabled
📱 Telegram: Enabled
⏰ Started: 2025-06-13 15:30:45 UTC

🚀 Bot is now monitoring for trading signals...
```

## ⚙️ Configuration Options

In your `.env` file, you can control the bot behavior:

```properties
# Enable/disable PVSRA analysis (affects Telegram notifications)
USE_PVSRA=True

# PVSRA signal weight in trading decisions
PVSRA_WEIGHT=0.7

# Whether to require PVSRA confirmation for trades
REQUIRE_PVSRA_CONFIRMATION=False

# Enable live trading (affects notification messages)
ENABLE_LIVE_TRADING=False

# Trading cooldown (affects signal frequency)
TRADE_COOLDOWN=5
```

## 🧪 Testing Your Setup

1. **Start your bot** with Telegram configured
2. **You should receive a startup notification** immediately
3. **Check the bot logs** for Telegram status:
   ```
   ✅ Telegram bot initialized
   📱 Telegram Notifications: ENABLED
   ```

## 🚨 Troubleshooting

### ❌ "Telegram bot disabled"
- Check that both `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` are set in `.env`
- Verify the token format is correct (should contain a colon)

### ❌ "Telegram API error: 401"
- Your bot token is invalid
- Create a new bot with @BotFather

### ❌ "Telegram API error: 403"
- Your chat ID is incorrect
- You haven't started a conversation with your bot
- Send a message to your bot first

### ❌ "Telegram API error: 400"
- Your chat ID format is wrong
- Make sure it's a number, not a username

## 📊 Notification Frequency

The bot sends notifications for:

- **PVSRA Signals**: Every time a new PVSRA pattern is detected
- **Trade Signals**: Only when confidence ≥ 60%
- **Trade Executions**: Every actual trade (live or simulation)
- **Errors**: Critical errors that need attention
- **Startup**: Once when the bot starts

## 🔒 Security Notes

- **Keep your bot token secret** - anyone with it can control your bot
- **Don't share your chat ID** - it could be used to send you spam
- **Use a private chat** - don't add the bot to public groups for trading signals
- **Bot token is in `.env`** - make sure this file is not committed to version control

## 📈 Advanced Features

### Group Notifications
To send notifications to a Telegram group:
1. Add your bot to the group
2. Make the bot an admin
3. Use the group's chat ID (starts with `-`)

### Multiple Recipients
To notify multiple people, you would need to modify the bot code to accept multiple chat IDs.

### Custom Messages
You can customize the message format by editing the `TelegramBot` class methods in `bot.py`.

## 🎉 You're All Set!

Once configured, your trading bot will keep you informed of all trading activity via Telegram. You'll never miss a signal or trade execution again!

---

**Need help?** Check the bot logs for detailed error messages, or verify your Telegram setup using the testing steps above.
