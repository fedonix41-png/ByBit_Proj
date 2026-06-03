"""Response generation AI agent."""
import json
from loguru import logger
from typing import Dict, Any
from .base_agent import BaseAIAgent

class ResponseGenerator(BaseAIAgent):
    """Generate responses to customer messages."""
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate response based on intent and context.
        
        Args:
            input_data: {
                "intent": "ready_to_pay",
                "message": "Здравствуйте, готов оплатить",
                "context": {
                    "order_id": "ORD123",
                    "order_amount": 10000,
                    "currency": "RUB",
                    "side": "SELL",
                    "payment_methods": ["Сбербанк", "Тинькофф"]
                }
            }
        
        Returns:
            {
                "response": "Здравствуйте! Отправьте реквизиты...",
                "tokens_used": 150,
                "model": "gpt-4-turbo-preview"
            }
        """
        intent = input_data.get("intent", "unknown")
        message = input_data.get("message", "")
        context = input_data.get("context", {})
        
        system_prompt = self._get_system_prompt()
        user_prompt = self._build_prompt(intent, message, context)
        
        try:
            result = await self.generate(system_prompt, user_prompt, temperature=0.7, json_mode=True)
            parsed = json.loads(result["content"])
            
            response_text = parsed.get("response", "")
            logger.debug(f"Response generated for intent '{intent}': {response_text[:50]}...")
            
            return {
                "response": response_text,
                "tone": parsed.get("tone", "neutral"),
                "tokens_used": result.get("tokens", 0),
                "model": result.get("model")
            }
        
        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            return {
                "response": self._get_fallback_response(intent),
                "tone": "neutral",
                "error": str(e)
            }
    
    def _get_system_prompt(self) -> str:
        return """Ты - профессиональный менеджер P2P торговли криптовалютой.

Твоя задача - генерировать вежливые, профессиональные и понятные ответы клиентам.

Правила:
1. Будь вежливым и профессиональным
2. Отвечай кратко и по делу
3. Используй эмодзи умеренно (1-2 на сообщение)
4. Давай чёткие инструкции
5. Не используй сленг
6. Адаптируй тон под намерение клиента

Намерения и стиль ответа:
- greeting: дружелюбный, приветственный
- ready_to_pay: деловой, с инструкциями
- payment_sent: подтверждающий, успокаивающий
- request_details: информативный, чёткий
- complaint: сочувствующий, решающий проблему
- question: информативный, помогающий
- cancel: понимающий, уточняющий

Верни JSON:
{
    "response": "текст ответа",
    "tone": "friendly/professional/empathetic"
}"""
    
    def _build_prompt(self, intent: str, message: str, context: Dict[str, Any]) -> str:
        prompt = f"Намерение клиента: {intent}\n"
        prompt += f"Сообщение клиента: {message}\n\n"
        
        prompt += "Контекст сделки:\n"
        if "order_id" in context:
            prompt += f"- Ордер: {context['order_id']}\n"
        if "order_amount" in context:
            prompt += f"- Сумма: {context['order_amount']} {context.get('currency', 'RUB')}\n"
        if "side" in context:
            side_text = "Покупка" if context['side'] == "BUY" else "Продажа"
            prompt += f"- Тип: {side_text}\n"
        if "payment_methods" in context:
            prompt += f"- Способы оплаты: {', '.join(context['payment_methods'])}\n"
        
        prompt += "\nСгенерируй подходящий ответ."
        return prompt
    
    def _get_fallback_response(self, intent: str) -> str:
        """Fallback responses if AI fails."""
        fallbacks = {
            "greeting": "Здравствуйте! Готов помочь с вашей сделкой.",
            "ready_to_pay": "Отлично! Отправьте реквизиты для перевода.",
            "payment_sent": "Спасибо! Проверяю платёж. Ожидайте подтверждения.",
            "request_details": "Реквизиты для оплаты будут отправлены в ближайшее время.",
            "complaint": "Приношу извинения за неудобства. Разбираюсь в ситуации.",
            "question": "Спасибо за вопрос. Уточняю информацию.",
            "cancel": "Понял ваше желание отменить сделку. Уточните причину.",
            "unknown": "Спасибо за сообщение. Обрабатываю ваш запрос."
        }
        return fallbacks.get(intent, fallbacks["unknown"])
