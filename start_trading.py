#!/usr/bin/env python3
"""
Quick Start Script for Auto Trading Bot
Simple launcher with safety checks
"""

import os
import sys
import json
from datetime import datetime

def check_requirements():
    """Check if all requirements are met"""
    print("🔍 Checking requirements...")
    
    # Check Python version
    if sys.version_info < (3, 7):
        print("❌ Python 3.7+ required")
        return False
    
    # Check required files
    required_files = [
        'auto_trader.py',
        'simplified_robust_strategy.py',
        'utils.py',
        'risk_manager.py',
        'execution.py',
        'requirements.txt'
    ]
    
    for file in required_files:
        if not os.path.exists(file):
            print(f"❌ Missing required file: {file}")
            return False
    
    # Check if MetaTrader5 is available
    try:
        import MetaTrader5 as mt5
        print("✅ MetaTrader5 module available")
    except ImportError:
        print("⚠️ MetaTrader5 not available - will use mock mode")
    
    print("✅ All requirements met")
    return True

def create_config_if_needed():
    """Create default config if it doesn't exist"""
    if not os.path.exists('config.json'):
        print("📋 Creating default configuration...")
        
        config = {
            "symbols": ["EURUSD"],
            "timeframe": "M15", 
            "check_interval": 60,
            "max_risk_per_trade": 0.01,
            "max_daily_loss": 0.05,
            "max_open_positions": 3,
            "trading_hours": {
                "start": "00:00",
                "end": "23:59"
            }
        }
        
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        print("✅ Default config.json created")
        print("💡 Edit config.json to customize settings")
        return True
    
    return False

def show_config():
    """Display current configuration"""
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        print("\n📋 Current Configuration:")
        print(f"   Symbols: {config.get('symbols', ['EURUSD'])}")
        print(f"   Risk per trade: {config.get('max_risk_per_trade', 0.01)*100}%")
        print(f"   Daily loss limit: {config.get('max_daily_loss', 0.05)*100}%")
        print(f"   Check interval: {config.get('check_interval', 60)}s")
        print(f"   Trading hours: {config.get('trading_hours', {}).get('start', '00:00')} - {config.get('trading_hours', {}).get('end', '23:59')}")
        
    except Exception as e:
        print(f"⚠️ Could not read config: {e}")

def safety_prompt():
    """Safety confirmation before starting"""
    print("\n🛡️ SAFETY REMINDER:")
    print("   • Always test on demo account first")
    print("   • Only trade with money you can afford to lose")
    print("   • Monitor the bot closely, especially initially")
    print("   • Use Ctrl+C to stop the bot safely")
    
    print(f"\n⏰ Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    response = input("\n🤖 Start auto trading? (y/N): ").lower().strip()
    return response in ['y', 'yes']

def main():
    """Main startup function"""
    print("🤖 Simplified Robust Auto Trading Bot")
    print("=" * 50)
    
    # Check requirements
    if not check_requirements():
        print("\n❌ Requirements not met. Please fix issues and try again.")
        return
    
    # Create config if needed
    config_created = create_config_if_needed()
    
    # Show current configuration
    show_config()
    
    if config_created:
        print("\n💡 Review the configuration above and edit config.json if needed")
        print("💡 Then run this script again to start trading")
        return
    
    # Safety confirmation
    if not safety_prompt():
        print("\n⏹️ Startup cancelled by user")
        return
    
    # Create logs directory
    os.makedirs('logs', exist_ok=True)
    
    # Start the auto trader
    print("\n🚀 Starting Auto Trading Bot...")
    print("📊 Press Ctrl+C to stop safely")
    print("-" * 50)
    
    try:
        from auto_trader import AutoTrader
        trader = AutoTrader()
        trader.run()
    except KeyboardInterrupt:
        print("\n⏹️ Bot stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting bot: {e}")
        print("💡 Check logs/auto_trader.log for details")

if __name__ == "__main__":
    main() 