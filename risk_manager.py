"""
Risk Management module.
Handles position sizing, drawdown limits, margin monitoring, and other risk controls.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
import os
from utils import TradeSignal, setup_logging, calculate_position_size, format_currency


class RiskManager:
    """
    Manages all risk-related aspects of trading.
    """
    
    def __init__(self, config: Dict[str, Any], data_feed):
        """
        Initialize risk manager.
        
        Args:
            config: Risk management configuration
            data_feed: MarketDataFeed instance
        """
        self.logger = setup_logging()
        self.config = config
        self.data_feed = data_feed
        
        # Risk parameters
        self.risk_per_trade = config.get('risk_per_trade', 0.01)  # 1% per trade
        self.daily_drawdown_limit = config.get('daily_drawdown_limit', 0.05)  # 5% daily
        self.margin_level_threshold = config.get('margin_level_threshold', 100.0)
        self.max_positions = config.get('max_positions', 5)
        
        # State tracking
        self.daily_start_balance = 0.0
        self.daily_peak_balance = 0.0
        self.trading_halted = False
        self.halt_reason = ""
        self.last_balance_update = datetime.utcnow()
        
        # Initialize daily tracking
        self._initialize_daily_tracking()
        
        self.logger.info(f"Risk Manager initialized - Risk per trade: {self.risk_per_trade*100:.1f}%, "
                        f"Daily drawdown limit: {self.daily_drawdown_limit*100:.1f}%, "
                        f"Max positions: {self.max_positions}")
    
    def validate_signal(self, signal: TradeSignal) -> tuple[bool, str]:
        """
        Validate if a trading signal should be executed based on risk rules.
        
        Args:
            signal: TradeSignal to validate
            
        Returns:
            Tuple of (is_valid, reason)
        """
        # Check if trading is halted
        if self.trading_halted:
            return False, f"Trading halted: {self.halt_reason}"
        
        # Get current account info
        account_info = self.data_feed.get_account_info()
        if not account_info:
            return False, "Cannot get account information"
        
        # Check margin level
        if account_info['margin_level'] < self.margin_level_threshold and account_info['margin'] > 0:
            self.halt_trading("Margin level below threshold")
            return False, f"Margin level too low: {account_info['margin_level']:.1f}%"
        
        # Check daily drawdown
        if not self._check_daily_drawdown(account_info['balance']):
            return False, f"Daily drawdown limit exceeded"
        
        # Check maximum positions
        current_positions = len(self.data_feed.get_positions() if hasattr(self.data_feed, 'get_positions') else [])
        if current_positions >= self.max_positions:
            return False, f"Maximum positions limit reached: {current_positions}/{self.max_positions}"
        
        # Check if we already have a position in this symbol (for strategies that don't allow multiple positions)
        existing_positions = [pos for pos in self.data_feed.get_positions() 
                            if pos.get('symbol') == signal.symbol] if hasattr(self.data_feed, 'get_positions') else []
        if existing_positions and signal.direction == 'BUY':  # New position, not closing
            return False, f"Already have position in {signal.symbol}"
        
        return True, "Signal validated"
    
    def calculate_position_size(self, signal: TradeSignal) -> float:
        """
        Calculate appropriate position size for signal.
        
        Args:
            signal: TradeSignal to size
            
        Returns:
            Calculated lot size
        """
        account_info = self.data_feed.get_account_info()
        if not account_info:
            self.logger.error("Cannot get account info for position sizing")
            return self.config.get('min_lot_size', 0.01)
        
        symbol_info = self.data_feed.get_symbol_info(signal.symbol)
        if not symbol_info:
            self.logger.error(f"Cannot get symbol info for {signal.symbol}")
            return self.config.get('min_lot_size', 0.01)
        
        # Calculate ATR in price units for stop loss distance
        if signal.sl > 0:
            sl_distance = abs(signal.entry_price - signal.sl)
        else:
            # Fallback: use 50 pips for major pairs, 0.5 yen for JPY pairs
            if "JPY" in signal.symbol:
                sl_distance = 0.50  # 50 pips for JPY pairs
            else:
                sl_distance = 0.0050  # 50 pips for major pairs
        
        # Calculate position size
        lot_size = calculate_position_size(
            balance=account_info['balance'],
            atr=sl_distance,
            risk_fraction=self.risk_per_trade,
            pip_value=symbol_info['pip_value'],
            symbol=signal.symbol,
            min_lot=symbol_info['min_lot'],
            max_lot=symbol_info['max_lot']
        )
        
        self.logger.info(f"Position size calculated for {signal.symbol}: {lot_size} lots "
                        f"(Risk: {format_currency(account_info['balance'] * self.risk_per_trade)}, "
                        f"SL distance: {sl_distance:.5f})")
        
        return lot_size
    
    def monitor_positions(self, executor) -> List[Dict]:
        """
        Monitor open positions and apply risk management rules.
        
        Args:
            executor: TradeExecutor instance
            
        Returns:
            List of actions taken
        """
        actions = []
        account_info = self.data_feed.get_account_info()
        
        if not account_info:
            return actions
        
        # Update daily tracking
        self._update_daily_tracking(account_info['balance'])
        
        # Check margin level
        if account_info['margin_level'] < self.margin_level_threshold and account_info['margin'] > 0:
            self.logger.warning(f"Margin level critical: {account_info['margin_level']:.1f}%")
            
            # Close all positions if margin too low
            close_results = executor.close_all_positions()
            if close_results:
                self.halt_trading("Margin level critical - all positions closed")
                actions.append({
                    'action': 'close_all_positions',
                    'reason': 'margin_level_critical',
                    'positions_closed': len(close_results)
                })
        
        # Check daily drawdown
        if not self._check_daily_drawdown(account_info['balance']):
            if not self.trading_halted:
                self.halt_trading("Daily drawdown limit exceeded")
                actions.append({
                    'action': 'halt_trading',
                    'reason': 'daily_drawdown_exceeded',
                    'current_drawdown': self._calculate_daily_drawdown(account_info['balance'])
                })
        
        return actions
    
    def halt_trading(self, reason: str):
        """
        Halt all trading activity.
        
        Args:
            reason: Reason for halting trading
        """
        self.trading_halted = True
        self.halt_reason = reason
        self.logger.warning(f"Trading halted: {reason}")
    
    def resume_trading(self):
        """Resume trading activity."""
        self.trading_halted = False
        self.halt_reason = ""
        self.logger.info("Trading resumed")
    
    def is_trading_halted(self) -> bool:
        """Check if trading is currently halted."""
        return self.trading_halted
    
    def get_halt_reason(self) -> str:
        """Get reason for trading halt."""
        return self.halt_reason
    
    def _initialize_daily_tracking(self):
        """Initialize daily balance tracking."""
        account_info = self.data_feed.get_account_info()
        if account_info:
            self.daily_start_balance = account_info['balance']
            self.daily_peak_balance = account_info['balance']
        
        # Reset halt status for new day
        if datetime.utcnow().hour == 0 and datetime.utcnow().minute < 5:
            self.resume_trading()
    
    def _update_daily_tracking(self, current_balance: float):
        """
        Update daily balance tracking.
        
        Args:
            current_balance: Current account balance
        """
        # Check if new day (reset at GMT 00:00)
        now = datetime.utcnow()
        if (now.hour == 0 and now.minute < 5 and 
            (now - self.last_balance_update).total_seconds() > 3600):
            
            self.daily_start_balance = current_balance
            self.daily_peak_balance = current_balance
            self.resume_trading()  # Reset halt status for new day
            self.logger.info(f"New trading day - Starting balance: {format_currency(current_balance)}")
        
        # Update peak balance
        if current_balance > self.daily_peak_balance:
            self.daily_peak_balance = current_balance
        
        self.last_balance_update = now
    
    def _check_daily_drawdown(self, current_balance: float) -> bool:
        """
        Check if daily drawdown limit is exceeded.
        
        Args:
            current_balance: Current account balance
            
        Returns:
            True if drawdown is within limits
        """
        if self.daily_start_balance <= 0:
            return True
        
        drawdown = self._calculate_daily_drawdown(current_balance)
        return drawdown < self.daily_drawdown_limit
    
    def _calculate_daily_drawdown(self, current_balance: float) -> float:
        """
        Calculate current daily drawdown.
        
        Args:
            current_balance: Current account balance
            
        Returns:
            Drawdown as fraction (0.05 = 5%)
        """
        if self.daily_start_balance <= 0:
            return 0.0
        
        return max(0.0, (self.daily_start_balance - current_balance) / self.daily_start_balance)
    
    def get_risk_metrics(self) -> Dict[str, Any]:
        """
        Get current risk metrics and status.
        
        Returns:
            Dictionary with risk metrics
        """
        account_info = self.data_feed.get_account_info()
        if not account_info:
            return {'error': 'Cannot get account information'}
        
        daily_drawdown = self._calculate_daily_drawdown(account_info['balance'])
        peak_drawdown = max(0.0, (self.daily_peak_balance - account_info['balance']) / self.daily_peak_balance) if self.daily_peak_balance > 0 else 0.0
        
        return {
            'trading_halted': self.trading_halted,
            'halt_reason': self.halt_reason,
            'daily_start_balance': self.daily_start_balance,
            'daily_peak_balance': self.daily_peak_balance,
            'current_balance': account_info['balance'],
            'daily_pnl': account_info['balance'] - self.daily_start_balance,
            'daily_pnl_percent': ((account_info['balance'] / self.daily_start_balance) - 1) * 100 if self.daily_start_balance > 0 else 0,
            'daily_drawdown': daily_drawdown,
            'daily_drawdown_percent': daily_drawdown * 100,
            'peak_drawdown': peak_drawdown,
            'peak_drawdown_percent': peak_drawdown * 100,
            'margin_level': account_info['margin_level'],
            'margin_level_ok': account_info['margin_level'] >= self.margin_level_threshold or account_info['margin'] == 0,
            'risk_per_trade_percent': self.risk_per_trade * 100,
            'daily_limit_percent': self.daily_drawdown_limit * 100,
            'max_positions': self.max_positions
        }
    
    def save_daily_report(self, file_path: str = "logs/daily_risk_report.json"):
        """
        Save daily risk report to file.
        
        Args:
            file_path: Path to save report
        """
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            metrics = self.get_risk_metrics()
            metrics['report_date'] = datetime.utcnow().isoformat()
            
            # Load existing reports
            reports = []
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r') as f:
                        reports = json.load(f)
                except:
                    pass
            
            # Add new report
            reports.append(metrics)
            
            # Keep only last 30 days
            if len(reports) > 30:
                reports = reports[-30:]
            
            # Save updated reports
            with open(file_path, 'w') as f:
                json.dump(reports, f, indent=2)
                
            self.logger.info(f"Daily risk report saved to {file_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to save daily report: {e}")
    
    def calculate_max_risk_exposure(self) -> Dict[str, float]:
        """
        Calculate maximum risk exposure across all positions.
        
        Returns:
            Dictionary with exposure metrics
        """
        account_info = self.data_feed.get_account_info()
        if not account_info:
            return {}
        
        positions = []
        if hasattr(self.data_feed, 'get_positions'):
            positions = self.data_feed.get_positions()
        
        total_risk = 0.0
        total_margin = 0.0
        
        for pos in positions:
            # Calculate potential loss if stop loss hit
            if pos.get('sl', 0) > 0:
                if pos['type'] == 'BUY':
                    potential_loss = (pos['price_open'] - pos['sl']) * pos['volume']
                else:
                    potential_loss = (pos['sl'] - pos['price_open']) * pos['volume']
                
                # Convert to account currency (simplified)
                symbol_info = self.data_feed.get_symbol_info(pos['symbol'])
                if symbol_info:
                    potential_loss *= symbol_info.get('pip_value', 10.0) / 10000
                
                total_risk += abs(potential_loss)
            
            # Add margin requirement
            total_margin += pos.get('volume', 0) * 1000  # Simplified margin calc
        
        return {
            'total_potential_loss': total_risk,
            'total_margin_used': total_margin,
            'risk_percentage': (total_risk / account_info['balance']) * 100 if account_info['balance'] > 0 else 0,
            'margin_percentage': (total_margin / account_info['balance']) * 100 if account_info['balance'] > 0 else 0
        } 