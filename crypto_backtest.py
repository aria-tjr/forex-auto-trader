#!/usr/bin/env python3
"""
Crypto Backtesting Engine
Professional backtesting system for the simplified robust strategy

Features:
- Realistic crypto price simulation
- Complete trade simulation
- Risk management integration
- Performance metrics
- Detailed reporting
"""

import sys
import os
import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging

# Import our modules
from simplified_robust_strategy import SimplifiedRobustStrategy, PriceData, Signal
from crypto_risk_manager import CryptoRiskManager

class CryptoDataGenerator:
    """Generate realistic crypto price data for backtesting"""
    
    def __init__(self, symbol: str = "BTCUSDT", initial_price: float = 45000.0):
        self.symbol = symbol
        self.initial_price = initial_price
        
    def generate_realistic_crypto_data(
        self, 
        days: int = 365, 
        timeframe_minutes: int = 15
    ) -> pd.DataFrame:
        """Generate realistic crypto price data with proper volatility"""
        
        # Calculate number of periods
        periods_per_day = 24 * 60 // timeframe_minutes
        total_periods = days * periods_per_day
        
        # Create timestamp index
        start_date = datetime.now() - timedelta(days=days)
        timestamps = [start_date + timedelta(minutes=i * timeframe_minutes) 
                     for i in range(total_periods)]
        
        # Generate realistic crypto price movements
        np.random.seed(42)  # For reproducible results
        
        # Crypto-specific parameters (higher volatility)
        daily_volatility = 0.04  # 4% daily volatility (realistic for crypto)
        period_volatility = daily_volatility / np.sqrt(periods_per_day)
        
        # Generate price returns with trends and volatility
        returns = []
        trend_change_prob = 0.01  # 1% chance of trend change per period
        current_trend = 0.0002  # Start with slight upward trend
        
        for i in range(total_periods):
            # Occasionally change trend direction
            if np.random.random() < trend_change_prob:
                current_trend = np.random.normal(0, 0.0003)
            
            # Add some mean reversion
            mean_reversion = -0.1 * current_trend if abs(current_trend) > 0.0005 else 0
            
            # Generate return with trend, volatility, and mean reversion
            period_return = (
                current_trend + 
                mean_reversion +
                np.random.normal(0, period_volatility)
            )
            
            returns.append(period_return)
        
        # Convert returns to prices
        prices = [self.initial_price]
        for ret in returns:
            new_price = prices[-1] * (1 + ret)
            prices.append(new_price)
        
        prices = prices[1:]  # Remove initial price
        
        # Generate OHLCV data
        data = []
        for i, (timestamp, close) in enumerate(zip(timestamps, prices)):
            # Generate realistic OHLC from close price
            volatility_factor = np.random.uniform(0.5, 1.5)
            high_low_range = close * period_volatility * volatility_factor * 2
            
            high = close + np.random.uniform(0, high_low_range)
            low = close - np.random.uniform(0, high_low_range)
            
            # Ensure OHLC logic is maintained
            if i == 0:
                open_price = close * (1 + np.random.uniform(-0.001, 0.001))
            else:
                open_price = data[-1]['close'] * (1 + np.random.uniform(-0.0005, 0.0005))
            
            high = max(high, open_price, close)
            low = min(low, open_price, close)
            
            # Generate realistic volume (higher during high volatility)
            base_volume = 1000000  # Base volume
            volatility_multiplier = abs(returns[i]) * 50 + 1
            volume = int(base_volume * volatility_multiplier * np.random.uniform(0.5, 2.0))
            
            data.append({
                'timestamp': timestamp,
                'open': round(open_price, 2),
                'high': round(high, 2),
                'low': round(low, 2),
                'close': round(close, 2),
                'volume': volume
            })
        
        return pd.DataFrame(data)

