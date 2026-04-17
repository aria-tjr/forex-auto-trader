"""
Trade Execution module for MetaTrader 5.
Handles order placement, modification, and management.
"""

import MetaTrader5 as mt5
from typing import Dict, List, Optional, Any
from datetime import datetime
import time
from utils import TradeSignal, setup_logging, format_price


class TradeExecutor:
    """
    Manages trade execution through MetaTrader 5.
    """
    
    def __init__(self, data_feed):
        """
        Initialize trade executor.
        
        Args:
            data_feed: MarketDataFeed instance for price and account data
        """
        self.logger = setup_logging()
        self.data_feed = data_feed
        self.pending_orders = {}
        self.open_positions = {}
        
    def execute_signal(self, signal: TradeSignal) -> Optional[Dict]:
        """
        Execute a trading signal.
        
        Args:
            signal: TradeSignal to execute
            
        Returns:
            Dictionary with execution result or None if failed
        """
        if not self.data_feed.is_connected():
            self.logger.error("Not connected to MT5 - cannot execute signal")
            return None
        
        # Get symbol info for execution
        symbol_info = self.data_feed.get_symbol_info(signal.symbol)
        if not symbol_info:
            self.logger.error(f"Failed to get symbol info for {signal.symbol}")
            return None
        
        # Prepare order request
        if signal.direction == 'BUY':
            order_type = mt5.ORDER_TYPE_BUY
            price = mt5.symbol_info_tick(signal.symbol).ask
        else:
            order_type = mt5.ORDER_TYPE_SELL
            price = mt5.symbol_info_tick(signal.symbol).bid
        
        # Round volume to valid step
        volume = self._round_volume(signal.volume, symbol_info)
        
        # Build order request
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": signal.symbol,
            "volume": volume,
            "type": order_type,
            "price": price,
            "sl": signal.sl if signal.sl > 0 else 0.0,
            "tp": signal.tp if signal.tp > 0 else 0.0,
            "deviation": 20,  # Price deviation in points
            "magic": 12345,  # Magic number for identification
            "comment": f"EMA_Crossover_{datetime.now().strftime('%H%M%S')}",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        # Validate order before sending
        check_result = mt5.order_check(request)
        if check_result is None:
            self.logger.error(f"Order check failed: {mt5.last_error()}")
            return None
        
        if check_result.retcode != mt5.TRADE_RETCODE_DONE:
            self.logger.error(f"Order validation failed: {check_result.retcode}, {check_result.comment}")
            return None
        
        # Send order
        result = mt5.order_send(request)
        if result is None:
            self.logger.error(f"Order send failed: {mt5.last_error()}")
            return None
        
        # Process result
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            self.logger.info(f"Order executed successfully: {signal.direction} {volume} {signal.symbol} "
                           f"@ {price:.5f}, Order: {result.order}, Deal: {result.deal}")
            
            # Track the position
            if result.deal > 0:
                self._track_position(signal, result, price)
            
            return {
                'success': True,
                'order_id': result.order,
                'deal_id': result.deal,
                'volume': result.volume,
                'price': result.price,
                'symbol': signal.symbol,
                'direction': signal.direction,
                'timestamp': datetime.utcnow()
            }
        else:
            self.logger.error(f"Order execution failed: {result.retcode}, {result.comment}")
            return {
                'success': False,
                'error_code': result.retcode,
                'error_message': result.comment
            }
    
    def close_position(self, symbol: str, volume: Optional[float] = None) -> Optional[Dict]:
        """
        Close position for given symbol.
        
        Args:
            symbol: Currency pair symbol
            volume: Volume to close (None for full position)
            
        Returns:
            Dictionary with close result or None if failed
        """
        if not self.data_feed.is_connected():
            self.logger.error("Not connected to MT5")
            return None
        
        # Get open positions for symbol
        positions = mt5.positions_get(symbol=symbol)
        if not positions:
            self.logger.warning(f"No open positions found for {symbol}")
            return None
        
        position = positions[0]  # Take first position
        
        # Determine close parameters
        if position.type == mt5.POSITION_TYPE_BUY:
            order_type = mt5.ORDER_TYPE_SELL
            price = mt5.symbol_info_tick(symbol).bid
        else:
            order_type = mt5.ORDER_TYPE_BUY
            price = mt5.symbol_info_tick(symbol).ask
        
        close_volume = volume if volume else position.volume
        
        # Build close request
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": close_volume,
            "type": order_type,
            "position": position.ticket,
            "price": price,
            "deviation": 20,
            "magic": 12345,
            "comment": f"Close_{datetime.now().strftime('%H%M%S')}",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        # Send close order
        result = mt5.order_send(request)
        if result is None:
            self.logger.error(f"Position close failed: {mt5.last_error()}")
            return None
        
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            self.logger.info(f"Position closed: {symbol}, Volume: {close_volume}, "
                           f"Price: {price:.5f}, P/L: {result.profit}")
            
            # Remove from tracking if fully closed
            if close_volume >= position.volume:
                self.open_positions.pop(symbol, None)
            
            return {
                'success': True,
                'symbol': symbol,
                'volume': result.volume,
                'price': result.price,
                'profit': result.profit,
                'timestamp': datetime.utcnow()
            }
        else:
            self.logger.error(f"Position close failed: {result.retcode}, {result.comment}")
            return None
    
    def close_all_positions(self) -> List[Dict]:
        """
        Close all open positions.
        
        Returns:
            List of close results
        """
        results = []
        positions = mt5.positions_get()
        
        if not positions:
            self.logger.info("No positions to close")
            return results
        
        for position in positions:
            result = self.close_position(position.symbol)
            if result:
                results.append(result)
        
        self.logger.info(f"Closed {len(results)} positions")
        return results
    
    def modify_position(self, symbol: str, new_sl: Optional[float] = None, 
                       new_tp: Optional[float] = None) -> bool:
        """
        Modify stop loss and/or take profit for position.
        
        Args:
            symbol: Currency pair symbol
            new_sl: New stop loss level
            new_tp: New take profit level
            
        Returns:
            True if modification successful
        """
        if not self.data_feed.is_connected():
            return False
        
        positions = mt5.positions_get(symbol=symbol)
        if not positions:
            self.logger.warning(f"No position found for {symbol}")
            return False
        
        position = positions[0]
        
        # Use current values if not specified
        sl = new_sl if new_sl is not None else position.sl
        tp = new_tp if new_tp is not None else position.tp
        
        # Build modification request
        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "symbol": symbol,
            "position": position.ticket,
            "sl": sl,
            "tp": tp,
        }
        
        result = mt5.order_send(request)
        if result and result.retcode == mt5.TRADE_RETCODE_DONE:
            self.logger.info(f"Position modified: {symbol}, SL: {sl:.5f}, TP: {tp:.5f}")
            return True
        else:
            error = mt5.last_error() if result is None else f"{result.retcode}: {result.comment}"
            self.logger.error(f"Position modification failed: {error}")
            return False
    
    def update_trailing_stops(self, positions_data: Dict[str, Dict]) -> List[Dict]:
        """
        Update trailing stops for positions.
        
        Args:
            positions_data: Dictionary with position data and new stop levels
            
        Returns:
            List of modification results
        """
        results = []
        
        for symbol, data in positions_data.items():
            new_sl = data.get('new_sl')
            if new_sl:
                success = self.modify_position(symbol, new_sl=new_sl)
                results.append({
                    'symbol': symbol,
                    'success': success,
                    'new_sl': new_sl
                })
        
        return results
    
    def get_positions(self) -> List[Dict]:
        """
        Get all open positions.
        
        Returns:
            List of position dictionaries
        """
        positions = mt5.positions_get()
        if not positions:
            return []
        
        result = []
        for pos in positions:
            result.append({
                'ticket': pos.ticket,
                'symbol': pos.symbol,
                'type': 'BUY' if pos.type == mt5.POSITION_TYPE_BUY else 'SELL',
                'volume': pos.volume,
                'price_open': pos.price_open,
                'price_current': pos.price_current,
                'sl': pos.sl,
                'tp': pos.tp,
                'profit': pos.profit,
                'swap': pos.swap,
                'commission': pos.commission,
                'time': datetime.fromtimestamp(pos.time),
                'comment': pos.comment
            })
        
        return result
    
    def _round_volume(self, volume: float, symbol_info: Dict) -> float:
        """
        Round volume to valid step for symbol.
        
        Args:
            volume: Desired volume
            symbol_info: Symbol specification
            
        Returns:
            Rounded volume
        """
        min_lot = symbol_info['min_lot']
        max_lot = symbol_info['max_lot']
        lot_step = symbol_info['lot_step']
        
        # Ensure within limits
        volume = max(min_lot, min(max_lot, volume))
        
        # Round to valid step
        steps = round(volume / lot_step)
        return steps * lot_step
    
    def _track_position(self, signal: TradeSignal, result, executed_price: float):
        """
        Track opened position internally.
        
        Args:
            signal: Original trade signal
            result: MT5 execution result
            executed_price: Actual execution price
        """
        self.open_positions[signal.symbol] = {
            'ticket': result.order,
            'deal_id': result.deal,
            'symbol': signal.symbol,
            'direction': signal.direction,
            'volume': result.volume,
            'entry_price': executed_price,
            'sl': signal.sl,
            'tp': signal.tp,
            'opened_at': datetime.utcnow()
        }
    
    def get_trade_history(self, days: int = 30) -> List[Dict]:
        """
        Get trade history for specified number of days.
        
        Args:
            days: Number of days to look back
            
        Returns:
            List of historical trades
        """
        if not self.data_feed.is_connected():
            return []
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Get deals (completed trades)
        deals = mt5.history_deals_get(start_date, end_date)
        if not deals:
            return []
        
        result = []
        for deal in deals:
            if deal.type in [mt5.DEAL_TYPE_BUY, mt5.DEAL_TYPE_SELL]:
                result.append({
                    'ticket': deal.ticket,
                    'order': deal.order,
                    'symbol': deal.symbol,
                    'type': 'BUY' if deal.type == mt5.DEAL_TYPE_BUY else 'SELL',
                    'volume': deal.volume,
                    'price': deal.price,
                    'profit': deal.profit,
                    'swap': deal.swap,
                    'commission': deal.commission,
                    'time': datetime.fromtimestamp(deal.time),
                    'comment': deal.comment
                })
        
        return result
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """
        Get execution statistics.
        
        Returns:
            Dictionary with execution statistics
        """
        positions = self.get_positions()
        history = self.get_trade_history(7)  # Last 7 days
        
        return {
            'open_positions': len(positions),
            'total_exposure': sum(pos['volume'] for pos in positions),
            'unrealized_profit': sum(pos['profit'] for pos in positions),
            'recent_trades': len(history),
            'recent_profit': sum(trade['profit'] for trade in history),
            'tracked_positions': len(self.open_positions)
        } 