"""Data models for P2P automation system."""
from typing import Optional, List, Literal
from datetime import datetime
from pydantic import BaseModel, Field
from typing_extensions import TypedDict

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

# LangGraph State (TypedDict for graph state)
class P2PState(TypedDict, total=False):
    """State for P2P automation graph."""
    messages: List[dict]  # Chat message history
    current_order_id: str
    last_message: Optional[dict]
    intent: str  # "greeting", "payment_details", "confirm_payment", "scam", "unknown"
    proposed_response: Optional[str]
    approval_required: bool
    approval_granted: Optional[bool]
    user_input: Optional[str]  # For manual input (amount, decision)
    error: Optional[str]
    run_id: Optional[str]

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