class CryptoBacktester:
    """Comprehensive crypto backtesting engine"""
    
    def __init__(self, initial_balance: float = 10000.0):
        """Initialize backtester"""
        self.initial_balance = initial_balance
        self.current_balance = initial_balance
        
        # Initialize components
        self.strategy = SimplifiedRobustStrategy()
        self.risk_manager = CryptoRiskManager(
            max_risk_per_trade=0.02,  # 2% risk per trade
            max_daily_loss=0.08,      # 8% daily loss limit
            max_open_positions=5
        )
        
        # Trading results
        self.trades: List[Dict] = []
        self.daily_balances: List[Dict] = []
        self.positions: Dict[str, Dict] = {}
        
        # Performance tracking
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_profit = 0.0
        self.total_loss = 0.0
        self.max_drawdown = 0.0
        self.peak_balance = initial_balance
        
        # Configuration
        self.stop_loss_pct = 0.03  # 3%
        self.take_profit_pct = 0.06  # 6%
        self.commission_rate = 0.001  # 0.1% per trade (Binance rate)
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def run_backtest(
        self, 
        data: pd.DataFrame, 
        symbol: str = "BTCUSDT"
    ) -> Dict:
        """Run complete backtest on provided data"""
        
        self.logger.info(f"🚀 Starting backtest for {symbol}")
        self.logger.info(f"💰 Initial balance: ${self.initial_balance:,.2f}")
        self.logger.info(f"📊 Data points: {len(data)}")
        self.logger.info(f"📅 Date range: {data['timestamp'].iloc[0]} to {data['timestamp'].iloc[-1]}")
        
        current_day = None
        
        for index, row in data.iterrows():
            try:
                # Create price data object
                price_data = PriceData(
                    timestamp=row['timestamp'],
                    open=row['open'],
                    high=row['high'],
                    low=row['low'],
                    close=row['close'],
                    volume=row['volume']
                )
                
                # Track daily balances
                day = row['timestamp'].date()
                if day != current_day:
                    self.daily_balances.append({
                        'date': day,
                        'balance': self.current_balance,
                        'equity': self._calculate_equity(row['close'])
                    })
                    current_day = day
                
                # Update existing positions
                self._update_positions(price_data, symbol)
                
                # Generate trading signal
                signal = self.strategy.add_price_data(price_data)
                
                if signal and signal.direction != 'NEUTRAL':
                    self._process_signal(signal, price_data, symbol)
                
                # Update performance metrics
                self._update_performance_metrics()
                
            except Exception as e:
                self.logger.error(f"❌ Error processing data at {row['timestamp']}: {e}")
                continue
        
        # Generate final report
        results = self._generate_performance_report()
        
        self.logger.info("✅ Backtest completed successfully")
        return results
    
    def _process_signal(self, signal: Signal, price_data: PriceData, symbol: str):
        """Process trading signal"""
        try:
            # Check if we can open position
            if not self.risk_manager.can_open_position(symbol, signal.direction):
                return
            
            # Check if we already have a position in this symbol
            if symbol in self.positions:
                return
            
            # Calculate position size
            position_size_usdt = self.risk_manager.calculate_position_size(
                self.current_balance,
                symbol,
                signal.direction,
                price_data.close,
                self.stop_loss_pct * 100
            )
            
            if position_size_usdt < 10:  # Minimum trade size
                return
            
            # Calculate quantity
            quantity = position_size_usdt / price_data.close
            
            # Calculate stop loss and take profit
            if signal.direction == 'BUY':
                stop_loss = price_data.close * (1 - self.stop_loss_pct)
                take_profit = price_data.close * (1 + self.take_profit_pct)
            else:  # SELL
                stop_loss = price_data.close * (1 + self.stop_loss_pct)
                take_profit = price_data.close * (1 - self.take_profit_pct)
            
            # Calculate commission
            commission = position_size_usdt * self.commission_rate
            
            # Create position
            position = {
                'symbol': symbol,
                'direction': signal.direction,
                'entry_price': price_data.close,
                'quantity': quantity,
                'position_size_usdt': position_size_usdt,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'entry_time': price_data.timestamp,
                'commission': commission,
                'signal_strength': signal.strength,
                'signal_reason': signal.reason
            }
            
            # Add position
            self.positions[symbol] = position
            self.current_balance -= commission  # Deduct entry commission
            
            # Update risk manager
            self.risk_manager.add_position(
                symbol, signal.direction, position_size_usdt,
                price_data.close, stop_loss, take_profit
            )
            
            self.logger.info(f"📈 {signal.direction} position opened: {symbol} @ {price_data.close:.2f}")
            
        except Exception as e:
            self.logger.error(f"❌ Error processing signal: {e}")
    
    def _update_positions(self, price_data: PriceData, symbol: str):
        """Update existing positions and check for exits"""
        if symbol not in self.positions:
            return
        
        position = self.positions[symbol]
        current_price = price_data.close
        
        # Check for stop loss or take profit
        should_close = False
        exit_reason = ""
        
        if position['direction'] == 'BUY':
            if current_price <= position['stop_loss']:
                should_close = True
                exit_reason = "Stop Loss"
            elif current_price >= position['take_profit']:
                should_close = True
                exit_reason = "Take Profit"
        else:  # SELL
            if current_price >= position['stop_loss']:
                should_close = True
                exit_reason = "Stop Loss"
            elif current_price <= position['take_profit']:
                should_close = True
                exit_reason = "Take Profit"
        
        if should_close:
            self._close_position(position, current_price, price_data.timestamp, exit_reason)
    
    def _close_position(self, position: Dict, exit_price: float, exit_time: datetime, reason: str):
        """Close position and calculate P&L"""
        try:
            symbol = position['symbol']
            
            # Calculate P&L
            if position['direction'] == 'BUY':
                pnl_usdt = (exit_price - position['entry_price']) / position['entry_price'] * position['position_size_usdt']
            else:  # SELL
                pnl_usdt = (position['entry_price'] - exit_price) / position['entry_price'] * position['position_size_usdt']
            
            # Calculate exit commission
            exit_commission = position['position_size_usdt'] * self.commission_rate
            net_pnl = pnl_usdt - exit_commission
            
            # Update balance
            self.current_balance += net_pnl
            
            # Create trade record
            trade = {
                'symbol': symbol,
                'direction': position['direction'],
                'entry_price': position['entry_price'],
                'exit_price': exit_price,
                'quantity': position['quantity'],
                'position_size_usdt': position['position_size_usdt'],
                'entry_time': position['entry_time'],
                'exit_time': exit_time,
                'duration': exit_time - position['entry_time'],
                'pnl_usdt': pnl_usdt,
                'net_pnl': net_pnl,
                'total_commission': position['commission'] + exit_commission,
                'return_pct': net_pnl / position['position_size_usdt'],
                'exit_reason': reason,
                'signal_strength': position['signal_strength'],
                'signal_reason': position['signal_reason']
            }
            
            self.trades.append(trade)
            
            # Update statistics
            self.total_trades += 1
            if net_pnl > 0:
                self.winning_trades += 1
                self.total_profit += net_pnl
            else:
                self.losing_trades += 1
                self.total_loss += abs(net_pnl)
            
            # Remove position
            del self.positions[symbol]
            
            # Update risk manager
            self.risk_manager.close_position(symbol, exit_price)
            
            self.logger.info(f"📉 Position closed: {symbol} @ {exit_price:.2f} | P&L: ${net_pnl:.2f} | Reason: {reason}")
            
        except Exception as e:
            self.logger.error(f"❌ Error closing position: {e}")
    
    def _calculate_equity(self, current_price: float) -> float:
        """Calculate current equity including unrealized P&L"""
        equity = self.current_balance
        
        for position in self.positions.values():
            if position['direction'] == 'BUY':
                unrealized_pnl = (current_price - position['entry_price']) / position['entry_price'] * position['position_size_usdt']
            else:
                unrealized_pnl = (position['entry_price'] - current_price) / position['entry_price'] * position['position_size_usdt']
            
            equity += unrealized_pnl
        
        return equity
    
    def _update_performance_metrics(self):
        """Update performance metrics"""
        if self.current_balance > self.peak_balance:
            self.peak_balance = self.current_balance
        
        current_drawdown = (self.peak_balance - self.current_balance) / self.peak_balance
        if current_drawdown > self.max_drawdown:
            self.max_drawdown = current_drawdown
    
    def _generate_performance_report(self) -> Dict:
        """Generate comprehensive performance report"""
        if not self.trades:
            return {'error': 'No trades executed'}
        
        # Basic metrics
        total_return = (self.current_balance - self.initial_balance) / self.initial_balance
        win_rate = self.winning_trades / self.total_trades if self.total_trades > 0 else 0
        
        # P&L metrics
        avg_win = self.total_profit / self.winning_trades if self.winning_trades > 0 else 0
        avg_loss = self.total_loss / self.losing_trades if self.losing_trades > 0 else 0
        profit_factor = self.total_profit / self.total_loss if self.total_loss > 0 else float('inf')
        
        # Trade duration analysis
        durations = [trade['duration'].total_seconds() / 3600 for trade in self.trades]  # in hours
        avg_duration = np.mean(durations) if durations else 0
        
        # Return analysis
        returns = [trade['return_pct'] for trade in self.trades]
        avg_return_per_trade = np.mean(returns) if returns else 0
        
        # Calculate Sharpe ratio (simplified)
        if len(returns) > 1:
            sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252) if np.std(returns) > 0 else 0
        else:
            sharpe_ratio = 0
        
        # Time-based metrics
        if self.daily_balances:
            days_traded = len(self.daily_balances)
            annual_return = (total_return + 1) ** (365 / days_traded) - 1 if days_traded > 0 else 0
        else:
            days_traded = 0
            annual_return = 0
        
        report = {
            'summary': {
                'initial_balance': self.initial_balance,
                'final_balance': self.current_balance,
                'total_return': total_return,
                'annual_return': annual_return,
                'max_drawdown': self.max_drawdown
            },
            'trading_metrics': {
                'total_trades': self.total_trades,
                'winning_trades': self.winning_trades,
                'losing_trades': self.losing_trades,
                'win_rate': win_rate,
                'profit_factor': profit_factor,
                'avg_return_per_trade': avg_return_per_trade
            },
            'pnl_metrics': {
                'total_profit': self.total_profit,
                'total_loss': self.total_loss,
                'net_profit': self.current_balance - self.initial_balance,
                'avg_win': avg_win,
                'avg_loss': avg_loss
            },
            'risk_metrics': {
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': self.max_drawdown,
                'days_traded': days_traded
            },
            'trade_analysis': {
                'avg_duration_hours': avg_duration,
                'total_commission': sum(trade['total_commission'] for trade in self.trades)
            }
        }
        
        return report

