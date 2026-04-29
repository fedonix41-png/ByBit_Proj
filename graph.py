"""LangGraph state machine for P2P automation with human-in-the-loop."""
import logging
from typing import Literal
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from models import P2PState
from bybit_client import bybit_client
import config

logger = logging.getLogger(__name__)

# Node functions
def check_new_message(state: P2PState) -> P2PState:
    """Check for new messages in the order chat."""
    order_id = state.get("current_order_id")
    if not order_id:
        state["error"] = "No order_id provided"
        return state
    
    try:
        messages = bybit_client.get_chat_messages(order_id)
        state["messages"] = [msg.model_dump() for msg in messages]
        
        if messages:
            # Get the last message from counterparty
            counterparty_msgs = [m for m in messages if m.sender == "counterparty"]
            if counterparty_msgs:
                state["last_message"] = counterparty_msgs[-1].model_dump()
                logger.info(f"New message detected: {state['last_message']['text']}")
            else:
                state["last_message"] = None
        else:
            state["last_message"] = None
            
    except Exception as e:
        state["error"] = f"Error checking messages: {str(e)}"
        logger.error(state["error"])
    
    return state

def classify_intent(state: P2PState) -> P2PState:
    """Classify the intent of the last message."""
    last_msg = state.get("last_message")
    if not last_msg:
        state["intent"] = "no_message"
        return state
    
    text = last_msg.get("text", "").lower()
    
    # Simple rule-based classification (can be replaced with LLM)
    if any(word in text for word in ["привет", "здравствуй", "добрый"]):
        state["intent"] = "greeting"
    elif any(word in text for word in ["реквизит", "карт", "счет", "номер", "перевод"]):
        state["intent"] = "payment_details"
    elif any(word in text for word in ["оплатил", "перевел", "отправил", "скинул"]):
        state["intent"] = "confirm_payment"
    elif any(word in text for word in ["мошенник", "обман", "скам"]):
        state["intent"] = "scam"
    else:
        state["intent"] = "unknown"
    
    logger.info(f"Classified intent: {state['intent']}")
    return state

def generate_response(state: P2PState) -> P2PState:
    """Generate appropriate response based on intent."""
    intent = state.get("intent", "unknown")
    
    responses = {
        "greeting": "Здравствуйте! Готов к сделке. Пожалуйста, отправьте реквизиты для перевода.",
        "payment_details": "Спасибо за реквизиты. Проверяю информацию. Ожидайте подтверждения.",
        "confirm_payment": "Проверяю поступление платежа. Пожалуйста, подождите.",
        "scam": "Обнаружено подозрительное сообщение. Требуется ручная проверка.",
        "unknown": "Спасибо за сообщение. Обрабатываю ваш запрос.",
        "no_message": ""
    }
    
    state["proposed_response"] = responses.get(intent, responses["unknown"])
    state["approval_required"] = True
    
    logger.info(f"Generated response: {state['proposed_response']}")
    return state

def await_human_approval(state: P2PState) -> P2PState:
    """Wait for human approval before proceeding."""
    # This is an interrupt point - execution will pause here
    state["approval_required"] = True
    logger.info("Waiting for human approval...")
    return state

def send_message(state: P2PState) -> P2PState:
    """Send the approved message."""
    if not state.get("approval_granted"):
        logger.info("Message sending cancelled by user")
        state["error"] = "Action cancelled by user"
        return state
    
    order_id = state.get("current_order_id")
    response = state.get("proposed_response")
    
    if not response:
        logger.info("No message to send")
        return state
    
    try:
        success = bybit_client.send_chat_message(order_id, response)
        if success:
            logger.info(f"Message sent successfully: {response}")
            state["approval_required"] = False
            state["approval_granted"] = None
        else:
            state["error"] = "Failed to send message"
    except Exception as e:
        state["error"] = f"Error sending message: {str(e)}"
        logger.error(state["error"])
    
    return state

def should_continue(state: P2PState) -> Literal["continue", "end"]:
    """Determine if the graph should continue or end."""
    if state.get("error") or state.get("intent") == "no_message":
        return "end"
    return "continue"

def should_send(state: P2PState) -> Literal["send", "end"]:
    """Determine if message should be sent or cancelled."""
    if state.get("approval_granted"):
        return "send"
    return "end"

# Build the graph
def create_graph():
    """Create and compile the LangGraph state machine."""
    workflow = StateGraph(P2PState)
    
    # Add nodes
    workflow.add_node("check_new_message", check_new_message)
    workflow.add_node("classify_intent", classify_intent)
    workflow.add_node("generate_response", generate_response)
    workflow.add_node("await_human_approval", await_human_approval)
    workflow.add_node("send_message", send_message)
    
    # Define edges
    workflow.set_entry_point("check_new_message")
    workflow.add_conditional_edges(
        "check_new_message",
        should_continue,
        {
            "continue": "classify_intent",
            "end": END
        }
    )
    workflow.add_edge("classify_intent", "generate_response")
    workflow.add_edge("generate_response", "await_human_approval")
    
    # Human-in-the-loop checkpoint
    workflow.add_conditional_edges(
        "await_human_approval",
        should_send,
        {
            "send": "send_message",
            "end": END
        }
    )
    workflow.add_edge("send_message", END)
    
    # Compile with checkpointing using MemorySaver
    memory = MemorySaver()
    graph = workflow.compile(checkpointer=memory, interrupt_before=["await_human_approval"])
    
    logger.info("Graph compiled successfully with MemorySaver checkpointing")
    return graph

# Global graph instance
p2p_graph = create_graph()
