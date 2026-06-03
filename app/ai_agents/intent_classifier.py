"""Intent classification AI agent."""
import json
from loguru import logger
from typing import Dict, Any
from .base_agent import BaseAIAgent

class IntentClassifier(BaseAIAgent):
    """Classify customer message intent."""
    
    INTENTS = {
        "greeting": "Приветствие",
        "ready_to_pay": "Готов оплатить",
        "payment_sent": "Платёж отправлен",
        "request_details": "Запрос реквизитов",
        "complaint": "Жалоба",
        "question": "Вопрос",
        "cancel": "Отмена сделки",
        "confirm_receipt": "Подтверждение получения",
        "unknown": "Неизвестно"
    }
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classify message intent.
        
        Args:
            input_data: {
                "message": "текст сообщения",
                "context": {
                    "order_amount": 10000,
                    "currency": "RUB",
                    "order_status": "pending"
                }
            }
        
        Returns:
            {
                "intent": "ready_to_pay",
                "confidence": 0.95,
                "entities": {
                    "amount": 10000,
                    "currency": "RUB"
                }
            }
        """
        message = input_data.get("message", "")
        context = input_data.get("context", {})
        
        system_prompt = self._get_system_prompt()
        user_prompt = self._build_prompt(message, context)
        
        try:
            result = await self.generate(system_prompt, user_prompt, temperature=0.3, json_mode=True)
            parsed = json.loads(result["content"])
            
            logger.debug(f"Intent classified: {parsed.get('intent')} (confidence: {parsed.get('confidence')})")
            
            return {
                "intent": parsed.get("intent", "unknown"),
                "confidence": parsed.get("confidence", 0.0),
                "entities": parsed.get("entities", {}),
                "tokens_used": result.get("tokens", 0),
                "model": result.get("model")
            }
        
        except Exception as e:
            logger.error(f"Intent classification failed: {e}")
            return {
                "intent": "unknown",
                "confidence": 0.0,
                "entities": {},
                "error": str(e)
            }
    
    def _get_system_prompt(self) -> str:
        return """Ты - эксперт по анализу намерений в P2P торговле криптовалютой.

Твоя задача - определить намерение клиента из его сообщения.

Возможные намерения:
- greeting: Приветствие, начало диалога
- ready_to_pay: Клиент готов оплатить
- payment_sent: Клиент отправил платёж (с доказательством или без)
- request_details: Запрос реквизитов для оплаты
- complaint: Жалоба, недовольство
- question: Вопрос о сделке
- cancel: Желание отменить сделку
- confirm_receipt: Подтверждение получения криптовалюты
- unknown: Неясное намерение

Извлекай сущности:
- amount: сумма (если упоминается)
- currency: валюта (RUB, USD, EUR и т.д.)
- card_number: номер карты (если упоминается)
- time: время платежа (если упоминается)

Верни JSON:
{
    "intent": "название_намерения",
    "confidence": 0.0-1.0,
    "entities": {
        "amount": число или null,
        "currency": "валюта" или null,
        "card_number": "номер" или null,
        "time": "время" или null
    }
}"""
    
    def _build_prompt(self, message: str, context: Dict[str, Any]) -> str:
        prompt = f"Сообщение клиента: {message}\n\n"
        
        if context:
            prompt += "Контекст сделки:\n"
            if "order_amount" in context:
                prompt += f"- Сумма сделки: {context['order_amount']} {context.get('currency', 'RUB')}\n"
            if "order_status" in context:
                prompt += f"- Статус: {context['order_status']}\n"
            if "side" in context:
                prompt += f"- Тип: {context['side']}\n"
        
        return prompt
