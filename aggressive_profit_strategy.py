#!/usr/bin/env python3
"""
AGGRESSIVE PROFIT STRATEGY
Target: 20-30% Annual Return
"""

import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta

class AggressiveProfitStrategy:
    def __init__(self):
        # Aggressive settings for higher returns
        self.ema_fast = 8
        self.ema_slow = 18
        self.rsi_period = 12
        self.base_risk_per_trade = 0.04  # 4% risk per trade
        self.max_portfolio_risk = 0.15   # 15% total exposure
        self.min_signal_strength = 0.45  # Lower threshold for more trades
        self.min_bars_between_signals = 3 # More frequent trading
        
        # State tracking
        self.price_history = []
        self.last_signal_bar = -999
        self.consecutive_losses = 0
        self.peak_balance = 10000
        self.current_drawdown = 0
        
    def calculate_indicators(self, data):
        if len(data) < 30:
            return {}
        close = data['close'].values
        ema_fast = self._ema(close, self.ema_fast)
        ema_slow = self._ema(close, self.ema_slow)
        rsi = self._rsi(close, self.rsi_period)
        momentum = (close[-1] - close[-5]) / close[-5] if len(close) >= 5 else 0
        volatility = np.std(np.diff(close) / close[:-1]) if len(close) > 10 else 0
        
        return {
            'ema_fast': ema_fast[-1], 'ema_slow': ema_slow[-1], 'rsi': rsi[-1],
            'momentum': momentum, 'volatility': volatility, 'price': close[-1]
        }
    
    def generate_signal(self, indicators, bar_index):
        if not indicators or bar_index - self.last_signal_bar < self.min_bars_between_signals:
            return {'direction': 'NEUTRAL', 'strength': 0}
        
        if self.consecutive_losses >= 3 or self.current_drawdown > 0.18:
            return {'direction': 'NEUTRAL', 'strength': 0}
        
        signals = []
        # EMA crossover
        if indicators['ema_fast'] > indicators['ema_slow']:
            signals.append('BUY')
        elif indicators['ema_fast'] < indicators['ema_slow']:
            signals.append('SELL')
        
        # RSI signals (more aggressive)
        rsi = indicators['rsi']
        if rsi < 45:
            signals.append('BUY')
        elif rsi > 55:
            signals.append('SELL')
        
        # Momentum signals
        if indicators['momentum'] > 0.008:
            signals.append('BUY')
        elif indicators['momentum'] < -0.008:
            signals.append('SELL')
        
        # Generate final signal
        buy_count = signals.count('BUY')
        sell_count = signals.count('SELL')
        
        if buy_count >= 2:
            strength = min(0.9, 0.5 + buy_count * 0.1)
            if strength >= self.min_signal_strength:
                return {'direction': 'BUY', 'strength': strength}
        elif sell_count >= 2:
            strength = min(0.9, 0.5 + sell_count * 0.1)
            if strength >= self.min_signal_strength:
                return {'direction': 'SELL', 'strength': strength}
        
        return {'direction': 'NEUTRAL', 'strength': 0}
    
    def calculate_position_size(self, balance, signal_strength):
        base_risk = self.base_risk_per_trade
        strength_multiplier = 0.7 + (signal_strength * 0.6)  # 0.7x to 1.3x
        drawdown_multiplier = max(0.5, 1 - (self.current_drawdown / 0.18))
        effective_risk = base_risk * strength_multiplier * drawdown_multiplier
        return balance * min(effective_risk, 0.06)  # Cap at 6%
    
    def add_price_data(self, price_data, bar_index):
        self.price_history.append(price_data)
        if len(self.price_history) > 100:
            self.price_history = self.price_history[-100:]
        
        if len(self.price_history) < 30:
            return {'direction': 'NEUTRAL', 'strength': 0}
        
        df = pd.DataFrame(self.price_history)
        indicators = self.calculate_indicators(df)
        signal = self.generate_signal(indicators, bar_index)
        
        if signal['direction'] != 'NEUTRAL':
            self.last_signal_bar = bar_index
        return signal
    
    def update_balance(self, new_balance):
        if new_balance > self.peak_balance:
            self.peak_balance = new_balance
        self.current_drawdown = (self.peak_balance - new_balance) / self.peak_balance
    
    def update_trade_outcome(self, profit_loss):
        if profit_loss < 0:
            self.consecutive_losses += 1
        else:
            self.consecutive_losses = 0
    
    def _ema(self, prices, period):
        if len(prices) < period:
            return np.array([prices[-1]] if len(prices) > 0 else [])
        alpha = 2.0 / (period + 1)
        ema = np.zeros_like(prices, dtype=float)
        ema[0] = prices[0]
        for i in range(1, len(prices)):
            ema[i] = alpha * prices[i] + (1 - alpha) * ema[i-1]
        return ema
    
    def _rsi(self, prices, period):
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

