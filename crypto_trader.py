#!/usr/bin/env python3
"""
Crypto Auto Trading Bot - Simplified Robust Strategy
Clean, production-ready implementation for crypto trading

Features:
- Simplified robust strategy (6 parameters, no overfitting)
- Proper risk management for crypto volatility
- Real-time signal generation
- Binance integration
- Comprehensive logging
- 24/7 crypto market support
"""

import sys
import os
import time
import json
import logging
import hmac
import hashlib
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd

# Try to import binance, fallback to mock for testing
try:
    from binance.client import Client
    from binance.exceptions import BinanceAPIException
    USING_MOCK = False
except ImportError:
    print("🔧 Binance client not available, using mock implementation...")
    import mock_binance as binance_client
    USING_MOCK = True

# Import our modules (adapted for crypto)
from simplified_robust_strategy import SimplifiedRobustStrategy, PriceData, Signal
from utils import setup_logging, format_currency, TradeSignal
from crypto_risk_manager import CryptoRiskManager
from crypto_execution import CryptoExecutionEngine

class CryptoAutoTrader:
    """
    Main crypto auto trading bot using simplified robust strategy
    """
    
    def __init__(self, config_file: str = "crypto_config.json"):
        """Initialize the crypto auto trader"""
        self.logger = setup_logging("INFO", "logs/crypto_trader.log")
        self.config = self._load_config(config_file)
        
        # Initialize Binance client
        self.client = None
        self.exchange_info = None
        
        # Initialize components (adapted for crypto)
        self.strategy = SimplifiedRobustStrategy()
        self.risk_manager = CryptoRiskManager(
            max_risk_per_trade=self.config.get('max_risk_per_trade', 0.02),  # Higher for crypto
            max_daily_loss=self.config.get('max_daily_loss', 0.08),  # Higher for crypto volatility
            max_open_positions=self.config.get('max_open_positions', 5)  # More positions for crypto
        )
        self.execution_engine = CryptoExecutionEngine()
        
        # Trading state
        self.is_running = False
        self.symbols = self.config.get('symbols', ['BTCUSDT', 'ETHUSDT', 'ADAUSDT'])
        # One strategy instance per symbol, so price histories are not mixed across symbols
        self.strategies = {sym: SimplifiedRobustStrategy() for sym in self.symbols}
        self._last_bar_open = {}
        self.timeframe = self.config.get('timeframe', '15m')  # Binance format
        self.check_interval = self.config.get('check_interval', 30)  # Faster for crypto
        
        # Statistics
        self.trades_today = 0
        self.daily_pnl = 0.0
        self.start_balance = 0.0
        self.base_currency = 'USDT'  # Crypto base currency
        
        self.logger.info("🚀 Crypto Auto Trader initialized successfully")
        self.logger.info(f"📊 Strategy: {self.strategy.get_strategy_info()['name']}")
        self.logger.info(f"₿ Symbols: {self.symbols}")
        self.logger.info(f"⏱️ Check interval: {self.check_interval}s")
    
    def _load_config(self, config_file: str) -> Dict:
        """Load configuration from file"""
        default_config = {
            "symbols": ["BTCUSDT", "ETHUSDT", "ADAUSDT", "BNBUSDT", "SOLUSDT"],
            "timeframe": "15m",  # Binance format: 1m, 5m, 15m, 1h, 4h, 1d
            "check_interval": 30,  # Faster for crypto markets
            "max_risk_per_trade": 0.02,  # 2% risk per trade (higher for crypto)
            "max_daily_loss": 0.08,  # 8% daily loss limit (crypto volatility)
            "max_open_positions": 5,
            "base_currency": "USDT",
            "min_notional": 10.0,  # Minimum trade size in USDT
            "api_keys": {
                "api_key": "",
                "api_secret": "",
                "testnet": True  # Start with testnet
            },
            "trading_mode": "spot",  # spot or futures
            "stop_loss_pct": 3.0,  # 3% stop loss (adjusted for crypto)
            "take_profit_pct": 6.0,  # 6% take profit (2:1 ratio)
            "trading_hours": {
                "enabled": False,  # Crypto trades 24/7
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
                # Create default config file
                with open(config_file, 'w') as f:
                    json.dump(default_config, f, indent=2)
                self.logger.info(f"📋 Created default {config_file}")
        except Exception as e:
            self.logger.error(f"❌ Error loading config: {e}")
            self.logger.info("📋 Using default config")
        
        return default_config
    
    def initialize_binance(self) -> bool:
        """Initialize Binance connection"""
        try:
            api_key = self.config['api_keys']['api_key']
            api_secret = self.config['api_keys']['api_secret']
            testnet = self.config['api_keys']['testnet']
            
            if not api_key or not api_secret:
                self.logger.error("❌ Binance API keys not configured")
                self.logger.info("💡 Please add your Binance API keys to crypto_config.json")
                return False
            
            # Initialize Binance client
            self.client = Client(
                api_key=api_key,
                api_secret=api_secret,
                testnet=testnet
            )
            
            # Test connection
            account = self.client.get_account()
            
            # Get USDT balance
            usdt_balance = 0.0
            for balance in account['balances']:
                if balance['asset'] == self.base_currency:
                    usdt_balance = float(balance['free'])
                    break
            
            self.start_balance = usdt_balance
            self.logger.info(f"✅ Binance {'Testnet' if testnet else 'Mainnet'} connected successfully")
            self.logger.info(f"💰 {self.base_currency} balance: {format_currency(usdt_balance)}")
            
            # Get exchange info for symbols
            self.exchange_info = self.client.get_exchange_info()
            
            return True
            
        except BinanceAPIException as e:
            self.logger.error(f"❌ Binance API error: {e}")
            return False
        except Exception as e:
            self.logger.error(f"❌ Binance initialization error: {e}")
            return False
    
    def get_latest_price_data(self, symbol: str) -> Optional[PriceData]:
        """Get latest price data for crypto symbol"""
        try:
            # Get the latest kline data
            # limit=2: klines[-1] is the still-forming candle, klines[-2] is the last CLOSED one.
            # Only closed candles are fed to the strategy, each exactly once.
            klines = self.client.get_klines(
                symbol=symbol,
                interval=self.timeframe,
                limit=2
            )
            
            if not klines or len(klines) < 2:
                return None
            
            kline = klines[-2]
            if self._last_bar_open.get(symbol) == kline[0]:
                return None  # already processed this closed candle
            self._last_bar_open[symbol] = kline[0]
            return PriceData(
                timestamp=datetime.fromtimestamp(kline[0] / 1000),
                open=float(kline[1]),
                high=float(kline[2]),
                low=float(kline[3]),
                close=float(kline[4]),
                volume=float(kline[5])
            )
            
        except Exception as e:
            self.logger.error(f"❌ Error getting price data for {symbol}: {e}")
            return None
    
    def get_symbol_info(self, symbol: str) -> Optional[Dict]:
        """Get trading rules for symbol"""
        try:
            for s in self.exchange_info['symbols']:
                if s['symbol'] == symbol:
                    return s
            return None
        except Exception as e:
            self.logger.error(f"❌ Error getting symbol info for {symbol}: {e}")
            return None
    
    def process_signal(self, symbol: str, signal: Signal) -> bool:
        """Process crypto trading signal"""
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
            
            # Get symbol info for lot size rules
            symbol_info = self.get_symbol_info(symbol)
            if not symbol_info:
                self.logger.error(f"❌ Could not get symbol info for {symbol}")
                return False
            
            # Get account balance
            account = self.client.get_account()
            usdt_balance = 0.0
            for balance in account['balances']:
                if balance['asset'] == self.base_currency:
                    usdt_balance = float(balance['free'])
                    break
            
            # Calculate position size for crypto
            position_size_usdt = self.risk_manager.calculate_position_size(
                usdt_balance,
                symbol,
                signal.direction,
                price_data.close
            )
            
            # Convert USDT amount to base crypto quantity
            quantity = position_size_usdt / price_data.close
            
            # Apply symbol lot size filters
            quantity = self._apply_lot_size_filter(quantity, symbol_info)
            
            if quantity == 0:
                self.logger.warning(f"⚠️ Position size too small for {symbol}")
                return False
            
            # Calculate stop loss and take profit prices
            if signal.direction == 'BUY':
                stop_price = price_data.close * (1 - self.config['stop_loss_pct'] / 100)
                take_profit_price = price_data.close * (1 + self.config['take_profit_pct'] / 100)
            else:  # SELL
                stop_price = price_data.close * (1 + self.config['stop_loss_pct'] / 100)
                take_profit_price = price_data.close * (1 - self.config['take_profit_pct'] / 100)
            
            # Execute trade
            result = self.execution_engine.place_crypto_order(
                client=self.client,
                symbol=symbol,
                side=signal.direction,
                quantity=quantity,
                price=price_data.close,
                stop_price=stop_price,
                take_profit_price=take_profit_price
            )
            
            if result:
                self.trades_today += 1
                self.logger.info(f"✅ {signal.direction} order placed for {symbol}")
                self.logger.info(f"📊 Quantity: {quantity:.6f}, Price: {price_data.close:.6f}")
                self.logger.info(f"🛡️ Stop Loss: {stop_price:.6f}, Take Profit: {take_profit_price:.6f}")
                self.logger.info(f"🎯 Reason: {signal.reason}")
                return True
            else:
                self.logger.error(f"❌ Failed to place order for {symbol}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error processing signal for {symbol}: {e}")
            return False
    
    def _apply_lot_size_filter(self, quantity: float, symbol_info: Dict) -> float:
        """Apply Binance lot size filters"""
        try:
            for filter in symbol_info['filters']:
                if filter['filterType'] == 'LOT_SIZE':
                    min_qty = float(filter['minQty'])
                    max_qty = float(filter['maxQty'])
                    step_size = float(filter['stepSize'])
                    
                    # Ensure quantity meets minimum
                    if quantity < min_qty:
                        return 0.0
                    
                    # Ensure quantity doesn't exceed maximum
                    if quantity > max_qty:
                        quantity = max_qty
                    
                    # Round to step size
                    quantity = round(quantity / step_size) * step_size
                    
                    # Remove floating point precision issues
                    precision = len(str(step_size).split('.')[-1]) if '.' in str(step_size) else 0
                    quantity = round(quantity, precision)
                    
                    return quantity
            
            return quantity
            
        except Exception as e:
            self.logger.error(f"❌ Error applying lot size filter: {e}")
            return 0.0
    
    def check_trading_hours(self) -> bool:
        """Check if within trading hours (crypto trades 24/7 by default)"""
        if not self.config.get('trading_hours', {}).get('enabled', False):
            return True  # Crypto markets are 24/7
        
        current_time = datetime.now().strftime('%H:%M')
        start_time = self.config['trading_hours']['start']
        end_time = self.config['trading_hours']['end']
        
        return start_time <= current_time <= end_time
    
    def update_daily_stats(self):
        """Update daily trading statistics"""
        try:
            if not self.client:
                return
            
            # Get account info
            account = self.client.get_account()
            current_balance = 0.0
            
            for balance in account['balances']:
                if balance['asset'] == self.base_currency:
                    current_balance = float(balance['free']) + float(balance['locked'])
                    break
            
            self.daily_pnl = current_balance - self.start_balance
            
            self.logger.info(f"📊 Daily Stats - Trades: {self.trades_today}, P&L: {format_currency(self.daily_pnl)}")
            
        except Exception as e:
            self.logger.error(f"❌ Error updating daily stats: {e}")
    
    def run(self):
        """Main trading loop for crypto"""
        try:
            self.logger.info("🚀 Starting Crypto Auto Trader...")
            
            # Initialize Binance connection
            if not self.initialize_binance():
                self.logger.error("❌ Failed to initialize Binance connection")
                return
            
            self.is_running = True
            self.logger.info("✅ Crypto trading bot is now running...")
            self.logger.info("📱 Trading 24/7 on crypto markets")
            self.logger.info("🛑 Press Ctrl+C to stop safely")
            
            while self.is_running:
                try:
                    # Check if within trading hours (if enabled)
                    if not self.check_trading_hours():
                        self.logger.debug("⏰ Outside trading hours, waiting...")
                        time.sleep(self.check_interval)
                        continue
                    
                    # Process each symbol
                    for symbol in self.symbols:
                        if not self.is_running:
                            break
                        
                        try:
                            # Get latest price data
                            price_data = self.get_latest_price_data(symbol)
                            if not price_data:
                                continue
                            
                            # Generate signal
                            signal = self.strategies[symbol].add_price_data(price_data)
                            
                            if signal and signal.direction != 'NEUTRAL':
                                self.logger.info(f"📈 Signal: {signal.direction} for {symbol} (strength: {signal.strength:.2f})")
                                
                                # Process the signal
                                self.process_signal(symbol, signal)
                            
                        except Exception as e:
                            self.logger.error(f"❌ Error processing {symbol}: {e}")
                            continue
                    
                    # Update daily statistics
                    self.update_daily_stats()
                    
                    # Sleep before next check
                    time.sleep(self.check_interval)
                    
                except KeyboardInterrupt:
                    self.logger.info("⏹️ Received stop signal...")
                    break
                except Exception as e:
                    self.logger.error(f"❌ Unexpected error in main loop: {e}")
                    time.sleep(self.check_interval)
            
        except Exception as e:
            self.logger.error(f"❌ Fatal error in run(): {e}")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean shutdown"""
        self.is_running = False
        self.logger.info("🧹 Cleaning up...")
        self.logger.info("✅ Crypto Auto Trader stopped safely")

def create_default_crypto_config():
    """Create default crypto configuration file"""
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
            "api_key": "YOUR_BINANCE_API_KEY",
            "api_secret": "YOUR_BINANCE_API_SECRET",
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
    
    with open("crypto_config.json", 'w') as f:
        json.dump(config, f, indent=2)
    
    print("📋 Created crypto_config.json")
    print("🔑 Please add your Binance API keys to the config file")

if __name__ == "__main__":
    # Create default config if it doesn't exist
    if not os.path.exists("crypto_config.json"):
        create_default_crypto_config()
        print("⚠️ Please configure your API keys in crypto_config.json before running")
        sys.exit(1)
    
    # Start the crypto trader
    trader = CryptoAutoTrader()
    try:
        trader.run()
    except KeyboardInterrupt:
        print("\n⏹️ Crypto trader stopped by user") 