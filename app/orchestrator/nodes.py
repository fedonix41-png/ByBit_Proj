"""Graph nodes for P2P automation."""
import logging
from typing import Dict, Any
from datetime import datetime
from .state import P2PAutomationState
from ..ai_agents.intent_classifier import IntentClassifier
from ..ai_agents.response_generator import ResponseGenerator
from ..ai_agents.payment_parser import PaymentParser
from ..ai_agents.fraud_analyzer import FraudAnalyzer
from ..integrations.processing_client import processing_client

logger = logging.getLogger(__name__)

# AI agents (lazy initialization)
_intent_classifier = None
_response_generator = None
_payment_parser = None
_fraud_analyzer = None

def get_intent_classifier():
    global _intent_classifier
    if _intent_classifier is None:
        _intent_classifier = IntentClassifier()
    return _intent_classifier

def get_response_generator():
    global _response_generator
    if _response_generator is None:
        _response_generator = ResponseGenerator()
    return _response_generator

def get_payment_parser():
    global _payment_parser
    if _payment_parser is None:
        _payment_parser = PaymentParser()
    return _payment_parser

def get_fraud_analyzer():
    global _fraud_analyzer
    if _fraud_analyzer is None:
        _fraud_analyzer = FraudAnalyzer()
    return _fraud_analyzer

async def fetch_order_details(state: P2PAutomationState) -> P2PAutomationState:
    """Fetch order details from Bybit."""
    from ..integrations.bybit_client import bybit_client
    
    order_id = state.get("order_id")
    logger.info(f"Fetching order details: {order_id}")
    
    try:
        order_details = bybit_client.get_order_details(order_id)
        state["order_data"] = order_details
        state["current_step"] = "fetch_order_details"
    except Exception as e:
        logger.error(f"Failed to fetch order: {e}")
        state["error"] = str(e)
    
    return state

async def check_new_messages(state: P2PAutomationState) -> P2PAutomationState:
    """Check for new messages."""
    from ..integrations.bybit_client import bybit_client
    
    order_id = state.get("order_id")
    logger.info(f"Checking messages for order: {order_id}")
    
    try:
        messages = bybit_client.get_chat_messages(order_id)
        state["messages"] = [msg.model_dump() for msg in messages]
        
        # Get last counterparty message
        counterparty_msgs = [m for m in messages if m.sender == "counterparty"]
        if counterparty_msgs:
            state["last_message"] = counterparty_msgs[-1].model_dump()
        
        state["current_step"] = "check_new_messages"
    except Exception as e:
        logger.error(f"Failed to check messages: {e}")
        state["error"] = str(e)
    
    return state

async def classify_intent(state: P2PAutomationState) -> P2PAutomationState:
    """Classify message intent using AI."""
    last_message = state.get("last_message")
    if not last_message:
        state["intent"] = "no_message"
        return state
    
    logger.info("Classifying intent...")
    
    try:
        order_data = state.get("order_data", {})
        result = await get_intent_classifier().process({
            "message": last_message.get("text", ""),
            "context": {
                "order_amount": order_data.get("amount"),
                "currency": order_data.get("currency"),
                "order_status": order_data.get("status"),
                "side": order_data.get("side")
            }
        })
        
        state["intent"] = result.get("intent")
        state["intent_confidence"] = result.get("confidence")
        state["entities"] = result.get("entities")
        state["current_step"] = "classify_intent"
        
        logger.info(f"Intent: {state['intent']} (confidence: {state['intent_confidence']})")
    
    except Exception as e:
        logger.error(f"Intent classification failed: {e}")
        state["error"] = str(e)
        state["intent"] = "unknown"
    
    return state

async def generate_response(state: P2PAutomationState) -> P2PAutomationState:
    """Generate response using AI."""
    logger.info("Generating response...")
    
    try:
        last_message = state.get("last_message", {})
        order_data = state.get("order_data", {})
        
        result = await get_response_generator().process({
            "intent": state.get("intent"),
            "message": last_message.get("text", ""),
            "context": {
                "order_id": state.get("order_id"),
                "order_amount": order_data.get("amount"),
                "currency": order_data.get("currency"),
                "side": order_data.get("side"),
                "payment_methods": ["Сбербанк", "Тинькофф"]
            }
        })
        
        state["proposed_response"] = result.get("response")
        state["response_tone"] = result.get("tone")
        state["response_approval_required"] = True
        state["current_step"] = "generate_response"
        
        logger.info(f"Response generated: {state['proposed_response'][:50]}...")
    
    except Exception as e:
        logger.error(f"Response generation failed: {e}")
        state["error"] = str(e)
    
    return state

async def await_response_approval(state: P2PAutomationState) -> P2PAutomationState:
    """Wait for human approval of response."""
    logger.info("Awaiting response approval...")
    state["current_step"] = "await_response_approval"
    return state

