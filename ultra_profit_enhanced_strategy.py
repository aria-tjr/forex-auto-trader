#!/usr/bin/env python3
"""
Ultra Profit Enhanced Strategy - Maximum Monthly & Annual Returns
Combines proven successful elements with advanced profit optimization techniques

TARGET PERFORMANCE:
- Monthly Return: 2.0-3.0% (vs current 0.65%)
- Annual Return: 24-36% (vs current 7.8%)
- Maintain 40%+ win rate and controlled risk

ENHANCEMENTS:
✅ Compound position sizing with account growth
✅ Regime-optimized position multipliers
✅ Dynamic profit targeting based on market conditions  
✅ Enhanced signal quality with profit-focused filtering
✅ Optimized trade frequency for maximum opportunities
✅ Advanced risk management with profit protection
"""

import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any
import logging

class CompoundPositionManager:
    """Advanced position sizing with compound growth"""
    
    def __init__(self, base_risk: float = 0.020):
        self.base_risk = base_risk
        self.initial_balance = None
        self.peak_balance = 0
        self.compound_multiplier = 1.0
        self.max_compound_multiplier = 2.0
        
    def update_compound_multiplier(self, current_balance: float):
        """Update compound multiplier based on account growth"""
        if self.initial_balance is None:
            self.initial_balance = current_balance
            
        if current_balance > self.peak_balance:
            self.peak_balance = current_balance
            
        # Calculate growth percentage
        growth_pct = (current_balance - self.initial_balance) / self.initial_balance
        
        # Progressive compound scaling
        if growth_pct > 0.50:  # 50% profit
            self.compound_multiplier = min(2.0, 1.0 + (growth_pct * 0.8))
        elif growth_pct > 0.25:  # 25% profit  
            self.compound_multiplier = min(1.6, 1.0 + (growth_pct * 0.6))
        elif growth_pct > 0.10:  # 10% profit
            self.compound_multiplier = min(1.3, 1.0 + (growth_pct * 0.4))
        else:
            self.compound_multiplier = 1.0
            
        # Reset multiplier if major drawdown
        current_drawdown = (self.peak_balance - current_balance) / self.peak_balance
        if current_drawdown > 0.15:  # 15% drawdown resets compound
            self.compound_multiplier = 1.0
            
    def get_enhanced_risk(self, signal_strength: float, regime: str) -> float:
        """Get compound and regime adjusted risk"""
        # Regime multipliers for higher profits
        regime_multipliers = {
            'STRONG_UPTREND': 1.4,    # 40% more aggressive
            'UPTREND': 1.2,           # 20% more aggressive  
            'STRONG_DOWNTREND': 1.3,  # 30% more aggressive
            'DOWNTREND': 1.1,         # 10% more aggressive
            'SIDEWAYS': 0.9,          # 10% less aggressive
            'HIGH_VOLATILITY': 0.6    # 40% less aggressive
        }
        
        regime_mult = regime_multipliers.get(regime, 1.0)
        signal_mult = 0.7 + (signal_strength * 0.6)  # 0.7x to 1.3x based on signal quality
        
        return self.base_risk * self.compound_multiplier * regime_mult * signal_mult

class AdvancedDrawdownManager:
    """Enhanced drawdown protection with profit preservation"""
    
    def __init__(self, max_drawdown: float = 0.18):
        self.max_drawdown = max_drawdown
        self.peak_equity = 0
        self.profit_protection_level = 0.10  # Protect 10% of profits
        self.trading_halted = False
        
    def update_and_check(self, current_equity: float) -> Dict:
        """Enhanced drawdown tracking with profit protection"""
        if current_equity > self.peak_equity:
            self.peak_equity = current_equity
            
        current_drawdown = (self.peak_equity - current_equity) / self.peak_equity if self.peak_equity > 0 else 0
        
        # Calculate profit level for protection
        initial_balance = 10000  # Assumed initial
        current_profit = (current_equity - initial_balance) / initial_balance
        profit_protection_trigger = current_profit > 0.15  # Protect after 15% profit
        
        # More aggressive halt conditions for profit protection
        should_halt = False
        if current_drawdown > self.max_drawdown:
            should_halt = True
        elif profit_protection_trigger and current_drawdown > 0.12:  # Protect profits at 12% drawdown
            should_halt = True
            
        if should_halt and not self.trading_halted:
            self.trading_halted = True
            
        return {
            'current_drawdown': current_drawdown,
            'halt_trading': self.trading_halted,
            'profit_protection_active': profit_protection_trigger,
            'risk_multiplier': max(0.4, 1 - (current_drawdown / self.max_drawdown))
        }

