#!/usr/bin/env python3
"""
Profit Enhanced Backtest V2 - Test Enhanced Strategy
Uses proven data generation approach from successful final optimized strategy

FEATURES:
✅ Same data generation as 16.1% return strategy
✅ Comprehensive performance tracking
✅ Enhanced position sizing validation
✅ Compound growth monitoring
✅ Target achievement tracking
"""

import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any
from profit_enhanced_strategy_v2 import ProfitEnhancedStrategyV2

def run_profit_enhanced_backtest_v2():
    """Run enhanced backtest using proven data generation"""
    
    print("🚀 Profit Enhanced Strategy V2 - Backtest")
    print("=" * 50)
    
    # Initialize strategy
    strategy = ProfitEnhancedStrategyV2()
    initial_balance = 10000.0
    balance = initial_balance
    
    # Use proven data generation from successful strategy
    np.random.seed(42)
    days = 730  # 2 years of data
    total_periods = days * 24
    
    print(f"📊 Generating {total_periods:,} hourly periods for {days} days")
    
    data = []
    current_price = 45000.0
    
    # Same stress periods as successful strategy
    stress_periods = [
        {'start': 100, 'duration': 200, 'type': 'crash', 'severity': -0.8},
        {'start': 500, 'duration': 50, 'type': 'flash_crash', 'severity': -0.3},
        {'start': 1200, 'duration': 300, 'type': 'bear_market', 'severity': -0.5},
        {'start': 8000, 'duration': 100, 'type': 'correction', 'severity': -0.25},
        {'start': 12000, 'duration': 150, 'type': 'volatility_spike', 'severity': -0.4},
    ]
    
    for i in range(total_periods):
        # Check stress periods
        in_stress = False
        stress_factor = 0
        
        for stress in stress_periods:
            if stress['start'] <= i < stress['start'] + stress['duration']:
                in_stress = True
                progress = (i - stress['start']) / stress['duration']
                
                if stress['type'] == 'crash':
                    stress_factor = stress['severity'] * progress * 0.01
                elif stress['type'] == 'flash_crash':
                    stress_factor = stress['severity'] * 0.02 if progress < 0.1 else stress['severity'] * 0.001
                elif stress['type'] == 'bear_market':
                    stress_factor = stress['severity'] * 0.005
                elif stress['type'] == 'correction':
                    stress_factor = stress['severity'] * 0.008
                elif stress['type'] == 'volatility_spike':
                    stress_factor = stress['severity'] * 0.015
                break
        
        # Base return generation
        if in_stress:
            base_return = stress_factor + np.random.normal(-0.001, 0.02)
        else:
            base_return = np.random.normal(0.0002, 0.008)
        
        # Market cycle effects
        cycle_factor = np.sin(i / 168) * 0.001  # Weekly cycle
        total_return = base_return + cycle_factor
        
        # Limit extreme moves
        max_change = 0.15 if in_stress else 0.08
        total_return = np.clip(total_return, -max_change, max_change)
        
        new_price = current_price * (1 + total_return)
        new_price = max(new_price, 1000)
        
        # OHLCV data generation
        volatility_range = abs(total_return) * 2 + 0.005
        high = new_price * (1 + volatility_range * 0.5)
        low = new_price * (1 - volatility_range * 0.5)
        open_price = current_price if i == 0 else data[-1]['close']
        
        high = max(high, open_price, new_price)
        low = min(low, open_price, new_price)
        
        volume = int(1000000 * (3 if in_stress else 1) * np.random.uniform(0.5, 2))
        timestamp = datetime.now() - timedelta(days=days) + timedelta(hours=i)
        
        data.append({
            'timestamp': timestamp,
            'open': round(open_price, 2),
            'high': round(high, 2),
            'low': round(low, 2),
            'close': round(new_price, 2),
            'volume': volume,
            'stress_period': in_stress
        })
        
        current_price = new_price
    
    df = pd.DataFrame(data)
    print(f"Generated data: {len(df)} bars, Price range: ${df['close'].min():.0f} - ${df['close'].max():.0f}")
    
    # Run backtest
    position = None
    trades = []
    daily_balances = []
    monthly_balances = []
    
    # Performance tracking
    peak_balance = balance
    max_drawdown = 0
    monthly_returns = []
    
    # Set strategy balance
    strategy.current_balance = balance
    
    print("\nRunning backtest...")
    for i, row in df.iterrows():
        # Update strategy balance
        strategy.current_balance = balance
        
        # Track peak and drawdown
        if balance > peak_balance:
            peak_balance = balance
        current_drawdown = (peak_balance - balance) / peak_balance
        max_drawdown = max(max_drawdown, current_drawdown)
        
        # Prepare price data
        price_data = {
            'timestamp': row['timestamp'],
            'open': row['open'],
            'high': row['high'],
            'low': row['low'],
            'close': row['close'],
            'volume': row['volume'],
            'stress_period': row['stress_period']
        }
        
        # Check existing position
        if position:
            current_price = row['close']
            
            # Check exit conditions
            exit_signal = None
            if position['direction'] == 'BUY':
                if current_price <= position['stop_loss']:
                    exit_signal = 'Stop Loss'
                elif current_price >= position['take_profit']:
                    exit_signal = 'Take Profit'
            else:  # SELL
                if current_price >= position['stop_loss']:
                    exit_signal = 'Stop Loss'
                elif current_price <= position['take_profit']:
                    exit_signal = 'Take Profit'
            
            # Time-based exit (48 hours)
            if i - position['entry_bar'] >= 48:
                exit_signal = 'Time Exit'
            
            # Close position if exit triggered
            if exit_signal:
                if position['direction'] == 'BUY':
                    gross_return = (current_price - position['entry_price']) / position['entry_price']
                else:
                    gross_return = (position['entry_price'] - current_price) / position['entry_price']
                
                gross_pnl = position['position_value'] * gross_return
                exit_cost = position['position_value'] * 0.003  # 0.3% exit cost
                net_pnl = gross_pnl - exit_cost
                
                # Update balance
                balance += position['position_value'] + net_pnl
                
                # Record trade
                trade_record = {
                    'entry_time': position['entry_time'],
                    'exit_time': row['timestamp'],
                    'direction': position['direction'],
                    'entry_price': position['entry_price'],
                    'exit_price': current_price,
                    'position_value': position['position_value'],
                    'gross_return': gross_return,
                    'net_pnl': net_pnl,
                    'exit_reason': exit_signal,
                    'regime': position['regime'],
                    'compound_multiplier': position['compound_multiplier'],
                    'hours_held': i - position['entry_bar']
                }
                trades.append(trade_record)
                position = None
        
        # Generate new signal if no position
        if not position:
            signal = strategy.add_price_data(price_data, i)
            
            if signal['direction'] != 'NEUTRAL':
                # Execute trade
                position_value = signal.get('position_size', 0)
                entry_cost = position_value * 0.003  # 0.3% entry cost
                
                # Check if we have enough balance
                if position_value + entry_cost <= balance:
                    # Deduct costs
                    balance -= entry_cost
                    
                    # Calculate stops and targets
                    stop_loss_pct = signal.get('stop_loss_pct', 1.8) / 100
                    profit_target_pct = signal.get('profit_target_pct', 3.0) / 100
                    
                    if signal['direction'] == 'BUY':
                        stop_loss = row['close'] * (1 - stop_loss_pct)
                        take_profit = row['close'] * (1 + profit_target_pct)
                    else:
                        stop_loss = row['close'] * (1 + stop_loss_pct)
                        take_profit = row['close'] * (1 - profit_target_pct)
                    
                    position = {
                        'direction': signal['direction'],
                        'entry_time': row['timestamp'],
                        'entry_bar': i,
                        'entry_price': row['close'],
                        'position_value': position_value,
                        'stop_loss': stop_loss,
                        'take_profit': take_profit,
                        'regime': signal.get('regime', 'UNKNOWN'),
                        'compound_multiplier': signal.get('compound_multiplier', 1.0)
                    }
        
        # Track daily balance (every 24 hours)
        if i % 24 == 0:
            daily_balances.append({
                'day': i // 24,
                'balance': balance,
                'drawdown': current_drawdown
            })
        
        # Track monthly performance (every 30 days)
        if i % (24 * 30) == 0 and i > 0:
            monthly_return = (balance - initial_balance) / initial_balance
            monthly_balances.append(balance)
            monthly_returns.append(monthly_return)
            
            print(f"Month {len(monthly_returns)}: ${balance:,.2f} "
                  f"(Return: {monthly_return:.2%}, "
                  f"Compound: {strategy.compound_manager.get_risk_multiplier(balance):.2f}x)")
    
    # Close any remaining position
    if position:
        final_price = df.iloc[-1]['close']
        if position['direction'] == 'BUY':
            gross_return = (final_price - position['entry_price']) / position['entry_price']
        else:
            gross_return = (position['entry_price'] - final_price) / position['entry_price']
        
        gross_pnl = position['position_value'] * gross_return
        net_pnl = gross_pnl  # No exit cost for final close
        balance += position['position_value'] + net_pnl
        
        trade_record = {
            'entry_time': position['entry_time'],
            'exit_time': df.iloc[-1]['timestamp'],
            'direction': position['direction'],
            'entry_price': position['entry_price'],
            'exit_price': final_price,
            'position_value': position['position_value'],
            'gross_return': gross_return,
            'net_pnl': net_pnl,
            'exit_reason': 'Backtest End',
            'regime': position['regime'],
            'compound_multiplier': position['compound_multiplier'],
            'hours_held': len(df) - position['entry_bar']
        }
        trades.append(trade_record)
    
    # Calculate final metrics
    total_return = (balance - initial_balance) / initial_balance
    annual_return = (1 + total_return) ** (365 / days) - 1
    monthly_return = annual_return / 12
    
    # Trade statistics
    if trades:
        winning_trades = [t for t in trades if t['net_pnl'] > 0]
        losing_trades = [t for t in trades if t['net_pnl'] <= 0]
        win_rate = len(winning_trades) / len(trades)
        
        avg_win = np.mean([t['net_pnl'] for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t['net_pnl'] for t in losing_trades]) if losing_trades else 0
        
        profit_factor = abs(sum(t['net_pnl'] for t in winning_trades) / 
                           sum(t['net_pnl'] for t in losing_trades)) if losing_trades else float('inf')
    else:
        win_rate = 0
        avg_win = 0
        avg_loss = 0
        profit_factor = 0
    
    # Calculate Sharpe ratio
    if len(daily_balances) > 1:
        daily_returns = []
        for i in range(1, len(daily_balances)):
            prev_balance = daily_balances[i-1]['balance']
            curr_balance = daily_balances[i]['balance']
            daily_return = (curr_balance - prev_balance) / prev_balance
            daily_returns.append(daily_return)
        
        volatility = np.std(daily_returns) * np.sqrt(365)
        sharpe_ratio = annual_return / volatility if volatility > 0 else 0
    else:
        volatility = 0
        sharpe_ratio = 0
    
    # Compound growth analysis
    max_compound_multiplier = max([strategy.compound_manager.get_risk_multiplier(mb) for mb in monthly_balances]) if monthly_balances else 1.0
    
    # Target achievements
    target_achievements = {
        'annual_15_pct': annual_return >= 0.15,
        'annual_20_pct': annual_return >= 0.20,
        'annual_25_pct': annual_return >= 0.25,
        'annual_30_pct': annual_return >= 0.30,
        'monthly_1_5_pct': monthly_return >= 0.015,
        'monthly_2_pct': monthly_return >= 0.02,
        'monthly_2_5_pct': monthly_return >= 0.025
    }
    
    results = {
        'final_balance': balance,
        'total_return': total_return,
        'annual_return': annual_return,
        'monthly_return': monthly_return,
        'total_trades': len(trades),
        'winning_trades': len(winning_trades) if trades else 0,
        'losing_trades': len(losing_trades) if trades else 0,
        'win_rate': win_rate,
        'profit_factor': profit_factor,
        'avg_win': avg_win,
        'avg_loss': avg_loss,
        'max_drawdown': max_drawdown,
        'sharpe_ratio': sharpe_ratio,
        'volatility': volatility,
        'max_compound_multiplier': max_compound_multiplier,
        'target_achievements': target_achievements,
        'sample_trades': trades[-10:] if len(trades) >= 10 else trades
    }
    
    # Display results
    print("\n🎯 PROFIT ENHANCED STRATEGY V2 RESULTS")
    print("=" * 50)
    print(f"Final Balance: ${results['final_balance']:,.2f}")
    print(f"Total Return: {results['total_return']:.2%}")
    print(f"Annual Return: {results['annual_return']:.2%}")
    print(f"Monthly Return: {results['monthly_return']:.2%}")
    print(f"Max Compound Multiplier: {results['max_compound_multiplier']:.2f}x")
    
    print(f"\nTrade Statistics:")
    print(f"Total Trades: {results['total_trades']}")
    print(f"Win Rate: {results['win_rate']:.1%}")
    print(f"Profit Factor: {results['profit_factor']:.2f}")
    print(f"Average Win: ${results['avg_win']:.2f}")
    print(f"Average Loss: ${results['avg_loss']:.2f}")
    print(f"Max Drawdown: {results['max_drawdown']:.1%}")
    print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
    
    print(f"\n🎯 Target Achievements:")
    targets = results['target_achievements']
    print(f"Annual 15%+: {'✅' if targets['annual_15_pct'] else '❌'}")
    print(f"Annual 20%+: {'✅' if targets['annual_20_pct'] else '❌'}")
    print(f"Annual 25%+: {'✅' if targets['annual_25_pct'] else '❌'}")
    print(f"Annual 30%+: {'✅' if targets['annual_30_pct'] else '❌'}")
    print(f"Monthly 1.5%+: {'✅' if targets['monthly_1_5_pct'] else '❌'}")
    print(f"Monthly 2.0%+: {'✅' if targets['monthly_2_pct'] else '❌'}")
    print(f"Monthly 2.5%+: {'✅' if targets['monthly_2_5_pct'] else '❌'}")
    
    # Performance comparison with baseline
    baseline_annual = 0.078  # 7.8% from final optimized strategy
    improvement = (annual_return - baseline_annual) / baseline_annual
    print(f"\n📈 Performance vs Baseline:")
    print(f"Baseline (Final Optimized): {baseline_annual:.1%}")
    print(f"Enhanced Strategy V2: {annual_return:.1%}")
    print(f"Improvement: {improvement:.1%}")
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"profit_enhanced_v2_results_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\nResults saved to: {filename}")
    
    return results

if __name__ == "__main__":
    run_profit_enhanced_backtest_v2() 