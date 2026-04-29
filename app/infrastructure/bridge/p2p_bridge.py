"""Bridge between Telegram interface and P2P orchestrator."""
from typing import Dict, Any, Optional
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type


class P2PBridgeService:
    """
    Adapter that translates between Telegram handlers and P2P orchestrator.
    
    Responsibilities:
    - Format incoming Telegram messages for P2P processing
    - Handle voice transcription results
    - Handle image analysis results
    - Convert P2P state to response format
    """
    
    def __init__(self, orchestrator=None, telegram_bot=None):
        from app.orchestrator.orchestrator import orchestrator as default_orchestrator
        self.orchestrator = orchestrator or default_orchestrator
        self.telegram_bot = telegram_bot
    
    def set_telegram_bot(self, bot):
        self.telegram_bot = bot
        self.orchestrator.set_telegram_bot(bot)
    
    def set_orchestrator(self, orchestrator):
        self.orchestrator = orchestrator
    
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
        
        await self.orchestrator.process_telegram_message(
            user_id=str(user_id),
            text=text,
            message_id=f"txt_{user_id}_{hash(text) % 1000000}",
            username=username
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
        
        if analysis and any(kw in analysis.lower() for kw in ["payment", "payment", "transfer", "receipt", "bank", "transaction"]):
            await self.orchestrator.process_payment_proof(
                user_id=str(user_id),
                photo_path=photo_path
            )
            return {
                "response_type": "text",
                "message": "Скриншот платежа получен. Анализирую..."
            }
        
        combined_message = f"{caption or ''} [Image context: {analysis or 'photo attached'}]".strip()
        return await self.process_text_message(user_id, combined_message)
    
    async def process_payment_proof(
        self,
        user_id: int,
        photo_path: str
    ) -> Dict[str, Any]:
        """Process payment proof directly."""
        logger.info(f"Processing payment proof from user {user_id}")
        
        await self.orchestrator.process_payment_proof(
            user_id=str(user_id),
            photo_path=photo_path
        )
        
        return {
            "response_type": "text",
            "message": "Скриншот платежа получен. Проверяю..."
        }


p2p_bridge = P2PBridgeService()
