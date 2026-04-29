"""Conditional edges for P2P automation graph."""
from typing import Literal
from .state import P2PAutomationState

def should_process_message(state: P2PAutomationState) -> Literal["process", "wait"]:
    """Check if there's a message to process."""
    if state.get("last_message"):
        return "process"
    return "wait"

def should_send_response(state: P2PAutomationState) -> Literal["send", "skip"]:
    """Check if response should be sent."""
    if state.get("response_approved"):
        return "send"
    return "skip"

def should_parse_payment(state: P2PAutomationState) -> Literal["parse", "skip"]:
    """Check if payment proof should be parsed."""
    intent = state.get("intent")
    if intent == "payment_sent" and state.get("payment_proof_path"):
        return "parse"
    return "skip"

def should_analyze_risk(state: P2PAutomationState) -> Literal["analyze", "skip"]:
    """Check if risk analysis is needed."""
    payment_data = state.get("payment_data")
    if payment_data and payment_data.get("confidence", 0) > 0.5:
        return "analyze"
    return "skip"

def should_submit_processing(state: P2PAutomationState) -> Literal["submit", "reject"]:
    """Check if transaction should be submitted to processing."""
    if state.get("risk_approved"):
        return "submit"
    return "reject"

def has_error(state: P2PAutomationState) -> Literal["error", "continue"]:
    """Check if there's an error."""
    if state.get("error"):
        return "error"
    return "continue"
