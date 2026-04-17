"""
Utility functions for the Forex trading bot.
Includes technical indicators, logging setup, and helper functions.
"""

import logging
import logging.handlers
import os
import json
from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd
from datetime import datetime, timedelta


def setup_logging(log_level: str = "INFO", log_file: str = "logs/bot.log") -> logging.Logger:
    """
    Set up comprehensive logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Path to log file
        
    Returns:
        Configured logger instance
    """
    # Ensure logs directory exists
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    # Create logger
    logger = logging.getLogger("ForexBot")
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(module)s:%(funcName)s:%(lineno)d] - %(message)s'
    )
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=10*1024*1024, backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_handler.setFormatter(simple_formatter)
    
    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


def calculate_ema(prices: List[float], period: int, previous_ema: Optional[float] = None) -> float:
    """
    Calculate Exponential Moving Average.
    
    Args:
        prices: List of price values
        period: EMA period
        previous_ema: Previous EMA value for incremental calculation
        
    Returns:
        Current EMA value
    """
    if len(prices) < period:
        return np.mean(prices)
    
    alpha = 2.0 / (period + 1)
    
    if previous_ema is None:
        # Calculate initial EMA using SMA
        return np.mean(prices[-period:])
    else:
        # Incremental EMA calculation
        return alpha * prices[-1] + (1 - alpha) * previous_ema


def calculate_atr(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> float:
    """
    Calculate Average True Range (ATR) for volatility measurement.
    
    Args:
        highs: List of high prices
        lows: List of low prices  
        closes: List of close prices
        period: ATR period
        
    Returns:
        Current ATR value
    """
    if len(highs) < period + 1:
        return 0.0
    
    true_ranges = []
    for i in range(1, len(highs)):
        tr1 = highs[i] - lows[i]
        tr2 = abs(highs[i] - closes[i-1])
        tr3 = abs(lows[i] - closes[i-1])
        true_ranges.append(max(tr1, tr2, tr3))
    
    return np.mean(true_ranges[-period:])


def calculate_position_size(
    balance: float, 
    atr: float, 
    risk_fraction: float, 
    pip_value: float,
    symbol: str,
    min_lot: float = 0.01,
    max_lot: float = 10.0
) -> float:
    """
    Calculate position size based on ATR and risk management.
    
    Args:
        balance: Account balance
        atr: Average True Range in price units
        risk_fraction: Risk per trade as fraction of balance (e.g., 0.01 for 1%)
        pip_value: Value per pip for 1 lot
        symbol: Currency pair symbol
        min_lot: Minimum lot size
        max_lot: Maximum lot size
        
    Returns:
        Calculated lot size
    """
    if atr <= 0 or pip_value <= 0:
        return min_lot
    
    risk_amount = balance * risk_fraction
    
    # Convert ATR to pips (assuming 4-decimal pairs like EURUSD)
    if "JPY" in symbol:
        atr_pips = atr * 100  # JPY pairs have 2 decimals
    else:
        atr_pips = atr * 10000  # Major pairs have 4 decimals
    
    # Calculate position size
    if atr_pips > 0:
        lot_size = risk_amount / (atr_pips * pip_value)
    else:
        lot_size = min_lot
    
    # Round to nearest 0.01 and apply limits
    lot_size = round(lot_size, 2)
    return max(min_lot, min(max_lot, lot_size))


def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load configuration from JSON file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Configuration dictionary
    """
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        raise Exception(f"Failed to load config from {config_path}: {e}")


def format_currency(amount: float, currency: str = "USD") -> str:
    """
    Format currency amount for display.
    
    Args:
        amount: Amount to format
        currency: Currency code
        
    Returns:
        Formatted currency string
    """
    return f"{amount:,.2f} {currency}"


def format_price(price: float, symbol: str) -> str:
    """
    Format price based on symbol decimal places.
    
    Args:
        price: Price to format
        symbol: Currency pair symbol
        
    Returns:
        Formatted price string
    """
    if "JPY" in symbol:
        return f"{price:.3f}"
    else:
        return f"{price:.5f}"


def is_market_open() -> bool:
    """
    Check if Forex market is generally open (basic check).
    
    Returns:
        True if market is likely open
    """
    now = datetime.utcnow()
    weekday = now.weekday()
    
    # Forex market is closed from Friday 22:00 UTC to Sunday 22:00 UTC
    if weekday == 5:  # Saturday
        return False
    elif weekday == 6:  # Sunday
        return now.hour >= 22
    elif weekday == 4:  # Friday
        return now.hour < 22
    else:
        return True


def validate_symbol(symbol: str) -> bool:
    """
    Validate if symbol format is correct for Forex.
    
    Args:
        symbol: Currency pair symbol
        
    Returns:
        True if valid symbol format
    """
    if len(symbol) != 6:
        return False
    
    # Check if it's a valid currency pair format
    major_currencies = ['USD', 'EUR', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD', 'NZD']
    base = symbol[:3]
    quote = symbol[3:]
    
    return base in major_currencies and quote in major_currencies and base != quote


class TradeSignal:
    """Data class for trade signals."""
    
    def __init__(self, symbol: str, direction: str, volume: float, 
                 entry_price: float, sl: float, tp: float, timestamp: datetime = None):
        self.symbol = symbol
        self.direction = direction.upper()  # BUY or SELL
        self.volume = volume
        self.entry_price = entry_price
        self.sl = sl
        self.tp = tp
        self.timestamp = timestamp or datetime.utcnow()
    
    def __str__(self) -> str:
        return (f"TradeSignal({self.direction} {self.volume} {self.symbol} "
                f"@ {self.entry_price}, SL: {self.sl}, TP: {self.tp})")


class PriceData:
    """Data class for price information."""
    
    def __init__(self, symbol: str, timestamp: datetime, open_price: float, 
                 high: float, low: float, close: float, tick_volume: int = 0):
        self.symbol = symbol
        self.timestamp = timestamp
        self.open = open_price
        self.high = high
        self.low = low
        self.close = close
        self.tick_volume = tick_volume
    
    def __str__(self) -> str:
        return (f"PriceData({self.symbol} {self.timestamp}: "
                f"O:{self.open} H:{self.high} L:{self.low} C:{self.close})") 