#!/usr/bin/env python3
"""
Crypto Risk Manager - Enhanced for Cryptocurrency Trading
Adapted risk management for higher volatility crypto markets

Key Adaptations for Crypto:
- Higher volatility tolerance
- 24/7 market considerations
- Crypto-specific position sizing
- USDT base currency calculations
- Dynamic risk adjustment based on market conditions
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import math

class CryptoRiskManager:
    """
    Enhanced risk management for cryptocurrency trading
    """
    
    def __init__(
        self, 
        max_risk_per_trade: float = 0.02,  # 2% for crypto (higher than forex)
        max_daily_loss: float = 0.08,      # 8% for crypto volatility
        max_open_positions: int = 5,       # More positions for diversification
        base_currency: str = "USDT"
    ):
        """Initialize crypto risk manager"""
        self.max_risk_per_trade = max_risk_per_trade
        self.max_daily_loss = max_daily_loss  
        self.max_open_positions = max_open_positions
        self.base_currency = base_currency
        
        # Track positions and P&L
        self.open_positions: Dict[str, Dict] = {}
        self.daily_pnl = 0.0
        self.trades_today = 0
        self.last_reset_date = datetime.now().date()
        
        # Crypto-specific settings
        self.min_trade_size_usdt = 10.0  # Minimum trade size
        self.max_trade_size_usdt = 10000.0  # Maximum single trade
        
        # Dynamic risk adjustment
        self.volatility_multiplier = 1.0
        self.market_fear_greed_adjustment = 1.0
        
        # Position tracking
        self.symbol_exposure: Dict[str, float] = {}
        self.correlation_limit = 0.6  # Limit correlated crypto positions
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("🛡️ Crypto Risk Manager initialized")
        self.logger.info(f"📊 Max risk per trade: {max_risk_per_trade*100}%")
        self.logger.info(f"📊 Max daily loss: {max_daily_loss*100}%")
        self.logger.info(f"📊 Max positions: {max_open_positions}")
    
    def can_open_position(self, symbol: str, direction: str) -> bool:
        """Check if we can open a new position considering crypto-specific risks"""
        try:
            # Reset daily counters if new day
            self._reset_daily_counters_if_needed()
            
            # Check daily loss limit
            if self.daily_pnl <= -abs(self.max_daily_loss):
                self.logger.warning(f"⛔ Daily loss limit reached: {self.daily_pnl:.2%}")
                return False
            
            # Check maximum open positions
            if len(self.open_positions) >= self.max_open_positions:
                self.logger.warning(f"⛔ Maximum positions limit reached: {len(self.open_positions)}")
                return False
            
            # Check if already have position in this symbol
            if symbol in self.open_positions:
                self.logger.debug(f"⚠️ Already have position in {symbol}")
                return False
            
            # Crypto-specific: Check symbol exposure
            if self._check_symbol_exposure(symbol):
                self.logger.warning(f"⛔ Symbol exposure limit reached for {symbol}")
                return False
            
            # Check correlation limits for crypto pairs
            if self._check_correlation_limits(symbol):
                self.logger.warning(f"⛔ Too many correlated positions, skipping {symbol}")
                return False
            
            # Check market volatility conditions
            if not self._check_volatility_conditions(symbol):
                self.logger.warning(f"⛔ Market too volatile for {symbol}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error in can_open_position: {e}")
            return False
    
    def calculate_position_size(
        self, 
        account_balance: float, 
        symbol: str, 
        direction: str, 
        entry_price: float,
        stop_loss_pct: float = 3.0  # 3% stop loss for crypto
    ) -> float:
        """Calculate position size in USDT for crypto trading"""
        try:
            # Effective balance (considering existing positions)
            effective_balance = self._get_effective_balance(account_balance)
            
            # Base risk amount
            risk_amount = effective_balance * self.max_risk_per_trade
            
            # Apply dynamic adjustments for crypto
            risk_amount *= self._get_dynamic_risk_multiplier(symbol)
            
            # Ensure minimum and maximum trade sizes
            risk_amount = max(self.min_trade_size_usdt, risk_amount)
            risk_amount = min(self.max_trade_size_usdt, risk_amount)
            
            # Calculate position size based on stop loss
            # Risk = Position Size * (Stop Loss %)
            # Position Size = Risk / Stop Loss %
            position_size_usdt = risk_amount / (stop_loss_pct / 100)
            
            # Apply additional safety limits
            max_position_usdt = effective_balance * 0.2  # Max 20% per position
            position_size_usdt = min(position_size_usdt, max_position_usdt)
            
            self.logger.info(f"💰 Position size calculated: {position_size_usdt:.2f} USDT for {symbol}")
            self.logger.info(f"🎯 Risk amount: {risk_amount:.2f} USDT ({self.max_risk_per_trade*100}%)")
            
            return position_size_usdt
            
        except Exception as e:
            self.logger.error(f"❌ Error calculating position size: {e}")
            return 0.0
    
    def add_position(
        self, 
        symbol: str, 
        direction: str, 
        size_usdt: float, 
        entry_price: float,
        stop_loss: float,
        take_profit: float
    ):
        """Add new position to tracking"""
        try:
            position_info = {
                'direction': direction,
                'size_usdt': size_usdt,
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'timestamp': datetime.now(),
                'unrealized_pnl': 0.0
            }
            
            self.open_positions[symbol] = position_info
            self.trades_today += 1
            
            # Update symbol exposure
            crypto_symbol = symbol.replace('USDT', '')  # e.g., BTC from BTCUSDT
            if crypto_symbol not in self.symbol_exposure:
                self.symbol_exposure[crypto_symbol] = 0.0
            self.symbol_exposure[crypto_symbol] += size_usdt
            
            self.logger.info(f"📈 Added {direction} position: {symbol} - {size_usdt:.2f} USDT")
            
        except Exception as e:
            self.logger.error(f"❌ Error adding position: {e}")
    
    def close_position(self, symbol: str, exit_price: float) -> float:
        """Close position and calculate P&L"""
        try:
            if symbol not in self.open_positions:
                return 0.0
            
            position = self.open_positions[symbol]
            
            # Calculate P&L in USDT
            if position['direction'] == 'BUY':
                pnl_usdt = (exit_price - position['entry_price']) / position['entry_price'] * position['size_usdt']
            else:  # SELL
                pnl_usdt = (position['entry_price'] - exit_price) / position['entry_price'] * position['size_usdt']
            
            # Update daily P&L
            self.daily_pnl += pnl_usdt / self._get_account_balance()  # Convert to percentage
            
            # Update symbol exposure
            crypto_symbol = symbol.replace('USDT', '')
            if crypto_symbol in self.symbol_exposure:
                self.symbol_exposure[crypto_symbol] -= position['size_usdt']
                if self.symbol_exposure[crypto_symbol] <= 0:
                    del self.symbol_exposure[crypto_symbol]
            
            # Remove from open positions
            del self.open_positions[symbol]
            
            self.logger.info(f"📉 Closed position: {symbol} - P&L: {pnl_usdt:.2f} USDT")
            
            return pnl_usdt
            
        except Exception as e:
            self.logger.error(f"❌ Error closing position: {e}")
            return 0.0
    
    def update_position_pnl(self, symbol: str, current_price: float):
        """Update unrealized P&L for position"""
        try:
            if symbol not in self.open_positions:
                return
            
            position = self.open_positions[symbol]
            
            # Calculate unrealized P&L
            if position['direction'] == 'BUY':
                unrealized_pnl = (current_price - position['entry_price']) / position['entry_price'] * position['size_usdt']
            else:  # SELL
                unrealized_pnl = (position['entry_price'] - current_price) / position['entry_price'] * position['size_usdt']
            
            position['unrealized_pnl'] = unrealized_pnl
            
        except Exception as e:
            self.logger.error(f"❌ Error updating position P&L: {e}")
    
    def get_total_unrealized_pnl(self) -> float:
        """Get total unrealized P&L across all positions"""
        total_pnl = 0.0
        for position in self.open_positions.values():
            total_pnl += position.get('unrealized_pnl', 0.0)
        return total_pnl
    
    def get_risk_metrics(self) -> Dict:
        """Get current risk metrics"""
        return {
            'open_positions': len(self.open_positions),
            'daily_pnl': self.daily_pnl,
            'trades_today': self.trades_today,
            'symbol_exposure': self.symbol_exposure.copy(),
            'total_unrealized_pnl': self.get_total_unrealized_pnl(),
            'risk_utilization': len(self.open_positions) / self.max_open_positions,
            'daily_loss_utilization': abs(self.daily_pnl) / self.max_daily_loss if self.daily_pnl < 0 else 0
        }
    
    def _reset_daily_counters_if_needed(self):
        """Reset daily counters at start of new day (crypto trades 24/7)"""
        current_date = datetime.now().date()
        if current_date > self.last_reset_date:
            self.daily_pnl = 0.0
            self.trades_today = 0
            self.last_reset_date = current_date
            self.logger.info("🔄 Daily counters reset for new trading day")
    
    def _get_effective_balance(self, account_balance: float) -> float:
        """Calculate effective balance considering open positions"""
        # Reserve margin for open positions
        reserved_margin = sum(pos['size_usdt'] for pos in self.open_positions.values())
        return account_balance - reserved_margin
    
    def _check_symbol_exposure(self, symbol: str) -> bool:
        """Check if symbol exposure is within limits"""
        crypto_symbol = symbol.replace('USDT', '')
        
        # Limit exposure per crypto (e.g., max 30% in BTC)
        max_exposure_per_crypto = 0.3
        current_exposure = self.symbol_exposure.get(crypto_symbol, 0.0)
        account_balance = self._get_account_balance()
        
        exposure_ratio = current_exposure / account_balance if account_balance > 0 else 0
        
        return exposure_ratio >= max_exposure_per_crypto
    
    def _check_correlation_limits(self, symbol: str) -> bool:
        """Check correlation limits for crypto pairs"""
        # Simplified correlation check for major crypto pairs
        high_correlation_groups = [
            ['BTC', 'ETH'],  # Major cryptos tend to correlate
            ['ADA', 'DOT', 'SOL'],  # Alt coins
            ['BNB', 'MATIC']  # Exchange tokens
        ]
        
        crypto_symbol = symbol.replace('USDT', '')
        
        for group in high_correlation_groups:
            if crypto_symbol in group:
                # Count how many from this group we already have
                group_positions = 0
                for pos_symbol in self.open_positions.keys():
                    pos_crypto = pos_symbol.replace('USDT', '')
                    if pos_crypto in group:
                        group_positions += 1
                
                # Limit to 2 positions from same correlation group
                if group_positions >= 2:
                    return True
        
        return False
    
    def _check_volatility_conditions(self, symbol: str) -> bool:
        """Check if market volatility allows for safe trading"""
        # This would ideally use real volatility data
        # For now, return True - could be enhanced with VIX-like crypto indicators
        return True
    
    def _get_dynamic_risk_multiplier(self, symbol: str) -> float:
        """Get dynamic risk multiplier based on market conditions"""
        multiplier = 1.0
        
        # Reduce risk for highly volatile assets
        volatile_cryptos = ['BTC', 'ETH']  # Could be expanded
        crypto_symbol = symbol.replace('USDT', '')
        
        if crypto_symbol in volatile_cryptos:
            multiplier *= 0.8  # Reduce risk by 20% for major volatile cryptos
        
        # Could add more dynamic adjustments based on:
        # - Market fear & greed index
        # - Recent volatility
        # - Time of day/week patterns
        
        return multiplier
    
    def _get_account_balance(self) -> float:
        """Get current account balance - placeholder"""
        # This would be provided by the main trader
        return 1000.0  # Placeholder value 