def run_aggressive_backtest():
    print("🚀 AGGRESSIVE PROFIT STRATEGY")
    print("🎯 Target: 20-30% Annual Return")
    
    # Generate test data
    data = []
    current_price = 45000.0
    hours = 24 * 365  # 1 year
    
    for i in range(hours):
        days = i / 24
        # More volatile phases for better opportunities
        if days < 90:
            base_return = np.random.normal(0.001, 0.018)
        elif days < 180:
            base_return = np.random.normal(-0.0003, 0.022)
        elif days < 270:
            base_return = np.random.normal(0.0008, 0.015)
        else:
            base_return = np.random.normal(0.0012, 0.020)
        
        # Add cycles
        cycle_return = np.sin(days / 30) * 0.0015
        momentum = np.sin(days / 60) * 0.0008
        total_return = np.clip(base_return + cycle_return + momentum, -0.15, 0.15)
        
        new_price = current_price * (1 + total_return)
        new_price = max(new_price, 5000)
        
        data.append({
            'timestamp': datetime.now() - timedelta(days=days) + timedelta(hours=i),
            'close': round(new_price, 2)
        })
        current_price = new_price
    
    df = pd.DataFrame(data)
    
    # Run backtest
    strategy = AggressiveProfitStrategy()
    initial_balance = 10000.0
    balance = initial_balance
    position = None
    trades = []
    
    for idx, row in df.iterrows():
        strategy.update_balance(balance)
        price_data = {'timestamp': row['timestamp'], 'close': row['close']}
        
        # Position management
        if position:
            current_price = row['close']
            should_exit = False
            exit_reason = ""
            
            if position['direction'] == 'BUY':
                if current_price <= position['stop_loss']:
                    should_exit, exit_reason = True, "Stop Loss"
                elif current_price >= position['take_profit']:
                    should_exit, exit_reason = True, "Take Profit"
            else:
                if current_price >= position['stop_loss']:
                    should_exit, exit_reason = True, "Stop Loss"
                elif current_price <= position['take_profit']:
                    should_exit, exit_reason = True, "Take Profit"
            
            if idx - position['entry_bar'] >= 36:  # 36 hour max hold
                should_exit, exit_reason = True, "Time Exit"
            
            if should_exit:
                if position['direction'] == 'BUY':
                    gross_return = (current_price - position['entry_price']) / position['entry_price']
                else:
                    gross_return = (position['entry_price'] - current_price) / position['entry_price']
                
                cost = position['position_size'] * 0.004  # 0.4% aggressive cost
                net_pnl = (position['position_size'] * gross_return) - cost
                balance += net_pnl
                strategy.update_trade_outcome(net_pnl)
                
                trades.append({
                    'entry_time': position['entry_time'], 'exit_time': row['timestamp'],
                    'direction': position['direction'], 'gross_return': gross_return,
                    'net_pnl': net_pnl, 'exit_reason': exit_reason
                })
                position = None
        
        # Generate signals
        signal = strategy.add_price_data(price_data, idx)
        
        if signal['direction'] != 'NEUTRAL' and not position:
            entry_price = row['close']
            strength = signal['strength']
            
            # Aggressive stops/targets
            base_stop = 0.025   # 2.5%
            base_target = 0.075 # 7.5%
            
            if signal['direction'] == 'BUY':
                stop_loss = entry_price * (1 - base_stop)
                take_profit = entry_price * (1 + base_target)
            else:
                stop_loss = entry_price * (1 + base_stop)
                take_profit = entry_price * (1 - base_target)
            
            position_size = strategy.calculate_position_size(balance, strength)
            
            position = {
                'direction': signal['direction'], 'entry_price': entry_price,
                'entry_time': row['timestamp'], 'entry_bar': idx,
                'stop_loss': stop_loss, 'take_profit': take_profit,
                'position_size': position_size
            }
    
    # Results
    total_return = (balance - initial_balance) / initial_balance
    annual_return = total_return  # 1 year data
    monthly_return = annual_return / 12
    
    winning_trades = [t for t in trades if t['net_pnl'] > 0]
    win_rate = len(winning_trades) / len(trades) if trades else 0
    
    print(f"\n📊 AGGRESSIVE STRATEGY RESULTS:")
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"📈 PERFORMANCE:")
    print(f"   Baseline Return:         7.8%")
    print(f"   AGGRESSIVE Return:       {annual_return:+.1%}")
    print(f"   IMPROVEMENT:             {annual_return - 0.078:+.1%}")
    print(f"   Final Balance:           ${balance:,.2f}")
    print(f"   Total Trades:            {len(trades)}")
    print(f"   Win Rate:                {win_rate:.1%}")
    
    print(f"\n💰 MONTHLY PROJECTIONS:")
    print(f"   Monthly Return:          {monthly_return:+.1%}")
    print(f"   $10K/Month:              ${10000 * monthly_return:,.0f}")
    print(f"   $50K/Month:              ${50000 * monthly_return:,.0f}")
    print(f"   $100K/Month:             ${100000 * monthly_return:,.0f}")
    
    target_met = annual_return >= 0.20
    print(f"\n🎯 20% TARGET:              {'✅ ACHIEVED' if target_met else '❌ Not Met'}")
    
    if target_met:
        improvement = annual_return / 0.078
        print(f"🎉 SUCCESS! {improvement:.1f}x improvement achieved!")
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results = {
        'annual_return': annual_return, 'monthly_return': monthly_return,
        'final_balance': balance, 'total_trades': len(trades),
        'win_rate': win_rate, 'target_achieved': target_met
    }
    
    filename = f"aggressive_results_{timestamp}.json"
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Results saved: {filename}")
    return results

if __name__ == "__main__":
    run_aggressive_backtest()
