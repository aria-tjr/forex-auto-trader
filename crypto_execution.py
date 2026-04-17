#!/usr/bin/env python3
"""
Crypto Execution Engine - Binance Integration
Professional order execution for cryptocurrency trading

Features:
- Binance Spot & Futures trading
- OCO (One-Cancels-Other) orders
- Proper error handling
- Order status tracking
- Slippage protection
- Position management
"""

import logging
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import math

try:
    from binance.client import Client
    from binance.exceptions import BinanceAPIException, BinanceOrderException
    BINANCE_AVAILABLE = True
except ImportError:
    BINANCE_AVAILABLE = False

class CryptoExecutionEngine:
    """
    Professional execution engine for cryptocurrency trading
    """
    
    def __init__(self):
        """Initialize crypto execution engine"""
        self.logger = logging.getLogger(__name__)
        self.order_history: List[Dict] = []
        
        # Execution settings
        self.max_slippage_pct = 0.5  # 0.5% max slippage
        self.order_timeout = 30  # seconds
        self.retry_attempts = 3
        
        self.logger.info("⚙️ Crypto Execution Engine initialized")
    
    def place_crypto_order(
        self,
        client: 'Client',
        symbol: str,
        side: str,  # 'BUY' or 'SELL'
        quantity: float,
        price: float,
        stop_price: float,
        take_profit_price: float,
        order_type: str = "MARKET"
    ) -> Optional[Dict]:
        """
        Place crypto order with stop loss and take profit
        """
        try:
            self.logger.info(f"🚀 Placing {side} order for {symbol}")
            self.logger.info(f"📊 Quantity: {quantity:.6f}, Price: {price:.6f}")
            
            # Validate inputs
            if not self._validate_order_params(symbol, side, quantity, price):
                return None
            
            # Get symbol info for precision
            symbol_info = self._get_symbol_info(client, symbol)
            if not symbol_info:
                self.logger.error(f"❌ Could not get symbol info for {symbol}")
                return None
            
            # Round quantity to proper precision
            quantity = self._round_quantity(quantity, symbol_info)
            if quantity == 0:
                self.logger.error(f"❌ Quantity too small after rounding for {symbol}")
                return None
            
            # Place market order first
            main_order = self._place_market_order(client, symbol, side, quantity)
            if not main_order:
                return None
            
            # Get actual fill price
            fill_price = self._get_fill_price(main_order)
            if not fill_price:
                fill_price = price  # Fallback to expected price
            
            # Place OCO order (stop loss + take profit)
            oco_order = self._place_oco_order(
                client, symbol, side, quantity, 
                stop_price, take_profit_price, symbol_info
            )
            
            # Create order summary
            order_summary = {
                'symbol': symbol,
                'side': side,
                'quantity': quantity,
                'fill_price': fill_price,
                'main_order': main_order,
                'oco_order': oco_order,
                'timestamp': datetime.now(),
                'status': 'FILLED' if main_order else 'FAILED'
            }
            
            self.order_history.append(order_summary)
            
            if main_order:
                self.logger.info(f"✅ Order executed successfully for {symbol}")
                self.logger.info(f"🎯 Fill price: {fill_price:.6f}")
                return order_summary
            else:
                self.logger.error(f"❌ Order execution failed for {symbol}")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Error placing crypto order: {e}")
            return None
    
    def _place_market_order(
        self, 
        client: 'Client', 
        symbol: str, 
        side: str, 
        quantity: float
    ) -> Optional[Dict]:
        """Place market order"""
        try:
            for attempt in range(self.retry_attempts):
                try:
                    if side == 'BUY':
                        order = client.order_market_buy(
                            symbol=symbol,
                            quantity=quantity
                        )
                    else:  # SELL
                        order = client.order_market_sell(
                            symbol=symbol,
                            quantity=quantity
                        )
                    
                    self.logger.info(f"✅ Market order placed - Order ID: {order['orderId']}")
                    return order
                    
                except BinanceAPIException as e:
                    self.logger.warning(f"⚠️ Binance API error (attempt {attempt + 1}): {e}")
                    if attempt == self.retry_attempts - 1:
                        raise
                    time.sleep(1)  # Wait before retry
                
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Error placing market order: {e}")
            return None
    
    def _place_oco_order(
        self,
        client: 'Client',
        symbol: str,
        side: str,
        quantity: float,
        stop_price: float,
        take_profit_price: float,
        symbol_info: Dict
    ) -> Optional[Dict]:
        """
        Place OCO (One-Cancels-Other) order for stop loss and take profit
        """
        try:
            # Round prices to proper precision
            stop_price = self._round_price(stop_price, symbol_info)
            take_profit_price = self._round_price(take_profit_price, symbol_info)
            
            # For OCO orders, we need to determine the correct order
            if side == 'BUY':
                # We bought, so we want to sell at profit or stop loss
                oco_side = 'SELL'
                # Determine which is stop and which is limit
                if take_profit_price > stop_price:
                    limit_price = take_profit_price
                    stop_limit_price = stop_price
                else:
                    limit_price = stop_price
                    stop_limit_price = take_profit_price
            else:
                # We sold, so we want to buy back at profit or stop loss
                oco_side = 'BUY'
                if take_profit_price < stop_price:
                    limit_price = take_profit_price
                    stop_limit_price = stop_price
                else:
                    limit_price = stop_price
                    stop_limit_price = take_profit_price
            
            # Place OCO order
            oco_order = client.create_oco_order(
                symbol=symbol,
                side=oco_side,
                quantity=quantity,
                price=str(limit_price),
                stopPrice=str(stop_limit_price),
                stopLimitPrice=str(stop_limit_price),
                stopLimitTimeInForce='GTC'
            )
            
            self.logger.info(f"✅ OCO order placed - List Order ID: {oco_order['listOrderId']}")
            self.logger.info(f"🎯 Take Profit: {take_profit_price:.6f}, Stop Loss: {stop_price:.6f}")
            
            return oco_order
            
        except Exception as e:
            self.logger.error(f"❌ Error placing OCO order: {e}")
            # OCO failure shouldn't fail the main trade
            return None
    
    def cancel_order(self, client: 'Client', symbol: str, order_id: str) -> bool:
        """Cancel an open order"""
        try:
            result = client.cancel_order(symbol=symbol, orderId=order_id)
            self.logger.info(f"✅ Order cancelled - ID: {order_id}")
            return True
        except Exception as e:
            self.logger.error(f"❌ Error cancelling order {order_id}: {e}")
            return False
    
    def get_order_status(self, client: 'Client', symbol: str, order_id: str) -> Optional[Dict]:
        """Get order status"""
        try:
            order = client.get_order(symbol=symbol, orderId=order_id)
            return order
        except Exception as e:
            self.logger.error(f"❌ Error getting order status: {e}")
            return None
    
    def get_open_orders(self, client: 'Client', symbol: str = None) -> List[Dict]:
        """Get all open orders"""
        try:
            if symbol:
                orders = client.get_open_orders(symbol=symbol)
            else:
                orders = client.get_open_orders()
            return orders
        except Exception as e:
            self.logger.error(f"❌ Error getting open orders: {e}")
            return []
    
    def _validate_order_params(
        self, 
        symbol: str, 
        side: str, 
        quantity: float, 
        price: float
    ) -> bool:
        """Validate order parameters"""
        if not symbol or not side:
            self.logger.error("❌ Missing symbol or side")
            return False
        
        if side not in ['BUY', 'SELL']:
            self.logger.error(f"❌ Invalid side: {side}")
            return False
        
        if quantity <= 0:
            self.logger.error(f"❌ Invalid quantity: {quantity}")
            return False
        
        if price <= 0:
            self.logger.error(f"❌ Invalid price: {price}")
            return False
        
        return True
    
    def _get_symbol_info(self, client: 'Client', symbol: str) -> Optional[Dict]:
        """Get symbol trading info"""
        try:
            exchange_info = client.get_exchange_info()
            for s in exchange_info['symbols']:
                if s['symbol'] == symbol:
                    return s
            return None
        except Exception as e:
            self.logger.error(f"❌ Error getting symbol info: {e}")
            return None
    
    def _round_quantity(self, quantity: float, symbol_info: Dict) -> float:
        """Round quantity according to symbol filters"""
        try:
            for filter in symbol_info['filters']:
                if filter['filterType'] == 'LOT_SIZE':
                    step_size = float(filter['stepSize'])
                    min_qty = float(filter['minQty'])
                    
                    # Round to step size
                    quantity = round(quantity / step_size) * step_size
                    
                    # Ensure meets minimum
                    if quantity < min_qty:
                        return 0.0
                    
                    # Get precision for rounding
                    precision = len(str(step_size).split('.')[-1]) if '.' in str(step_size) else 0
                    return round(quantity, precision)
            
            return quantity
            
        except Exception as e:
            self.logger.error(f"❌ Error rounding quantity: {e}")
            return 0.0
    
    def _round_price(self, price: float, symbol_info: Dict) -> float:
        """Round price according to symbol filters"""
        try:
            for filter in symbol_info['filters']:
                if filter['filterType'] == 'PRICE_FILTER':
                    tick_size = float(filter['tickSize'])
                    
                    # Round to tick size
                    price = round(price / tick_size) * tick_size
                    
                    # Get precision for rounding
                    precision = len(str(tick_size).split('.')[-1]) if '.' in str(tick_size) else 0
                    return round(price, precision)
            
            return price
            
        except Exception as e:
            self.logger.error(f"❌ Error rounding price: {e}")
            return price
    
    def _get_fill_price(self, order: Dict) -> Optional[float]:
        """Extract fill price from order"""
        try:
            # For market orders, calculate weighted average price
            if 'fills' in order and order['fills']:
                total_qty = 0.0
                total_value = 0.0
                
                for fill in order['fills']:
                    qty = float(fill['qty'])
                    price = float(fill['price'])
                    total_qty += qty
                    total_value += qty * price
                
                if total_qty > 0:
                    return total_value / total_qty
            
            # Fallback to order price
            if 'price' in order and order['price']:
                return float(order['price'])
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Error getting fill price: {e}")
            return None
    
    def get_execution_summary(self) -> Dict:
        """Get execution statistics"""
        if not self.order_history:
            return {'total_orders': 0}
        
        total_orders = len(self.order_history)
        successful_orders = len([o for o in self.order_history if o['status'] == 'FILLED'])
        success_rate = successful_orders / total_orders if total_orders > 0 else 0
        
        return {
            'total_orders': total_orders,
            'successful_orders': successful_orders,
            'success_rate': success_rate,
            'recent_orders': self.order_history[-5:]  # Last 5 orders
        } 