def print_backtest_results(results: Dict):
    """Print formatted backtest results"""
    if 'error' in results:
        print(f"❌ {results['error']}")
        return
    
    print("\n" + "="*60)
    print("₿ CRYPTO BACKTEST RESULTS - Simplified Robust Strategy")
    print("="*60)
    
    # Summary
    summary = results['summary']
    print(f"\n💰 PERFORMANCE SUMMARY")
    print(f"   Initial Balance:    ${summary['initial_balance']:,.2f}")
    print(f"   Final Balance:      ${summary['final_balance']:,.2f}")
    print(f"   Total Return:       {summary['total_return']:.2%}")
    print(f"   Annual Return:      {summary['annual_return']:.2%}")
    print(f"   Max Drawdown:       {summary['max_drawdown']:.2%}")
    
    # Trading metrics
    trading = results['trading_metrics']
    print(f"\n📊 TRADING METRICS")
    print(f"   Total Trades:       {trading['total_trades']}")
    print(f"   Winning Trades:     {trading['winning_trades']}")
    print(f"   Losing Trades:      {trading['losing_trades']}")
    print(f"   Win Rate:           {trading['win_rate']:.2%}")
    print(f"   Profit Factor:      {trading['profit_factor']:.2f}")
    print(f"   Avg Return/Trade:   {trading['avg_return_per_trade']:.2%}")
    
    # P&L metrics
    pnl = results['pnl_metrics']
    print(f"\n💵 P&L BREAKDOWN")
    print(f"   Total Profit:       ${pnl['total_profit']:,.2f}")
    print(f"   Total Loss:         ${pnl['total_loss']:,.2f}")
    print(f"   Net Profit:         ${pnl['net_profit']:,.2f}")
    print(f"   Average Win:        ${pnl['avg_win']:,.2f}")
    print(f"   Average Loss:       ${pnl['avg_loss']:,.2f}")
    
    # Risk metrics
    risk = results['risk_metrics']
    print(f"\n🛡️ RISK METRICS")
    print(f"   Sharpe Ratio:       {risk['sharpe_ratio']:.2f}")
    print(f"   Max Drawdown:       {risk['max_drawdown']:.2%}")
    print(f"   Days Traded:        {risk['days_traded']}")
    
    # Trade analysis
    trade_analysis = results['trade_analysis']
    print(f"\n⏱️ TRADE ANALYSIS")
    print(f"   Avg Duration:       {trade_analysis['avg_duration_hours']:.1f} hours")
    print(f"   Total Commission:   ${trade_analysis['total_commission']:,.2f}")
    
    print("\n" + "="*60)
    
    # Assessment
    print("📈 STRATEGY ASSESSMENT:")
    
    if summary['annual_return'] > 0.10:  # 10%
        print("   ✅ Strong annual returns")
    elif summary['annual_return'] > 0.05:  # 5%
        print("   ✅ Decent annual returns")
    else:
        print("   ⚠️  Low annual returns")
    
    if trading['win_rate'] > 0.6:  # 60%
        print("   ✅ Good win rate")
    elif trading['win_rate'] > 0.5:  # 50%
        print("   ✅ Acceptable win rate")
    else:
        print("   ⚠️  Low win rate")
    
    if trading['profit_factor'] > 1.5:
        print("   ✅ Excellent profit factor")
    elif trading['profit_factor'] > 1.2:
        print("   ✅ Good profit factor")
    elif trading['profit_factor'] > 1.0:
        print("   ✅ Profitable strategy")
    else:
        print("   ❌ Unprofitable strategy")
    
    if risk['max_drawdown'] < 0.2:  # 20%
        print("   ✅ Reasonable drawdown")
    elif risk['max_drawdown'] < 0.4:  # 40%
        print("   ⚠️  High but acceptable drawdown")
    else:
        print("   ❌ Very high drawdown")

