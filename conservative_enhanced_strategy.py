#!/usr/bin/env python3
"""
Conservative Enhanced Strategy - MINIMAL Changes to Proven Strategy
Based EXACTLY on final_optimized_strategy.py with TINY conservative improvements

MINIMAL ENHANCEMENTS:
✅ Position size: 1.5% → 1.8% (small increase)
✅ Signal threshold: 0.60 → 0.58 (slightly more permissive)
✅ ALL other parameters EXACTLY the same as successful strategy
✅ NO compound growth, NO exotic features

REALISTIC TARGETS:
- Annual Return: 9-11% (vs current 7.8%)
- Monthly Return: 0.75-0.9% (vs current 0.65%)
- Maintain all safety and robustness
"""

import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any

class ConservativeEnhancedStrategy:
    """Minimal enhancement of proven final_optimized_strategy"""
    
    def __init__(self):
        # EXACT SAME PARAMETERS as successful strategy
        self.ema_fast = 12
        self.ema_slow = 26  
        self.ema_trend = 50
        self.rsi_period = 14
        
        # MINIMAL ENHANCEMENTS
        self.min_signal_strength = 0.58        # Lowered from 0.60 (tiny change)
        self.min_confirmations_trending = 2    # EXACT same
        self.min_confirmations_ranging = 3     # EXACT same
        self.min_bars_between_signals = 24    # EXACT same (no change)
        
        # SMALL RISK ENHANCEMENT
        self.base_risk_per_trade = 0.018      # Increased from 1.5% → 1.8%
        self.max_portfolio_risk = 0.06        # EXACT same
        self.max_daily_trades = 2             # EXACT same
        
        # STATE TRACKING (exact same)
        self.price_history = []
        self.last_signal_bar = -999
        self.current_regime = 'UNKNOWN'
        self.daily_trades_count = 0
        self.last_trade_date = None
        
        # EXACT SAME COSTS
        self.trading_costs = {
            'total_per_trade': 0.003  # 0.3% total cost
        }
        
    def calculate_indicators(self, data: pd.DataFrame) -> Dict:
        """Calculate indicators - EXACT same as successful strategy"""
        if len(data) < 50:
            return {}
        
        close = data['close'].values
        
        # EMAs (exact same)
        ema_fast = self._ema(close, self.ema_fast)
        ema_slow = self._ema(close, self.ema_slow)
        ema_trend = self._ema(close, self.ema_trend)
        
        # RSI (exact same)
        rsi = self._rsi(close, self.rsi_period)
        
        # Volatility (exact same)
        volatility = np.std(close[-20:]) / np.mean(close[-20:])
        
        # Trend strength (exact same)
        trend_strength = abs(ema_fast[-1] - ema_slow[-1]) / ema_slow[-1]
        
        # Price momentum (exact same)
        momentum = (close[-1] - close[-4]) / close[-4] if len(close) >= 4 else 0
        
        return {
            'ema_fast': ema_fast[-1],
            'ema_slow': ema_slow[-1], 
            'ema_trend': ema_trend[-1],
            'rsi': rsi[-1],
            'price': close[-1],
            'volatility': volatility,
            'trend_strength': trend_strength,
            'momentum': momentum
        }
    
    def determine_market_regime(self, indicators: Dict) -> str:
        """Market regime - EXACT same as successful strategy"""
        if not indicators:
            return 'UNKNOWN'
        
        price = indicators['price']
        ema_fast = indicators['ema_fast']
        ema_slow = indicators['ema_slow']
        ema_trend = indicators['ema_trend']
        volatility = indicators['volatility']
        
        # EXACT same volatility filter
        if volatility > 0.035:  # 3.5% volatility threshold
            return 'HIGH_VOLATILITY'
        
        # EXACT same trend determination
        fast_above_slow = ema_fast > ema_slow
        price_above_trend = price > ema_trend
        trend_strength = indicators['trend_strength']
        
        # EXACT same trend requirements
        if fast_above_slow and price_above_trend and trend_strength > 0.015:
            return 'UPTREND'
        elif not fast_above_slow and not price_above_trend and trend_strength > 0.015:
            return 'DOWNTREND'
        else:
            return 'SIDEWAYS'
    
    def generate_optimized_signal(self, indicators: Dict, bar_index: int) -> Dict:
        """Generate signals - EXACT same logic as successful strategy"""
        if not indicators:
            return {'direction': 'NEUTRAL', 'strength': 0, 'confirmations': [], 'reason': 'No data'}
        
        # EXACT same cooldown check
        if bar_index - self.last_signal_bar < self.min_bars_between_signals:
            return {'direction': 'NEUTRAL', 'strength': 0, 'confirmations': [], 'reason': 'Cooldown period'}
        
        # Market regime (exact same)
        regime = self.determine_market_regime(indicators)
        self.current_regime = regime
        
        # EXACT same regime filtering
        if regime == 'UNKNOWN':
            return {'direction': 'NEUTRAL', 'strength': 0, 'confirmations': [], 'reason': f'Unknown regime'}
        
        # EXACT same volatility filtering
        if regime == 'HIGH_VOLATILITY':
            return {'direction': 'NEUTRAL', 'strength': 0, 'confirmations': [], 'reason': 'High volatility'}
        
        confirmations = []
        
        # EXACT SAME CONFIRMATIONS as successful strategy
        
        # CONFIRMATION 1: EMA Alignment (exact same)
        if indicators['ema_fast'] > indicators['ema_slow']:
            confirmations.append(('BUY', 'EMA Bullish'))
        elif indicators['ema_fast'] < indicators['ema_slow']:
            confirmations.append(('SELL', 'EMA Bearish'))
        
        # CONFIRMATION 2: RSI (exact same ranges)
        rsi = indicators['rsi']
        if regime == 'UPTREND':
            if 25 < rsi < 55:  # EXACT same range
                confirmations.append(('BUY', 'RSI Favorable in Uptrend'))
        elif regime == 'DOWNTREND':
            if 45 < rsi < 75:  # EXACT same range
                confirmations.append(('SELL', 'RSI Favorable in Downtrend'))
        elif regime == 'SIDEWAYS':
            if rsi < 35:  # EXACT same
                confirmations.append(('BUY', 'RSI Oversold'))
            elif rsi > 65:  # EXACT same
                confirmations.append(('SELL', 'RSI Overbought'))
        
        # CONFIRMATION 3: Price vs Trend (exact same)
        price_trend_ratio = indicators['price'] / indicators['ema_trend']
        if regime in ['UPTREND', 'SIDEWAYS'] and 0.98 < price_trend_ratio < 1.08:
            confirmations.append(('BUY', 'Price Near Trend'))
        elif regime in ['DOWNTREND', 'SIDEWAYS'] and 0.92 < price_trend_ratio < 1.02:
            confirmations.append(('SELL', 'Price Near Trend'))
        
        # CONFIRMATION 4: Momentum (exact same)
        momentum = indicators['momentum']
        if momentum > 0.005:  # EXACT same threshold
            confirmations.append(('BUY', 'Positive Momentum'))
        elif momentum < -0.005:  # EXACT same threshold
            confirmations.append(('SELL', 'Negative Momentum'))
        
        # CONFIRMATION 5: Trend Strength (exact same)
        if indicators['trend_strength'] > 0.01:  # EXACT same threshold
            if regime == 'UPTREND':
                confirmations.append(('BUY', 'Uptrend Strength'))
            elif regime == 'DOWNTREND':
                confirmations.append(('SELL', 'Downtrend Strength'))
        
        # Aggregate confirmations (exact same logic)
        buy_confirmations = [c for c in confirmations if c[0] == 'BUY']
        sell_confirmations = [c for c in confirmations if c[0] == 'SELL']
        
        # EXACT same confirmation requirements
        required_confirmations = self.min_confirmations_trending if regime in ['UPTREND', 'DOWNTREND'] else self.min_confirmations_ranging
        
        if len(buy_confirmations) >= required_confirmations:
            signal_strength = min(len(buy_confirmations) / 5.0, 1.0)
            if signal_strength >= self.min_signal_strength:  # Only change: 0.58 vs 0.60
                return {
                    'direction': 'BUY',
                    'strength': signal_strength,
                    'confirmations': buy_confirmations,
                    'reason': f'{len(buy_confirmations)} bullish confirmations in {regime}'
                }
        elif len(sell_confirmations) >= required_confirmations:
            signal_strength = min(len(sell_confirmations) / 5.0, 1.0)
            if signal_strength >= self.min_signal_strength:  # Only change: 0.58 vs 0.60
                return {
                    'direction': 'SELL',
                    'strength': signal_strength,
                    'confirmations': sell_confirmations,
                    'reason': f'{len(sell_confirmations)} bearish confirmations in {regime}'
                }
        
        return {'direction': 'NEUTRAL', 'strength': 0, 'confirmations': [], 'reason': 'Insufficient confirmations'}
    
    def add_price_data(self, price_data: Dict, bar_index: int) -> Dict:
        """Add price data - EXACT same as successful strategy"""
        
        # Add to price history
        self.price_history.append(price_data)
        
        # Ensure we have enough data
        if len(self.price_history) < 50:
            return {'direction': 'NEUTRAL', 'strength': 0, 'reason': 'Insufficient data'}
        
        # Create DataFrame for indicator calculation
        df = pd.DataFrame(self.price_history)
        
        # Calculate indicators
        indicators = self.calculate_indicators(df)
        
        if not indicators:
            return {'direction': 'NEUTRAL', 'strength': 0, 'reason': 'Indicator calculation failed'}
        
        # Generate signal
        signal = self.generate_optimized_signal(indicators, bar_index)
        
        # Update last signal bar if signal generated
        if signal['direction'] != 'NEUTRAL':
            self.last_signal_bar = bar_index
        
        return signal
    
    def calculate_position_size(self, balance: float, entry_price: float, 
                              stop_loss_price: float, signal_strength: float) -> Dict:
        """Calculate position size - EXACT same as successful strategy (with tiny risk increase)"""
        
        # Small enhancement: 1.5% → 1.8% risk
        risk_per_trade = self.base_risk_per_trade
        
        # Calculate risk amount
        risk_amount = balance * risk_per_trade
        
        # Calculate position size based on stop loss distance
        stop_loss_distance = abs(entry_price - stop_loss_price) / entry_price
        
        if stop_loss_distance > 0:
            position_value = risk_amount / stop_loss_distance
        else:
            position_value = balance * 0.01  # Fallback: 1% of balance
        
        # Safety limits (exact same)
        max_position_value = balance * 0.25  # Maximum 25% of balance
        position_value = min(position_value, max_position_value)
        
        # Ensure we don't exceed portfolio risk limits
        if position_value > balance * self.max_portfolio_risk:
            position_value = balance * self.max_portfolio_risk
        
        return {
            'position_value': position_value,
            'risk_amount': risk_amount,
            'stop_loss_distance': stop_loss_distance
        }
    
    def _ema(self, prices: np.ndarray, period: int) -> np.ndarray:
        """Calculate EMA - EXACT same"""
        alpha = 2.0 / (period + 1.0)
        ema = np.zeros_like(prices)
        ema[0] = prices[0]
        
        for i in range(1, len(prices)):
            ema[i] = alpha * prices[i] + (1 - alpha) * ema[i-1]
        
        return ema
    
    def _rsi(self, prices: np.ndarray, period: int) -> np.ndarray:
        """Calculate RSI - EXACT same"""
        if len(prices) < period + 1:
            return np.full_like(prices, 50.0)
        
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gains = np.zeros_like(prices)
        avg_losses = np.zeros_like(prices)
        
        # Initial SMA
        avg_gains[period] = np.mean(gains[:period])
        avg_losses[period] = np.mean(losses[:period])
        
        # Subsequent EMA
        for i in range(period + 1, len(prices)):
            avg_gains[i] = (avg_gains[i-1] * (period - 1) + gains[i-1]) / period
            avg_losses[i] = (avg_losses[i-1] * (period - 1) + losses[i-1]) / period
        
        rs = np.divide(avg_gains, avg_losses, out=np.ones_like(avg_gains), where=avg_losses!=0)
        rsi = 100 - (100 / (1 + rs))
        
        return rsi 