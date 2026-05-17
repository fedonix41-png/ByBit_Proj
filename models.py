"""Data models for P2P automation system."""
from typing import Optional, List, Literal, Dict
from datetime import datetime
from pydantic import BaseModel

# Pydantic models for API responses
class Order(BaseModel):
    """P2P order/advertisement model."""
    order_id: str
    ad_id: Optional[str] = None
    side: Literal["BUY", "SELL"]
    currency: str
    crypto: str
    price: float
    amount: float
    status: str
    created_at: Optional[datetime] = None
    counterparty: Optional[str] = None

class ChatMessage(BaseModel):
    """Chat message model."""
    message_id: str
    order_id: str
    sender: Literal["me", "counterparty"]
    text: str
    timestamp: datetime
    read: bool = False

class Balance(BaseModel):
    """Account balance model."""
    currency: str
    available: float
    locked: float
    total: float

# API Request/Response models
class StartMonitorRequest(BaseModel):
    """Request to start monitoring an order."""
    order_id: str

class ApprovalRequest(BaseModel):
    """Request to approve/reject an action."""
    approved: bool
    user_input: Optional[str] = None

class StateResponse(BaseModel):
    """Current state response."""
    run_id: str
    order_id: str
    status: str
    approval_required: bool
    proposed_response: Optional[str] = None
    intent: Optional[str] = None
    error: Optional[str] = None

class CreateAdRequest(BaseModel):
    """Request to create a new P2P advertisement."""
    side: Literal["BUY", "SELL"]
    currency: str
    crypto: str
    price: float
    min_amount: float
    max_amount: float
    payment_methods: List[str]

class UpdateAdRequest(BaseModel):
    """Request to update an existing advertisement."""
    price: Optional[float] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None

class SendMessageRequest(BaseModel):
    """Request to send a chat message."""
    text: str

class MarkPaidRequest(BaseModel):
    """Request to mark an order as paid."""
    payment_type: str
    payment_id: str

class AccountInfo(BaseModel):
    """User account information."""
    user_id: str
    nickname: str
    status: str
    level: int
    registered_at: Optional[datetime] = None

class CounterpartyInfo(BaseModel):
    """Counterparty information from an order."""
    nickname: str
    rating: float = 0.0
    trades_count: int = 0
    cancellation_rate: float = 0.0
    online_status: str = "unknown"

class OnlineAdsRequest(BaseModel):
    """Request to search online advertisements."""
    token: str = "USDT"
    currency: str = "RUB"
    side: Literal["BUY", "SELL"] = "SELL"

class AdDetails(BaseModel):
    """Detailed advertisement information."""
    ad_id: str
    side: str
    crypto: str
    currency: str
    price: float
    min_amount: float
    max_amount: float
    available_amount: float
    status: str
    payment_methods: List[Dict] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
