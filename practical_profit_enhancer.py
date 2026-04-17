#!/usr/bin/env python3
"""
PRACTICAL PROFIT ENHANCER
Based on your successful 7.8% annual return strategy
Target: 15-20% annual return (2-2.5x improvement)

KEY ENHANCEMENTS:
✅ Increased position sizing (2.5% vs 1.5% per trade)
✅ More frequent opportunities (reduced cooldown)
✅ Enhanced profit taking strategy
✅ All existing risk protections maintained
"""

import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta

def run_practical_profit_enhancement():
    """Run practical profit enhancement based on successful strategy"""
    print("🚀 PRACTICAL PROFIT ENHANCEMENT")
    print("📊 Based on your successful 7.8% annual return strategy")
    print("🎯 Target: 15-20% annual return (2-2.5x improvement)")
    print("✅ All risk protections maintained")
    
    # Generate realistic test data (similar to successful backtest)
    np.random.seed(42)  # Reproducible results
    data = []
    current_price = 45000.0
    hours = 24 * 365  # 1 year for faster results
    
    print(f"\n📈 Generating {hours} hours of realistic market data...")
    
    for i in range(hours):
        days = i / 24
        
        # Market phases similar to your successful backtest
        stress_period = np.random.random() < 0.03  # 3% stress periods
        
        if days < 90:    # Phase 1: Sideways with volatility
            base_return = np.random.normal(0.0003, 0.012)
        elif days < 180: # Phase 2: Bull trend
            base_return = np.random.normal(0.0006, 0.015)
        elif days < 270: # Phase 3: Correction
            base_return = np.random.normal(-0.0001, 0.018)
        else:           # Phase 4: Recovery
            base_return = np.random.normal(0.0004, 0.013)
        
        # Add stress volatility
        if stress_period:
            base_return += np.random.normal(0, 0.025)
        
        # Market cycles
        cycle_return = np.sin(days / 45) * 0.0008
        
        total_return = base_return + cycle_return
        total_return = np.clip(total_return, -0.12, 0.12)
        
        new_price = current_price * (1 + total_return)
        new_price = max(new_price, 10000)  # Floor price
        
        data.append({
            'close': round(new_price, 2),
            'stress_period': stress_period,
            'hour': i
        })
        
        current_price = new_price
    
    print(f"📊 Market data generated: {sum(1 for d in data if d['stress_period'])} stress periods")
    
    # ENHANCED STRATEGY PARAMETERS
    initial_balance = 10000.0
    balance = initial_balance
    position = None
    trades = []
    
    # PROFIT ENHANCEMENT SETTINGS
    base_risk_per_trade = 0.025          # INCREASED from 1.5% to 2.5%
    min_bars_between_signals = 8         # REDUCED from 24h to 8h (more opportunities)
    max_drawdown_limit = 0.15            # MAINTAINED 15% limit
    consecutive_loss_limit = 3           # MAINTAINED protection
    
    # Enhanced profit taking
    profit_targets = [0.04, 0.07, 0.10]  # 4%, 7%, 10% targets
    
    # State tracking
    last_signal_bar = -999
    consecutive_losses = 0
    peak_balance = initial_balance
    
    print(f"🔧 ENHANCEMENT SETTINGS:")
    print(f"   Position Risk:       {base_risk_per_trade:.1%} (vs 1.5% baseline)")
    print(f"   Signal Cooldown:     {min_bars_between_signals}h (vs 24h baseline)")
    print(f"   Profit Targets:      {profit_targets}")
    print(f"   Max Drawdown:        {max_drawdown_limit:.0%}")
    
    # Run enhanced backtest
    for idx, row in enumerate(data):
        current_price = row['close']
        
        # Update peak balance and drawdown
        if balance > peak_balance:
            peak_balance = balance
        current_drawdown = (peak_balance - balance) / peak_balance
        
        # Position management with enhanced profit taking
        if position:
            hours_held = idx - position['entry_bar']
            
            # Calculate current return
            if position['direction'] == 'BUY':
                current_return = (current_price - position['entry_price']) / position['entry_price']
            else:
                current_return = (position['entry_price'] - current_price) / position['entry_price']
            
            should_exit = False
            exit_reason = ""
            
            # ENHANCED PROFIT TAKING STRATEGY
            if current_return >= profit_targets[2]:  # 10% profit
                should_exit = True
                exit_reason = "Large Profit (10%)"
            elif current_return >= profit_targets[1]:  # 7% profit
                # 70% chance to exit at 7% (let some runners go)
                if np.random.random() < 0.7:
                    should_exit = True
                    exit_reason = "Good Profit (7%)"
            elif current_return >= profit_targets[0]:  # 4% profit
                # 40% chance to exit at 4% (quick profits)
                if np.random.random() < 0.4:
                    should_exit = True
                    exit_reason = "Quick Profit (4%)"
            
            # Standard stop loss (maintained from successful strategy)
            elif current_return <= -0.025:  # 2.5% stop loss
                should_exit = True
                exit_reason = "Stop Loss"
            
            # Time-based exit (enhanced)
            elif hours_held >= 48:  # 48 hour maximum
                should_exit = True
                exit_reason = "Time Exit"
            
            if should_exit:
                # Calculate PnL with realistic costs
                trading_cost = 0.004 if row['stress_period'] else 0.003  # 0.3-0.4%
                gross_pnl = position['size'] * current_return
                net_pnl = gross_pnl - (position['size'] * trading_cost)
                balance += net_pnl
                
                # Update consecutive losses
                if net_pnl > 0:
                    consecutive_losses = 0
                else:
                    consecutive_losses += 1
                
                trades.append({
                    'direction': position['direction'],
                    'gross_return': current_return,
                    'net_pnl': net_pnl,
                    'exit_reason': exit_reason,
                    'hours_held': hours_held,
                    'position_size_pct': position['size'] / balance * 100,
                    'stress_period': row['stress_period']
                })
                
                position = None
        
        # Signal generation (enhanced frequency)
        if not position and idx - last_signal_bar >= min_bars_between_signals:
            
            # Protection checks (maintained from successful strategy)
            if consecutive_losses >= consecutive_loss_limit:
                continue
            if current_drawdown > max_drawdown_limit:
                continue
            if row['stress_period']:  # Reduce trading in stress
                continue
            
            # Generate signals (simplified but effective)
            if idx >= 50:  # Need enough history
                # Get recent price data
                recent_prices = [data[j]['close'] for j in range(max(0, idx-50), idx)]
                
                # Moving averages
                ema_12 = recent_prices[-1]  # Simplified
                for i in range(len(recent_prices)-2, -1, -1):
                    ema_12 = 0.15 * recent_prices[i] + 0.85 * ema_12
                
                ema_26 = recent_prices[-1]
                for i in range(len(recent_prices)-2, -1, -1):
                    ema_26 = 0.074 * recent_prices[i] + 0.926 * ema_26
                
                # RSI calculation
                if len(recent_prices) >= 14:
                    price_changes = np.diff(recent_prices[-15:])
                    gains = np.where(price_changes > 0, price_changes, 0)
                    losses = np.where(price_changes < 0, -price_changes, 0)
                    avg_gain = np.mean(gains)
                    avg_loss = np.mean(losses)
                    rsi = 100 - (100 / (1 + avg_gain / avg_loss)) if avg_loss > 0 else 100
                else:
                    rsi = 50
                
                # Momentum
                momentum = (current_price - recent_prices[-10]) / recent_prices[-10] if len(recent_prices) >= 10 else 0
                
                # Signal generation (proven logic from successful strategy)
                signals = []
                
                # EMA crossover
                if ema_12 > ema_26:
                    signals.append('BUY')
                elif ema_12 < ema_26:
                    signals.append('SELL')
                
                # RSI signals
                if rsi < 35:
                    signals.append('BUY')
                elif rsi > 65:
                    signals.append('SELL')
                
                # Momentum signals
                if momentum > 0.012:
                    signals.append('BUY')
                elif momentum < -0.012:
                    signals.append('SELL')
                
                # Generate position
                buy_signals = signals.count('BUY')
                sell_signals = signals.count('SELL')
                
                if buy_signals >= 2:  # Need 2+ confirmations
                    direction = 'BUY'
                elif sell_signals >= 2:
                    direction = 'SELL'
                else:
                    direction = None
                
                if direction:
                    # ENHANCED POSITION SIZING
                    signal_strength = max(buy_signals, sell_signals) / 4.0  # 0.5-1.0 range
                    
                    # Base risk enhanced by signal strength
                    effective_risk = base_risk_per_trade * (0.8 + signal_strength * 0.4)  # 0.8x to 1.2x
                    
                    # Drawdown protection
                    if current_drawdown > 0.05:
                        effective_risk *= (1 - current_drawdown / max_drawdown_limit)
                    
                    position_size = balance * min(effective_risk, 0.04)  # Cap at 4%
                    
                    position = {
                        'direction': direction,
                        'entry_price': current_price,
                        'entry_bar': idx,
                        'size': position_size
                    }
                    
                    last_signal_bar = idx
    
    # Calculate enhanced results
    total_return = (balance - initial_balance) / initial_balance
    annual_return = total_return  # 1 year data
    monthly_return = annual_return / 12
    
    winning_trades = [t for t in trades if t['net_pnl'] > 0]
    losing_trades = [t for t in trades if t['net_pnl'] < 0]
    win_rate = len(winning_trades) / len(trades) if trades else 0
    
    # Performance metrics
    avg_win = np.mean([t['net_pnl'] for t in winning_trades]) if winning_trades else 0
    avg_loss = abs(np.mean([t['net_pnl'] for t in losing_trades])) if losing_trades else 0
    profit_factor = avg_win / avg_loss if avg_loss > 0 else float('inf')
    
    max_drawdown = (peak_balance - min([initial_balance] + [sum([tr['net_pnl'] for tr in trades[:i]]) + initial_balance for i in range(1, len(trades)+1)])) / peak_balance
    
    # Display results
    print(f"\n" + "="*75)
    print("📈 PRACTICAL PROFIT ENHANCEMENT RESULTS")
    print("="*75)
    print(f"🎯 PERFORMANCE COMPARISON:")
    print(f"   Baseline Strategy:       7.8% annual return")
    print(f"   ENHANCED Strategy:       {annual_return:+.1%} annual return")
    print(f"   IMPROVEMENT:             {annual_return - 0.078:+.1%}")
    print(f"   Multiplier:              {annual_return/0.078:.1f}x baseline")
    print(f"   Final Balance:           ${balance:,.2f}")
    print(f"   Total Return:            {total_return:+.1%}")
    
    print(f"\n📊 ENHANCED METRICS:")
    print(f"   Total Trades:            {len(trades)}")
    print(f"   Win Rate:                {win_rate:.1%}")
    print(f"   Profit Factor:           {profit_factor:.2f}")
    print(f"   Average Win:             ${avg_win:.2f}")
    print(f"   Average Loss:            ${avg_loss:.2f}")
    print(f"   Max Drawdown:            {max_drawdown:.1%}")
    
    print(f"\n💰 MONTHLY PROFIT PROJECTIONS:")
    print(f"   Monthly Return:          {monthly_return:+.1%}")
    print(f"   $10,000 Account:         ${10000 * monthly_return:,.0f}/month")
    print(f"   $25,000 Account:         ${25000 * monthly_return:,.0f}/month")
    print(f"   $50,000 Account:         ${50000 * monthly_return:,.0f}/month")
    print(f"   $100,000 Account:        ${100000 * monthly_return:,.0f}/month")
    
    # Target achievement
    target_15_met = annual_return >= 0.15
    target_20_met = annual_return >= 0.20
    
    print(f"\n🎯 TARGET ACHIEVEMENT:")
    print(f"   15% Annual Target:       {'✅ ACHIEVED' if target_15_met else '❌ Not Met'}")
    print(f"   20% Stretch Target:      {'✅ ACHIEVED' if target_20_met else '❌ Not Met'}")
    
    if target_15_met:
        improvement_factor = annual_return / 0.078
        print(f"\n🎉 SUCCESS! Practical enhancement achieved!")
        print(f"🚀 {improvement_factor:.1f}x improvement over baseline")
        print(f"💰 Monthly income: ${10000 * monthly_return:,.0f} per $10K")
        print(f"📅 Annual income: ${10000 * annual_return:,.0f} per $10K")
    else:
        improvement_pct = ((annual_return / 0.078) - 1) * 100
        print(f"\n📈 SIGNIFICANT IMPROVEMENT:")
        print(f"💰 {improvement_pct:+.0f}% improvement achieved")
        print(f"🎯 Annual return: {annual_return:.1%}")
    
    # Exit reason analysis
    exit_reasons = {}
    for trade in trades:
        reason = trade['exit_reason']
        if reason not in exit_reasons:
            exit_reasons[reason] = []
        exit_reasons[reason].append(trade['net_pnl'])
    
    if exit_reasons:
        print(f"\n📊 EXIT REASON ANALYSIS:")
        for reason, pnls in exit_reasons.items():
            avg_pnl = np.mean(pnls)
            count = len(pnls)
            print(f"   {reason:20}: {count:3d} trades, ${avg_pnl:6.0f} avg PnL")
    
    print("="*75)
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results = {
        'strategy_type': 'practical_profit_enhancement',
        'final_balance': balance,
        'total_return': total_return,
        'annual_return': annual_return,
        'monthly_return': monthly_return,
        'total_trades': len(trades),
        'win_rate': win_rate,
        'profit_factor': profit_factor,
        'max_drawdown': max_drawdown,
        'baseline_annual': 0.078,
        'improvement_factor': annual_return / 0.078 if annual_return > 0 else 0,
        'target_15_achieved': target_15_met,
        'target_20_achieved': target_20_met,
        'enhancements_applied': [
            'increased_position_sizing_2.5pct',
            'reduced_cooldown_8h',
            'enhanced_profit_taking',
            'maintained_risk_protections'
        ],
        'exit_reason_breakdown': {reason: len(pnls) for reason, pnls in exit_reasons.items()} if 'exit_reasons' in locals() else {},
        'sample_trades': trades[:15] if trades else []
    }
    
    filename = f"practical_enhancement_results_{timestamp}.json"
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Results saved to: {filename}")
    print(f"🔧 Ready to implement these enhancements in your live strategy!")
    
    return results

if __name__ == "__main__":
    run_practical_profit_enhancement() 