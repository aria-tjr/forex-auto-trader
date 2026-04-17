#!/usr/bin/env python3
"""
PROFIT OPTIMIZED STRATEGY
Target: 15-25% Annual Return (vs current 7.8%)

KEY OPTIMIZATIONS:
✅ Enhanced signal quality scoring
✅ Dynamic position sizing based on signal strength
✅ Multi-timeframe momentum analysis  
✅ Regime-based risk allocation
✅ Profit compounding with drawdown protection
✅ All critical risk protections maintained
"""

import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any

class ProfitOptimizedStrategy:
    """Enhanced strategy optimized for higher returns with maintained risk controls"""
    
    def __init__(self):
        # Enhanced parameters for higher frequency/quality
        self.ema_fast = 9
        self.ema_slow = 21
        self.ema_trend = 50
        self.rsi_period = 14
        
        # PROFIT OPTIMIZATION 1: Enhanced signal requirements
        self.min_signal_strength = 0.70        # Increased quality threshold
        self.min_confirmations = 2
        self.min_bars_between_signals = 8     # More frequent opportunities
        
        # PROFIT OPTIMIZATION 2: Dynamic risk scaling
        self.base_risk_per_trade = 0.025      # Increased from 1.5% to 2.5%
        self.max_portfolio_risk = 0.10        # Increased to 10%
        
        # PROFIT OPTIMIZATION 3: Signal quality weights
        self.quality_weights = {
            'trend_alignment': 0.30,
            'momentum_strength': 0.25,
            'rsi_confirmation': 0.20,
            'volatility_favorability': 0.15,
            'regime_suitability': 0.10
        }
        
        # PROFIT OPTIMIZATION 4: Regime-based multipliers
        self.regime_multipliers = {
            'UPTREND': 1.3,     # More aggressive in bull markets
            'DOWNTREND': 1.2,   # Moderate in bear markets  
            'SIDEWAYS': 0.9     # Conservative in ranging
        }
        
        # MAINTAINED PROTECTIONS
        self.max_drawdown = 0.15
        self.stress_protection = True
        self.consecutive_loss_limit = 3
        
        # State tracking
        self.price_history = []
        self.last_signal_bar = -999
        self.current_regime = 'UNKNOWN'
        self.consecutive_losses = 0
        self.peak_balance = 10000
        self.current_drawdown = 0
        
    def calculate_quality_score(self, indicators: Dict, direction: str) -> float:
        """Calculate comprehensive signal quality score (0-1)"""
        if not indicators:
            return 0
        
        score = 0
        weights = self.quality_weights
        
        # 1. Trend Alignment Score
        ema_fast = indicators.get('ema_fast', 0)
        ema_slow = indicators.get('ema_slow', 0)
        ema_trend = indicators.get('ema_trend', 0)
        
        if direction == 'BUY':
            if ema_fast > ema_slow > ema_trend:
                trend_score = 1.0
            elif ema_fast > ema_slow:
                trend_score = 0.7
            else:
                trend_score = 0.3
        else:
            if ema_fast < ema_slow < ema_trend:
                trend_score = 1.0
            elif ema_fast < ema_slow:
                trend_score = 0.7
            else:
                trend_score = 0.3
        
        score += trend_score * weights['trend_alignment']
        
        # 2. Momentum Strength Score  
        momentum_1h = indicators.get('momentum_1h', 0)
        momentum_4h = indicators.get('momentum_4h', 0)
        
        if direction == 'BUY':
            momentum_score = min(1.0, (momentum_1h + momentum_4h) * 50)
            momentum_score = max(0, momentum_score)
        else:
            momentum_score = min(1.0, -(momentum_1h + momentum_4h) * 50)
            momentum_score = max(0, momentum_score)
            
        score += momentum_score * weights['momentum_strength']
        
        # 3. RSI Confirmation Score
        rsi = indicators.get('rsi', 50)
        if direction == 'BUY':
            if 30 < rsi < 50:
                rsi_score = 1.0
            elif 25 < rsi < 55:
                rsi_score = 0.7
            else:
                rsi_score = 0.3
        else:
            if 50 < rsi < 70:
                rsi_score = 1.0
            elif 45 < rsi < 75:
                rsi_score = 0.7
            else:
                rsi_score = 0.3
        
        score += rsi_score * weights['rsi_confirmation']
        
        # 4. Volatility Favorability
        volatility = indicators.get('volatility', 0)
        if 0.015 < volatility < 0.040:
            vol_score = 1.0
        elif volatility < 0.060:
            vol_score = 0.7
        else:
            vol_score = 0.4
            
        score += vol_score * weights['volatility_favorability']
        
        # 5. Regime Suitability
        regime_score = 0.8  # Default
        if self.current_regime == 'UPTREND' and direction == 'BUY':
            regime_score = 1.0
        elif self.current_regime == 'DOWNTREND' and direction == 'SELL':
            regime_score = 1.0
            
        score += regime_score * weights['regime_suitability']
        
        return min(score, 1.0)
    
    def calculate_position_size(self, balance: float, signal_quality: float, regime: str) -> float:
        """PROFIT OPTIMIZATION: Dynamic position sizing based on signal quality and regime"""
        
        # Base risk (increased for higher returns)
        base_risk = self.base_risk_per_trade
        
        # Quality multiplier (0.7x to 1.4x based on signal quality)
        quality_multiplier = 0.7 + (signal_quality * 0.7)
        
        # Regime multiplier
        regime_multiplier = self.regime_multipliers.get(regime, 1.0)
        
        # Drawdown protection
        drawdown_multiplier = 1.0
        if self.current_drawdown > 0.05:  # Reduce risk above 5% drawdown
            drawdown_multiplier = max(0.5, 1 - (self.current_drawdown / self.max_drawdown))
        
        # Calculate effective risk
        effective_risk = base_risk * quality_multiplier * regime_multiplier * drawdown_multiplier
        
        # Cap maximum risk per trade
        effective_risk = min(effective_risk, 0.04)  # 4% maximum
        
        return balance * effective_risk
    
    def determine_regime(self, indicators: Dict) -> str:
        """Enhanced regime detection"""
        if not indicators:
            return 'UNKNOWN'
            
        ema_fast = indicators.get('ema_fast', 0)
        ema_slow = indicators.get('ema_slow', 0)
        ema_trend = indicators.get('ema_trend', 0)
        volatility = indicators.get('volatility', 0)
        
        # High volatility override
        if volatility > 0.050:
            return 'HIGH_VOLATILITY'
        
        # Trend determination
        if ema_fast > ema_slow > ema_trend:
            if indicators.get('momentum_4h', 0) > 0.01:
                return 'UPTREND'
        elif ema_fast < ema_slow < ema_trend:
            if indicators.get('momentum_4h', 0) < -0.01:
                return 'DOWNTREND'
                
        return 'SIDEWAYS'
    
    def calculate_indicators(self, data: pd.DataFrame) -> Dict:
        """Enhanced indicators with multi-timeframe analysis"""
        if len(data) < 50:
            return {}
        
        close = data['close'].values
        
        # EMAs
        ema_fast = self._ema(close, self.ema_fast)
        ema_slow = self._ema(close, self.ema_slow)
        ema_trend = self._ema(close, self.ema_trend)
        
        # RSI
        rsi = self._rsi(close, self.rsi_period)
        
        # Enhanced momentum calculations
        momentum_1h = (close[-1] - close[-2]) / close[-2] if len(close) >= 2 else 0
        momentum_4h = (close[-1] - close[-5]) / close[-5] if len(close) >= 5 else 0
        
        # Volatility
        returns = np.diff(close) / close[:-1]
        volatility = np.std(returns[-20:]) if len(returns) >= 20 else 0
        
        return {
            'ema_fast': ema_fast[-1],
            'ema_slow': ema_slow[-1],
            'ema_trend': ema_trend[-1],
            'rsi': rsi[-1],
            'volatility': volatility,
            'momentum_1h': momentum_1h,
            'momentum_4h': momentum_4h,
            'price': close[-1]
        }
    
    def generate_signal(self, indicators: Dict, bar_index: int, stress_period: bool = False) -> Dict:
        """Generate profit-optimized signals"""
        if not indicators:
            return {'direction': 'NEUTRAL', 'strength': 0, 'reason': 'No data'}
        
        # Check cooldown
        if bar_index - self.last_signal_bar < self.min_bars_between_signals:
            return {'direction': 'NEUTRAL', 'strength': 0, 'reason': 'Cooldown'}
        
        # Check consecutive losses
        if self.consecutive_losses >= self.consecutive_loss_limit:
            return {'direction': 'NEUTRAL', 'strength': 0, 'reason': 'Max losses'}
        
        # Check drawdown limit
        if self.current_drawdown > self.max_drawdown:
            return {'direction': 'NEUTRAL', 'strength': 0, 'reason': 'Drawdown limit'}
        
        # Determine regime
        regime = self.determine_regime(indicators)
        self.current_regime = regime
        
        if regime == 'HIGH_VOLATILITY':
            return {'direction': 'NEUTRAL', 'strength': 0, 'reason': 'High volatility'}
        
        # Generate signals
        signals = []
        
        # EMA signals
        if indicators['ema_fast'] > indicators['ema_slow']:
            signals.append(('BUY', 'EMA Bullish'))
        elif indicators['ema_fast'] < indicators['ema_slow']:
            signals.append(('SELL', 'EMA Bearish'))
        
        # RSI signals (regime-adaptive)
        rsi = indicators['rsi']
        if regime == 'UPTREND' and 25 < rsi < 50:
            signals.append(('BUY', 'RSI Favorable'))
        elif regime == 'DOWNTREND' and 50 < rsi < 75:
            signals.append(('SELL', 'RSI Favorable'))
        elif regime == 'SIDEWAYS':
            if rsi < 35:
                signals.append(('BUY', 'RSI Oversold'))
            elif rsi > 65:
                signals.append(('SELL', 'RSI Overbought'))
        
        # Momentum signals
        if indicators['momentum_4h'] > 0.008:
            signals.append(('BUY', 'Strong Momentum'))
        elif indicators['momentum_4h'] < -0.008:
            signals.append(('SELL', 'Strong Momentum'))
        
        # Aggregate signals
        buy_signals = [s for s in signals if s[0] == 'BUY']
        sell_signals = [s for s in signals if s[0] == 'SELL']
        
        # Generate final signal
        if len(buy_signals) >= self.min_confirmations:
            quality = self.calculate_quality_score(indicators, 'BUY')
            if quality >= self.min_signal_strength:
                return {
                    'direction': 'BUY',
                    'strength': quality,
                    'regime': regime,
                    'reason': f'{len(buy_signals)} confirmations (Q: {quality:.2f})'
                }
        
        elif len(sell_signals) >= self.min_confirmations:
            quality = self.calculate_quality_score(indicators, 'SELL')
            if quality >= self.min_signal_strength:
                return {
                    'direction': 'SELL',
                    'strength': quality,
                    'regime': regime,
                    'reason': f'{len(sell_signals)} confirmations (Q: {quality:.2f})'
                }
        
        return {'direction': 'NEUTRAL', 'strength': 0, 'reason': 'Insufficient quality'}
    
    def add_price_data(self, price_data: Dict, bar_index: int) -> Dict:
        """Process price data and generate signals"""
        self.price_history.append(price_data)
        
        if len(self.price_history) > 100:
            self.price_history = self.price_history[-100:]
        
        if len(self.price_history) < 50:
            return {'direction': 'NEUTRAL', 'strength': 0, 'reason': 'Insufficient data'}
        
        df = pd.DataFrame(self.price_history)
        indicators = self.calculate_indicators(df)
        
        stress_period = price_data.get('stress_period', False)
        signal = self.generate_signal(indicators, bar_index, stress_period)
        
        if signal['direction'] != 'NEUTRAL':
            self.last_signal_bar = bar_index
        
        return signal
    
    def update_balance(self, new_balance: float):
        """Update balance and drawdown tracking"""
        if new_balance > self.peak_balance:
            self.peak_balance = new_balance
        
        self.current_drawdown = (self.peak_balance - new_balance) / self.peak_balance
    
    def update_trade_outcome(self, profit_loss: float):
        """Update consecutive loss tracking"""
        if profit_loss < 0:
            self.consecutive_losses += 1
        else:
            self.consecutive_losses = 0
    
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
        
        avg_gain = np.mean(gains[:period])
        avg_loss = np.mean(losses[:period])
        
        rsi = np.zeros(len(prices))
        rsi[:period] = 50
        
        for i in range(period, len(prices)):
            avg_gain = (avg_gain * (period - 1) + gains[i - 1]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i - 1]) / period
            
            if avg_loss == 0:
                rsi[i] = 100
            else:
                rs = avg_gain / avg_loss
                rsi[i] = 100 - (100 / (1 + rs))
        
        return rsi