class UltraProfitEnhancedStrategy:
    """Ultra profit-focused strategy for maximum returns"""
    
    def __init__(self):
        # CORE PARAMETERS - Optimized for profit
        self.ema_fast = 8           # Faster for more signals
        self.ema_slow = 21          # Optimized ratio
        self.ema_trend = 50
        self.rsi_period = 14
        
        # AGGRESSIVE SIGNAL THRESHOLDS FOR MORE TRADES
        self.min_signal_strength = 0.55        # Lowered for more opportunities
        self.min_confirmations_trending = 2    # Fewer confirmations needed
        self.min_confirmations_ranging = 2     # Even ranging markets get 2
        self.min_bars_between_signals = 12    # 12-hour cooldown for more trades
        
        # ENHANCED RISK MANAGEMENT
        self.base_risk_per_trade = 0.025      # Increased base risk for higher returns
        self.max_portfolio_risk = 0.08        # Higher total exposure
        self.max_daily_trades = 3             # Allow more trades per day
        
        # PROFIT OPTIMIZATION FEATURES
        self.position_manager = CompoundPositionManager(base_risk=0.025)
        self.drawdown_manager = AdvancedDrawdownManager(max_drawdown=0.18)
        
        # DYNAMIC PROFIT TARGETS
        self.profit_targets = {
            'STRONG_UPTREND': 0.045,   # 4.5% profit target
            'UPTREND': 0.035,          # 3.5% profit target
            'STRONG_DOWNTREND': 0.040, # 4.0% profit target  
            'DOWNTREND': 0.030,        # 3.0% profit target
            'SIDEWAYS': 0.025,         # 2.5% profit target
            'HIGH_VOLATILITY': 0.020   # 2.0% profit target
        }
        
        # DYNAMIC STOP LOSSES
        self.stop_losses = {
            'STRONG_UPTREND': 0.022,   # 2.2% stop loss
            'UPTREND': 0.020,          # 2.0% stop loss
            'STRONG_DOWNTREND': 0.022, # 2.2% stop loss
            'DOWNTREND': 0.020,        # 2.0% stop loss  
            'SIDEWAYS': 0.018,         # 1.8% stop loss
            'HIGH_VOLATILITY': 0.015   # 1.5% stop loss
        }
        
        # STATE TRACKING
        self.price_history = []
        self.last_signal_bar = -999
        self.current_regime = 'UNKNOWN'
        self.daily_trades_count = 0
        self.last_trade_date = None
        self.total_trades = 0
        self.consecutive_losses = 0
        self.max_consecutive_losses = 4  # Allow more consecutive losses
        
        # ENHANCED COSTS - Optimistic but realistic
        self.trading_costs = 0.002  # 0.2% total cost
        
    def calculate_enhanced_indicators(self, data: pd.DataFrame) -> Dict:
        """Enhanced indicators for profit optimization"""
        if len(data) < 50:
            return {}
        
        close = data['close'].values
        high = data['high'].values
        low = data['low'].values
        volume = data.get('volume', pd.Series([1]*len(data))).values
        
        # Enhanced EMAs
        ema_fast = self._ema(close, self.ema_fast)
        ema_slow = self._ema(close, self.ema_slow)
        ema_trend = self._ema(close, self.ema_trend)
        
        # RSI
        rsi = self._rsi(close, self.rsi_period)
        
        # Enhanced volatility calculation
        returns = np.diff(close) / close[:-1]
        volatility = np.std(returns[-20:]) if len(returns) >= 20 else 0
        
        # Trend strength with momentum
        trend_strength = abs(ema_fast[-1] - ema_slow[-1]) / ema_slow[-1]
        momentum_3 = (close[-1] - close[-4]) / close[-4] if len(close) >= 4 else 0
        momentum_5 = (close[-1] - close[-6]) / close[-6] if len(close) >= 6 else 0
        
        # Price position relative to range
        price_range_position = (close[-1] - min(low[-20:])) / (max(high[-20:]) - min(low[-20:])) if len(high) >= 20 else 0.5
        
        # Volume trend (if available)
        volume_trend = np.mean(volume[-5:]) / np.mean(volume[-20:]) if len(volume) >= 20 else 1.0
        
        return {
            'ema_fast': ema_fast[-1],
            'ema_slow': ema_slow[-1], 
            'ema_trend': ema_trend[-1],
            'rsi': rsi[-1],
            'price': close[-1],
            'volatility': volatility,
            'trend_strength': trend_strength,
            'momentum_3': momentum_3,
            'momentum_5': momentum_5,
            'price_range_position': price_range_position,
            'volume_trend': volume_trend
        }
    
    def determine_enhanced_regime(self, indicators: Dict) -> str:
        """Enhanced regime detection for profit optimization"""
        if not indicators:
            return 'UNKNOWN'
        
        price = indicators['price']
        ema_fast = indicators['ema_fast']
        ema_slow = indicators['ema_slow']
        ema_trend = indicators['ema_trend']
        volatility = indicators['volatility']
        trend_strength = indicators['trend_strength']
        momentum_3 = indicators['momentum_3']
        
        # Volatility filter
        if volatility > 0.045:  # 4.5% volatility threshold
            return 'HIGH_VOLATILITY'
        
        # Enhanced trend classification
        fast_above_slow = ema_fast > ema_slow
        price_above_trend = price > ema_trend
        strong_trend = trend_strength > 0.025
        very_strong_trend = trend_strength > 0.040
        positive_momentum = momentum_3 > 0.008
        negative_momentum = momentum_3 < -0.008
        
        # Strong uptrend identification
        if (fast_above_slow and price_above_trend and very_strong_trend and positive_momentum):
            return 'STRONG_UPTREND'
        elif (fast_above_slow and price_above_trend and strong_trend):
            return 'UPTREND'
        # Strong downtrend identification  
        elif (not fast_above_slow and not price_above_trend and very_strong_trend and negative_momentum):
            return 'STRONG_DOWNTREND'
        elif (not fast_above_slow and not price_above_trend and strong_trend):
            return 'DOWNTREND'
        else:
            return 'SIDEWAYS'
    
    def generate_profit_optimized_signal(self, indicators: Dict, bar_index: int, stress_period: bool = False) -> Dict:
        """Generate signals optimized for maximum profit"""
        if not indicators:
            return {'direction': 'NEUTRAL', 'strength': 0, 'reason': 'No data'}
        
        # Cooldown check (reduced for more trades)
        if bar_index - self.last_signal_bar < self.min_bars_between_signals:
            return {'direction': 'NEUTRAL', 'strength': 0, 'reason': 'Cooldown period'}
        
        # Enhanced regime detection
        regime = self.determine_enhanced_regime(indicators)
        self.current_regime = regime
        
        # Filter extreme conditions only
        if regime == 'HIGH_VOLATILITY' and stress_period:
            return {'direction': 'NEUTRAL', 'strength': 0, 'reason': 'Extreme volatility + stress'}
        
        # Check drawdown protection
        current_balance = getattr(self, 'current_balance', 10000)
        drawdown_status = self.drawdown_manager.update_and_check(current_balance)
        if drawdown_status['halt_trading']:
            return {'direction': 'NEUTRAL', 'strength': 0, 'reason': 'Drawdown protection'}
        
        # Check consecutive losses (more lenient)
        if self.consecutive_losses >= self.max_consecutive_losses:
            return {'direction': 'NEUTRAL', 'strength': 0, 'reason': f'Max consecutive losses: {self.consecutive_losses}'}
        
        confirmations = []
        
        # ENHANCED CONFIRMATIONS FOR PROFIT
        
        # 1. EMA Alignment (more aggressive)
        if indicators['ema_fast'] > indicators['ema_slow'] * 1.001:  # 0.1% threshold
            confirmations.append(('BUY', 'Strong EMA Bullish'))
        elif indicators['ema_fast'] < indicators['ema_slow'] * 0.999:  # 0.1% threshold  
            confirmations.append(('SELL', 'Strong EMA Bearish'))
        
        # 2. Enhanced RSI (wider profitable ranges)
        rsi = indicators['rsi']
        if regime in ['STRONG_UPTREND', 'UPTREND']:
            if 20 < rsi < 65:  # Very wide range for uptrends
                confirmations.append(('BUY', f'RSI Favorable in {regime}'))
        elif regime in ['STRONG_DOWNTREND', 'DOWNTREND']:
            if 35 < rsi < 80:  # Very wide range for downtrends
                confirmations.append(('SELL', f'RSI Favorable in {regime}'))
        elif regime == 'SIDEWAYS':
            if rsi < 40:  # More aggressive oversold
                confirmations.append(('BUY', 'RSI Oversold'))
            elif rsi > 60:  # More aggressive overbought
                confirmations.append(('SELL', 'RSI Overbought'))
        
        # 3. Momentum Confirmation (multiple timeframes)
        momentum_3 = indicators['momentum_3']
        momentum_5 = indicators['momentum_5']
        
        if momentum_3 > 0.003 and momentum_5 > 0.005:  # Strong bullish momentum
            confirmations.append(('BUY', 'Strong Bullish Momentum'))
        elif momentum_3 < -0.003 and momentum_5 < -0.005:  # Strong bearish momentum
            confirmations.append(('SELL', 'Strong Bearish Momentum'))
        elif momentum_3 > 0.001:  # Mild bullish momentum
            confirmations.append(('BUY', 'Bullish Momentum'))
        elif momentum_3 < -0.001:  # Mild bearish momentum
            confirmations.append(('SELL', 'Bearish Momentum'))
        
        # 4. Price Position in Range
        range_pos = indicators['price_range_position']
        if regime in ['STRONG_UPTREND', 'UPTREND'] and 0.2 < range_pos < 0.9:
            confirmations.append(('BUY', 'Good Price Position for Uptrend'))
        elif regime in ['STRONG_DOWNTREND', 'DOWNTREND'] and 0.1 < range_pos < 0.8:
            confirmations.append(('SELL', 'Good Price Position for Downtrend'))
        elif regime == 'SIDEWAYS':
            if range_pos < 0.3:
                confirmations.append(('BUY', 'Near Range Bottom'))
            elif range_pos > 0.7:
                confirmations.append(('SELL', 'Near Range Top'))
        
        # 5. Trend Strength Confirmation
        trend_strength = indicators['trend_strength']
        if trend_strength > 0.015:  # Any meaningful trend
            if regime in ['STRONG_UPTREND', 'UPTREND']:
                confirmations.append(('BUY', f'Strong {regime}'))
            elif regime in ['STRONG_DOWNTREND', 'DOWNTREND']:
                confirmations.append(('SELL', f'Strong {regime}'))
        
        # 6. Volume Confirmation (if available)
        volume_trend = indicators.get('volume_trend', 1.0)
        if volume_trend > 1.2:  # 20% above average volume
            if regime in ['STRONG_UPTREND', 'UPTREND']:
                confirmations.append(('BUY', 'High Volume Uptrend'))
            elif regime in ['STRONG_DOWNTREND', 'DOWNTREND']:
                confirmations.append(('SELL', 'High Volume Downtrend'))
        
        # Aggregate confirmations
        buy_confirmations = [c for c in confirmations if c[0] == 'BUY']
        sell_confirmations = [c for c in confirmations if c[0] == 'SELL']
        
        # Dynamic confirmation requirements based on regime
        if regime in ['STRONG_UPTREND', 'STRONG_DOWNTREND']:
            required_confirmations = 2  # Strong trends need fewer confirmations
        else:
            required_confirmations = self.min_confirmations_ranging
        
        # Generate signals
        if len(buy_confirmations) >= required_confirmations:
            signal_strength = min(len(buy_confirmations) / 6.0, 1.0)  # Up to 6 confirmations
            if signal_strength >= self.min_signal_strength:
                return {
                    'direction': 'BUY',
                    'strength': signal_strength,
                    'confirmations': buy_confirmations,
                    'regime': regime,
                    'reason': f'{len(buy_confirmations)} bullish confirmations in {regime}'
                }
        elif len(sell_confirmations) >= required_confirmations:
            signal_strength = min(len(sell_confirmations) / 6.0, 1.0)
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
        # Update compound multiplier
        self.position_manager.update_compound_multiplier(balance)
        
        # Get enhanced risk based on regime and signal strength
        enhanced_risk = self.position_manager.get_enhanced_risk(signal_strength, regime)
        
        # Dynamic stop loss based on regime
        stop_loss_pct = self.stop_losses.get(regime, 0.020)
        
        # Calculate position size correctly
        risk_amount = balance * enhanced_risk  # Dollar amount to risk
        
        # Position size should be in dollar terms, not units
        # The position size represents the dollar value of the position
        position_value = risk_amount / stop_loss_pct  # Dollar value of position
        
        # Ensure position doesn't exceed balance (with margin for costs)
        max_position_value = balance * 0.8  # Maximum 80% of balance
        position_value = min(position_value, max_position_value)
        
        # Position size percentage of balance
        position_size_pct = (position_value / balance) * 100
        
        # Profit target based on regime
        profit_target_pct = self.profit_targets.get(regime, 0.030)
        
        return {
            'position_size': position_value,  # Dollar value of position
            'position_size_pct': position_size_pct,
            'risk_amount': risk_amount,
            'risk_pct': enhanced_risk * 100,
            'stop_loss_pct': stop_loss_pct * 100,
            'profit_target_pct': profit_target_pct * 100,
            'compound_multiplier': self.position_manager.compound_multiplier,
            'regime': regime
        }
    
    def add_price_data(self, price_data: Dict, bar_index: int) -> Dict:
        """Main strategy entry point"""
        self.price_history.append(price_data)
        
        # Keep last 200 bars for indicators
        if len(self.price_history) > 200:
            self.price_history = self.price_history[-200:]
        
        # Need sufficient data
        if len(self.price_history) < 50:
            return {'direction': 'NEUTRAL', 'strength': 0, 'reason': 'Insufficient data'}
        
        # Convert to DataFrame
        df = pd.DataFrame(self.price_history)
        
        # Calculate enhanced indicators
        indicators = self.calculate_enhanced_indicators(df)
        
        # Generate profit-optimized signal
        stress_period = price_data.get('stress_period', False)
        signal = self.generate_profit_optimized_signal(indicators, bar_index, stress_period)
        
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
    
    def update_trade_outcome(self, profit_loss: float):
        """Update strategy state after trade"""
        if profit_loss < 0:
            self.consecutive_losses += 1
        else:
            self.consecutive_losses = 0
    
    def get_strategy_status(self) -> Dict:
        """Get current strategy status"""
        return {
            'current_regime': self.current_regime,
            'total_trades': self.total_trades,
            'consecutive_losses': self.consecutive_losses,
            'compound_multiplier': self.position_manager.compound_multiplier,
            'last_signal_bar': self.last_signal_bar
        }
    
    def _ema(self, prices: np.ndarray, period: int) -> np.ndarray:
        """Calculate EMA"""
        alpha = 2.0 / (period + 1)
        ema = np.zeros_like(prices)
        ema[0] = prices[0]
        
        for i in range(1, len(prices)):
            ema[i] = alpha * prices[i] + (1 - alpha) * ema[i-1]
        
        return ema
    
    def _rsi(self, prices: np.ndarray, period: int) -> np.ndarray:
        """Calculate RSI"""
        if len(prices) < period + 1:
            return np.array([50.0] * len(prices))
        
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gains = np.zeros_like(prices)
        avg_losses = np.zeros_like(prices)
        
        avg_gains[period] = np.mean(gains[:period])
        avg_losses[period] = np.mean(losses[:period])
        
        for i in range(period + 1, len(prices)):
            avg_gains[i] = (avg_gains[i-1] * (period - 1) + gains[i-1]) / period
            avg_losses[i] = (avg_losses[i-1] * (period - 1) + losses[i-1]) / period
        
        rs = avg_gains / (avg_losses + 1e-8)
        rsi = 100 - (100 / (1 + rs))
        
        return rsi

if __name__ == "__main__":
    print("Ultra Profit Enhanced Strategy - Maximum Return Optimization")
    print("🎯 Target: 24-36% annual returns")
    print("✅ Compound position sizing")
    print("✅ Regime-optimized parameters")
    print("✅ Dynamic profit targeting")
    print("✅ Enhanced signal quality")
    print("Ready for maximum profit deployment!")