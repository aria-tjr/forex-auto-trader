#!/usr/bin/env python3
"""
Quick Crypto Backtest - Simplified Version
Fast backtesting to validate strategy performance

Features:
- Simplified risk management
- Fast execution
- Clear performance metrics
- Realistic crypto data simulation
"""

import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional

# Import our strategy
from simplified_robust_strategy import SimplifiedRobustStrategy, PriceData, Signal

class QuickBacktester:
    """Simplified backtesting engine for quick validation"""
    
    def __init__(self, initial_balance: float = 10000.0):
        """Initialize backtester"""
        self.initial_balance = initial_balance
        self.current_balance = initial_balance
        self.strategy = SimplifiedRobustStrategy()
        
        # Simple position tracking
        self.position = None  # Single position for simplicity
        self.trades: List[Dict] = []
        
        # Configuration
        self.risk_per_trade = 0.02  # 2% risk per trade
        self.stop_loss_pct = 0.03   # 3% stop loss
        self.take_profit_pct = 0.06 # 6% take profit
        self.commission_rate = 0.001 # 0.1% commission
        
    def generate_crypto_data(self, days: int = 90) -> pd.DataFrame:
        """Generate realistic crypto price data"""
        np.random.seed(42)  # Reproducible results
        
        # Generate 15-minute data
        periods = days * 96  # 96 periods per day (15-min intervals)
        timestamps = [datetime.now() - timedelta(days=days) + timedelta(minutes=15*i) 
                     for i in range(periods)]
        
        # Simulate realistic crypto price movements
        initial_price = 45000.0  # Starting BTC price
        daily_vol = 0.04  # 4% daily volatility
        period_vol = daily_vol / np.sqrt(96)  # 15-min volatility
        
        prices = [initial_price]
        for i in range(periods):
            # Add trend and volatility
            trend = np.random.normal(0, 0.0001)  # Small random trend
            noise = np.random.normal(0, period_vol)
            
            new_price = prices[-1] * (1 + trend + noise)
            prices.append(new_price)
        
        # Create OHLCV data
        data = []
        for i, (timestamp, close) in enumerate(zip(timestamps, prices[1:])):
            # Generate OHLC from close
            range_pct = np.random.uniform(0.005, 0.02)  # 0.5-2% range
            high = close * (1 + range_pct/2)
            low = close * (1 - range_pct/2)
            
            if i == 0:
                open_price = close * (1 + np.random.uniform(-0.001, 0.001))
            else:
                open_price = data[-1]['close']
            
            # Ensure OHLC logic
            high = max(high, open_price, close)
            low = min(low, open_price, close)
            
            volume = int(np.random.uniform(500000, 2000000))
            
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
        """Run simplified backtest"""
        print(f"🚀 Running quick backtest...")
        print(f"💰 Initial balance: ${self.initial_balance:,.2f}")
        print(f"📊 Data points: {len(data)}")
        print(f"📅 Period: {data['timestamp'].iloc[0].strftime('%Y-%m-%d')} to {data['timestamp'].iloc[-1].strftime('%Y-%m-%d')}")
        
        signals_generated = 0
        trades_executed = 0
        
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
                
                # Generate signal
                signal = self.strategy.add_price_data(price_data)
                
                if signal and signal.direction != 'NEUTRAL':
                    signals_generated += 1
                    
                    # Try to open position if we don't have one
                    if not self.position:
                        if self._open_position(signal, price_data):
                            trades_executed += 1
                            
                if index % 1000 == 0:  # Progress indicator
                    print(f"📈 Processed {index:,} data points...")
                    
            except Exception as e:
                print(f"❌ Error at index {index}: {e}")
                continue
        
        # Close any remaining position
        if self.position:
            self._close_position(data.iloc[-1]['close'], data.iloc[-1]['timestamp'], "End of backtest")
        
        # Generate results
        results = self._calculate_performance()
        
        print(f"✅ Backtest completed!")
        print(f"📡 Signals generated: {signals_generated}")
        print(f"💼 Trades executed: {trades_executed}")
        
        return results
    
    def _open_position(self, signal: Signal, price_data: PriceData) -> bool:
        """Open a new position"""
        try:
            # Calculate position size
            risk_amount = self.current_balance * self.risk_per_trade
            
            if signal.direction == 'BUY':
                stop_loss = price_data.close * (1 - self.stop_loss_pct)
                take_profit = price_data.close * (1 + self.take_profit_pct)
            else:  # SELL
                stop_loss = price_data.close * (1 + self.stop_loss_pct)
                take_profit = price_data.close * (1 - self.take_profit_pct)
            
            # Calculate position size based on stop loss
            price_diff = abs(price_data.close - stop_loss)
            if price_diff == 0:
                return False
                
            position_size_usdt = risk_amount / (price_diff / price_data.close)
            
            # Limit position size to current balance
            max_position_size = self.current_balance * 0.5  # Max 50% of balance per trade
            position_size_usdt = min(position_size_usdt, max_position_size)
            
            if position_size_usdt < 10:  # Minimum trade size
                return False
            
            # Calculate commission
            commission = position_size_usdt * self.commission_rate
            
            # Create position
            self.position = {
                'direction': signal.direction,
                'entry_price': price_data.close,
                'position_size_usdt': position_size_usdt,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'entry_time': price_data.timestamp,
                'commission': commission,
                'signal_strength': signal.strength
            }
            
            # Deduct commission
            self.current_balance -= commission
            
            print(f"📈 {signal.direction} position opened at ${price_data.close:,.2f} | Size: ${position_size_usdt:,.2f}")
            return True
            
        except Exception as e:
            print(f"❌ Error opening position: {e}")
            return False
    
    def _check_position_exit(self, price_data: PriceData):
        """Check if current position should be closed"""
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
        """Close current position"""
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
            
            # Record trade
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
                'signal_strength': self.position['signal_strength']
            }
            
            self.trades.append(trade)
            
            print(f"📉 Position closed at ${exit_price:,.2f} | P&L: ${net_pnl:+,.2f} | Reason: {reason}")
            
            # Clear position
            self.position = None
            
        except Exception as e:
            print(f"❌ Error closing position: {e}")
    
    def _calculate_performance(self) -> Dict:
        """Calculate performance metrics"""
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
        
        # Return metrics
        returns = [t['return_pct'] for t in self.trades]
        avg_return_per_trade = np.mean(returns) if returns else 0
        
        # Calculate maximum drawdown (simplified)
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
        
        # Duration metrics
        durations = [t['duration_hours'] for t in self.trades]
        avg_duration = np.mean(durations) if durations else 0
        
        # Time-based metrics
        if self.trades:
            start_date = min(t['entry_time'] for t in self.trades)
            end_date = max(t['exit_time'] for t in self.trades)
            days_traded = (end_date - start_date).days + 1
            annual_return = (total_return + 1) ** (365 / days_traded) - 1 if days_traded > 0 else 0
        else:
            days_traded = 0
            annual_return = 0
        
        return {
            'summary': {
                'initial_balance': self.initial_balance,
                'final_balance': self.current_balance,
                'total_return': total_return,
                'annual_return': annual_return,
                'max_drawdown': max_drawdown
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
            }
        }

