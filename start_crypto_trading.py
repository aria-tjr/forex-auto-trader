#!/usr/bin/env python3
"""
Quick Start Script for Crypto Auto Trading Bot
Simple launcher with safety checks for cryptocurrency trading
"""

import os
import sys
import json
from datetime import datetime

def check_crypto_requirements():
    """Check if all crypto trading requirements are met"""
    print("🔍 Checking crypto trading requirements...")
    
    # Check Python version
    if sys.version_info < (3, 7):
        print("❌ Python 3.7+ required")
        return False
    
    # Check required files
    required_files = [
        'crypto_trader.py',
        'simplified_robust_strategy.py',
        'utils.py',
        'crypto_risk_manager.py',
        'crypto_execution.py',
        'crypto_requirements.txt'
    ]
    
    for file in required_files:
        if not os.path.exists(file):
            print(f"❌ Missing required file: {file}")
            return False
    
    # Check if python-binance is available
    try:
        from binance.client import Client
        print("✅ python-binance module available")
    except ImportError:
        print("⚠️ python-binance not available")
        print("💡 Install with: pip install python-binance")
        return False
    
    print("✅ All crypto requirements met")
    return True

def create_crypto_config_if_needed():
    """Create default crypto config if it doesn't exist"""
    if not os.path.exists('crypto_config.json'):
        print("📋 Creating default crypto configuration...")
        
        config = {
            "symbols": ["BTCUSDT", "ETHUSDT", "ADAUSDT", "BNBUSDT", "SOLUSDT"],
            "timeframe": "15m",
            "check_interval": 30,
            "max_risk_per_trade": 0.02,
            "max_daily_loss": 0.08,
            "max_open_positions": 5,
            "base_currency": "USDT",
            "min_notional": 10.0,
            "api_keys": {
                "api_key": "YOUR_BINANCE_API_KEY_HERE",
                "api_secret": "YOUR_BINANCE_API_SECRET_HERE",
                "testnet": True
            },
            "trading_mode": "spot",
            "stop_loss_pct": 3.0,
            "take_profit_pct": 6.0,
            "trading_hours": {
                "enabled": False,
                "start": "00:00",
                "end": "23:59"
            }
        }
        
        with open('crypto_config.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        print("✅ Default crypto_config.json created")
        print("🔑 ⚠️  IMPORTANT: Add your Binance API keys to crypto_config.json")
        print("🔒 💡 Start with testnet=true for safe testing")
        return True
    
    return False

def show_crypto_config():
    """Display current crypto configuration"""
    try:
        with open('crypto_config.json', 'r') as f:
            config = json.load(f)
        
        print("\n📋 Current Crypto Configuration:")
        print(f"   Symbols: {config.get('symbols', ['BTCUSDT'])}")
        print(f"   Risk per trade: {config.get('max_risk_per_trade', 0.02)*100}%")
        print(f"   Daily loss limit: {config.get('max_daily_loss', 0.08)*100}%")
        print(f"   Check interval: {config.get('check_interval', 30)}s")
        print(f"   Base currency: {config.get('base_currency', 'USDT')}")
        print(f"   Stop loss: {config.get('stop_loss_pct', 3.0)}%")
        print(f"   Take profit: {config.get('take_profit_pct', 6.0)}%")
        
        # Check API keys
        api_keys = config.get('api_keys', {})
        if api_keys.get('api_key') == 'YOUR_BINANCE_API_KEY_HERE':
            print("   🔑 API Keys: ❌ NOT CONFIGURED")
        else:
            print("   🔑 API Keys: ✅ Configured")
        
        print(f"   🧪 Testnet: {'✅ ON' if api_keys.get('testnet', True) else '❌ OFF (REAL MONEY!)'}")
        
    except Exception as e:
        print(f"⚠️ Could not read config: {e}")

def validate_api_keys():
    """Validate that API keys are configured"""
    try:
        with open('crypto_config.json', 'r') as f:
            config = json.load(f)
        
        api_keys = config.get('api_keys', {})
        api_key = api_keys.get('api_key', '')
        api_secret = api_keys.get('api_secret', '')
        
        if api_key == 'YOUR_BINANCE_API_KEY_HERE' or not api_key:
            print("\n❌ Binance API key not configured!")
            print("💡 Please edit crypto_config.json and add your Binance API credentials")
            print("🔒 Get API keys from: https://www.binance.com/en/my/settings/api-management")
            return False
        
        if not api_secret or api_secret == 'YOUR_BINANCE_API_SECRET_HERE':
            print("\n❌ Binance API secret not configured!")
            print("💡 Please edit crypto_config.json and add your Binance API secret")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error validating API keys: {e}")
        return False

def crypto_safety_prompt():
    """Enhanced safety confirmation for crypto trading"""
    print("\n🛡️ CRYPTO TRADING SAFETY REMINDER:")
    print("   • 📊 Crypto markets are more volatile than forex")
    print("   • 🧪 ALWAYS test on Binance Testnet first")
    print("   • 💰 Only trade with money you can afford to lose")
    print("   • 🔄 Crypto trades 24/7 - monitor regularly")
    print("   • 🛑 Use Ctrl+C to stop the bot safely")
    print("   • 🔒 Never share your API keys")
    
    try:
        with open('crypto_config.json', 'r') as f:
            config = json.load(f)
        
        testnet = config.get('api_keys', {}).get('testnet', True)
        if testnet:
            print(f"\n✅ TESTNET MODE: You're trading with fake money (safe)")
        else:
            print(f"\n⚠️  MAINNET MODE: You're trading with REAL MONEY!")
            
    except:
        pass
    
    print(f"\n⏰ Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    response = input("\n🤖 Start crypto auto trading? (y/N): ").lower().strip()
    return response in ['y', 'yes']

def main():
    """Main crypto startup function"""
    print("₿ Crypto Auto Trading Bot - Simplified Robust Strategy")
    print("=" * 60)
    
    # Check requirements
    if not check_crypto_requirements():
        print("\n❌ Requirements not met. Please fix issues and try again.")
        return
    
    # Create config if needed
    config_created = create_crypto_config_if_needed()
    
    # Show current configuration
    show_crypto_config()
    
    if config_created:
        print("\n💡 Configuration created! Please follow these steps:")
        print("   1. Get Binance API keys from https://www.binance.com/en/my/settings/api-management")
        print("   2. Edit crypto_config.json and add your API credentials")
        print("   3. Start with testnet=true for safe testing")
        print("   4. Run this script again to start trading")
        return
    
    # Validate API keys
    if not validate_api_keys():
        return
    
    # Safety confirmation
    if not crypto_safety_prompt():
        print("\n⏹️ Crypto trading startup cancelled by user")
        return
    
    # Create logs directory
    os.makedirs('logs', exist_ok=True)
    
    # Start the crypto auto trader
    print("\n🚀 Starting Crypto Auto Trading Bot...")
    print("📊 Press Ctrl+C to stop safely")
    print("₿ Trading cryptocurrencies 24/7...")
    print("-" * 60)
    
    try:
        from crypto_trader import CryptoAutoTrader
        trader = CryptoAutoTrader()
        trader.run()
    except KeyboardInterrupt:
        print("\n⏹️ Crypto bot stopped by user")
    except ImportError as e:
        print(f"\n❌ Import error: {e}")
        print("💡 Make sure all required files are present")
    except Exception as e:
        print(f"\n❌ Error starting crypto bot: {e}")
        print("💡 Check logs/crypto_trader.log for details")

if __name__ == "__main__":
    main() 