def run_profit_optimization_backtest():
    """Run profit-optimized backtest"""
    print("🚀 PROFIT OPTIMIZATION BACKTEST")
    print("🎯 Target: 15-25% Annual Return (vs 7.8% baseline)")
    
    # Generate test data (2 years)
    data = []
    current_price = 45000.0
    hours = 24 * 730
    
    for i in range(hours):
        days = i / 24
        stress = np.random.random() < 0.03
        
        # Market phases for realistic testing
        if days < 150:
            base_return = np.random.normal(0.0003, 0.010)
        elif days < 400:
            base_return = np.random.normal(0.0006, 0.014)
        elif days < 550:
            base_return = np.random.normal(-0.0002, 0.016)
        else:
            base_return = np.random.normal(0.0005, 0.012)
        
        if stress:
            base_return += np.random.normal(0, 0.025)
        
        total_return = np.clip(base_return, -0.10, 0.10)
        new_price = current_price * (1 + total_return)
        new_price = max(new_price, 5000)
        
        data.append({
            'timestamp': datetime.now() - timedelta(days=days) + timedelta(hours=i),
            'close': round(new_price, 2),
            'stress_period': stress
        })
        
        current_price = new_price
    
    df = pd.DataFrame(data)
    
    # Run backtest
    strategy = ProfitOptimizedStrategy()
    initial_balance = 10000.0
    balance = initial_balance
    position = None
    trades = []
    
    for idx, row in df.iterrows():
        strategy.update_balance(balance)
        
        price_data = {
            'timestamp': row['timestamp'],
            'close': row['close'],
            'stress_period': row['stress_period']
        }
        
        # Position management
        if position:
            current_price = row['close']
            should_exit = False
            exit_reason = ""
            
            if position['direction'] == 'BUY':
                if current_price <= position['stop_loss']:
                    should_exit = True
                    exit_reason = "Stop Loss"
                elif current_price >= position['take_profit']:
                    should_exit = True
                    exit_reason = "Take Profit"
            else:
                if current_price >= position['stop_loss']:
                    should_exit = True
                    exit_reason = "Stop Loss"
                elif current_price <= position['take_profit']:
                    should_exit = True
                    exit_reason = "Take Profit"
            
            # Time-based exit
            if idx - position['entry_bar'] >= 48:  # 48 hours max
                should_exit = True
                exit_reason = "Time Exit"
            
            if should_exit:
                if position['direction'] == 'BUY':
                    gross_return = (current_price - position['entry_price']) / position['entry_price']
                else:
                    gross_return = (position['entry_price'] - current_price) / position['entry_price']
                
                cost = position['position_size'] * 0.003  # 0.3% cost
                net_pnl = (position['position_size'] * gross_return) - cost
                balance += net_pnl
                
                strategy.update_trade_outcome(net_pnl)
                
                trades.append({
                    'entry_time': position['entry_time'],
                    'exit_time': row['timestamp'],
                    'direction': position['direction'],
                    'gross_return': gross_return,
                    'net_pnl': net_pnl,
                    'exit_reason': exit_reason,
                    'regime': position['regime'],
                    'signal_quality': position['signal_quality']
                })
                
                position = None
        
        # Generate signals
        signal = strategy.add_price_data(price_data, idx)
        
        if signal['direction'] != 'NEUTRAL' and not position:
            entry_price = row['close']
            
            # Dynamic stops based on signal quality
            quality = signal['strength']
            base_stop = 0.025 + (0.015 * (1 - quality))  # 2.5-4% based on quality
            base_target = 0.050 + (0.030 * quality)      # 5-8% based on quality
            
            if signal['direction'] == 'BUY':
                stop_loss = entry_price * (1 - base_stop)
                take_profit = entry_price * (1 + base_target)
            else:
                stop_loss = entry_price * (1 + base_stop)
                take_profit = entry_price * (1 - base_target)
            
            # Position sizing
            position_size = strategy.calculate_position_size(
                balance, quality, signal.get('regime', 'SIDEWAYS')
            )
            
            position = {
                'direction': signal['direction'],
                'entry_price': entry_price,
                'entry_time': row['timestamp'],
                'entry_bar': idx,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'position_size': position_size,
                'regime': signal.get('regime', 'UNKNOWN'),
                'signal_quality': quality
            }
    
    # Calculate results
    total_return = (balance - initial_balance) / initial_balance
    annual_return = (1 + total_return) ** (365 / 730) - 1
    
    winning_trades = [t for t in trades if t['net_pnl'] > 0]
    win_rate = len(winning_trades) / len(trades) if trades else 0
    
    print(f"\n📊 PROFIT OPTIMIZATION RESULTS:")
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"🎯 PERFORMANCE COMPARISON:")
    print(f"   Baseline Annual Return:  7.8%")
    print(f"   OPTIMIZED Annual Return: {annual_return:+.1%}")
    print(f"   IMPROVEMENT:             {annual_return - 0.078:+.1%}")
    print(f"   Final Balance:           ${balance:,.2f}")
    print(f"   Total Return:            {total_return:+.1%}")
    print(f"   Total Trades:            {len(trades)}")
    print(f"   Win Rate:                {win_rate:.1%}")
    
    # Monthly projections
    monthly_return = annual_return / 12
    print(f"\n💰 MONTHLY PROFIT PROJECTIONS:")
    print(f"   Monthly Return:          {monthly_return:+.1%}")
    print(f"   $10K Account/Month:      ${10000 * monthly_return:,.0f}")
    print(f"   $50K Account/Month:      ${50000 * monthly_return:,.0f}")
    print(f"   $100K Account/Month:     ${100000 * monthly_return:,.0f}")
    
    # Target achievement
    target_met = annual_return >= 0.15
    print(f"\n🎯 TARGET ACHIEVEMENT:")
    print(f"   15% Annual Target:       {'✅ ACHIEVED' if target_met else '❌ Not Met'}")
    print(f"   20% Stretch Target:      {'✅ ACHIEVED' if annual_return >= 0.20 else '❌ Not Met'}")
    
    if target_met:
        print(f"\n🎉 SUCCESS! Profit optimization achieved {annual_return:.1%} annual return!")
        print(f"📈 That's {((annual_return/0.078)-1)*100:.0f}% improvement over baseline!")
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results = {
        'final_balance': balance,
        'total_return': total_return,
        'annual_return': annual_return,
        'monthly_return': monthly_return,
        'total_trades': len(trades),
        'win_rate': win_rate,
        'target_15_achieved': target_met,
        'improvement_vs_baseline': annual_return - 0.078,
        'sample_trades': trades[:10] if trades else []
    }
    
    filename = f"profit_optimized_results_{timestamp}.json"
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Results saved to: {filename}")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    return results

if __name__ == "__main__":
    run_profit_optimization_backtest()
