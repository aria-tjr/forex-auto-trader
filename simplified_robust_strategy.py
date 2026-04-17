#!/usr/bin/env python3
"""
Simplified Robust Multi-Signal Strategy
Reduced complexity version to prevent overfitting

Key Changes from Enhanced Strategy:
1. Only 2-3 core signals (EMA crossover + RSI + optional Bollinger)
2. Standard indicator parameters (no optimization)
3. Simple confirmation logic
4. Fixed thresholds
5. Reduced parameter count from 15+ to 6
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

@dataclass
class PriceData:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int = 0

@dataclass
class Signal:
    direction: str  # 'BUY', 'SELL', 'NEUTRAL'
    strength: float  # 0.0 to 1.0
    reason: str
    timestamp: datetime

class SimplifiedRobustStrategy:
    """
    Simplified Multi-Signal Strategy with reduced complexity
    
    Core Signals (Only 3):
    1. EMA Crossover (21/50) - Trend direction
    2. RSI(14) - Momentum confirmation  
    3. Bollinger Bands - Volatility/reversal
    
    Rules:
    - BUY: Fast EMA > Slow EMA AND RSI < 70 AND Price near lower BB
    - SELL: Fast EMA < Slow EMA AND RSI > 30 AND Price near upper BB
    - Require 2/3 signals minimum (reduced from 4+ confirmations)
    """
    
    def __init__(self, config: Dict = None):
        # FIXED PARAMETERS (No optimization to prevent overfitting)
        self.fast_ema_period = 21      # Standard, not optimized
        self.slow_ema_period = 50      # Standard, not optimized  
        self.rsi_period = 14           # Standard RSI period
        self.bb_period = 20            # Standard Bollinger period
        self.bb_std = 2.0              # Standard deviation
        
        # FIXED THRESHOLDS (No optimization)
        self.rsi_oversold = 30         # Standard levels
        self.rsi_overbought = 70       # Standard levels
        self.bb_threshold = 0.2        # Distance from BB bands (20%)
        
        # Minimum confirmations (reduced from 4+ to 2)
        self.min_confirmations = 2
        
        # Data storage
        self.price_history: List[PriceData] = []
        self.signals_history: List[Signal] = []
        
        # Indicators cache
        self.ema_fast = []
        self.ema_slow = []
        self.rsi = []
        self.bb_upper = []
        self.bb_lower = []
        self.bb_middle = []
        
        logging.info("Initialized Simplified Robust Strategy with fixed parameters")
    
    def add_price_data(self, price_data: PriceData) -> Optional[Signal]:
        """Add new price data and generate signal if conditions met"""
        self.price_history.append(price_data)
        
        # Need minimum data for indicators
        if len(self.price_history) < max(self.slow_ema_period, self.bb_period, self.rsi_period):
            return None
        
        # Update indicators
        self._update_indicators()
        
        # Generate signal
        signal = self._generate_signal(price_data)
        
        if signal and signal.direction != 'NEUTRAL':
            self.signals_history.append(signal)
            
        return signal
    
    def _update_indicators(self):
        """Update all technical indicators with latest data"""
        closes = [p.close for p in self.price_history]
        
        # EMA calculations (simple, standard)
        self.ema_fast = self._calculate_ema(closes, self.fast_ema_period)
        self.ema_slow = self._calculate_ema(closes, self.slow_ema_period)
        
        # RSI calculation (standard 14-period)
        self.rsi = self._calculate_rsi(closes, self.rsi_period)
        
        # Bollinger Bands (standard 20,2)
        self.bb_upper, self.bb_middle, self.bb_lower = self._calculate_bollinger_bands(
            closes, self.bb_period, self.bb_std
        )
    
    def _generate_signal(self, current_price: PriceData) -> Signal:
        """Generate trading signal based on simplified logic"""
        if len(self.ema_fast) < 2 or len(self.rsi) < 1:
            return Signal('NEUTRAL', 0.0, 'Insufficient data', current_price.timestamp)
        
        current_close = current_price.close
        current_rsi = self.rsi[-1]
        current_ema_fast = self.ema_fast[-1]
        current_ema_slow = self.ema_slow[-1]
        current_bb_upper = self.bb_upper[-1]
        current_bb_lower = self.bb_lower[-1]
        
        # Signal 1: EMA Trend
        ema_signal = self._get_ema_signal(current_ema_fast, current_ema_slow)
        
        # Signal 2: RSI Momentum  
        rsi_signal = self._get_rsi_signal(current_rsi)
        
        # Signal 3: Bollinger Bands Position
        bb_signal = self._get_bb_signal(current_close, current_bb_upper, current_bb_lower)
        
        # Combine signals (require 2/3 confirmations)
        buy_signals = [s for s in [ema_signal, rsi_signal, bb_signal] if s == 'BUY']
        sell_signals = [s for s in [ema_signal, rsi_signal, bb_signal] if s == 'SELL']
        
        if len(buy_signals) >= self.min_confirmations:
            strength = len(buy_signals) / 3.0
            reasons = f"EMA: {ema_signal}, RSI: {rsi_signal}, BB: {bb_signal}"
            return Signal('BUY', strength, f"Buy confirmations: {len(buy_signals)}/3 - {reasons}", 
                         current_price.timestamp)
        
        elif len(sell_signals) >= self.min_confirmations:
            strength = len(sell_signals) / 3.0
            reasons = f"EMA: {ema_signal}, RSI: {rsi_signal}, BB: {bb_signal}"
            return Signal('SELL', strength, f"Sell confirmations: {len(sell_signals)}/3 - {reasons}", 
                         current_price.timestamp)
        
        return Signal('NEUTRAL', 0.0, f"Insufficient confirmations - EMA: {ema_signal}, RSI: {rsi_signal}, BB: {bb_signal}", 
                     current_price.timestamp)
    
    def _get_ema_signal(self, fast_ema: float, slow_ema: float) -> str:
        """Simple EMA crossover signal"""
        if fast_ema > slow_ema * 1.001:  # Small buffer to avoid noise
            return 'BUY'
        elif fast_ema < slow_ema * 0.999:
            return 'SELL'
        return 'NEUTRAL'
    
    def _get_rsi_signal(self, rsi: float) -> str:
        """Standard RSI momentum signal"""
        if rsi < self.rsi_oversold:
            return 'BUY'  # Oversold
        elif rsi > self.rsi_overbought:
            return 'SELL'  # Overbought
        return 'NEUTRAL'
    
    def _get_bb_signal(self, price: float, bb_upper: float, bb_lower: float) -> str:
        """Bollinger Bands mean reversion signal"""
        bb_range = bb_upper - bb_lower
        lower_threshold = bb_lower + (bb_range * self.bb_threshold)
        upper_threshold = bb_upper - (bb_range * self.bb_threshold)
        
        if price <= lower_threshold:
            return 'BUY'  # Near lower band - potential bounce
        elif price >= upper_threshold:
            return 'SELL'  # Near upper band - potential reversal
        return 'NEUTRAL'
    
    def _calculate_ema(self, prices: List[float], period: int) -> List[float]:
        """Calculate Exponential Moving Average"""
        if len(prices) < period:
            return []
        
        ema = []
        multiplier = 2 / (period + 1)
        
        # Start with SMA for first value
        sma = sum(prices[:period]) / period
        ema.append(sma)
        
        # Calculate EMA for remaining values
        for i in range(period, len(prices)):
            ema_value = (prices[i] * multiplier) + (ema[-1] * (1 - multiplier))
            ema.append(ema_value)
        
        return ema
    
    def _calculate_rsi(self, prices: List[float], period: int) -> List[float]:
        """Calculate Relative Strength Index"""
        if len(prices) < period + 1:
            return []
        
        rsi = []
        gains = []
        losses = []
        
        # Calculate price changes
        for i in range(1, len(prices)):
            change = prices[i] - prices[i-1]
            gains.append(max(change, 0))
            losses.append(max(-change, 0))
        
        if len(gains) < period:
            return []
        
        # Calculate RSI
        for i in range(period-1, len(gains)):
            avg_gain = sum(gains[i-period+1:i+1]) / period
            avg_loss = sum(losses[i-period+1:i+1]) / period
            
            if avg_loss == 0:
                rsi.append(100)
            else:
                rs = avg_gain / avg_loss
                rsi_value = 100 - (100 / (1 + rs))
                rsi.append(rsi_value)
        
        return rsi
    
    def _calculate_bollinger_bands(self, prices: List[float], period: int, std_dev: float) -> Tuple[List[float], List[float], List[float]]:
        """Calculate Bollinger Bands"""
        if len(prices) < period:
            return [], [], []
        
        upper_band = []
        middle_band = []
        lower_band = []
        
        for i in range(period-1, len(prices)):
            window = prices[i-period+1:i+1]
            sma = sum(window) / period
            variance = sum((x - sma) ** 2 for x in window) / period
            std = variance ** 0.5
            
            middle_band.append(sma)
            upper_band.append(sma + (std * std_dev))
            lower_band.append(sma - (std * std_dev))
        
        return upper_band, middle_band, lower_band
    
    def get_strategy_info(self) -> Dict:
        """Return strategy configuration and statistics"""
        return {
            'name': 'Simplified Robust Multi-Signal Strategy',
            'version': '1.0',
            'complexity_score': 6,  # Reduced from 15+
            'parameters': {
                'fast_ema_period': self.fast_ema_period,
                'slow_ema_period': self.slow_ema_period,
                'rsi_period': self.rsi_period,
                'rsi_oversold': self.rsi_oversold,
                'rsi_overbought': self.rsi_overbought,
                'min_confirmations': self.min_confirmations
            },
            'signals_generated': len(self.signals_history),
            'data_points': len(self.price_history)
        } 