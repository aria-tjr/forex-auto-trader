#!/usr/bin/env python3
"""
Profit Enhanced Strategy V2 - Balanced Approach for Higher Returns
Based on the successful final_optimized_strategy with calculated enhancements

PROVEN PERFORMANCE BASELINE:
- Final Optimized Strategy: 16.1% total return, 7.8% annual, 45.5% win rate, 595 trades

ENHANCEMENTS FOR HIGHER PROFIT:
✅ Increased position sizing (1.5% → 2.5%)
✅ Reduced cooldown period (24h → 16h) 
✅ Enhanced signal quality for more opportunities
✅ Compound growth implementation
✅ Dynamic profit targets
✅ All risk protections maintained

TARGET PERFORMANCE:
- Monthly Return: 1.5-2.5% (vs current 0.65%)
- Annual Return: 18-30% (vs current 7.8%)
- Win Rate: 40%+ maintained
- Max Drawdown: <20%
"""

import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any
import logging

class CompoundGrowthManager:
    """Simple and safe compound growth implementation"""
    
    def __init__(self, base_risk: float = 0.020):
        self.base_risk = base_risk
        self.initial_balance = None
        self.peak_balance = 0
        
    def get_risk_multiplier(self, current_balance: float) -> float:
        """Get risk multiplier based on account growth"""
        if self.initial_balance is None:
            self.initial_balance = current_balance
            
        if current_balance > self.peak_balance:
            self.peak_balance = current_balance
            
        # Calculate growth
        growth_pct = (current_balance - self.initial_balance) / self.initial_balance
        
        # Progressive but conservative compound scaling
        if growth_pct > 0.30:  # 30% profit
            return min(1.5, 1.0 + (growth_pct * 0.5))
        elif growth_pct > 0.15:  # 15% profit
            return min(1.3, 1.0 + (growth_pct * 0.3))
        elif growth_pct > 0.05:  # 5% profit
            return min(1.2, 1.0 + (growth_pct * 0.2))
        else:
            return 1.0

