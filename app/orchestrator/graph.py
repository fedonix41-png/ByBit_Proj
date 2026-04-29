"""Main P2P automation graph."""
import logging
import sqlite3
from pathlib import Path
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
from .state import P2PAutomationState
from .nodes import (
    fetch_order_details,
    check_new_messages,
    classify_intent,
    generate_response,
    await_response_approval,
    send_response,
    parse_payment_proof,
    analyze_fraud_risk,
    await_risk_approval,
    submit_to_processing,
    confirm_payment,
    notify_completion
)
from .edges import (
    should_process_message,
    should_send_response,
    should_parse_payment,
    should_analyze_risk,
    should_submit_processing,
    has_error
)

logger = logging.getLogger(__name__)

def create_p2p_graph():
    """Create P2P automation graph."""
    
    workflow = StateGraph(P2PAutomationState)
    
    # Add nodes
    workflow.add_node("fetch_order", fetch_order_details)
    workflow.add_node("check_messages", check_new_messages)
    workflow.add_node("classify_intent", classify_intent)
    workflow.add_node("generate_response", generate_response)
    workflow.add_node("await_response_approval", await_response_approval)
    workflow.add_node("send_response", send_response)
    workflow.add_node("parse_payment", parse_payment_proof)
    workflow.add_node("analyze_risk", analyze_fraud_risk)
    workflow.add_node("await_risk_approval", await_risk_approval)
    workflow.add_node("submit_processing", submit_to_processing)
    workflow.add_node("confirm_payment", confirm_payment)
    workflow.add_node("notify_completion", notify_completion)
    
    # Entry point
    workflow.set_entry_point("fetch_order")
    
    # Edges
    workflow.add_edge("fetch_order", "check_messages")
    
    workflow.add_conditional_edges(
        "check_messages",
        should_process_message,
        {
            "process": "classify_intent",
            "wait": END
        }
    )
    
    workflow.add_edge("classify_intent", "generate_response")
    workflow.add_edge("generate_response", "await_response_approval")
    
    workflow.add_conditional_edges(
        "await_response_approval",
        should_send_response,
        {
            "send": "send_response",
            "skip": END
        }
    )
    
    workflow.add_conditional_edges(
        "send_response",
        should_parse_payment,
        {
            "parse": "parse_payment",
            "skip": END
        }
    )
    
    workflow.add_conditional_edges(
        "parse_payment",
        should_analyze_risk,
        {
            "analyze": "analyze_risk",
            "skip": END
        }
    )
    
    workflow.add_edge("analyze_risk", "await_risk_approval")
    
    workflow.add_conditional_edges(
        "await_risk_approval",
        should_submit_processing,
        {
            "submit": "submit_processing",
            "reject": END
        }
    )
    
    workflow.add_edge("submit_processing", "confirm_payment")
    workflow.add_edge("confirm_payment", "notify_completion")
    workflow.add_edge("notify_completion", END)
    
    db_path = Path("/app/data/checkpoints/p2p_state.db")
    try:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(db_path), check_same_thread=False)
    except (PermissionError, sqlite3.OperationalError):
        db_path = Path("/tmp/p2p_state.db")
        conn = sqlite3.connect(str(db_path), check_same_thread=False)
    
    memory = SqliteSaver(conn)
    
    graph = workflow.compile(
        checkpointer=memory,
        interrupt_before=["await_response_approval", "await_risk_approval"]
    )
    
    logger.info("P2P automation graph compiled successfully")
    return graph

# Global graph instance
p2p_graph = create_p2p_graph()
