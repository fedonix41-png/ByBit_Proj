"""Intent router for determining response type."""
import json
from loguru import logger
from typing import Dict, Any, Literal
from .base_agent import BaseAIAgent

ResponseType = Literal["text", "action", "info"]

class IntentRouter(BaseAIAgent):
    """Determine response type based on user message and context."""
    
    RESPONSE_TYPES = {
        "text": "Текстовый ответ пользователю",
        "action": "Выполнение действия (подтверждение платежа, отмена)",
        "info": "Информационный ответ (статус, детали ордера)"
    }
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Determine response type and routing.
        
        Args:
            input_data: {
                "message": "текст сообщения",
                "intent": "готовое намерение из IntentClassifier",
                "context": {
                    "has_image": bool,
                    "has_voice": bool,
                    "order_status": str
                }
            }
        
        Returns:
            {
                "response_type": "text" | "action" | "info",
                "routing": {
                    "node": "target_node_name",
                    "requires_approval": bool
                },
                "confidence": 0.0-1.0
            }
        """
        message = input_data.get("message", "")
        intent = input_data.get("intent", "unknown")
        context = input_data.get("context", {})
        
        if self._is_mock_mode():
            return self._mock_route(intent, context)
        
        system_prompt = self._get_system_prompt()
        user_prompt = self._build_prompt(message, intent, context)
        
        try:
            result = await self.generate(system_prompt, user_prompt, temperature=0.2, json_mode=True)
            parsed = json.loads(result["content"])
            
            logger.debug(f"Routed to: {parsed.get('response_type')} -> {parsed.get('routing', {}).get('node')}")
            
            return {
                "response_type": parsed.get("response_type", "text"),
                "routing": parsed.get("routing", {"node": "generate_response", "requires_approval": True}),
                "confidence": parsed.get("confidence", 0.8),
                "tokens_used": result.get("tokens", 0)
            }
        
        except Exception as e:
            logger.error(f"Intent routing failed: {e}")
            return self._fallback_route(intent, context)
    
    def _is_mock_mode(self) -> bool:
        from config import USE_AI_MOCK
        return USE_AI_MOCK
    
    def _mock_route(self, intent: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Mock routing logic for development."""
        return self._fallback_route(intent, context)
    
    def _fallback_route(self, intent: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Rule-based fallback routing."""
        routing_map = {
            "greeting": {"node": "generate_response", "requires_approval": False},
            "ready_to_pay": {"node": "generate_response", "requires_approval": True},
            "payment_sent": {"node": "parse_payment", "requires_approval": True},
            "request_details": {"node": "generate_response", "requires_approval": False},
            "complaint": {"node": "generate_response", "requires_approval": True},
            "question": {"node": "generate_response", "requires_approval": False},
            "cancel": {"node": "handle_cancel", "requires_approval": True},
            "confirm_receipt": {"node": "generate_response", "requires_approval": False},
            "unknown": {"node": "generate_response", "requires_approval": True}
        }
        
        response_type = "action" if intent in ["payment_sent", "cancel"] else "text"
        if intent in ["question", "request_details", "greeting"]:
            response_type = "info"
        
        routing = routing_map.get(intent, routing_map["unknown"])
        
        if context.get("has_image") and intent == "payment_sent":
            routing = {"node": "parse_payment", "requires_approval": True}
            response_type = "action"
        
        return {
            "response_type": response_type,
            "routing": routing,
            "confidence": 0.9
        }
    
    def _get_system_prompt(self) -> str:
        return """Ты - роутер для P2P Telegram бота по торговле криптовалютой.

Твоя задача - определить тип ответа и маршрут обработки сообщения.

Типы ответов:
- text: Обычный текстовый ответ (приветствие, ответы на вопросы)
- action: Выполнение действия (подтверждение платежа, отмена ордера)
- info: Информационный ответ (статус ордера, реквизиты, баланс)

Узлы обработки:
- generate_response: Генерация текстового ответа
- parse_payment: Обработка скриншота платежа
- handle_cancel: Обработка отмены ордера
- check_status: Проверка статуса ордера

Верни JSON:
{
    "response_type": "text|action|info",
    "routing": {
        "node": "имя_узла",
        "requires_approval": true/false
    },
    "confidence": 0.0-1.0
}"""
    
    def _build_prompt(self, message: str, intent: str, context: Dict[str, Any]) -> str:
        prompt = f"Сообщение: {message}\n"
        prompt += f"Определённое намерение: {intent}\n\n"
        
        if context:
            prompt += "Контекст:\n"
            if context.get("has_image"):
                prompt += "- Пользователь прислал изображение\n"
            if context.get("has_voice"):
                prompt += "- Пользователь прислал голосовое сообщение\n"
            if context.get("order_status"):
                prompt += f"- Статус ордера: {context['order_status']}\n"
        
        return prompt
