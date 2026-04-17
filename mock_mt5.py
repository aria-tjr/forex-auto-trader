"""
Mock MetaTrader5 implementation for testing on macOS
Generates realistic synthetic OHLC data for backtesting
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import random

# Constants
TIMEFRAME_M1 = 1
TIMEFRAME_M5 = 5
TIMEFRAME_M15 = 15
TIMEFRAME_M30 = 30
TIMEFRAME_H1 = 60
TIMEFRAME_H4 = 240
TIMEFRAME_D1 = 1440

ORDER_TYPE_BUY = 0
ORDER_TYPE_SELL = 1

TRADE_ACTION_DEAL = 1
TRADE_RETCODE_DONE = 10009
ORDER_TIME_GTC = 0
ORDER_FILLING_IOC = 1

class MockTradeRequest:
    def __init__(self):
        self.action = TRADE_ACTION_DEAL
        self.symbol = ""
        self.volume = 0.0
        self.type = ORDER_TYPE_BUY
        self.price = 0.0
        self.sl = 0.0
        self.tp = 0.0
        self.deviation = 20
        self.magic = 0
        self.comment = ""
        self.type_time = 0
        self.type_filling = 0

def initialize() -> bool:
    """Mock initialization."""
    print("🔧 Mock MT5: Initialized successfully")
    return True

def shutdown():
    """Mock shutdown."""
    print("🔧 Mock MT5: Shutdown")

def terminal_info():
    """Mock terminal info."""
    class TerminalInfo:
        def __init__(self):
            self.build = 3560
            self.company = "Mock MetaQuotes Ltd."
            self.name = "MetaTrader 5 Mock"
            self.path = "/Applications/MetaTrader 5/terminal64.exe"
            self.data_path = "/Users/Mock/AppData/Roaming/MetaQuotes/Terminal"
            
        def _asdict(self):
            return {
                'build': self.build,
                'company': self.company,
                'name': self.name,
                'path': self.path,
                'data_path': self.data_path
            }
    
    return TerminalInfo()

def login(login: int, password: str, server: str) -> bool:
    """Mock login."""
    print(f"🔧 Mock MT5: Logged in to {server}")
    return True

def account_info():
    """Mock account info."""
    class AccountInfo:
        def __init__(self):
            self.login = 12345678
            self.server = "MockBroker-Demo"
            self.balance = 10000.0
            self.equity = 10000.0
            self.margin = 0.0
            self.free_margin = 10000.0
            self.margin_level = 0.0 if self.margin == 0 else (self.equity / self.margin) * 100
            self.trade_mode = 0  # 0 = Demo account
            
        def _asdict(self):
            return {
                'login': self.login,
                'server': self.server,
                'balance': self.balance,
                'equity': self.equity,
                'margin': self.margin,
                'free_margin': self.free_margin,
                'margin_level': self.margin_level,
                'trade_mode': self.trade_mode
            }
    
    return AccountInfo()

def symbol_info(symbol: str):
    """Mock symbol info."""
    class SymbolInfo:
        def __init__(self):
            self.spread = 15  # 1.5 pips
            self.point = 0.00001
            self.digits = 5
            self.trade_contract_size = 100000.0
            self.volume_min = 0.01
            self.volume_max = 100.0
            self.volume_step = 0.01
            
        def _asdict(self):
            return {
                'spread': self.spread,
                'point': self.point,
                'digits': self.digits,
                'trade_contract_size': self.trade_contract_size,
                'volume_min': self.volume_min,
                'volume_max': self.volume_max,
                'volume_step': self.volume_step
            }
    
    return SymbolInfo()

def symbol_info_tick(symbol: str):
    """Mock tick info."""
    class TickInfo:
        def __init__(self):
            # Realistic forex price based on symbol
            if symbol == "EURUSD":
                base_price = 1.0850
            elif symbol == "GBPUSD":
                base_price = 1.2750
            elif symbol == "USDJPY":
                base_price = 149.50
            elif symbol == "AUDUSD":
                base_price = 0.6650
            else:
                base_price = 1.1000
                
            # Add small random variation
            variation = random.uniform(-0.005, 0.005)
            self.ask = base_price + variation + 0.0001
            self.bid = base_price + variation
            self.time = int(datetime.now().timestamp())
            
        def _asdict(self):
            return {
                'ask': self.ask,
                'bid': self.bid,
                'time': self.time
            }
    
    return TickInfo()

def copy_rates_range(symbol: str, timeframe: int, date_from: datetime, date_to: datetime) -> Optional[np.ndarray]:
    """Generate realistic synthetic OHLC data."""
    
    # Calculate number of periods
    if timeframe == TIMEFRAME_M15:
        delta = timedelta(minutes=15)
    elif timeframe == TIMEFRAME_H1:
        delta = timedelta(hours=1)
    elif timeframe == TIMEFRAME_H4:
        delta = timedelta(hours=4)
    elif timeframe == TIMEFRAME_D1:
        delta = timedelta(days=1)
    else:
        delta = timedelta(minutes=15)  # Default
    
    periods = int((date_to - date_from) / delta)
    if periods <= 0:
        return None
    
    # Base prices for different symbols
    if symbol == "EURUSD":
        base_price = 1.0850
        daily_volatility = 0.008  # 0.8% daily volatility
    elif symbol == "GBPUSD":
        base_price = 1.2750
        daily_volatility = 0.012  # 1.2% daily volatility
    elif symbol == "USDJPY":
        base_price = 149.50
        daily_volatility = 0.010  # 1.0% daily volatility
    elif symbol == "AUDUSD":
        base_price = 0.6650
        daily_volatility = 0.009  # 0.9% daily volatility
    else:
        base_price = 1.1000
        daily_volatility = 0.008
    
    # Calculate volatility per period
    periods_per_day = 1440 / (delta.total_seconds() / 60)
    period_volatility = daily_volatility / np.sqrt(periods_per_day)
    
    # Generate price data with realistic patterns
    np.random.seed(42)  # For reproducible results
    
    prices = []
    current_price = base_price
    
    # Add some trending behavior
    trend_strength = random.uniform(-0.0005, 0.0005)  # Smaller random trend
    mean_reversion = 0.98  # Stronger mean reversion
    
    for i in range(periods):
        # Add trend and random walk with bounds checking
        price_change = (trend_strength + 
                       np.random.normal(0, period_volatility) +
                       (base_price - current_price) * (1 - mean_reversion) * 0.0005)
        
        # Ensure price stays within reasonable bounds
        new_price = current_price + price_change
        
        # Prevent negative prices and extreme deviations
        min_price = base_price * 0.8  # Maximum 20% below base
        max_price = base_price * 1.2  # Maximum 20% above base
        
        current_price = max(min_price, min(max_price, new_price))
        
        # Generate OHLC from current price
        volatility_factor = np.random.uniform(0.3, 1.5)
        tick_range = period_volatility * volatility_factor * current_price
        
        # Open is previous close (or current price for first bar)
        open_price = current_price
        
        # High and low around the open
        high_offset = np.random.uniform(0, tick_range)
        low_offset = np.random.uniform(0, tick_range)
        
        high_price = open_price + high_offset
        low_price = open_price - low_offset
        
        # Close within the range
        close_price = np.random.uniform(low_price, high_price)
        
        # Ensure OHLC relationships are valid
        high_price = max(high_price, open_price, close_price)
        low_price = min(low_price, open_price, close_price)
        
        # Create timestamp
        timestamp = date_from + i * delta
        
        prices.append({
            'time': int(timestamp.timestamp()),
            'open': round(open_price, 5),
            'high': round(high_price, 5),
            'low': round(low_price, 5),
            'close': round(close_price, 5),
            'tick_volume': random.randint(50, 500),
            'spread': random.randint(10, 25),
            'real_volume': 0
        })
        
        current_price = close_price
    
    # Convert to numpy structured array (MT5 format)
    dtype = [
        ('time', 'datetime64[s]'),
        ('open', 'f8'),
        ('high', 'f8'),
        ('low', 'f8'),
        ('close', 'f8'),
        ('tick_volume', 'u8'),
        ('spread', 'i4'),
        ('real_volume', 'u8')
    ]
    
    result = np.array([(
        np.datetime64(datetime.fromtimestamp(p['time'])),
        p['open'], p['high'], p['low'], p['close'],
        p['tick_volume'], p['spread'], p['real_volume']
    ) for p in prices], dtype=dtype)
    
    return result

def copy_rates_from_pos(symbol: str, timeframe: int, start_pos: int, count: int) -> Optional[np.ndarray]:
    """Generate realistic synthetic OHLC data from position."""
    
    # Calculate time range
    if timeframe == TIMEFRAME_M1:
        delta = timedelta(minutes=1)
    elif timeframe == TIMEFRAME_M5:
        delta = timedelta(minutes=5)
    elif timeframe == TIMEFRAME_M15:
        delta = timedelta(minutes=15)
    elif timeframe == TIMEFRAME_M30:
        delta = timedelta(minutes=30)
    elif timeframe == TIMEFRAME_H1:
        delta = timedelta(hours=1)
    elif timeframe == TIMEFRAME_H4:
        delta = timedelta(hours=4)
    elif timeframe == TIMEFRAME_D1:
        delta = timedelta(days=1)
    else:
        delta = timedelta(minutes=5)  # Default to M5
    
    # Calculate start time (going back from current time)
    current_time = datetime.now()
    start_time = current_time - delta * (count + start_pos)
    end_time = current_time - delta * start_pos if start_pos > 0 else current_time
    
    return copy_rates_range(symbol, timeframe, start_time, end_time)

def order_send(request) -> object:
    """Mock order sending."""
    # Handle both dict and object requests
    if isinstance(request, dict):
        symbol = request.get('symbol', 'UNKNOWN')
        volume = request.get('volume', 0.0)
        price = request.get('price', 0.0)
    else:
        symbol = getattr(request, 'symbol', 'UNKNOWN')
        volume = getattr(request, 'volume', 0.0)
        price = getattr(request, 'price', 0.0)
    
    # Create result object
    class TradeResult:
        def __init__(self):
            self.retcode = TRADE_RETCODE_DONE
            self.deal = random.randint(100000, 999999)
            self.order = random.randint(100000, 999999)
            self.volume = volume
            self.price = price
            self.comment = 'Mock trade executed'
            self.request_id = random.randint(1, 1000)
    
    result = TradeResult()
    print(f"🔧 Mock MT5: Order executed - {symbol} {volume} @ {price}")
    return result

def positions_get(symbol: str = None) -> List:
    """Mock positions."""
    return []  # No open positions for testing

def orders_get(symbol: str = None) -> List:
    """Mock pending orders."""
    return []  # No pending orders for testing

def history_deals_get(date_from: datetime, date_to: datetime, group: str = "*") -> List:
    """Mock historical deals."""
    return []  # No historical deals for testing

# Additional mock constants and functions
COPY_TICKS_ALL = 1
COPY_TICKS_INFO = 2
COPY_TICKS_TRADE = 3

def last_error():
    """Mock last error."""
    return (0, "No error")

def version():
    """Mock version."""
    return (500, 3000, "Mock MT5 for testing") 