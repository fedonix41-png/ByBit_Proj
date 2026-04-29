"""Main orchestrator for P2P automation."""
import logging
from typing import Dict, Any, List, Optional
from .graph import p2p_graph
from .state import P2PAutomationState
from ..database.session import get_db
from ..database.models import Order, Message, Decision

logger = logging.getLogger(__name__)

class P2POrchestrator:
    """Main orchestrator for P2P automation."""
    
    def __init__(self):
        self.graph = p2p_graph
        self.telegram_bot = None
    
    def set_telegram_bot(self, bot):
        """Set Telegram bot instance."""
        self.telegram_bot = bot
    
    async def process_telegram_message(self, user_id: str, text: str, 
                                      message_id: str, username: str = None):
        """Process message from Telegram."""
        logger.info(f"Processing Telegram message from {user_id}: {text}")
        
        # Find active order for user
        order_id = await self._find_user_order(user_id)
        if not order_id:
            if self.telegram_bot:
                await self.telegram_bot.send_message(
                    user_id, 
                    "У вас нет активных ордеров. Отправьте номер ордера для начала."
                )
            return
        
        # Save message to DB
        await self._save_message(order_id, "counterparty", text, "telegram")
        
        # Run graph
        run_id = f"tg_{user_id}_{message_id}"
        initial_state: P2PAutomationState = {
            "order_id": order_id,
            "user_id": user_id,
            "username": username,
            "run_id": run_id,
            "response_approval_required": False,
            "risk_approval_required": False
        }
        
        config = {"configurable": {"thread_id": run_id}}
        
        try:
            for event in self.graph.stream(initial_state, config):
                logger.info(f"Graph event: {list(event.keys())}")
                
                # Check if waiting for approval
                for node_name, node_state in event.items():
                    if isinstance(node_state, dict):
                        if node_state.get("response_approval_required"):
                            # Send proposed response to admin for approval
                            await self._request_response_approval(node_state)
                        
                        if node_state.get("risk_approval_required"):
                            # Send risk analysis to admin for approval
                            await self._request_risk_approval(node_state)
        
        except Exception as e:
            logger.error(f"Graph execution error: {e}", exc_info=True)
            if self.telegram_bot:
                await self.telegram_bot.send_message(user_id, "❌ Произошла ошибка обработки")
    
    async def process_payment_proof(self, user_id: str, photo_path: str):
        """Process payment proof screenshot."""
        logger.info(f"Processing payment proof from {user_id}")
        
        order_id = await self._find_user_order(user_id)
        if not order_id:
            return
        
        # Update state with payment proof
        run_id = f"tg_{user_id}_payment"
        config = {"configurable": {"thread_id": run_id}}
        
        # Get current state
        state = self.graph.get_state(config)
        if state:
            state.values["payment_proof_path"] = photo_path
            
            # Continue graph execution
            self.graph.update_state(config, state.values)
    
    async def approve_response(self, run_id: str, approved: bool, 
                              modified_response: str = None):
        """Approve or reject proposed response."""
        logger.info(f"Response approval: {run_id} - {approved}")
        
        config = {"configurable": {"thread_id": run_id}}
        
        # Update state
        update = {
            "response_approved": approved,
            "response_approval_required": False
        }
        
        if modified_response:
            update["proposed_response"] = modified_response
        
        self.graph.update_state(config, update)
        
        # Save decision to DB
        state = self.graph.get_state(config)
        if state and state.values.get("order_id"):
            await self._save_decision(
                state.values["order_id"],
                "response_approval",
                approved,
                state.values.get("proposed_response")
            )
    
    async def approve_risk(self, run_id: str, approved: bool, reason: str = None):
        """Approve or reject risk assessment."""
        logger.info(f"Risk approval: {run_id} - {approved}")
        
        config = {"configurable": {"thread_id": run_id}}
        
        # Update state
        update = {
            "risk_approved": approved,
            "risk_approval_required": False
        }
        
        self.graph.update_state(config, update)
        
        # Save decision to DB
        state = self.graph.get_state(config)
        if state and state.values.get("order_id"):
            await self._save_decision(
                state.values["order_id"],
                "risk_approval",
                approved,
                reason,
                state.values.get("risk_score")
            )
    
    async def get_user_orders(self, user_id: str) -> List[Dict[str, Any]]:
        """Get active orders for user."""
        with get_db() as db:
            orders = db.query(Order).filter(
                Order.counterparty_telegram_id == user_id,
                Order.status.in_(["pending", "active"])
            ).all()
            
            return [
                {
                    "order_id": o.order_id,
                    "status": o.status,
                    "amount": o.amount,
                    "crypto": o.crypto,
                    "price": o.price,
                    "currency": o.currency
                }
                for o in orders
            ]
    
    async def _find_user_order(self, user_id: str) -> Optional[str]:
        """Find active order for user."""
        orders = await self.get_user_orders(user_id)
        return orders[0]["order_id"] if orders else None
    
    async def _save_message(self, order_id: str, sender: str, text: str, source: str):
        """Save message to database."""
        with get_db() as db:
            message = Message(
                order_id=order_id,
                message_id=f"{source}_{order_id}_{int(datetime.now().timestamp())}",
                sender=sender,
                text=text,
                source=source
            )
            db.add(message)
    
    async def _save_decision(self, order_id: str, decision_type: str, 
                            approved: bool, proposed_action: str = None,
                            risk_score: float = None):
        """Save decision to database."""
        with get_db() as db:
            decision = Decision(
                order_id=order_id,
                decision_type=decision_type,
                approved=approved,
                proposed_action=proposed_action,
                risk_score=risk_score,
                decided_by="human"
            )
            db.add(decision)
    
    async def _request_response_approval(self, state: Dict[str, Any]):
        """Request response approval from admin."""
        # TODO: Send to admin UI via WebSocket
        logger.info(f"Response approval requested: {state.get('proposed_response')}")
    
    async def _request_risk_approval(self, state: Dict[str, Any]):
        """Request risk approval from admin."""
        # TODO: Send to admin UI via WebSocket
        logger.info(f"Risk approval requested: score={state.get('risk_score')}")

# Global orchestrator instance
orchestrator = P2POrchestrator()