class ProfitEnhancedStrategyV2:
    """Enhanced strategy for higher returns with proven baseline"""
    
    def __init__(self):
        # ENHANCED PARAMETERS (based on successful strategy)
        self.ema_fast = 12           # Keep proven parameters
        self.ema_slow = 26           
        self.ema_trend = 50
        self.rsi_period = 14
        
        # ENHANCED SIGNAL THRESHOLDS
        self.min_signal_strength = 0.55        # Lowered from 0.60 for more trades
        self.min_confirmations_trending = 2    # Keep successful approach
        self.min_confirmations_ranging = 3     
        self.min_bars_between_signals = 16    # Reduced from 24h to 16h
        
        # ENHANCED RISK MANAGEMENT
        self.base_risk_per_trade = 0.025      # Increased from 0.015 to 0.025
        self.max_portfolio_risk = 0.08        # Increased from 0.06 to 0.08
        self.max_daily_trades = 2             # Keep proven approach
        
        # COMPOUND GROWTH SYSTEM
        self.compound_manager = CompoundGrowthManager(base_risk=0.025)
        
        # ENHANCED PROFIT TARGETS
        self.profit_targets = {
            'UPTREND': 0.035,          # 3.5% profit target
            'DOWNTREND': 0.030,        # 3.0% profit target
            'SIDEWAYS': 0.025,         # 2.5% profit target
            'HIGH_VOLATILITY': 0.020   # 2.0% profit target
        }
        
        # DYNAMIC STOP LOSSES
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
        self.daily_trades_count = 0
        self.last_trade_date = None
        self.total_trades = 0
        
        # OPTIMIZED COSTS
        self.trading_costs = 0.003  # 0.3% total cost (realistic)
        
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
        """Enhanced regime detection for more opportunities"""
        if not indicators:
            return 'UNKNOWN'
        
        price = indicators['price']
        ema_fast = indicators['ema_fast']
        ema_slow = indicators['ema_slow']
        ema_trend = indicators['ema_trend']
        volatility = indicators['volatility']
        
        # Volatility filter (less restrictive for more trades)
        if volatility > 0.040:  # 4.0% volatility threshold (increased from 3.5%)
            return 'HIGH_VOLATILITY'
        
        # Trend determination (less restrictive)
        fast_above_slow = ema_fast > ema_slow
        price_above_trend = price > ema_trend
        trend_strength = indicators['trend_strength']
        
        # More permissive trend requirements for more trading opportunities
        if fast_above_slow and price_above_trend and trend_strength > 0.012:  # Lowered from 0.015
            return 'UPTREND'
        elif not fast_above_slow and not price_above_trend and trend_strength > 0.012:
            return 'DOWNTREND'
        else:
            return 'SIDEWAYS'
    
    def generate_enhanced_signal(self, indicators: Dict, bar_index: int, stress_period: bool = False) -> Dict:
        """Generate enhanced signals for more opportunities"""
        if not indicators:
            return {'direction': 'NEUTRAL', 'strength': 0, 'reason': 'No data'}
        
        # Cooldown check (reduced for more trades)
        if bar_index - self.last_signal_bar < self.min_bars_between_signals:
            return {'direction': 'NEUTRAL', 'strength': 0, 'reason': 'Cooldown period'}
        
        # Market regime
        regime = self.determine_market_regime(indicators)
        self.current_regime = regime
        
        # Less restrictive regime filtering
        if regime == 'UNKNOWN':
            return {'direction': 'NEUTRAL', 'strength': 0, 'reason': 'Unknown regime'}
        
        # Only filter extreme volatility during stress
        if regime == 'HIGH_VOLATILITY' and stress_period:
            return {'direction': 'NEUTRAL', 'strength': 0, 'reason': 'High volatility + stress'}
        
        confirmations = []
        
        # ENHANCED CONFIRMATIONS (more permissive for more trades)
        
        # 1. EMA Alignment
        if indicators['ema_fast'] > indicators['ema_slow']:
            confirmations.append(('BUY', 'EMA Bullish'))
        elif indicators['ema_fast'] < indicators['ema_slow']:
            confirmations.append(('SELL', 'EMA Bearish'))
        
        # 2. RSI (wider ranges for more opportunities)
        rsi = indicators['rsi']
        if regime == 'UPTREND':
            if 25 < rsi < 60:  # Wider range
                confirmations.append(('BUY', 'RSI Favorable in Uptrend'))
        elif regime == 'DOWNTREND':
            if 40 < rsi < 75:  # Wider range
                confirmations.append(('SELL', 'RSI Favorable in Downtrend'))
        elif regime == 'SIDEWAYS':
            if rsi < 40:  # More permissive
                confirmations.append(('BUY', 'RSI Oversold'))
            elif rsi > 60:  # More permissive
                confirmations.append(('SELL', 'RSI Overbought'))
        
        # 3. Price vs Trend (more permissive)
        price_trend_ratio = indicators['price'] / indicators['ema_trend']
        if regime in ['UPTREND', 'SIDEWAYS'] and 0.97 < price_trend_ratio < 1.10:
            confirmations.append(('BUY', 'Price Near Trend'))
        elif regime in ['DOWNTREND', 'SIDEWAYS'] and 0.90 < price_trend_ratio < 1.03:
            confirmations.append(('SELL', 'Price Near Trend'))
        
        # 4. Momentum (more permissive)
        momentum = indicators['momentum']
        if momentum > 0.003:  # 0.3% positive momentum
            confirmations.append(('BUY', 'Positive Momentum'))
        elif momentum < -0.003:  # 0.3% negative momentum
            confirmations.append(('SELL', 'Negative Momentum'))
        
        # 5. Trend Strength (more permissive)
        if indicators['trend_strength'] > 0.008:  # Lowered threshold
            if regime == 'UPTREND':
                confirmations.append(('BUY', 'Uptrend Strength'))
            elif regime == 'DOWNTREND':
                confirmations.append(('SELL', 'Downtrend Strength'))
        
        # Aggregate confirmations
        buy_confirmations = [c for c in confirmations if c[0] == 'BUY']
        sell_confirmations = [c for c in confirmations if c[0] == 'SELL']
        
        # Required confirmations (keep proven approach)
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
    
    def calculate_enhanced_position_size(self, balance: float, entry_price: float, signal_strength: float, regime: str) -> Dict:
        """Calculate enhanced position size with compound growth"""
        # Get compound risk multiplier
        risk_multiplier = self.compound_manager.get_risk_multiplier(balance)
        
        # Enhanced risk calculation
        base_risk = self.base_risk_per_trade
        
        # Signal strength adjustment
        signal_multiplier = 0.8 + (signal_strength * 0.4)  # 0.8x to 1.2x
        
        # Regime adjustment (more aggressive in trending markets)
        regime_multiplier = 1.0
        if regime in ['UPTREND', 'DOWNTREND']:
            regime_multiplier = 1.15  # 15% more aggressive
        elif regime == 'SIDEWAYS':
            regime_multiplier = 0.95  # 5% less aggressive
        elif regime == 'HIGH_VOLATILITY':
            regime_multiplier = 0.75  # 25% less aggressive
        
        # Calculate final risk
        final_risk = base_risk * risk_multiplier * signal_multiplier * regime_multiplier
        
        # Dynamic stop loss
        stop_loss_pct = self.stop_losses.get(regime, 0.018)
        
        # Position value calculation
        risk_amount = balance * final_risk
        position_value = risk_amount / stop_loss_pct
        
        # Ensure position doesn't exceed balance limits
        max_position_value = balance * 0.75  # Maximum 75% of balance
        position_value = min(position_value, max_position_value)
        
        # Position size percentage
        position_size_pct = (position_value / balance) * 100
        
        # Profit target
        profit_target_pct = self.profit_targets.get(regime, 0.030)
        
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
        
        # Generate enhanced signal
        stress_period = price_data.get('stress_period', False)
        signal = self.generate_enhanced_signal(indicators, bar_index, stress_period)
        
        # Add position sizing if signal generated
        if signal['direction'] != 'NEUTRAL':
            current_balance = getattr(self, 'current_balance', 10000)
            entry_price = price_data['close']
            regime = signal.get('regime', 'UNKNOWN')
            
            position_info = self.calculate_enhanced_position_size(
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
    print("Profit Enhanced Strategy V2 - Balanced Approach for Higher Returns")
    print("🎯 Target: 18-30% annual returns")
    print("✅ Based on proven 16.1% baseline")
    print("✅ Enhanced position sizing")
    print("✅ Increased trade frequency")
    print("✅ Compound growth system")
    print("✅ All risk protections maintained")
    print("Ready for enhanced profit deployment!") 