def print_results(results: Dict):
    """Print formatted results"""
    if 'error' in results:
        print(f"❌ {results['error']}")
        return
    
    print("\n" + "="*50)
    print("₿ CRYPTO BACKTEST RESULTS")
    print("="*50)
    
    # Summary
    s = results['summary']
    print(f"\n💰 PERFORMANCE SUMMARY")
    print(f"   Initial Balance:    ${s['initial_balance']:,.2f}")
    print(f"   Final Balance:      ${s['final_balance']:,.2f}")
    print(f"   Total Return:       {s['total_return']:.2%}")
    print(f"   Annual Return:      {s['annual_return']:.2%}")
    print(f"   Max Drawdown:       {s['max_drawdown']:.2%}")
    
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
    
    # Time
    tm = results['time_metrics']
    print(f"\n⏱️ TIME ANALYSIS")
    print(f"   Days Traded:        {tm['days_traded']}")
    print(f"   Avg Duration:       {tm['avg_duration_hours']:.1f} hours")
    print(f"   Total Commission:   ${tm['total_commission']:,.2f}")
    
    print("\n" + "="*50)
    
    # Assessment
    print("📈 STRATEGY ASSESSMENT:")
    
    if s['annual_return'] > 0.15:  # 15%
        print("   ✅ Strong annual returns for crypto")
    elif s['annual_return'] > 0.08:  # 8%
        print("   ✅ Good annual returns")
    elif s['annual_return'] > 0:
        print("   ✅ Profitable strategy")
    else:
        print("   ❌ Losing strategy")
    
    if t['win_rate'] > 0.6:  # 60%
        print("   ✅ Excellent win rate")
    elif t['win_rate'] > 0.5:  # 50%
        print("   ✅ Good win rate")
    else:
        print("   ⚠️  Low win rate")
    
    if t['profit_factor'] > 1.5:
        print("   ✅ Excellent profit factor")
    elif t['profit_factor'] > 1.2:
        print("   ✅ Good profit factor")
    elif t['profit_factor'] > 1.0:
        print("   ✅ Profitable")
    else:
        print("   ❌ Unprofitable")

def main():
    """Run quick backtest"""
    print("🚀 Starting Quick Crypto Backtest")
    print("📊 Testing Simplified Robust Strategy")
    
    # Create backtester
    backtester = QuickBacktester(initial_balance=10000.0)
    
    # Generate data
    print("\n📈 Generating crypto market data...")
    data = backtester.generate_crypto_data(days=90)  # 90 days of data
    print(f"✅ Generated {len(data)} data points")
    print(f"💹 Price range: ${data['close'].min():,.2f} - ${data['close'].max():,.2f}")
    
    # Run backtest
    print("\n🔄 Running backtest...")
    results = backtester.run_backtest(data)
    
    # Print results
    print_results(results)
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"quick_backtest_results_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Results saved to: {filename}")

if __name__ == "__main__":
    main() 