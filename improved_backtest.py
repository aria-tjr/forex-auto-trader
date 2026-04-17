#!/usr/bin/env python3
"""
Improved Crypto Backtest - Testing Enhanced Strategy
Demonstrates improvements from addressing weak points
"""

import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional

# Import our improved strategy
from improved_strategy import ImprovedCryptoStrategy, PriceData, Signal

class ImprovedBacktester:
    """Enhanced backtesting engine with improved strategy"""
    
    def __init__(self, initial_balance: float = 10000.0):
        """Initialize improved backtester"""
        self.initial_balance = initial_balance
        self.current_balance = initial_balance
        self.strategy = ImprovedCryptoStrategy()
        
        # Enhanced position tracking
        self.position = None
        self.trades: List[Dict] = []
        
        # Improved configuration
        self.risk_per_trade = 0.02  # 2% risk per trade
        self.stop_loss_pct = 0.025  # Tighter: 2.5% stop loss
        self.take_profit_pct = 0.05 # Tighter: 5% take profit (better risk:reward)
        self.commission_rate = 0.001 # 0.1% commission
        
        # Signal quality tracking
        self.signals_by_regime = {}
        self.performance_by_regime = {}
        
    def generate_crypto_data(self, days: int = 120) -> pd.DataFrame:
        """Generate more realistic crypto data with market cycles"""
        np.random.seed(42)  # Reproducible results
        
        # Generate 15-minute data
        periods = days * 96  # 96 periods per day (15-min intervals)
        timestamps = [datetime.now() - timedelta(days=days) + timedelta(minutes=15*i) 
                     for i in range(periods)]
        
        # More realistic crypto simulation with market cycles
        initial_price = 45000.0
        daily_vol = 0.035  # 3.5% daily volatility (slightly lower)
        period_vol = daily_vol / np.sqrt(96)
        
        # Create market cycles (trending vs ranging periods)
        cycle_length = 480  # ~5 days per cycle
        num_cycles = periods // cycle_length + 1
        
        prices = [initial_price]
        for cycle in range(num_cycles):
            # Determine cycle type
            cycle_type = np.random.choice(['trending_up', 'trending_down', 'ranging'], 
                                        p=[0.3, 0.3, 0.4])  # 40% ranging markets
            
            cycle_start = cycle * cycle_length
            cycle_end = min((cycle + 1) * cycle_length, periods)
            
            for i in range(cycle_start, cycle_end):
                if i >= len(prices):
                    break
                    
                # Generate returns based on cycle type
                if cycle_type == 'trending_up':
                    trend = np.random.normal(0.0003, 0.0001)  # Positive trend
                    noise = np.random.normal(0, period_vol * 0.8)  # Less noise in trends
                elif cycle_type == 'trending_down':
                    trend = np.random.normal(-0.0003, 0.0001)  # Negative trend
                    noise = np.random.normal(0, period_vol * 0.8)  # Less noise in trends
                else:  # ranging
                    trend = np.random.normal(0, 0.00005)  # No trend
                    noise = np.random.normal(0, period_vol * 1.2)  # More noise in ranges
                
                # Add mean reversion in ranging markets
                if cycle_type == 'ranging':
                    if len(prices) >= 20:
                        sma_20 = np.mean(prices[-20:])
                        mean_reversion = (sma_20 - prices[-1]) / sma_20 * 0.1
                        trend += mean_reversion
                
                new_price = prices[-1] * (1 + trend + noise)
                prices.append(new_price)
        
        # Create OHLCV data
        data = []
        for i, (timestamp, close) in enumerate(zip(timestamps, prices[1:])):
            # Generate more realistic OHLC
            volatility = abs(close - prices[i]) / close if i > 0 else 0.01
            range_pct = max(0.003, min(0.025, volatility * 2))  # Dynamic range based on volatility
            
            high = close * (1 + range_pct * np.random.uniform(0.3, 1.0))
            low = close * (1 - range_pct * np.random.uniform(0.3, 1.0))
            
            if i == 0:
                open_price = close * (1 + np.random.uniform(-0.002, 0.002))
            else:
                open_price = data[-1]['close'] * (1 + np.random.uniform(-0.001, 0.001))
            
            # Ensure OHLC logic
            high = max(high, open_price, close)
            low = min(low, open_price, close)
            
            # More realistic volume
            base_volume = 1000000
            volatility_multiplier = (volatility * 100) + 1
            volume = int(base_volume * volatility_multiplier * np.random.uniform(0.7, 1.5))
            
            data.append({
                'timestamp': timestamp,
                'open': round(open_price, 2),
                'high': round(high, 2),
                'low': round(low, 2),
                'close': round(close, 2),
                'volume': volume
            })
        
        return pd.DataFrame(data)
    
    def run_backtest(self, data: pd.DataFrame) -> Dict:
        """Run improved backtest with enhanced strategy"""
        print(f"🚀 Running IMPROVED backtest...")
        print(f"💰 Initial balance: ${self.initial_balance:,.2f}")
        print(f"📊 Data points: {len(data)}")
        print(f"📅 Period: {data['timestamp'].iloc[0].strftime('%Y-%m-%d')} to {data['timestamp'].iloc[-1].strftime('%Y-%m-%d')}")
        
        signals_generated = 0
        trades_executed = 0
        regime_changes = 0
        last_regime = "UNKNOWN"
        
        for index, row in data.iterrows():
            try:
                # Create price data
                price_data = PriceData(
                    timestamp=row['timestamp'],
                    open=row['open'],
                    high=row['high'],
                    low=row['low'],
                    close=row['close'],
                    volume=row['volume']
                )
                
                # Update position (check for exit conditions)
                if self.position:
                    self._check_position_exit(price_data)
                
                # Generate signal with improved strategy
                signal = self.strategy.add_price_data(price_data)
                
                # Track regime changes
                current_regime = self.strategy.market_regime
                if current_regime != last_regime and last_regime != "UNKNOWN":
                    regime_changes += 1
                    print(f"📊 Market regime changed: {last_regime} -> {current_regime} at {row['timestamp'].strftime('%m-%d %H:%M')}")
                last_regime = current_regime
                
                if signal and signal.direction != 'NEUTRAL':
                    signals_generated += 1
                    
                    # Track signals by regime
                    if current_regime not in self.signals_by_regime:
                        self.signals_by_regime[current_regime] = []
                    self.signals_by_regime[current_regime].append(signal)
                    
                    # Try to open position if we don't have one
                    if not self.position:
                        if self._open_improved_position(signal, price_data):
                            trades_executed += 1
                            
                if index % 2000 == 0:  # Progress indicator
                    print(f"📈 Processed {index:,} | Regime: {current_regime} | Trend: {self.strategy.trend_strength:.2f}")
                    
            except Exception as e:
                print(f"❌ Error at index {index}: {e}")
                continue
        
        # Close any remaining position
        if self.position:
            self._close_position(data.iloc[-1]['close'], data.iloc[-1]['timestamp'], "End of backtest")
        
        # Generate enhanced results
        results = self._calculate_enhanced_performance()
        
        print(f"✅ IMPROVED Backtest completed!")
        print(f"📡 Signals generated: {signals_generated}")
        print(f"💼 Trades executed: {trades_executed}")
        print(f"🔄 Regime changes: {regime_changes}")
        
        return results
    
    def _open_improved_position(self, signal: Signal, price_data: PriceData) -> bool:
        """Open position with improved logic"""
        try:
            # Enhanced position sizing based on signal confidence
            base_risk = self.risk_per_trade
            confidence_multiplier = 0.7 + (signal.confidence * 0.6)  # 0.7x to 1.3x based on confidence
            adjusted_risk = base_risk * confidence_multiplier
            
            risk_amount = self.current_balance * adjusted_risk
            
            # Dynamic stop loss based on market regime and volatility
            if self.strategy.market_regime in ["STRONG_UPTREND", "STRONG_DOWNTREND"]:
                # Wider stops in trending markets
                stop_loss_pct = self.stop_loss_pct * 1.2
                take_profit_pct = self.take_profit_pct * 1.3
            else:
                # Tighter stops in ranging markets
                stop_loss_pct = self.stop_loss_pct * 0.8
                take_profit_pct = self.take_profit_pct * 0.9
            
            # Adjust for volatility regime
            if self.strategy.volatility_regime == "HIGH":
                stop_loss_pct *= 1.3
                take_profit_pct *= 1.2
            elif self.strategy.volatility_regime == "LOW":
                stop_loss_pct *= 0.8
                take_profit_pct *= 0.9
            
            if signal.direction == 'BUY':
                stop_loss = price_data.close * (1 - stop_loss_pct)
                take_profit = price_data.close * (1 + take_profit_pct)
            else:  # SELL
                stop_loss = price_data.close * (1 + stop_loss_pct)
                take_profit = price_data.close * (1 - take_profit_pct)
            
            # Calculate position size
            price_diff = abs(price_data.close - stop_loss)
            if price_diff == 0:
                return False
                
            position_size_usdt = risk_amount / (price_diff / price_data.close)
            
            # Limit position size
            max_position_size = self.current_balance * 0.4  # Max 40% per trade
            position_size_usdt = min(position_size_usdt, max_position_size)
            
            if position_size_usdt < 10:  # Minimum trade size
                return False
            
            # Calculate commission
            commission = position_size_usdt * self.commission_rate
            
            # Create enhanced position
            self.position = {
                'direction': signal.direction,
                'entry_price': price_data.close,
                'position_size_usdt': position_size_usdt,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'entry_time': price_data.timestamp,
                'commission': commission,
                'signal_strength': signal.strength,
                'signal_confidence': signal.confidence,
                'market_regime': self.strategy.market_regime,
                'trend_strength': self.strategy.trend_strength,
                'volatility_regime': self.strategy.volatility_regime,
                'signal_reason': signal.reason
            }
            
            # Deduct commission
            self.current_balance -= commission
            
            print(f"📈 {signal.direction} @ ${price_data.close:,.2f} | Size: ${position_size_usdt:,.2f} | "
                  f"Regime: {self.strategy.market_regime} | Conf: {signal.confidence:.2f}")
            return True
            
        except Exception as e:
            print(f"❌ Error opening improved position: {e}")
            return False
    
    def _check_position_exit(self, price_data: PriceData):
        """Check position exit with improved logic"""
        if not self.position:
            return
        
        current_price = price_data.close
        should_close = False
        exit_reason = ""
        
        if self.position['direction'] == 'BUY':
            if current_price <= self.position['stop_loss']:
                should_close = True
                exit_reason = "Stop Loss"
            elif current_price >= self.position['take_profit']:
                should_close = True
                exit_reason = "Take Profit"
        else:  # SELL
            if current_price >= self.position['stop_loss']:
                should_close = True
                exit_reason = "Stop Loss"
            elif current_price <= self.position['take_profit']:
                should_close = True
                exit_reason = "Take Profit"
        
        if should_close:
            self._close_position(current_price, price_data.timestamp, exit_reason)
    
    def _close_position(self, exit_price: float, exit_time: datetime, reason: str):
        """Close position with enhanced tracking"""
        if not self.position:
            return
        
        try:
            # Calculate P&L
            if self.position['direction'] == 'BUY':
                pnl_pct = (exit_price - self.position['entry_price']) / self.position['entry_price']
            else:  # SELL
                pnl_pct = (self.position['entry_price'] - exit_price) / self.position['entry_price']
            
            pnl_usdt = pnl_pct * self.position['position_size_usdt']
            
            # Calculate exit commission
            exit_commission = self.position['position_size_usdt'] * self.commission_rate
            net_pnl = pnl_usdt - exit_commission
            
            # Update balance
            self.current_balance += net_pnl
            
            # Enhanced trade record
            trade = {
                'direction': self.position['direction'],
                'entry_price': self.position['entry_price'],
                'exit_price': exit_price,
                'entry_time': self.position['entry_time'],
                'exit_time': exit_time,
                'duration_hours': (exit_time - self.position['entry_time']).total_seconds() / 3600,
                'position_size_usdt': self.position['position_size_usdt'],
                'pnl_usdt': pnl_usdt,
                'net_pnl': net_pnl,
                'return_pct': net_pnl / self.position['position_size_usdt'],
                'total_commission': self.position['commission'] + exit_commission,
                'exit_reason': reason,
                'signal_strength': self.position['signal_strength'],
                'signal_confidence': self.position['signal_confidence'],
                'market_regime': self.position['market_regime'],
                'trend_strength': self.position['trend_strength'],
                'volatility_regime': self.position['volatility_regime'],
                'signal_reason': self.position['signal_reason']
            }
            
            self.trades.append(trade)
            
            # Track performance by regime
            regime = self.position['market_regime']
            if regime not in self.performance_by_regime:
                self.performance_by_regime[regime] = {'trades': 0, 'pnl': 0, 'wins': 0}
            
            self.performance_by_regime[regime]['trades'] += 1
            self.performance_by_regime[regime]['pnl'] += net_pnl
            if net_pnl > 0:
                self.performance_by_regime[regime]['wins'] += 1
            
            print(f"📉 Closed @ ${exit_price:,.2f} | P&L: ${net_pnl:+,.2f} | {reason} | {regime}")
            
            # Clear position
            self.position = None
            
        except Exception as e:
            print(f"❌ Error closing improved position: {e}")
    
    def _calculate_enhanced_performance(self) -> Dict:
        """Calculate enhanced performance metrics"""
        if not self.trades:
            return {'error': 'No trades executed'}
        
        # Basic metrics
        total_return = (self.current_balance - self.initial_balance) / self.initial_balance
        total_trades = len(self.trades)
        winning_trades = len([t for t in self.trades if t['net_pnl'] > 0])
        losing_trades = total_trades - winning_trades
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        # P&L metrics
        total_profit = sum(t['net_pnl'] for t in self.trades if t['net_pnl'] > 0)
        total_loss = abs(sum(t['net_pnl'] for t in self.trades if t['net_pnl'] < 0))
        profit_factor = total_profit / total_loss if total_loss > 0 else float('inf')
        
        avg_win = total_profit / winning_trades if winning_trades > 0 else 0
        avg_loss = total_loss / losing_trades if losing_trades > 0 else 0
        
        # Enhanced metrics
        returns = [t['return_pct'] for t in self.trades]
        avg_return_per_trade = np.mean(returns) if returns else 0
        
        # Calculate Sharpe ratio
        if len(returns) > 1:
            sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252) if np.std(returns) > 0 else 0
        else:
            sharpe_ratio = 0
        
        # Maximum drawdown
        balance_history = [self.initial_balance]
        for trade in self.trades:
            balance_history.append(balance_history[-1] + trade['net_pnl'])
        
        peak = self.initial_balance
        max_drawdown = 0
        for balance in balance_history:
            if balance > peak:
                peak = balance
            drawdown = (peak - balance) / peak
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        # Time metrics
        durations = [t['duration_hours'] for t in self.trades]
        avg_duration = np.mean(durations) if durations else 0
        
        if self.trades:
            start_date = min(t['entry_time'] for t in self.trades)
            end_date = max(t['exit_time'] for t in self.trades)
            days_traded = (end_date - start_date).days + 1
            annual_return = (total_return + 1) ** (365 / days_traded) - 1 if days_traded > 0 else 0
        else:
            days_traded = 0
            annual_return = 0
        
        # Regime analysis
        regime_performance = {}
        for regime, data in self.performance_by_regime.items():
            if data['trades'] > 0:
                regime_performance[regime] = {
                    'trades': data['trades'],
                    'win_rate': data['wins'] / data['trades'],
                    'total_pnl': data['pnl'],
                    'avg_pnl': data['pnl'] / data['trades']
                }
        
        return {
            'summary': {
                'initial_balance': self.initial_balance,
                'final_balance': self.current_balance,
                'total_return': total_return,
                'annual_return': annual_return,
                'max_drawdown': max_drawdown,
                'sharpe_ratio': sharpe_ratio
            },
            'trading_metrics': {
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'win_rate': win_rate,
                'profit_factor': profit_factor,
                'avg_return_per_trade': avg_return_per_trade
            },
            'pnl_metrics': {
                'total_profit': total_profit,
                'total_loss': total_loss,
                'net_profit': self.current_balance - self.initial_balance,
                'avg_win': avg_win,
                'avg_loss': avg_loss
            },
            'time_metrics': {
                'days_traded': days_traded,
                'avg_duration_hours': avg_duration,
                'total_commission': sum(t['total_commission'] for t in self.trades)
            },
            'regime_analysis': regime_performance,
            'improvements': {
                'market_regime_detection': True,
                'adaptive_thresholds': True,
                'signal_quality_filtering': True,
                'confidence_based_sizing': True
            }
        }

