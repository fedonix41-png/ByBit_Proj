"""Bybit P2P API client wrapper.

Uses the official bybit_p2p library.
Documentation: https://bybit-exchange.github.io/docs/p2p/guide
"""
import logging
import uuid
from typing import List, Optional, Dict
from datetime import datetime
from models import Order, ChatMessage, Balance
import config

logger = logging.getLogger(__name__)

# Try to import real client, fallback to mock mode
try:
    from bybit_p2p import P2P
    REAL_API_AVAILABLE = True
except ImportError:
    REAL_API_AVAILABLE = False
    logger.warning("bybit-p2p not installed. Running in MOCK mode. Install: uv pip install bybit-p2p")


class BybitClient:
    """Singleton client for Bybit P2P API operations.
    
    Uses official bybit_p2p library.
    API Documentation: https://bybit-exchange.github.io/docs/p2p/guide
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        # Validate configuration (raises if required env vars missing)
        config.validate_config()
        self.api_key = config.BYBIT_API_KEY
        self.api_secret = config.BYBIT_API_SECRET
        self.testnet = config.BYBIT_TESTNET
        self.use_mock = not REAL_API_AVAILABLE or config.USE_MOCK_DATA
        self._initialized = True
        
        if not self.use_mock:
            try:
                self.client = P2P(
                    api_key=self.api_key,
                    api_secret=self.api_secret,
                    testnet=self.testnet
                )
                if self.testnet:
                    logger.info("✅ BybitClient initialized with TESTNET API (safe for development)")
                else:
                    logger.warning("⚠️  BybitClient initialized with PRODUCTION API (real funds at risk!)")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Bybit API client: {e}")
                logger.error("💡 Check your API keys and network connection")
                logger.error("💡 Falling back to MOCK mode")
                self.use_mock = True

        if self.use_mock:
            logger.info("🔧 BybitClient initialized in MOCK mode (limited functionality)")
    
    def _check_response(self, response: dict, method_name: str) -> bool:
        """Check API response for errors.
        
        P2P methods use: ret_code / ret_msg (snake_case)
        Wallet methods use: retCode / retMsg (camelCase)
        """
        ret_code = response.get('ret_code')
        if ret_code is None:
            ret_code = response.get('retCode')
        
        if ret_code == 0:
            return True
        
        ret_msg = response.get('ret_msg') or response.get('retMsg') or 'unknown error'
        logger.error(f"{method_name} failed: [{ret_code}] {ret_msg}")
        return False
    
    # =========================================================================
    # ADVERTISEMENTS
    # =========================================================================
    
    def get_ads_list(self) -> List[Order]:
        """Get list of user's P2P advertisements.
        
        API: get_ads_list()
        Response: result.items
        """
        try:
            if not self.use_mock:
                response = self.client.get_ads_list()
                if not self._check_response(response, 'get_ads_list'):
                    return []
                
                orders = []
                items = response.get('result', {}).get('items', [])
                for item in items:
                    orders.append(Order(
                        order_id=item.get('id', ''),
                        ad_id=item.get('id'),
                        side='SELL' if item.get('side') == '1' else 'BUY',
                        currency=item.get('currencyId', 'RUB'),
                        crypto=item.get('tokenId', 'USDT'),
                        price=float(item.get('price', 0)),
                        amount=float(item.get('lastQuantity', 0)),
                        status=item.get('status', 'active'),
                        created_at=datetime.fromtimestamp(int(item.get('createDate', 0)) / 1000) if item.get('createDate') else None,
                        counterparty=item.get('nickName')
                    ))
                return orders
            
            # Mock data
            return [
                Order(
                    order_id="ORD001",
                    ad_id="AD001",
                    side="SELL",
                    currency="RUB",
                    crypto="USDT",
                    price=95.50,
                    amount=1000.0,
                    status="active",
                    created_at=datetime.now()
                ),
            ]
        except Exception as e:
            logger.error(f"Error fetching ads: {e}")
            raise
    
    def get_online_ads(self, token: str = "USDT", currency: str = "RUB", side: str = "1") -> List[Dict]:
        """Get public online advertisements.
        
        API: get_online_ads(tokenId, currencyId, side)
        side: "1" = sell, "0" = buy
        Response: result.items
        """
        try:
            if not self.use_mock:
                response = self.client.get_online_ads(
                    tokenId=token,
                    currencyId=currency,
                    side=side
                )
                if not self._check_response(response, 'get_online_ads'):
                    return []
                return response.get('result', {}).get('items', [])
            
            return []
        except Exception as e:
            logger.error(f"Error fetching online ads: {e}")
            return []
    
    # =========================================================================
    # ORDERS
    # =========================================================================
    
    def get_orders(self, page: int = 1, size: int = 20) -> List[Dict]:
        """Get all orders.
        
        API: get_orders(page, size)
        Response: result.items
        """
        try:
            if not self.use_mock:
                response = self.client.get_orders(page=page, size=size)
                if not self._check_response(response, 'get_orders'):
                    return []
                return response.get('result', {}).get('items', [])
            
            return []
        except Exception as e:
            logger.error(f"Error fetching orders: {e}")
            return []
    
    def get_pending_orders(self, page: int = 1, size: int = 20) -> List[Dict]:
        """Get pending orders.
        
        API: get_pending_orders(page, size)
        Response: result.items
        """
        try:
            if not self.use_mock:
                response = self.client.get_pending_orders(page=page, size=size)
                if not self._check_response(response, 'get_pending_orders'):
                    return []
                return response.get('result', {}).get('items', [])
            
            return []
        except Exception as e:
            logger.error(f"Error fetching pending orders: {e}")
            return []
    
    def get_order_details(self, order_id: str) -> Optional[Dict]:
        """Get detailed order information.
        
        API: get_order_details(orderId)
        Response: result
        """
        try:
            if not self.use_mock:
                response = self.client.get_order_details(orderId=order_id)
                if not self._check_response(response, 'get_order_details'):
                    return None
                return response.get('result')
            
            # Mock data
            return {
                "order_id": order_id,
                "status": "pending",
                "side": "SELL",
                "crypto": "USDT",
                "amount": 1000.0,
                "price": 95.5,
                "currency": "RUB",
                "payment_method": "Сбербанк",
                "counterparty": "user123",
                "created_at": datetime.now().isoformat(),
                "expires_at": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error fetching order details: {e}")
            return None
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel an advertisement.
        
        API: remove_ad(adId)
        """
        try:
            if not self.use_mock:
                response = self.client.remove_ad(adId=order_id)
                success = self._check_response(response, 'remove_ad')
                if success:
                    logger.info(f"Cancelled ad {order_id}")
                return success
            
            logger.info(f"[MOCK] Cancelling order {order_id}")
            return True
        except Exception as e:
            logger.error(f"Error cancelling order: {e}")
            return False
    
    # =========================================================================
    # PAYMENT & RELEASE
    # =========================================================================
    
    def mark_as_paid(self, order_id: str, payment_type: str, payment_id: str) -> bool:
        """Mark order as paid (buyer action).
        
        API: mark_as_paid(orderId, paymentType, paymentId)
        Required: paymentType and paymentId from user's payment methods.
        """
        try:
            if not self.use_mock:
                response = self.client.mark_as_paid(
                    orderId=order_id,
                    paymentType=payment_type,
                    paymentId=payment_id
                )
                success = self._check_response(response, 'mark_as_paid')
                if success:
                    logger.info(f"Marked order {order_id} as paid")
                return success
            
            logger.info(f"[MOCK] Marking order {order_id} as paid")
            return True
        except Exception as e:
            logger.error(f"Error marking order as paid: {e}")
            return False
    
    def release_assets(self, order_id: str) -> bool:
        """Release crypto to buyer (seller action after payment received).
        
        API: release_assets(orderId)
        """
        try:
            if not self.use_mock:
                response = self.client.release_assets(orderId=order_id)
                success = self._check_response(response, 'release_assets')
                if success:
                    logger.info(f"Released assets for order {order_id}")
                return success
            
            logger.info(f"[MOCK] Releasing assets for order {order_id}")
            return True
        except Exception as e:
            logger.error(f"Error releasing assets: {e}")
            return False
    
    def confirm_payment(self, order_id: str) -> bool:
        """Confirm payment received (deprecated - use release_assets for sellers).
        
        This method is kept for backward compatibility.
        For sellers: use release_assets() to release crypto after receiving payment.
        For buyers: use mark_as_paid() to mark order as paid.
        """
        logger.warning("confirm_payment() is deprecated. Use release_assets() for sellers.")
        return self.release_assets(order_id)
    
    # =========================================================================
    # CHAT / MESSAGES
    # =========================================================================
    
    def get_chat_messages(self, order_id: str, size: int = 30) -> List[ChatMessage]:
        """Get chat messages for a specific order.
        
        API: get_chat_messages(orderId, size)
        Response: result.result (nested!)
        """
        try:
            if not self.use_mock:
                response = self.client.get_chat_messages(orderId=order_id, size=str(size))
                if not self._check_response(response, 'get_chat_messages'):
                    return []
                
                messages = []
                # Note: nested result.result
                items = response.get('result', {}).get('result', [])
                for item in items:
                    messages.append(ChatMessage(
                        message_id=item.get('id', ''),
                        order_id=order_id,
                        sender="me" if item.get('roleType') == 'user' else "counterparty",
                        text=item.get('message', ''),
                        timestamp=datetime.fromtimestamp(int(item.get('createDate', 0)) / 1000) if item.get('createDate') else datetime.now(),
                        read=item.get('isRead', 0) == 1
                    ))
                return messages
            
            # Mock data
            return [
                ChatMessage(
                    message_id="MSG001",
                    order_id=order_id,
                    sender="counterparty",
                    text="Здравствуйте, готов к сделке",
                    timestamp=datetime.now(),
                    read=True
                ),
            ]
        except Exception as e:
            logger.error(f"Error fetching messages for {order_id}: {e}")
            raise
    
    def send_chat_message(self, order_id: str, text: str) -> bool:
        """Send a text message in order chat.
        
        API: send_chat_message(orderId, message, contentType, msgUuid)
        contentType: "str" for text
        msgUuid: unique message ID (required)
        """
        try:
            if not self.use_mock:
                response = self.client.send_chat_message(
                    orderId=order_id,
                    message=text,
                    contentType="str",
                    msgUuid=uuid.uuid4().hex
                )
                success = self._check_response(response, 'send_chat_message')
                if success:
                    logger.info(f"Message sent to {order_id}: {text}")
                return success
            
            logger.info(f"[MOCK] Sending message to {order_id}: {text}")
            return True
        except Exception as e:
            logger.error(f"Error sending message to {order_id}: {e}")
            return False
    
    # =========================================================================
    # USER & PAYMENT METHODS
    # =========================================================================
    
    def get_user_payment_types(self) -> List[Dict]:
        """Get user's payment methods.
        
        API: get_user_payment_types()
        Response: result
        """
        try:
            if not self.use_mock:
                response = self.client.get_user_payment_types()
                if not self._check_response(response, 'get_user_payment_types'):
                    return []
                return response.get('result', [])
            
            # Mock data
            return [
                {"id": "1", "name": "Сбербанк", "type": "BANK_CARD"},
                {"id": "2", "name": "Тинькофф", "type": "BANK_CARD"},
            ]
        except Exception as e:
            logger.error(f"Error fetching payment types: {e}")
            return []
    
    def get_payment_methods(self) -> List[Dict]:
        """Get available payment methods (alias for get_user_payment_types)."""
        return self.get_user_payment_types()
    
    # =========================================================================
    # BALANCE
    # =========================================================================
    
    def get_balance(self, account_type: str = "FUND", coin: str = None) -> List[Balance]:
        """Get account balance.
        
        API: get_current_balance(accountType, coin)
        Response: result.balance with fields:
          - coin: currency
          - transferBalance: available for transfer
          - walletBalance: total balance
          - bonus: bonus amount
        """
        try:
            if not self.use_mock:
                params = {"accountType": account_type}
                if coin:
                    params["coin"] = coin
                
                response = self.client.get_current_balance(**params)
                
                # Wallet methods use camelCase
                ret_code = response.get('retCode')
                if ret_code != 0:
                    logger.error(f"get_balance failed: [{ret_code}] {response.get('retMsg')}")
                    return []
                
                balances = []
                items = response.get('result', {}).get('balance', [])
                for item in items:
                    wallet_balance = float(item.get('walletBalance', 0) or 0)
                    transfer_balance = float(item.get('transferBalance', 0) or 0)
                    
                    balances.append(Balance(
                        currency=item.get('coin', ''),
                        available=transfer_balance,
                        locked=wallet_balance - transfer_balance,
                        total=wallet_balance
                    ))
                return balances
            
            # Mock data
            return [
                Balance(currency="USDT", available=1500.0, locked=500.0, total=2000.0),
            ]
        except Exception as e:
            logger.error(f"Error fetching balance: {e}")
            raise
    
    # =========================================================================
    # CREATE ADVERTISEMENT
    # =========================================================================
    
    def create_ad(self, side: str, currency: str, crypto: str, 
                  price: float, min_amount: float, max_amount: float,
                  payment_methods: List[str]) -> Optional[str]:
        """Create a new P2P advertisement.
        
        API: post_new_ad(...)
        Note: This is a simplified version. Real API requires more parameters.
        """
        try:
            if not self.use_mock:
                response = self.client.post_new_ad(
                    side="1" if side.upper() == "SELL" else "0",
                    tokenId=crypto,
                    currencyId=currency,
                    price=str(price),
                    minAmount=str(min_amount),
                    maxAmount=str(max_amount),
                    paymentIds=payment_methods
                )
                if not self._check_response(response, 'post_new_ad'):
                    return None
                result = response.get('result', {})
                ad_id = result.get('id') or result.get('adId')
                logger.info(f"Created ad {ad_id}")
                return ad_id
            
            logger.info(f"[MOCK] Creating {side} ad: {crypto}/{currency} at {price}")
            return f"AD{int(datetime.now().timestamp())}"
        except Exception as e:
            logger.error(f"Error creating ad: {e}")
            return None
    
    def create_order(self, side: str, currency: str, crypto: str,
                     price: float, amount: float) -> Optional[str]:
        """Create a new P2P order (alias for create_ad)."""
        return self.create_ad(
            side=side,
            currency=currency,
            crypto=crypto,
            price=price,
            min_amount=amount * 0.9,
            max_amount=amount * 1.1,
            payment_methods=[]
        )
    
    # =========================================================================
    # TRADE HISTORY
    # =========================================================================
    
    def get_trade_history(self, limit: int = 20) -> List[Dict]:
        """Get trade history (uses get_orders)."""
        try:
            orders = self.get_orders(page=1, size=limit)
            history = []
            for order in orders:
                history.append({
                    "order_id": order.get('id', ''),
                    "side": "SELL" if order.get('side') == '1' else "BUY",
                    "crypto": order.get('tokenId', 'USDT'),
                    "amount": float(order.get('amount', 0)),
                    "price": float(order.get('price', 0)),
                    "currency": order.get('currencyId', 'RUB'),
                    "status": order.get('status', 'unknown'),
                    "completed_at": order.get('updateDate'),
                })
            return history
        except Exception as e:
            logger.error(f"Error fetching trade history: {e}")
            return []
    
    # =========================================================================
    # APPEAL (Not implemented in bybit_p2p SDK)
    # =========================================================================
    
    def appeal_order(self, order_id: str, reason: str) -> bool:
        """Create an appeal for an order.
        
        Note: This method is not available in bybit_p2p SDK.
        Would need direct API call.
        """
        logger.warning("appeal_order() is not implemented in bybit_p2p SDK")
        if self.use_mock:
            logger.info(f"[MOCK] Creating appeal for order {order_id}: {reason}")
        return False


# Global instance
bybit_client = BybitClient()
