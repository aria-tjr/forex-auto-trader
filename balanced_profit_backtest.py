#!/usr/bin/env python3
"""
Balanced Profit Enhanced Backtest - Conservative Testing
Uses the same proven data generation as the successful final_optimized_strategy

TARGET: Achieve 10-14% annual returns (vs 7.8% baseline) through conservative enhancements
"""

import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
from balanced_profit_enhanced_strategy import BalancedProfitEnhancedStrategy

def run_balanced_backtest():
    """Run balanced backtest with proven data generation"""
    
    print("🚀 Balanced Profit Enhanced Strategy - Conservative Backtest")
    print("=" * 60)
    
    # Initialize strategy
    strategy = BalancedProfitEnhancedStrategy()
    initial_balance = 10000.0
    balance = initial_balance
    
    # Use EXACT same data generation as successful final_optimized_strategy
    np.random.seed(42)  # Same seed for consistency
    days = 365  # 1 year of data
    total_periods = days * 24
    
    print(f"📊 Generating {total_periods:,} hourly periods for {days} days")
    print("Using PROVEN data generation from final_optimized_strategy")
    
    data = []
    current_price = 45000.0
    
    # Same stress periods as successful strategy
    stress_periods = [
        {'start': 100, 'duration': 200, 'type': 'crash', 'severity': -0.8},
        {'start': 500, 'duration': 50, 'type': 'flash_crash', 'severity': -0.3},
        {'start': 1200, 'duration': 300, 'type': 'bear_market', 'severity': -0.5},
        {'start': 6000, 'duration': 100, 'type': 'correction', 'severity': -0.25},
    ]
    
    for i in range(total_periods):
        # Check stress periods (EXACT same logic)
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
                break
        
        # EXACT same base return generation
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
        
        # EXACT same OHLCV data generation
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
    
    # Run backtest with EXACT same approach as successful strategy
    position = None
    trades = []
    monthly_balances = []
    
    # Performance tracking
    peak_balance = balance
    max_drawdown = 0
    monthly_returns = []
    
    print("\nRunning backtest...")
    for i, row in df.iterrows():
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
                exit_cost = position['position_value'] * strategy.trading_costs
                net_pnl = gross_pnl - exit_cost
                
                # Update balance (NO COMPOUND MULTIPLICATION)
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
                # Calculate position size
                position_info = strategy.calculate_position_size(
                    balance, 
                    row['close'], 
                    signal['strength'], 
                    strategy.current_regime
                )
                
                # Calculate stop loss and take profit prices
                if signal['direction'] == 'BUY':
                    stop_loss_price = row['close'] * (1 - position_info['stop_loss_pct'])
                    take_profit_price = row['close'] * (1 + position_info['take_profit_pct'])
                else:  # SELL
                    stop_loss_price = row['close'] * (1 + position_info['stop_loss_pct'])
                    take_profit_price = row['close'] * (1 - position_info['take_profit_pct'])
                
                # Entry cost
                entry_cost = position_info['position_value'] * strategy.trading_costs
                
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
        
        # Track monthly performance
        if i % (24 * 30) == 0 and i > 0:  # Monthly
            month_num = i // (24 * 30)
            monthly_return = (balance - initial_balance) / initial_balance
            monthly_returns.append(monthly_return)
            monthly_balances.append(balance)
            
            print(f"Month {month_num}: ${balance:,.2f} (Return: {monthly_return:.2%})")
    
    # Close final position if exists
    if position:
        current_price = df.iloc[-1]['close']
        if position['direction'] == 'BUY':
            gross_return = (current_price - position['entry_price']) / position['entry_price']
        else:
            gross_return = (position['entry_price'] - current_price) / position['entry_price']
        
        gross_pnl = position['position_value'] * gross_return
        exit_cost = position['position_value'] * strategy.trading_costs
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
    annual_return = total_return  # 1 year of data
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
        'target_10_achieved': annual_return >= 0.10,
        'target_12_achieved': annual_return >= 0.12,
        'target_15_achieved': annual_return >= 0.15,
        'monthly_balances': monthly_balances,
        'sample_trades': trades[:10]  # First 10 trades
    }
    
    # Print results
    print("\n🎯 BALANCED PROFIT ENHANCED STRATEGY RESULTS")
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
    print(f"Annual 10%+: {'✅' if results['target_10_achieved'] else '❌'}")
    print(f"Annual 12%+: {'✅' if results['target_12_achieved'] else '❌'}")
    print(f"Annual 15%+: {'✅' if results['target_15_achieved'] else '❌'}")
    
    print(f"\n📈 Performance vs Baseline:")
    print(f"Baseline (Final Optimized): 7.8%")
    print(f"Balanced Enhanced: {annual_return:.1%}")
    improvement_pct = ((annual_return / 0.078) - 1) * 100 if annual_return > 0 else -100
    print(f"Improvement: {improvement_pct:.0f}% better")
    
    print(f"\n💰 Monthly Income Projections:")
    print(f"$10,000 account: ${monthly_return * 10000:.0f}/month, ${annual_return * 10000:.0f}/year")
    print(f"$25,000 account: ${monthly_return * 25000:.0f}/month, ${annual_return * 25000:.0f}/year")
    print(f"$50,000 account: ${monthly_return * 50000:.0f}/month, ${annual_return * 50000:.0f}/year")
    print(f"$100,000 account: ${monthly_return * 100000:.0f}/month, ${annual_return * 100000:.0f}/year")
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"balanced_enhanced_results_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\nResults saved to: {filename}")

if __name__ == "__main__":
    run_balanced_backtest() 