def run_crypto_backtest(
    symbol: str = "BTCUSDT",
    days: int = 365,
    initial_balance: float = 10000.0
):
    """Run a complete crypto backtest"""
    
    print(f"🚀 Starting crypto backtest for {symbol}")
    print(f"📅 Testing period: {days} days")
    print(f"💰 Initial balance: ${initial_balance:,.2f}")
    
    # Generate data
    print("📊 Generating realistic crypto market data...")
    data_generator = CryptoDataGenerator(symbol, initial_price=45000.0)
    data = data_generator.generate_realistic_crypto_data(days=days)
    
    print(f"✅ Generated {len(data)} data points")
    print(f"📈 Price range: ${data['close'].min():.2f} - ${data['close'].max():.2f}")
    
    # Run backtest
    backtester = CryptoBacktester(initial_balance)
    results = backtester.run_backtest(data, symbol)
    
    # Print results
    print_backtest_results(results)
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"backtest_results_{symbol}_{timestamp}.json"
    
    with open(results_file, 'w') as f:
        # Convert datetime objects to strings for JSON serialization
        json_results = results.copy()
        json.dump(json_results, f, indent=2, default=str)
    
    print(f"\n💾 Results saved to: {results_file}")
    
    return results

if __name__ == "__main__":
    # Run backtest with default parameters
    run_crypto_backtest(
        symbol="BTCUSDT",
        days=365,
        initial_balance=10000.0
    ) 