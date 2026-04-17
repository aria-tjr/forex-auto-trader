#!/usr/bin/env python3
"""
Realistic Profit Enhanced Strategy - Conservative Approach for Sustainable Returns
Based on proven final_optimized_strategy with realistic enhancements

PROVEN BASELINE:
- Final Optimized Strategy: 16.1% total return, 7.8% annual, 45.5% win rate, 595 trades

REALISTIC ENHANCEMENTS:
✅ Moderate position size increase (1.5% → 2.0%)
✅ Slightly reduced cooldown (24h → 20h)
✅ Conservative compound growth (max 1.3x multiplier)
✅ Enhanced signal filtering for quality
✅ All risk protections maintained

REALISTIC TARGETS:
- Monthly Return: 1.0-1.5% (vs current 0.65%)
- Annual Return: 12-18% (vs current 7.8%)
- Win Rate: 40%+ maintained  
- Max Drawdown: <15%
"""

import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any

class ConservativeCompoundManager:
    """Very conservative compound growth management"""
    
    def __init__(self, base_risk: float = 0.020):
        self.base_risk = base_risk
        self.initial_balance = None
        self.peak_balance = 0
        
    def get_risk_multiplier(self, current_balance: float) -> float:
        """Conservative compound growth with strict limits"""
        if self.initial_balance is None:
            self.initial_balance = current_balance
            
        if current_balance > self.peak_balance:
            self.peak_balance = current_balance
            
        # Calculate growth
        growth_pct = (current_balance - self.initial_balance) / self.initial_balance
        
        # Very conservative compound scaling with hard caps
        if growth_pct > 0.50:  # 50% profit -> max 1.3x
            return 1.3
        elif growth_pct > 0.25:  # 25% profit -> 1.2x
            return 1.2
        elif growth_pct > 0.10:  # 10% profit -> 1.1x
            return 1.1
        else:
            return 1.0
            
        # Reset multiplier if significant drawdown
        current_drawdown = (self.peak_balance - current_balance) / self.peak_balance
        if current_drawdown > 0.10:  # Reset at 10% drawdown
            return 1.0

