#!/usr/bin/env python3
"""
Auto Trading Bot - Simplified Robust Strategy
Clean, production-ready implementation for live trading

Features:
- Simplified robust strategy (6 parameters, no overfitting)
- Proper risk management
- Real-time signal generation
- MT5 integration
- Comprehensive logging
"""

import sys
import os
import time
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Try to import MetaTrader5, fallback to mock for testing
try:
    import MetaTrader5 as mt5
    USING_MOCK = False
except ImportError:
    print("🔧 MetaTrader5 not available, using mock implementation...")
    import mock_mt5 as mt5
    USING_MOCK = True

# Import our modules
from simplified_robust_strategy import SimplifiedRobustStrategy, PriceData, Signal
from utils import setup_logging, format_currency, TradeSignal
from risk_manager import RiskManager
from execution import ExecutionEngine

class AutoTrader:
    """
    Main auto trading bot using simplified robust strategy
    """
    
    def __init__(self, config_file: str = "config.json"):
        """Initialize the auto trader"""
        self.logger = setup_logging("INFO", "logs/auto_trader.log")
        self.config = self._load_config(config_file)
        
        # Initialize components
        self.strategy = SimplifiedRobustStrategy()
        self.risk_manager = RiskManager(
            max_risk_per_trade=self.config.get('max_risk_per_trade', 0.01),
            max_daily_loss=self.config.get('max_daily_loss', 0.05),
            max_open_positions=self.config.get('max_open_positions', 3)
        )
        self.execution_engine = ExecutionEngine()
        
        # Trading state
        self.is_running = False
        self.symbols = self.config.get('symbols', ['EURUSD'])
        self.timeframe = self.config.get('timeframe', mt5.TIMEFRAME_M15)
        self.check_interval = self.config.get('check_interval', 60)  # seconds
        
        # Statistics
        self.trades_today = 0
        self.daily_pnl = 0.0
        self.start_balance = 0.0
        
        self.logger.info("🚀 Auto Trader initialized successfully")
        self.logger.info(f"📊 Strategy: {self.strategy.get_strategy_info()['name']}")
        self.logger.info(f"💱 Symbols: {self.symbols}")
        self.logger.info(f"⏱️ Check interval: {self.check_interval}s")
    
    def _load_config(self, config_file: str) -> Dict:
        """Load configuration from file"""
        default_config = {
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
        
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    user_config = json.load(f)
                default_config.update(user_config)
                self.logger.info(f"📋 Loaded config from {config_file}")
            else:
                self.logger.info(f"📋 Using default config (no {config_file} found)")
        except Exception as e:
            self.logger.error(f"❌ Error loading config: {e}")
            self.logger.info("📋 Using default config")
        
        return default_config
    
    def initialize_mt5(self) -> bool:
        """Initialize MetaTrader 5 connection"""
        try:
            if not mt5.initialize():
                self.logger.error("❌ Failed to initialize MT5")
                return False
            
            # Get account info
            account_info = mt5.account_info()
            if account_info is None:
                self.logger.error("❌ Failed to get account info")
                return False
            
            self.start_balance = account_info.balance
            self.logger.info(f"✅ MT5 initialized successfully")
            self.logger.info(f"💰 Account balance: {format_currency(account_info.balance)}")
            self.logger.info(f"🏦 Account: {account_info.login}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ MT5 initialization error: {e}")
            return False
    
    def get_latest_price_data(self, symbol: str) -> Optional[PriceData]:
        """Get latest price data for symbol"""
        try:
            # Get the latest bar
            rates = mt5.copy_rates_from_pos(symbol, self.timeframe, 0, 1)
            if rates is None or len(rates) == 0:
                return None
            
            rate = rates[0]
            return PriceData(
                timestamp=datetime.fromtimestamp(rate['time']),
                open=rate['open'],
                high=rate['high'],
                low=rate['low'],
                close=rate['close'],
                volume=rate['tick_volume']
            )
            
        except Exception as e:
            self.logger.error(f"❌ Error getting price data for {symbol}: {e}")
            return None
    
    def process_signal(self, symbol: str, signal: Signal) -> bool:
        """Process trading signal"""
        try:
            if signal.direction == 'NEUTRAL':
                return False
            
            # Check risk management
            if not self.risk_manager.can_open_position(symbol, signal.direction):
                self.logger.warning(f"⚠️ Risk manager blocked {signal.direction} signal for {symbol}")
                return False
            
            # Get current price for entry
            price_data = self.get_latest_price_data(symbol)
            if not price_data:
                self.logger.error(f"❌ Could not get current price for {symbol}")
                return False
            
            # Calculate position size
            account_info = mt5.account_info()
            position_size = self.risk_manager.calculate_position_size(
                account_info.balance,
                symbol,
                signal.direction,
                price_data.close
            )
            
            # Create trade request
            trade_request = {
                'symbol': symbol,
                'action': mt5.TRADE_ACTION_DEAL,
                'type': mt5.ORDER_TYPE_BUY if signal.direction == 'BUY' else mt5.ORDER_TYPE_SELL,
                'volume': position_size,
                'price': price_data.close,
                'sl': self._calculate_stop_loss(price_data.close, signal.direction),
                'tp': self._calculate_take_profit(price_data.close, signal.direction),
                'deviation': 20,
                'magic': 12345,
                'comment': f"SimplifiedRobust_{signal.strength:.2f}",
                'type_time': mt5.ORDER_TIME_GTC,
                'type_filling': mt5.ORDER_FILLING_IOC,
            }
            
            # Execute trade
            result = self.execution_engine.place_order(trade_request)
            
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                self.trades_today += 1
                self.logger.info(f"✅ {signal.direction} order placed for {symbol}")
                self.logger.info(f"📊 Volume: {position_size}, Price: {price_data.close:.5f}")
                self.logger.info(f"🎯 Reason: {signal.reason}")
                return True
            else:
                error_code = result.retcode if result else "Unknown"
                self.logger.error(f"❌ Failed to place order for {symbol}: {error_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error processing signal for {symbol}: {e}")
            return False
    
    def _calculate_stop_loss(self, entry_price: float, direction: str) -> float:
        """Calculate stop loss (50 pips)"""
        sl_distance = 0.0050  # 50 pips
        if direction == 'BUY':
            return entry_price - sl_distance
        else:
            return entry_price + sl_distance
    
    def _calculate_take_profit(self, entry_price: float, direction: str) -> float:
        """Calculate take profit (100 pips, 2:1 R:R)"""
        tp_distance = 0.0100  # 100 pips
        if direction == 'BUY':
            return entry_price + tp_distance
        else:
            return entry_price - tp_distance
    
    def check_trading_hours(self) -> bool:
        """Check if we're in trading hours"""
        now = datetime.now().time()
        start_time = datetime.strptime(self.config['trading_hours']['start'], "%H:%M").time()
        end_time = datetime.strptime(self.config['trading_hours']['end'], "%H:%M").time()
        
        if start_time <= end_time:
            return start_time <= now <= end_time
        else:  # Overnight trading
            return now >= start_time or now <= end_time
    
    def update_daily_stats(self):
        """Update daily trading statistics"""
        try:
            account_info = mt5.account_info()
            if account_info:
                current_balance = account_info.balance
                self.daily_pnl = current_balance - self.start_balance
                
                # Check daily loss limit
                if self.daily_pnl < -abs(self.start_balance * self.config['max_daily_loss']):
                    self.logger.warning(f"⚠️ Daily loss limit reached: {format_currency(self.daily_pnl)}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"❌ Error updating daily stats: {e}")
        
        return True
    
    def run(self):
        """Main trading loop"""
        self.logger.info("🚀 Starting Auto Trader...")
        
        if not self.initialize_mt5():
            self.logger.error("❌ Failed to initialize MT5. Exiting.")
            return
        
        self.is_running = True
        
        try:
            while self.is_running:
                # Check if we're in trading hours
                if not self.check_trading_hours():
                    time.sleep(60)  # Check every minute
                    continue
                
                # Update daily statistics
                if not self.update_daily_stats():
                    self.logger.warning("⚠️ Daily limits reached. Stopping trading.")
                    break
                
                # Process each symbol
                for symbol in self.symbols:
                    try:
                        # Get latest price data
                        price_data = self.get_latest_price_data(symbol)
                        if not price_data:
                            continue
                        
                        # Get signal from strategy
                        signal = self.strategy.add_price_data(price_data)
                        
                        if signal and signal.direction != 'NEUTRAL':
                            self.logger.info(f"📈 Signal: {signal.direction} {symbol} - {signal.reason}")
                            self.process_signal(symbol, signal)
                        
                    except Exception as e:
                        self.logger.error(f"❌ Error processing {symbol}: {e}")
                        continue
                
                # Log status every hour
                if self.trades_today % 10 == 0 and self.trades_today > 0:
                    self.logger.info(f"📊 Status: {self.trades_today} trades today, P&L: {format_currency(self.daily_pnl)}")
                
                # Wait before next check
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            self.logger.info("⏹️ Auto Trader stopped by user")
        except Exception as e:
            self.logger.error(f"❌ Fatal error in trading loop: {e}")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources"""
        self.is_running = False
        mt5.shutdown()
        self.logger.info("🔄 Auto Trader shutdown complete")

def create_default_config():
    """Create default configuration file"""
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
    
    with open("config.json", "w") as f:
        json.dump(config, f, indent=2)
    
    print("📋 Created default config.json file")

if __name__ == "__main__":
    print("🤖 Simplified Robust Auto Trader")
    print("=" * 50)
    
    # Create config if it doesn't exist
    if not os.path.exists("config.json"):
        create_default_config()
    
    # Create logs directory
    os.makedirs("logs", exist_ok=True)
    
    # Start auto trader
    trader = AutoTrader()
    trader.run() 