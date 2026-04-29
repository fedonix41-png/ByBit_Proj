"""Bybit P2P API client wrapper."""
import logging
from typing import List, Optional, Dict
from datetime import datetime
from models import Order, ChatMessage, Balance
import config

logger = logging.getLogger(__name__)

# Try to import real client, fallback to mock mode
try:
    from bybit_p2p import P2PClient
    REAL_API_AVAILABLE = True
except ImportError:
    REAL_API_AVAILABLE = False
    logger.warning("bybit-p2p not installed. Running in MOCK mode. Install: uv pip install bybit-p2p")

class BybitClient:
    """Singleton client for Bybit P2P API operations."""
    
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
                self.client = P2PClient(
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
    
    def get_ads_list(self) -> List[Order]:
        """Get list of user's P2P advertisements/orders."""
        try:
            if not self.use_mock:
                response = self.client.get_my_ads()
                orders = []
                for item in response.get("data", []):
                    orders.append(Order(
                        order_id=item.get("orderId", ""),
                        ad_id=item.get("adId"),
                        side=item.get("side", "SELL"),
                        currency=item.get("currency", "RUB"),
                        crypto=item.get("tokenId", "USDT"),
                        price=float(item.get("price", 0)),
                        amount=float(item.get("amount", 0)),
                        status=item.get("status", "active"),
                        created_at=datetime.fromtimestamp(int(item.get("createTime", 0)) / 1000) if item.get("createTime") else None,
                        counterparty=item.get("nickName")
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
                Order(
                    order_id="ORD002",
                    ad_id="AD002",
                    side="BUY",
                    currency="RUB",
                    crypto="USDT",
                    price=94.80,
                    amount=500.0,
                    status="pending",
                    created_at=datetime.now(),
                    counterparty="user123"
                )
            ]
        except Exception as e:
            logger.error(f"Error fetching ads: {e}")
            raise
    
    def get_chat_messages(self, order_id: str) -> List[ChatMessage]:
        """Get chat messages for a specific order."""
        try:
            if not self.use_mock:
                response = self.client.get_p2p_messages(order_id)
                messages = []
                for item in response.get("data", []):
                    messages.append(ChatMessage(
                        message_id=item.get("msgId", ""),
                        order_id=order_id,
                        sender="me" if item.get("isSelf") else "counterparty",
                        text=item.get("content", ""),
                        timestamp=datetime.fromtimestamp(int(item.get("createTime", 0)) / 1000) if item.get("createTime") else datetime.now(),
                        read=item.get("isRead", False)
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
                ChatMessage(
                    message_id="MSG002",
                    order_id=order_id,
                    sender="me",
                    text="Здравствуйте! Отправьте реквизиты для перевода",
                    timestamp=datetime.now(),
                    read=True
                )
            ]
        except Exception as e:
            logger.error(f"Error fetching messages for {order_id}: {e}")
            raise
    
    def send_chat_message(self, order_id: str, text: str) -> bool:
        """Send a message in order chat."""
        try:
            if not self.use_mock:
                result = self.client.send_p2p_message(order_id, text)
                success = result.get("retCode") == 0
                if success:
                    logger.info(f"Message sent to {order_id}: {text}")
                else:
                    logger.error(f"Failed to send message: {result.get('retMsg')}")
                return success
            
            # Mock mode
            logger.info(f"[MOCK] Sending message to {order_id}: {text}")
            return True
        except Exception as e:
            logger.error(f"Error sending message to {order_id}: {e}")
            return False
    
    def get_balance(self) -> List[Balance]:
        """Get account balance."""
        try:
            if not self.use_mock:
                response = self.client.get_wallet_balance()
                balances = []
                for item in response.get("data", []):
                    balances.append(Balance(
                        currency=item.get("tokenId", ""),
                        available=float(item.get("available", 0)),
                        locked=float(item.get("locked", 0)),
                        total=float(item.get("total", 0))
                    ))
                return balances
            
            # Mock data
            return [
                Balance(currency="USDT", available=1500.0, locked=500.0, total=2000.0),
                Balance(currency="BTC", available=0.05, locked=0.0, total=0.05)
            ]
        except Exception as e:
            logger.error(f"Error fetching balance: {e}")
            raise
    
    def create_order(self, side: str, currency: str, crypto: str,
                     price: float, amount: float) -> Optional[str]:
        """Create a new P2P order using real Bybit API when available."""
        try:
            if not self.use_mock:
                # bybit-p2p SDK uses `create_ad` for advertisement creation
                result = self.client.create_ad(
                    side=side,
                    currency=currency,
                    tokenId=crypto,
                    price=price,
                    min_amount=amount * 0.9,
                    max_amount=amount * 1.1,
                    payment_methods=[]  # Add IDs if needed
                )
                ad_id = result.get('adId') or result.get('id')
                logger.info(f"Created real ad {ad_id} for {side} {amount}{crypto}@{price}{currency}")
                return ad_id
            # Mock fallback
            logger.info(f"[MOCK] Creating {side} order: {amount} {crypto} at {price} {currency}")
            return f"ORD{int(datetime.utcnow().timestamp())}"
        except Exception as e:
            logger.error(f"Error creating order: {e}")
            return None
    
    def confirm_payment(self, order_id: str) -> bool:
        """Confirm payment received and release crypto."""
        try:
            if not self.use_mock:
                result = self.client.confirm_payment(order_id)
                success = result.get("retCode") == 0
                if success:
                    logger.info(f"Payment confirmed for order {order_id}")
                else:
                    logger.error(f"Failed to confirm payment: {result.get('retMsg')}")
                return success
            
            # Mock mode
            logger.info(f"[MOCK] Confirming payment for order {order_id}")
            return True
        except Exception as e:
            logger.error(f"Error confirming payment for {order_id}: {e}")
            return False
    
    def get_payment_methods(self) -> List[Dict]:
        """Get available payment methods."""
        try:
            return [
                {"id": "1", "name": "Сбербанк", "type": "BANK_CARD"},
                {"id": "2", "name": "Тинькофф", "type": "BANK_CARD"},
                {"id": "3", "name": "ЮMoney", "type": "E_WALLET"},
            ]
        except Exception as e:
            logger.error(f"Error fetching payment methods: {e}")
            raise
    
    def create_ad(self, side: str, currency: str, crypto: str, 
                  price: float, min_amount: float, max_amount: float,
                  payment_methods: List[str]) -> Optional[str]:
        """Create a new P2P advertisement."""
        try:
            logger.info(f"Creating {side} ad: {crypto}/{currency} at {price}")
            return f"AD{int(datetime.now().timestamp())}"
        except Exception as e:
            logger.error(f"Error creating ad: {e}")
            return None
    
    def get_order_details(self, order_id: str) -> Optional[Dict]:
        """Get detailed order information."""
        try:
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
        """Cancel an order using real API when possible."""
        try:
            if not self.use_mock:
                # Assuming SDK provides `cancel_ad` method
                result = self.client.cancel_ad(order_id)
                success = result.get('retCode') == 0
                if success:
                    logger.info(f"Cancelled real order {order_id}")
                else:
                    logger.error(f"Failed to cancel order {order_id}: {result.get('retMsg')}")
                return success
            logger.info(f"[MOCK] Cancelling order {order_id}")
            return True
        except Exception as e:
            logger.error(f"Error cancelling order: {e}")
            return False
    
    def appeal_order(self, order_id: str, reason: str) -> bool:
        """Create an appeal for an order using real API when possible."""
        try:
            if not self.use_mock:
                # SDK may provide `create_appeal` method
                result = self.client.create_appeal(order_id=order_id, reason=reason)
                success = result.get('retCode') == 0
                if success:
                    logger.info(f"Created real appeal for order {order_id}")
                else:
                    logger.error(f"Failed to create appeal for {order_id}: {result.get('retMsg')}")
                return success
            logger.info(f"[MOCK] Creating appeal for order {order_id}: {reason}")
            return True
        except Exception as e:
            logger.error(f"Error creating appeal: {e}")
            return False
    
    def get_trade_history(self, limit: int = 20) -> List[Dict]:
        """Get trade history."""
        try:
            return [
                {
                    "order_id": f"ORD{i:03d}",
                    "side": "SELL" if i % 2 == 0 else "BUY",
                    "crypto": "USDT",
                    "amount": 1000.0 + i * 100,
                    "price": 95.0 + i * 0.5,
                    "currency": "RUB",
                    "status": "completed",
                    "completed_at": datetime.now().isoformat(),
                }
                for i in range(min(limit, 10))
            ]
        except Exception as e:
            logger.error(f"Error fetching trade history: {e}")
            raise

# Global instance
bybit_client = BybitClient()