def print_improved_results(results: Dict):
    """Print enhanced results with regime analysis"""
    if 'error' in results:
        print(f"❌ {results['error']}")
        return
    
    print("\n" + "="*60)
    print("🚀 IMPROVED CRYPTO BACKTEST RESULTS")
    print("="*60)
    
    # Summary
    s = results['summary']
    print(f"\n💰 PERFORMANCE SUMMARY")
    print(f"   Initial Balance:    ${s['initial_balance']:,.2f}")
    print(f"   Final Balance:      ${s['final_balance']:,.2f}")
    print(f"   Total Return:       {s['total_return']:.2%}")
    print(f"   Annual Return:      {s['annual_return']:.2%}")
    print(f"   Max Drawdown:       {s['max_drawdown']:.2%}")
    print(f"   Sharpe Ratio:       {s['sharpe_ratio']:.2f}")
    
    # Trading
    t = results['trading_metrics']
    print(f"\n📊 TRADING METRICS")
    print(f"   Total Trades:       {t['total_trades']}")
    print(f"   Winning Trades:     {t['winning_trades']}")
    print(f"   Losing Trades:      {t['losing_trades']}")
    print(f"   Win Rate:           {t['win_rate']:.2%}")
    print(f"   Profit Factor:      {t['profit_factor']:.2f}")
    print(f"   Avg Return/Trade:   {t['avg_return_per_trade']:.2%}")
    
    # P&L
    p = results['pnl_metrics']
    print(f"\n💵 P&L BREAKDOWN")
    print(f"   Total Profit:       ${p['total_profit']:,.2f}")
    print(f"   Total Loss:         ${p['total_loss']:,.2f}")
    print(f"   Net Profit:         ${p['net_profit']:,.2f}")
    print(f"   Average Win:        ${p['avg_win']:,.2f}")
    print(f"   Average Loss:       ${p['avg_loss']:,.2f}")
    
    # Regime Analysis
    regime_data = results.get('regime_analysis', {})
    if regime_data:
        print(f"\n🎯 MARKET REGIME PERFORMANCE")
        for regime, data in regime_data.items():
            print(f"   {regime}:")
            print(f"     Trades: {data['trades']} | Win Rate: {data['win_rate']:.1%} | "
                  f"Total P&L: ${data['total_pnl']:+,.2f} | Avg: ${data['avg_pnl']:+,.2f}")
    
    # Time
    tm = results['time_metrics']
    print(f"\n⏱️ TIME ANALYSIS")
    print(f"   Days Traded:        {tm['days_traded']}")
    print(f"   Avg Duration:       {tm['avg_duration_hours']:.1f} hours")
    print(f"   Total Commission:   ${tm['total_commission']:,.2f}")
    
    print(f"\n🔧 IMPROVEMENTS IMPLEMENTED")
    improvements = results.get('improvements', {})
    for improvement, enabled in improvements.items():
        status = "✅" if enabled else "❌"
        print(f"   {status} {improvement.replace('_', ' ').title()}")
    
    print("\n" + "="*60)
    
    # Enhanced Assessment
    print("📈 IMPROVED STRATEGY ASSESSMENT:")
    
    if s['annual_return'] > 0.20:  # 20%
        print("   ✅ Excellent annual returns for crypto")
    elif s['annual_return'] > 0.10:  # 10%
        print("   ✅ Good annual returns")
    elif s['annual_return'] > 0:
        print("   ✅ Profitable strategy")
    else:
        print("   ❌ Still losing strategy")
    
    if t['win_rate'] > 0.55:  # 55%
        print("   ✅ Good win rate (target achieved)")
    elif t['win_rate'] > 0.45:  # 45%
        print("   ✅ Improved win rate")
    else:
        print("   ⚠️  Win rate still needs work")
    
    if t['profit_factor'] > 1.3:
        print("   ✅ Excellent profit factor")
    elif t['profit_factor'] > 1.1:
        print("   ✅ Good profit factor")
    elif t['profit_factor'] > 1.0:
        print("   ✅ Profitable")
    else:
        print("   ❌ Still unprofitable")

def main():
    """Run improved backtest"""
    print("🚀 Starting IMPROVED Crypto Backtest")
    print("📊 Testing Enhanced Strategy with Market Regime Detection")
    
    # Create improved backtester
    backtester = ImprovedBacktester(initial_balance=10000.0)
    
    # Generate enhanced data
    print("\n📈 Generating enhanced crypto market data...")
    data = backtester.generate_crypto_data(days=120)  # 4 months of data
    print(f"✅ Generated {len(data)} data points")
    print(f"💹 Price range: ${data['close'].min():,.2f} - ${data['close'].max():,.2f}")
    
    # Run improved backtest
    print("\n🔄 Running IMPROVED backtest...")
    results = backtester.run_backtest(data)
    
    # Print enhanced results
    print_improved_results(results)
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"improved_backtest_results_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Results saved to: {filename}")

if __name__ == "__main__":
    main() 