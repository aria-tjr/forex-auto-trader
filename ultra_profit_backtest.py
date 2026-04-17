#!/usr/bin/env python3
"""
Ultra Profit Backtest Engine - Comprehensive Strategy Validation
Tests the Ultra Profit Enhanced Strategy with detailed performance analysis

FEATURES:
✅ Comprehensive performance metrics
✅ Monthly/annual return tracking
✅ Compound growth validation
✅ Regime-specific performance analysis
✅ Risk-adjusted return metrics
✅ Profit enhancement validation
"""

import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any
import logging
from ultra_profit_enhanced_strategy import UltraProfitEnhancedStrategy

class UltraProfitBacktestEngine:
    """Advanced backtest engine for ultra profit validation"""
    
    def __init__(self, initial_balance: float = 10000):
        self.initial_balance = initial_balance
        self.current_balance = initial_balance
        self.peak_balance = initial_balance
        self.strategy = UltraProfitEnhancedStrategy()
        
        # Performance tracking
        self.trades = []
        self.daily_balances = []
        self.monthly_returns = []
        self.regime_performance = {}
        
        # Advanced metrics
        self.compound_growth_log = []
        self.risk_metrics = {}
        
        # Realistic trading costs
        self.trading_costs = {
            'spread': 0.0008,        # 0.08% spread
            'commission': 0.0005,    # 0.05% commission  
            'slippage': 0.0003,      # 0.03% slippage
            'total': 0.0016          # 0.16% total cost (optimistic)
        }
        
    def load_data(self, data_file: str = None) -> pd.DataFrame:
        """Load or generate test data"""
        if data_file:
            return pd.read_csv(data_file)
        else:
            # Generate realistic synthetic data with various market regimes
            np.random.seed(42)
            periods = 8760  # 1 year of hourly data
            
            dates = pd.date_range(start='2023-01-01', periods=periods, freq='H')
            
            # Create different market regimes
            regime_changes = [0, 1500, 3000, 4500, 6000, 7500, 8760]  # Regime change points
            regime_types = ['UPTREND', 'SIDEWAYS', 'DOWNTREND', 'STRONG_UPTREND', 'SIDEWAYS', 'STRONG_DOWNTREND']
            
            prices = []
            volumes = []
            stress_periods = []
            
            current_price = 30000  # Starting price (crypto-like)
            
            for i in range(periods):
                # Determine current regime
                regime_idx = 0
                for j, change_point in enumerate(regime_changes[1:]):
                    if i < change_point:
                        regime_idx = j
                        break
                else:
                    regime_idx = len(regime_types) - 1
                    
                regime = regime_types[regime_idx]
                
                # Generate price movement based on regime
                if regime == 'STRONG_UPTREND':
                    trend = 0.0015 + np.random.normal(0, 0.008)  # Strong upward bias
                    volatility = 0.015
                elif regime == 'UPTREND':
                    trend = 0.0008 + np.random.normal(0, 0.006)  # Moderate upward bias
                    volatility = 0.012
                elif regime == 'STRONG_DOWNTREND':
                    trend = -0.0015 + np.random.normal(0, 0.008)  # Strong downward bias
                    volatility = 0.018
                elif regime == 'DOWNTREND':
                    trend = -0.0008 + np.random.normal(0, 0.006)  # Moderate downward bias
                    volatility = 0.015
                else:  # SIDEWAYS
                    trend = np.random.normal(0, 0.003)  # No bias
                    volatility = 0.010
                
                # Add some random stress periods
                is_stress = np.random.random() < 0.05  # 5% chance of stress
                if is_stress:
                    volatility *= 2.5  # Higher volatility during stress
                    
                # Calculate price change
                price_change = trend + np.random.normal(0, volatility)
                current_price *= (1 + price_change)
                
                # Ensure price doesn't go negative
                current_price = max(current_price, 1000)
                
                prices.append(current_price)
                volumes.append(np.random.lognormal(12, 0.5))  # Random volume
                stress_periods.append(is_stress)
            
            # Create OHLC data
            data = pd.DataFrame({
                'timestamp': dates,
                'open': prices,
                'high': [p * (1 + abs(np.random.normal(0, 0.005))) for p in prices],
                'low': [p * (1 - abs(np.random.normal(0, 0.005))) for p in prices],
                'close': prices,
                'volume': volumes,
                'stress_period': stress_periods
            })
            
            return data
    
    def execute_trade(self, signal: Dict, current_price: float, bar_index: int) -> Dict:
        """Execute a trade based on signal"""
        if signal['direction'] == 'NEUTRAL':
            return None
            
        # Position size is now in dollar value
        position_value = signal.get('position_size', 0)
        if position_value <= 0 or position_value > self.current_balance:
            return None
            
        # Apply trading costs based on position value
        total_cost = position_value * self.trading_costs['total']
        
        # Check if we have enough balance for the trade
        total_required = position_value + total_cost
        if total_required > self.current_balance:
            return None
        
        # Calculate stop loss and take profit levels
        stop_loss_pct = signal.get('stop_loss_pct', 2.0) / 100
        profit_target_pct = signal.get('profit_target_pct', 3.0) / 100
        
        if signal['direction'] == 'BUY':
            stop_loss_price = current_price * (1 - stop_loss_pct)
            take_profit_price = current_price * (1 + profit_target_pct)
        else:  # SELL
            stop_loss_price = current_price * (1 + stop_loss_pct)
            take_profit_price = current_price * (1 - profit_target_pct)
        
        trade = {
            'entry_time': bar_index,
            'entry_price': current_price,
            'direction': signal['direction'],
            'position_value': position_value,  # Dollar value invested
            'stop_loss_price': stop_loss_price,
            'take_profit_price': take_profit_price,
            'regime': signal.get('regime', 'UNKNOWN'),
            'signal_strength': signal.get('strength', 0),
            'compound_multiplier': signal.get('compound_multiplier', 1.0),
            'entry_cost': total_cost,
            'status': 'OPEN'
        }
        
        # Deduct position value and costs from balance
        self.current_balance -= total_required
        
        return trade
    
    def update_open_trades(self, open_trades: List[Dict], current_price: float, bar_index: int) -> List[Dict]:
        """Update open trades and close them if needed"""
        updated_trades = []
        
        for trade in open_trades:
            if trade['status'] != 'OPEN':
                continue
                
            exit_reason = None
            exit_price = current_price
            
            # Check stop loss and take profit
            if trade['direction'] == 'BUY':
                if current_price <= trade['stop_loss_price']:
                    exit_reason = 'Stop Loss'
                    exit_price = trade['stop_loss_price']
                elif current_price >= trade['take_profit_price']:
                    exit_reason = 'Take Profit'
                    exit_price = trade['take_profit_price']
            else:  # SELL
                if current_price >= trade['stop_loss_price']:
                    exit_reason = 'Stop Loss'
                    exit_price = trade['stop_loss_price']
                elif current_price <= trade['take_profit_price']:
                    exit_reason = 'Take Profit'
                    exit_price = trade['take_profit_price']
            
            # Time-based exit (48 hours maximum)
            if bar_index - trade['entry_time'] >= 48:
                exit_reason = 'Time Exit'
                exit_price = current_price
            
            if exit_reason:
                # Close the trade
                if trade['direction'] == 'BUY':
                    gross_return = (exit_price - trade['entry_price']) / trade['entry_price']
                else:  # SELL
                    gross_return = (trade['entry_price'] - exit_price) / trade['entry_price']
                
                # Calculate P&L based on position value
                position_value = trade['position_value']
                gross_pnl = position_value * gross_return
                exit_cost = position_value * self.trading_costs['total']
                net_pnl = gross_pnl - exit_cost
                
                # Update balance - return the original position value plus/minus the P&L
                self.current_balance += position_value + net_pnl
                
                # Complete trade record
                trade.update({
                    'exit_time': bar_index,
                    'exit_price': exit_price,
                    'exit_reason': exit_reason,
                    'gross_return': gross_return,
                    'gross_pnl': gross_pnl,
                    'net_pnl': net_pnl,
                    'total_cost': trade['entry_cost'] + exit_cost,
                    'status': 'CLOSED'
                })
                
                # Add to completed trades
                self.trades.append(trade)
                
                # Update strategy with outcome
                self.strategy.update_trade_outcome(net_pnl)
                
                # Track regime performance
                regime = trade['regime']
                if regime not in self.regime_performance:
                    self.regime_performance[regime] = {'trades': 0, 'total_pnl': 0, 'wins': 0}
                
                self.regime_performance[regime]['trades'] += 1
                self.regime_performance[regime]['total_pnl'] += net_pnl
                if net_pnl > 0:
                    self.regime_performance[regime]['wins'] += 1
            else:
                updated_trades.append(trade)
        
        return updated_trades
    
    def run_backtest(self, data: pd.DataFrame) -> Dict:
        """Run the complete backtest"""
        print("Starting Ultra Profit Enhanced Strategy Backtest...")
        print(f"Initial Balance: ${self.initial_balance:,.2f}")
        
        open_trades = []
        monthly_balance_history = []
        
        # Set initial balance for strategy
        self.strategy.current_balance = self.current_balance
        
        for i, row in data.iterrows():
            # Update strategy balance
            self.strategy.current_balance = self.current_balance
            
            # Track peak balance
            if self.current_balance > self.peak_balance:
                self.peak_balance = self.current_balance
            
            # Prepare price data for strategy
            price_data = {
                'timestamp': row['timestamp'],
                'open': row['open'],
                'high': row['high'],
                'low': row['low'],
                'close': row['close'],
                'volume': row['volume'],
                'stress_period': row['stress_period']
            }
            
            # Update open trades first
            open_trades = self.update_open_trades(open_trades, row['close'], i)
            
            # Generate new signal (only if no open trades for now)
            if len(open_trades) == 0:
                signal = self.strategy.add_price_data(price_data, i)
                
                # Execute trade if signal generated
                if signal['direction'] != 'NEUTRAL':
                    new_trade = self.execute_trade(signal, row['close'], i)
                    if new_trade:
                        open_trades.append(new_trade)
            
            # Track daily balance (every 24 hours)
            if i % 24 == 0:
                self.daily_balances.append({
                    'day': i // 24,
                    'balance': self.current_balance,
                    'drawdown': (self.peak_balance - self.current_balance) / self.peak_balance
                })
            
            # Track monthly performance
            if i % (24 * 30) == 0 and i > 0:  # Approximately monthly
                monthly_return = (self.current_balance - self.initial_balance) / self.initial_balance
                self.monthly_returns.append(monthly_return)
                monthly_balance_history.append(self.current_balance)
                
                # Log compound growth
                self.compound_growth_log.append({
                    'month': len(self.monthly_returns),
                    'balance': self.current_balance,
                    'compound_multiplier': self.strategy.position_manager.compound_multiplier,
                    'monthly_return': monthly_return
                })
                
                print(f"Month {len(self.monthly_returns)}: Balance ${self.current_balance:,.2f} "
                      f"(Return: {monthly_return:.2%}, Compound: {self.strategy.position_manager.compound_multiplier:.2f}x)")
        
        # Close any remaining open trades
        if open_trades:
            final_price = data.iloc[-1]['close']
            final_trades = self.update_open_trades(open_trades, final_price, len(data))
            # Force close any still open trades
            for trade in final_trades:
                if trade['status'] == 'OPEN':
                    trade['exit_reason'] = 'Backtest End'
                    # Simple exit calculation
                    if trade['direction'] == 'BUY':
                        gross_return = (final_price - trade['entry_price']) / trade['entry_price']
                    else:
                        gross_return = (trade['entry_price'] - final_price) / trade['entry_price']
                    
                    net_pnl = trade['position_value'] * gross_return
                    self.current_balance += trade['position_value'] + net_pnl
                    trade.update({
                        'exit_price': final_price,
                        'gross_return': gross_return,
                        'net_pnl': net_pnl,
                        'status': 'CLOSED'
                    })
                    self.trades.append(trade)
        
        return self.calculate_final_metrics()
    
    def calculate_final_metrics(self) -> Dict:
        """Calculate comprehensive performance metrics"""
        if not self.trades:
            return {'error': 'No trades executed'}
        
        # Basic performance
        total_return = (self.current_balance - self.initial_balance) / self.initial_balance
        total_days = len(self.daily_balances)
        annual_return = (1 + total_return) ** (365 / max(total_days, 1)) - 1
        monthly_return = annual_return / 12
        
        # Trade statistics
        winning_trades = [t for t in self.trades if t['net_pnl'] > 0]
        losing_trades = [t for t in self.trades if t['net_pnl'] <= 0]
        
        win_rate = len(winning_trades) / len(self.trades) if self.trades else 0
        
        avg_win = np.mean([t['net_pnl'] for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t['net_pnl'] for t in losing_trades]) if losing_trades else 0
        
        profit_factor = abs(sum(t['net_pnl'] for t in winning_trades) / 
                           sum(t['net_pnl'] for t in losing_trades)) if losing_trades else float('inf')
        
        # Risk metrics
        daily_returns = []
        if len(self.daily_balances) > 1:
            for i in range(1, len(self.daily_balances)):
                prev_balance = self.daily_balances[i-1]['balance']
                curr_balance = self.daily_balances[i]['balance']
                daily_return = (curr_balance - prev_balance) / prev_balance
                daily_returns.append(daily_return)
        
        volatility = np.std(daily_returns) * np.sqrt(365) if daily_returns else 0
        sharpe_ratio = annual_return / volatility if volatility > 0 else 0
        
        max_drawdown = max([d['drawdown'] for d in self.daily_balances]) if self.daily_balances else 0
        
        # Enhanced metrics
        compound_growth_achieved = self.current_balance / self.initial_balance
        max_compound_multiplier = max([log['compound_multiplier'] for log in self.compound_growth_log]) if self.compound_growth_log else 1.0
        
        # Monthly performance analysis
        if len(self.monthly_returns) > 1:
            monthly_volatility = np.std(self.monthly_returns)
            best_month = max(self.monthly_returns)
            worst_month = min(self.monthly_returns)
        else:
            monthly_volatility = 0
            best_month = monthly_return
            worst_month = monthly_return
        
        # Target achievement
        target_annual_15 = annual_return >= 0.15
        target_annual_20 = annual_return >= 0.20
        target_annual_25 = annual_return >= 0.25
        target_annual_30 = annual_return >= 0.30
        
        target_monthly_1 = monthly_return >= 0.01
        target_monthly_2 = monthly_return >= 0.02
        target_monthly_3 = monthly_return >= 0.03
        
        results = {
            # Core Performance
            'final_balance': self.current_balance,
            'total_return': total_return,
            'annual_return': annual_return,
            'monthly_return': monthly_return,
            
            # Enhanced Performance Metrics
            'compound_growth_factor': compound_growth_achieved,
            'max_compound_multiplier_used': max_compound_multiplier,
            'best_monthly_return': best_month,
            'worst_monthly_return': worst_month,
            'monthly_volatility': monthly_volatility,
            
            # Trade Statistics
            'total_trades': len(self.trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            
            # Risk Metrics
            'max_drawdown': max_drawdown,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            
            # Target Achievement
            'target_achievements': {
                'annual_15_pct': target_annual_15,
                'annual_20_pct': target_annual_20,
                'annual_25_pct': target_annual_25,
                'annual_30_pct': target_annual_30,
                'monthly_1_pct': target_monthly_1,
                'monthly_2_pct': target_monthly_2,
                'monthly_3_pct': target_monthly_3
            },
            
            # Regime Performance
            'regime_performance': self.regime_performance,
            
            # Sample Trades
            'sample_trades': self.trades[-10:] if len(self.trades) >= 10 else self.trades,
            
            # Compound Growth Log
            'compound_growth_log': self.compound_growth_log[-6:] if len(self.compound_growth_log) >= 6 else self.compound_growth_log
        }
        
        return results

def run_ultra_profit_backtest():
    """Run the ultra profit backtest and save results"""
    print("🚀 Ultra Profit Enhanced Strategy Backtest")
    print("=" * 50)
    
    # Initialize backtest
    backtest = UltraProfitBacktestEngine(initial_balance=10000)
    
    # Load data
    print("Loading market data...")
    data = backtest.load_data()
    print(f"Loaded {len(data)} data points ({len(data)/24:.1f} days)")
    
    # Run backtest
    results = backtest.run_backtest(data)
    
    # Display results
    print("\n🎯 ULTRA PROFIT BACKTEST RESULTS")
    print("=" * 50)
    print(f"Final Balance: ${results['final_balance']:,.2f}")
    print(f"Total Return: {results['total_return']:.2%}")
    print(f"Annual Return: {results['annual_return']:.2%}")
    print(f"Monthly Return: {results['monthly_return']:.2%}")
    print(f"Compound Growth: {results['compound_growth_factor']:.2f}x")
    print(f"Max Compound Multiplier: {results['max_compound_multiplier_used']:.2f}x")
    
    print(f"\nTrade Statistics:")
    print(f"Total Trades: {results['total_trades']}")
    print(f"Win Rate: {results['win_rate']:.1%}")
    print(f"Profit Factor: {results['profit_factor']:.2f}")
    print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
    print(f"Max Drawdown: {results['max_drawdown']:.1%}")
    
    print(f"\n🎯 Target Achievements:")
    targets = results['target_achievements']
    print(f"Annual 15%+: {'✅' if targets['annual_15_pct'] else '❌'}")
    print(f"Annual 20%+: {'✅' if targets['annual_20_pct'] else '❌'}")
    print(f"Annual 25%+: {'✅' if targets['annual_25_pct'] else '❌'}")
    print(f"Annual 30%+: {'✅' if targets['annual_30_pct'] else '❌'}")
    print(f"Monthly 2%+: {'✅' if targets['monthly_2_pct'] else '❌'}")
    print(f"Monthly 3%+: {'✅' if targets['monthly_3_pct'] else '❌'}")
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"ultra_profit_results_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\nResults saved to: {filename}")
    
    return results

if __name__ == "__main__":
    run_ultra_profit_backtest()