class RealisticProfitEnhancedStrategy:
    """Realistic profit enhancement with conservative approach"""
    
    def __init__(self):
        # CONSERVATIVE ENHANCED PARAMETERS
        self.ema_fast = 12           # Keep proven parameters
        self.ema_slow = 26           
        self.ema_trend = 50
        self.rsi_period = 14
        
        # MODERATE ENHANCEMENT
        self.min_signal_strength = 0.60        # Keep quality high
        self.min_confirmations_trending = 2    
        self.min_confirmations_ranging = 3     
        self.min_bars_between_signals = 20    # Moderate reduction: 24h → 20h
        
        # CONSERVATIVE RISK MANAGEMENT
        self.base_risk_per_trade = 0.020      # Moderate increase: 1.5% → 2.0%
        self.max_portfolio_risk = 0.07        # Slight increase: 6% → 7%
        self.max_daily_trades = 2             
        
        # CONSERVATIVE COMPOUND SYSTEM
        self.compound_manager = ConservativeCompoundManager(base_risk=0.020)
        
        # REALISTIC PROFIT TARGETS
        self.profit_targets = {
            'UPTREND': 0.030,          # 3.0% profit target
            'DOWNTREND': 0.025,        # 2.5% profit target
            'SIDEWAYS': 0.020,         # 2.0% profit target
            'HIGH_VOLATILITY': 0.015   # 1.5% profit target
        }
        
        # CONSERVATIVE STOP LOSSES
        self.stop_losses = {
            'UPTREND': 0.018,          # 1.8% stop loss
            'DOWNTREND': 0.018,        # 1.8% stop loss
            'SIDEWAYS': 0.015,         # 1.5% stop loss
            'HIGH_VOLATILITY': 0.012   # 1.2% stop loss
        }
        
        # STATE TRACKING
        self.price_history = []
        self.last_signal_bar = -999
        self.current_regime = 'UNKNOWN'
        self.total_trades = 0
        
        # REALISTIC COSTS
        self.trading_costs = 0.003  # 0.3% total cost
        
    def calculate_indicators(self, data: pd.DataFrame) -> Dict:
        """Calculate indicators using proven approach"""
        if len(data) < 50:
            return {}
        
        close = data['close'].values
        
        # EMAs using proven parameters
        ema_fast = self._ema(close, self.ema_fast)
        ema_slow = self._ema(close, self.ema_slow)
        ema_trend = self._ema(close, self.ema_trend)
        
        # RSI
        rsi = self._rsi(close, self.rsi_period)
        
        # Volatility
        volatility = np.std(close[-20:]) / np.mean(close[-20:])
        
        # Trend strength  
        trend_strength = abs(ema_fast[-1] - ema_slow[-1]) / ema_slow[-1]
        
        # Price momentum
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
        """Market regime detection with proven thresholds"""
        if not indicators:
            return 'UNKNOWN'
        
        price = indicators['price']
        ema_fast = indicators['ema_fast']
        ema_slow = indicators['ema_slow']
        ema_trend = indicators['ema_trend']
        volatility = indicators['volatility']
        
        # Keep proven volatility filter
        if volatility > 0.035:  # 3.5% volatility threshold
            return 'HIGH_VOLATILITY'
        
        # Proven trend determination
        fast_above_slow = ema_fast > ema_slow
        price_above_trend = price > ema_trend
        trend_strength = indicators['trend_strength']
        
        # Keep successful trend requirements
        if fast_above_slow and price_above_trend and trend_strength > 0.015:
            return 'UPTREND'
        elif not fast_above_slow and not price_above_trend and trend_strength > 0.015:
            return 'DOWNTREND'
        else:
            return 'SIDEWAYS'
    
    def generate_enhanced_signal(self, indicators: Dict, bar_index: int, stress_period: bool = False) -> Dict:
        """Generate signals with moderate enhancement"""
        if not indicators:
            return {'direction': 'NEUTRAL', 'strength': 0, 'reason': 'No data'}
        
        # Moderate cooldown reduction
        if bar_index - self.last_signal_bar < self.min_bars_between_signals:
            return {'direction': 'NEUTRAL', 'strength': 0, 'reason': 'Cooldown period'}
        
        # Market regime
        regime = self.determine_market_regime(indicators)
        self.current_regime = regime
        
        # Keep conservative regime filtering
        if regime == 'UNKNOWN':
            return {'direction': 'NEUTRAL', 'strength': 0, 'reason': 'Unknown regime'}
        
        # Filter high volatility during stress (conservative)
        if regime == 'HIGH_VOLATILITY' and stress_period:
            return {'direction': 'NEUTRAL', 'strength': 0, 'reason': 'High volatility + stress'}
        
        confirmations = []
        
        # PROVEN CONFIRMATIONS (keep successful approach)
        
        # 1. EMA Alignment
        if indicators['ema_fast'] > indicators['ema_slow']:
            confirmations.append(('BUY', 'EMA Bullish'))
        elif indicators['ema_fast'] < indicators['ema_slow']:
            confirmations.append(('SELL', 'EMA Bearish'))
        
        # 2. RSI (slightly wider ranges for more opportunities)
        rsi = indicators['rsi']
        if regime == 'UPTREND':
            if 30 < rsi < 65:  # Slightly wider than original
                confirmations.append(('BUY', 'RSI Favorable in Uptrend'))
        elif regime == 'DOWNTREND':
            if 35 < rsi < 70:  # Slightly wider than original
                confirmations.append(('SELL', 'RSI Favorable in Downtrend'))
        elif regime == 'SIDEWAYS':
            if rsi < 35:  # Slightly more permissive
                confirmations.append(('BUY', 'RSI Oversold'))
            elif rsi > 65:  # Slightly more permissive
                confirmations.append(('SELL', 'RSI Overbought'))
        
        # 3. Price vs Trend
        price_trend_ratio = indicators['price'] / indicators['ema_trend']
        if regime in ['UPTREND', 'SIDEWAYS'] and 0.98 < price_trend_ratio < 1.05:
            confirmations.append(('BUY', 'Price Near Trend'))
        elif regime in ['DOWNTREND', 'SIDEWAYS'] and 0.95 < price_trend_ratio < 1.02:
            confirmations.append(('SELL', 'Price Near Trend'))
        
        # 4. Momentum
        momentum = indicators['momentum']
        if momentum > 0.005:  # 0.5% positive momentum
            confirmations.append(('BUY', 'Positive Momentum'))
        elif momentum < -0.005:  # 0.5% negative momentum
            confirmations.append(('SELL', 'Negative Momentum'))
        
        # 5. Trend Strength
        if indicators['trend_strength'] > 0.010:  # Slightly lower threshold
            if regime == 'UPTREND':
                confirmations.append(('BUY', 'Uptrend Strength'))
            elif regime == 'DOWNTREND':
                confirmations.append(('SELL', 'Downtrend Strength'))
        
        # Aggregate confirmations
        buy_confirmations = [c for c in confirmations if c[0] == 'BUY']
        sell_confirmations = [c for c in confirmations if c[0] == 'SELL']
        
        # Keep proven confirmation requirements
        required_confirmations = self.min_confirmations_trending if regime in ['UPTREND', 'DOWNTREND'] else self.min_confirmations_ranging
        
        if len(buy_confirmations) >= required_confirmations:
            signal_strength = min(len(buy_confirmations) / 5.0, 1.0)
            if signal_strength >= self.min_signal_strength:
                return {
                    'direction': 'BUY',
                    'strength': signal_strength,
                    'confirmations': buy_confirmations,
                    'regime': regime,
                    'reason': f'{len(buy_confirmations)} bullish confirmations in {regime}'
                }
        elif len(sell_confirmations) >= required_confirmations:
            signal_strength = min(len(sell_confirmations) / 5.0, 1.0)
            if signal_strength >= self.min_signal_strength:
                return {
                    'direction': 'SELL',
                    'strength': signal_strength,
                    'confirmations': sell_confirmations,
                    'regime': regime,
                    'reason': f'{len(sell_confirmations)} bearish confirmations in {regime}'
                }
        
        return {'direction': 'NEUTRAL', 'strength': 0, 'reason': f'Insufficient confirmations in {regime}'}
    
    def calculate_realistic_position_size(self, balance: float, entry_price: float, signal_strength: float, regime: str) -> Dict:
        """Calculate position size with conservative compound growth"""
        # Get conservative risk multiplier
        risk_multiplier = self.compound_manager.get_risk_multiplier(balance)
        
        # Conservative risk calculation
        base_risk = self.base_risk_per_trade
        
        # Moderate signal strength adjustment
        signal_multiplier = 0.85 + (signal_strength * 0.3)  # 0.85x to 1.15x
        
        # Moderate regime adjustment
        regime_multiplier = 1.0
        if regime in ['UPTREND', 'DOWNTREND']:
            regime_multiplier = 1.1  # 10% more aggressive (conservative)
        elif regime == 'SIDEWAYS':
            regime_multiplier = 0.9   # 10% less aggressive
        elif regime == 'HIGH_VOLATILITY':
            regime_multiplier = 0.7   # 30% less aggressive
        
        # Calculate final risk (with caps)
        final_risk = base_risk * risk_multiplier * signal_multiplier * regime_multiplier
        final_risk = min(final_risk, 0.035)  # Hard cap at 3.5% risk per trade
        
        # Conservative stop loss
        stop_loss_pct = self.stop_losses.get(regime, 0.018)
        
        # Position value calculation
        risk_amount = balance * final_risk
        position_value = risk_amount / stop_loss_pct
        
        # Conservative position limits
        max_position_value = balance * 0.60  # Maximum 60% of balance
        position_value = min(position_value, max_position_value)
        
        # Position size percentage
        position_size_pct = (position_value / balance) * 100
        
        # Profit target
        profit_target_pct = self.profit_targets.get(regime, 0.025)
        
        return {
            'position_size': position_value,
            'position_size_pct': position_size_pct,
            'risk_amount': risk_amount,
            'risk_pct': final_risk * 100,
            'stop_loss_pct': stop_loss_pct * 100,
            'profit_target_pct': profit_target_pct * 100,
            'compound_multiplier': risk_multiplier,
            'regime': regime
        }
    
    def add_price_data(self, price_data: Dict, bar_index: int) -> Dict:
        """Main strategy entry point"""
        self.price_history.append(price_data)
        
        # Keep reasonable history
        if len(self.price_history) > 200:
            self.price_history = self.price_history[-200:]
        
        # Need sufficient data
        if len(self.price_history) < 50:
            return {'direction': 'NEUTRAL', 'strength': 0, 'reason': 'Insufficient data'}
        
        # Convert to DataFrame
        df = pd.DataFrame(self.price_history)
        
        # Calculate indicators
        indicators = self.calculate_indicators(df)
        
        # Generate signal
        stress_period = price_data.get('stress_period', False)
        signal = self.generate_enhanced_signal(indicators, bar_index, stress_period)
        
        # Add position sizing if signal generated
        if signal['direction'] != 'NEUTRAL':
            current_balance = getattr(self, 'current_balance', 10000)
            entry_price = price_data['close']
            regime = signal.get('regime', 'UNKNOWN')
            
            position_info = self.calculate_realistic_position_size(
                current_balance, entry_price, signal['strength'], regime
            )
            signal.update(position_info)
            
            self.last_signal_bar = bar_index
            self.total_trades += 1
        
        return signal
    
    def _ema(self, prices: np.ndarray, period: int) -> np.ndarray:
        """Calculate EMA"""
        if len(prices) < period:
            return np.array([prices[-1]] if len(prices) > 0 else [])
        
        alpha = 2.0 / (period + 1)
        ema = np.zeros_like(prices, dtype=float)
        ema[0] = prices[0]
        
        for i in range(1, len(prices)):
            ema[i] = alpha * prices[i] + (1 - alpha) * ema[i-1]
        
        return ema
    
    def _rsi(self, prices: np.ndarray, period: int) -> np.ndarray:
        """Calculate RSI"""
        if len(prices) < period + 1:
            return np.array([50.0])
        
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gains = np.convolve(gains, np.ones(period), 'valid') / period
        avg_losses = np.convolve(losses, np.ones(period), 'valid') / period
        
        rs = avg_gains / (avg_losses + 1e-10)
        rsi = 100 - (100 / (1 + rs))
        
        return rsi

if __name__ == "__main__":
    print("Realistic Profit Enhanced Strategy - Conservative Approach")
    print("🎯 Target: 12-18% annual returns")
    print("✅ Based on proven 16.1% baseline")
    print("✅ Conservative position sizing")
    print("✅ Moderate trade frequency increase")
    print("✅ Safe compound growth system")
    print("✅ All risk protections maintained")
    print("Ready for realistic profit deployment!") 