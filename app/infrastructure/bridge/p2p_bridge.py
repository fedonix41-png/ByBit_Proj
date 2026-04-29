"""Bridge between Telegram interface and P2P orchestrator."""
from typing import Dict, Any, Optional, List
from datetime import datetime
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.domain.prompts.semantic_markers import (
    format_image_message,
    format_voice_message,
    format_payment_proof,
    format_context_message
)


class P2PBridgeService:
    """
    Adapter that translates between Telegram handlers and P2P orchestrator.
    
    Responsibilities:
    - Format incoming Telegram messages for P2P processing
    - Handle voice transcription results
    - Handle image analysis results
    - Convert P2P state to response format
    - Manage conversation context
    """
    
    def __init__(self, orchestrator=None, telegram_bot=None):
        from app.orchestrator.orchestrator import orchestrator as default_orchestrator
        self.orchestrator = orchestrator or default_orchestrator
        self.telegram_bot = telegram_bot
        self._conversation_context: Dict[str, List[Dict[str, str]]] = {}
    
    def set_telegram_bot(self, bot):
        self.telegram_bot = bot
        self.orchestrator.set_telegram_bot(bot)
    
    def set_orchestrator(self, orchestrator):
        self.orchestrator = orchestrator
    
    def _get_conversation_history(self, user_id: str) -> List[Dict[str, str]]:
        """Get conversation history for user."""
        return self._conversation_context.get(str(user_id), [])
    
    def _add_to_history(self, user_id: str, role: str, content: str):
        """Add message to conversation history."""
        user_id = str(user_id)
        if user_id not in self._conversation_context:
            self._conversation_context[user_id] = []
        
        self._conversation_context[user_id].append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        
        from config import settings
        max_history = getattr(settings, 'MAX_CONVERSATION_HISTORY', 20)
        if len(self._conversation_context[user_id]) > max_history:
            self._conversation_context[user_id] = self._conversation_context[user_id][-max_history:]
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception),
        reraise=True
    )
    async def process_text_message(
        self, 
        user_id: int, 
        text: str, 
        username: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process text message from Telegram."""
        logger.info(f"Processing text from user {user_id}: {text[:50]}...")
        
        self._add_to_history(user_id, "user", text)
        
        context_msg = format_context_message({
            "username": username,
            "message_type": "text",
            "history_length": len(self._get_conversation_history(user_id))
        })
        
        await self.orchestrator.process_telegram_message(
            user_id=str(user_id),
            text=text,
            message_id=f"txt_{user_id}_{hash(text) % 1000000}",
            username=username,
            context={
                "input_type": "text",
                "conversation_history": self._get_conversation_history(user_id)
            }
        )
        
        return {
            "response_type": "text",
            "message": None
        }
    
    async def process_voice_message(
        self,
        user_id: int,
        transcription: str,
        username: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process transcribed voice message."""
        logger.info(f"Processing voice from user {user_id}: {transcription[:50]}...")
        
        formatted_message = format_voice_message(transcription)
        self._add_to_history(user_id, "user", f"[VOICE] {transcription}")
        
        return await self.process_text_message(user_id, transcription, username)
    
    async def process_photo_with_analysis(
        self,
        user_id: int,
        photo_path: str,
        analysis: Optional[str] = None,
        caption: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process photo with optional AI analysis."""
        logger.info(f"Processing photo from user {user_id}")
        
        self._add_to_history(user_id, "user", f"[PHOTO] {caption or 'no caption'}")
        
        payment_keywords = ["payment", "платёж", "перевод", "receipt", "чек", 
                           "bank", "банк", "transaction", "транзакция", "transfer"]
        
        if analysis and any(kw in analysis.lower() for kw in payment_keywords):
            formatted = format_payment_proof(analysis, {"source": "vision_analysis"})
            
            await self.orchestrator.process_payment_proof(
                user_id=str(user_id),
                photo_path=photo_path
            )
            return {
                "response_type": "text",
                "message": "📷 Скриншот платежа получен. Анализирую..."
            }
        
        combined_message = format_image_message(caption or "", analysis or "photo attached")
        
        return await self.process_text_message(user_id, combined_message, None)
    
    async def process_payment_proof(
        self,
        user_id: int,
        photo_path: str
    ) -> Dict[str, Any]:
        """Process payment proof directly."""
        logger.info(f"Processing payment proof from user {user_id}")
        
        self._add_to_history(user_id, "user", "[PAYMENT_PROOF]")
        
        await self.orchestrator.process_payment_proof(
            user_id=str(user_id),
            photo_path=photo_path
        )
        
        return {
            "response_type": "text",
            "message": "📷 Скриншот платежа получен. Проверяю..."
        }
    
    def get_conversation_summary(self, user_id: str) -> Dict[str, Any]:
        """Get conversation summary for user."""
        history = self._get_conversation_history(user_id)
        return {
            "user_id": user_id,
            "message_count": len(history),
            "last_message": history[-1] if history else None,
            "session_start": history[0]["timestamp"] if history else None
        }
    
    def clear_conversation(self, user_id: str):
        """Clear conversation history for user."""
        self._conversation_context.pop(str(user_id), None)
        logger.info(f"Cleared conversation for user {user_id}")


p2p_bridge = P2PBridgeService()
