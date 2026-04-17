#!/usr/bin/env python3
"""
Conservative Enhanced Backtest - EXACT Same Approach as Successful Strategy
Uses proven final_optimized_strategy backtest with only tiny changes

TARGET: Achieve 9-11% annual returns (vs 7.8% baseline) through minimal conservative enhancements
"""

import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
from conservative_enhanced_strategy import ConservativeEnhancedStrategy

def run_conservative_backtest():
    """Run conservative backtest using EXACT same approach as successful strategy"""
    
    print("🎯 Conservative Enhanced Strategy - Minimal Changes")
    print("=" * 50)
    print("Based EXACTLY on proven final_optimized_strategy.py")
    print("Only changes: 1.5%→1.8% risk, 0.60→0.58 signal threshold")
    
    # Initialize strategy
    strategy = ConservativeEnhancedStrategy()
    initial_balance = 10000.0
    balance = initial_balance
    
    # Use EXACT SAME data generation as successful final_optimized_strategy
    np.random.seed(42)  # Same seed
    days = 730  # Same 2 years
    total_periods = days * 24
    
    print(f"📊 Generating {total_periods:,} hourly periods for {days} days")
    print("Using EXACT data generation from successful strategy")
    
    data = []
    current_price = 45000.0
    
    # EXACT same stress periods as successful strategy
    stress_periods = [
        {'start': 100, 'duration': 200, 'type': 'crash', 'severity': -0.8},
        {'start': 500, 'duration': 50, 'type': 'flash_crash', 'severity': -0.3},
        {'start': 1200, 'duration': 300, 'type': 'bear_market', 'severity': -0.5},
    ]
    
    for i in range(total_periods):
        # EXACT same stress period logic
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
                break
        
        # EXACT same return generation
        if in_stress:
            base_return = stress_factor + np.random.normal(-0.001, 0.02)
        else:
            base_return = np.random.normal(0.0002, 0.008)
        
        cycle_factor = np.sin(i / 168) * 0.001
        total_return = base_return + cycle_factor
        
        # EXACT same limits
        max_change = 0.15 if in_stress else 0.08
        total_return = np.clip(total_return, -max_change, max_change)
        
        new_price = current_price * (1 + total_return)
        new_price = max(new_price, 1000)
        
        # EXACT same OHLCV generation
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
    
    # Run backtest with EXACT same logic as successful strategy
    position = None
    trades = []
    
    # Performance tracking
    peak_balance = balance
    max_drawdown = 0
    
    print("\nRunning backtest...")
    for i, row in df.iterrows():
        # Track peak and drawdown
        if balance > peak_balance:
            peak_balance = balance
        current_drawdown = (peak_balance - balance) / peak_balance
        max_drawdown = max(max_drawdown, current_drawdown)
        
        # Prepare price data - simplified format for strategy
        price_data = {
            'timestamp': row['timestamp'],
            'close': row['close'],
            'stress_period': row['stress_period']
        }
        
        # Check existing position
        if position:
            current_price = row['close']
            
            # Check exit conditions (EXACT same as successful strategy)
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
            
            # Time-based exit (48 hours - same as successful strategy)
            if i - position['entry_bar'] >= 48:
                exit_signal = 'Time Exit'
            
            # Close position if exit triggered
            if exit_signal:
                if position['direction'] == 'BUY':
                    gross_return = (current_price - position['entry_price']) / position['entry_price']
                else:
                    gross_return = (position['entry_price'] - current_price) / position['entry_price']
                
                gross_pnl = position['position_value'] * gross_return
                exit_cost = position['position_value'] * strategy.trading_costs['total_per_trade']
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
                    'hours_held': i - position['entry_bar'],
                    'stress_period': row['stress_period']
                }
                trades.append(trade_record)
                position = None
        
        # Generate new signal if no position
        if not position:
            signal = strategy.add_price_data(price_data, i)
            
            if signal['direction'] != 'NEUTRAL':
                # Calculate stop loss and take profit (EXACT same logic)
                stop_loss_pct = 0.02  # 2% stop loss (same as successful strategy)
                take_profit_pct = 0.03  # 3% take profit (same as successful strategy)
                
                if signal['direction'] == 'BUY':
                    stop_loss_price = row['close'] * (1 - stop_loss_pct)
                    take_profit_price = row['close'] * (1 + take_profit_pct)
                else:  # SELL
                    stop_loss_price = row['close'] * (1 + stop_loss_pct)
                    take_profit_price = row['close'] * (1 - take_profit_pct)
                
                # Calculate position size using strategy method
                position_info = strategy.calculate_position_size(
                    balance, 
                    row['close'], 
                    stop_loss_price,
                    signal['strength']
                )
                
                # Entry cost
                entry_cost = position_info['position_value'] * strategy.trading_costs['total_per_trade']
                
                # Update balance (subtract position value and entry cost)
                balance -= position_info['position_value'] + entry_cost
                
                # Create position
                position = {
                    'entry_time': row['timestamp'],
                    'entry_bar': i,
                    'direction': signal['direction'],
                    'entry_price': row['close'],
                    'position_value': position_info['position_value'],
                    'stop_loss': stop_loss_price,
                    'take_profit': take_profit_price,
                    'regime': strategy.current_regime,
                    'signal_strength': signal['strength']
                }
        
        # Progress update every 1000 bars
        if i % 1000 == 0 and i > 0:
            current_return = (balance - initial_balance) / initial_balance
            print(f"Progress: {i:,}/{len(df):,} bars, Balance: ${balance:,.0f} ({current_return:.1%})")
    
    # Close final position if exists
    if position:
        current_price = df.iloc[-1]['close']
        if position['direction'] == 'BUY':
            gross_return = (current_price - position['entry_price']) / position['entry_price']
        else:
            gross_return = (position['entry_price'] - current_price) / position['entry_price']
        
        gross_pnl = position['position_value'] * gross_return
        exit_cost = position['position_value'] * strategy.trading_costs['total_per_trade']
        net_pnl = gross_pnl - exit_cost
        balance += position['position_value'] + net_pnl
        
        trade_record = {
            'entry_time': position['entry_time'],
            'exit_time': df.iloc[-1]['timestamp'],
            'direction': position['direction'],
            'entry_price': position['entry_price'],
            'exit_price': current_price,
            'position_value': position['position_value'],
            'gross_return': gross_return,
            'net_pnl': net_pnl,
            'exit_reason': 'Backtest End',
            'regime': position['regime'],
            'hours_held': len(df) - position['entry_bar'],
            'stress_period': df.iloc[-1]['stress_period']
        }
        trades.append(trade_record)
    
    # Calculate performance metrics
    final_balance = balance
    total_return = (final_balance - initial_balance) / initial_balance
    annual_return = total_return / (days / 365)  # Annualized
    monthly_return = annual_return / 12
    
    # Trade statistics
    winning_trades = [t for t in trades if t['net_pnl'] > 0]
    losing_trades = [t for t in trades if t['net_pnl'] <= 0]
    
    win_rate = len(winning_trades) / len(trades) if trades else 0
    
    avg_win = np.mean([t['net_pnl'] for t in winning_trades]) if winning_trades else 0
    avg_loss = np.mean([t['net_pnl'] for t in losing_trades]) if losing_trades else 0
    
    profit_factor = abs(sum(t['net_pnl'] for t in winning_trades) / sum(t['net_pnl'] for t in losing_trades)) if losing_trades else float('inf')
    
    # Results
    results = {
        'final_balance': final_balance,
        'total_return': total_return,
        'annual_return': annual_return,
        'monthly_return': monthly_return,
        'total_trades': len(trades),
        'winning_trades': len(winning_trades),
        'losing_trades': len(losing_trades),
        'win_rate': win_rate,
        'profit_factor': profit_factor,
        'avg_win': avg_win,
        'avg_loss': avg_loss,
        'max_drawdown': max_drawdown,
        'baseline_annual': 0.078,  # 7.8% baseline
        'improvement_factor': annual_return / 0.078 if annual_return > 0 else 0,
        'target_9_achieved': annual_return >= 0.09,
        'target_10_achieved': annual_return >= 0.10,
        'target_12_achieved': annual_return >= 0.12,
        'sample_trades': trades[:10]  # First 10 trades
    }
    
    # Print results
    print("\n🎯 CONSERVATIVE ENHANCED STRATEGY RESULTS")
    print("=" * 50)
    print(f"Final Balance: ${final_balance:,.2f}")
    print(f"Total Return: {total_return:.2%}")
    print(f"Annual Return: {annual_return:.2%}")
    print(f"Monthly Return: {monthly_return:.2%}")
    
    print(f"\nTrade Statistics:")
    print(f"Total Trades: {len(trades)}")
    print(f"Win Rate: {win_rate:.1%}")
    print(f"Profit Factor: {profit_factor:.2f}")
    print(f"Average Win: ${avg_win:.2f}")
    print(f"Average Loss: ${avg_loss:.2f}")
    print(f"Max Drawdown: {max_drawdown:.1%}")
    
    print(f"\n🎯 Target Achievements:")
    print(f"Annual 9%+: {'✅' if results['target_9_achieved'] else '❌'}")
    print(f"Annual 10%+: {'✅' if results['target_10_achieved'] else '❌'}")
    print(f"Annual 12%+: {'✅' if results['target_12_achieved'] else '❌'}")
    
    print(f"\n📈 Performance vs Baseline:")
    print(f"Baseline (Final Optimized): 7.8%")
    print(f"Conservative Enhanced: {annual_return:.1%}")
    improvement_pct = ((annual_return / 0.078) - 1) * 100 if annual_return > 0 else -100
    print(f"Improvement: {improvement_pct:.0f}% better")
    
    print(f"\n💰 Monthly Income Projections:")
    print(f"$10,000 account: ${monthly_return * 10000:.0f}/month, ${annual_return * 10000:.0f}/year")
    print(f"$25,000 account: ${monthly_return * 25000:.0f}/month, ${annual_return * 25000:.0f}/year")
    print(f"$50,000 account: ${monthly_return * 50000:.0f}/month, ${annual_return * 50000:.0f}/year")
    print(f"$100,000 account: ${monthly_return * 100000:.0f}/month, ${annual_return * 100000:.0f}/year")
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"conservative_enhanced_results_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\nResults saved to: {filename}")

if __name__ == "__main__":
    run_conservative_backtest() 