async def send_response(state: P2PAutomationState) -> P2PAutomationState:
    """Send approved response."""
    from ..integrations.bybit_client import bybit_client
    
    if not state.get("response_approved"):
        logger.info("Response not approved, skipping send")
        return state
    
    order_id = state.get("order_id")
    response = state.get("proposed_response")
    
    logger.info(f"Sending response to order {order_id}")
    
    try:
        success = bybit_client.send_chat_message(order_id, response)
        if success:
            state["response_approval_required"] = False
            state["current_step"] = "send_response"
        else:
            state["error"] = "Failed to send message"
    
    except Exception as e:
        logger.error(f"Failed to send response: {e}")
        state["error"] = str(e)
    
    return state

async def parse_payment_proof(state: P2PAutomationState) -> P2PAutomationState:
    """Parse payment proof screenshot."""
    payment_proof_path = state.get("payment_proof_path")
    if not payment_proof_path:
        logger.info("No payment proof to parse")
        return state
    
    logger.info("Parsing payment proof...")
    
    try:
        order_data = state.get("order_data", {})
        result = await get_payment_parser().process({
            "image_path": payment_proof_path,
            "expected_amount": order_data.get("amount"),
            "expected_currency": order_data.get("currency")
        })
        
        state["payment_data"] = result
        state["current_step"] = "parse_payment_proof"
        
        logger.info(f"Payment parsed: amount={result.get('amount')}, confidence={result.get('confidence')}")
    
    except Exception as e:
        logger.error(f"Payment parsing failed: {e}")
        state["error"] = str(e)
    
    return state

async def analyze_fraud_risk(state: P2PAutomationState) -> P2PAutomationState:
    """Analyze fraud risk."""
    logger.info("Analyzing fraud risk...")
    
    try:
        payment_data = state.get("payment_data", {})
        order_data = state.get("order_data", {})
        
        result = await get_fraud_analyzer().process({
            "payment_data": payment_data,
            "order_data": order_data,
            "counterparty_history": {
                "total_trades": 5,
                "successful_trades": 5,
                "disputes": 0
            }
        })
        
        state["risk_score"] = result.get("risk_score")
        state["risk_level"] = result.get("risk_level")
        state["risk_flags"] = result.get("flags")
        state["risk_checks"] = result.get("checks")
        state["risk_approval_required"] = True
        state["current_step"] = "analyze_fraud_risk"
        
        logger.info(f"Risk analysis: score={state['risk_score']}, level={state['risk_level']}")
    
    except Exception as e:
        logger.error(f"Risk analysis failed: {e}")
        state["error"] = str(e)
    
    return state

async def await_risk_approval(state: P2PAutomationState) -> P2PAutomationState:
    """Wait for human approval of risk assessment."""
    logger.info("Awaiting risk approval...")
    state["current_step"] = "await_risk_approval"
    return state

async def submit_to_processing(state: P2PAutomationState) -> P2PAutomationState:
    """Submit transaction to processing API."""
    if not state.get("risk_approved"):
        logger.info("Risk not approved, skipping processing")
        return state
    
    logger.info("Submitting to processing...")
    
    try:
        order_data = state.get("order_data", {})
        payment_data = state.get("payment_data", {})
        
        result = await processing_client.submit_transaction({
            "order_id": state.get("order_id"),
            "amount": payment_data.get("amount"),
            "currency": payment_data.get("currency"),
            "card_number": payment_data.get("card_number"),
            "payment_proof_url": state.get("payment_proof_path"),
            "extra_metadata": {
                "risk_score": state.get("risk_score"),
                "risk_level": state.get("risk_level")
            }
        })
        
        state["processing_id"] = result.get("processing_id")
        state["processing_status"] = result.get("status")
        state["current_step"] = "submit_to_processing"
        
        logger.info(f"Submitted to processing: {state['processing_id']}")
    
    except Exception as e:
        logger.error(f"Processing submission failed: {e}")
        state["error"] = str(e)
    
    return state

async def confirm_payment(state: P2PAutomationState) -> P2PAutomationState:
    """Confirm payment in Bybit."""
    from ..integrations.bybit_client import bybit_client
    
    order_id = state.get("order_id")
    logger.info(f"Confirming payment for order {order_id}")
    
    try:
        success = bybit_client.confirm_payment(order_id)
        if success:
            state["current_step"] = "confirm_payment"
        else:
            state["error"] = "Failed to confirm payment"
    
    except Exception as e:
        logger.error(f"Payment confirmation failed: {e}")
        state["error"] = str(e)
    
    return state

async def notify_completion(state: P2PAutomationState) -> P2PAutomationState:
    """Send completion notification."""
    logger.info("Sending completion notification...")
    
    # TODO: Send Telegram notification
    state["current_step"] = "notify_completion"
    
    return state
