"""State definition for P2P automation graph."""
from typing import TypedDict, Optional, List, Dict, Any

class P2PAutomationState(TypedDict, total=False):
    """State for P2P automation workflow."""
    
    # Order info
    order_id: str
    order_data: Optional[Dict[str, Any]]
    
    # Messages
    messages: List[Dict[str, Any]]
    last_message: Optional[Dict[str, Any]]
    
    # AI analysis
    intent: Optional[str]
    intent_confidence: Optional[float]
    entities: Optional[Dict[str, Any]]
    
    # Response generation
    proposed_response: Optional[str]
    response_tone: Optional[str]
    
    # Payment processing
    payment_proof_path: Optional[str]
    payment_data: Optional[Dict[str, Any]]
    
    # Risk analysis
    risk_score: Optional[float]
    risk_level: Optional[str]
    risk_flags: Optional[List[str]]
    risk_checks: Optional[Dict[str, bool]]
    
    # Processing
    processing_id: Optional[str]
    processing_status: Optional[str]
    
    # Approvals
    response_approval_required: bool
    response_approved: Optional[bool]
    risk_approval_required: bool
    risk_approved: Optional[bool]
    
    # User context
    user_id: Optional[str]
    username: Optional[str]
    
    # Metadata
    run_id: Optional[str]
    error: Optional[str]
    current_step: Optional[str]
    extra_metadata: Optional[Dict[str, Any]]
