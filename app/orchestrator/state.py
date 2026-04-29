"""State definition for P2P automation graph."""
from typing import TypedDict, Optional, List, Dict, Any

class P2PAutomationState(TypedDict, total=False):
    """State for P2P automation workflow."""
    
    order_id: str
    order_data: Optional[Dict[str, Any]]
    
    messages: List[Dict[str, Any]]
    last_message: Optional[Dict[str, Any]]
    
    conversation_history: List[Dict[str, str]]
    message_count: int
    session_start: Optional[str]
    
    input_type: Optional[str]
    has_image: bool
    has_voice: bool
    image_analysis: Optional[str]
    voice_transcription: Optional[str]
    
    intent: Optional[str]
    intent_confidence: Optional[float]
    entities: Optional[Dict[str, Any]]
    
    response_type: Optional[str]
    routing: Optional[Dict[str, Any]]
    
    proposed_response: Optional[str]
    response_tone: Optional[str]
    
    payment_proof_path: Optional[str]
    payment_data: Optional[Dict[str, Any]]
    
    risk_score: Optional[float]
    risk_level: Optional[str]
    risk_flags: Optional[List[str]]
    risk_checks: Optional[Dict[str, bool]]
    
    processing_id: Optional[str]
    processing_status: Optional[str]
    
    response_approval_required: bool
    response_approved: Optional[bool]
    risk_approval_required: bool
    risk_approved: Optional[bool]
    
    user_id: Optional[str]
    username: Optional[str]
    user_context: Optional[Dict[str, Any]]
    
    run_id: Optional[str]
    error: Optional[str]
    current_step: Optional[str]
    extra_metadata: Optional[Dict[str, Any]]
