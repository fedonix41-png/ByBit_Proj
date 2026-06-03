"""AI interaction logger for database."""
from loguru import logger
import time
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class PricingInfo:
    price_per_1k_input: float
    price_per_1k_output: float


PRICING_TABLE: Dict[str, PricingInfo] = {
    "openai": {
        "gpt-4-turbo": PricingInfo(0.01, 0.03),
        "gpt-4-turbo-preview": PricingInfo(0.01, 0.03),
        "gpt-4o": PricingInfo(0.0025, 0.01),
        "gpt-4o-mini": PricingInfo(0.00015, 0.0006),
        "gpt-3.5-turbo": PricingInfo(0.0005, 0.0015),
    },
    "anthropic": {
        "claude-3-opus-20240229": PricingInfo(0.015, 0.075),
        "claude-3-sonnet-20240229": PricingInfo(0.003, 0.015),
        "claude-3-haiku-20240307": PricingInfo(0.00025, 0.00125),
    },
    "groq": {
        "mixtral-8x7b-32768": PricingInfo(0.00027, 0.00027),
        "llama2-70b-4096": PricingInfo(0.00070, 0.00080),
        "gemma-7b-it": PricingInfo(0.00007, 0.00007),
    },
    "together": {
        "mistralai/Mixtral-8x7B-Instruct-v0.1": PricingInfo(0.0006, 0.0006),
    },
    "mistral": {
        "mistral-large-latest": PricingInfo(0.004, 0.012),
        "mistral-medium-latest": PricingInfo(0.0027, 0.0081),
        "mistral-small-latest": PricingInfo(0.0002, 0.0006),
    },
    "openrouter": {
        "default": PricingInfo(0.00015, 0.00015),
        "openai/gpt-4o-mini": PricingInfo(0.00015, 0.0006),
        "openai/gpt-4o": PricingInfo(0.0025, 0.01),
        "anthropic/claude-3.5-sonnet": PricingInfo(0.003, 0.015),
    },
    "local": {
        "default": PricingInfo(0.0, 0.0),
    },
    "mock": {
        "default": PricingInfo(0.0, 0.0),
    },
}


class AILogger:
    def __init__(self) -> None:
        self._session_local = None

    def _get_session_local(self):
        if self._session_local is None:
            from app.database.session import SessionLocal
            self._session_local = SessionLocal
        return self._session_local

    def calculate_cost(
        self,
        provider: str,
        model: str,
        tokens_used: int,
        input_tokens: Optional[int] = None,
        output_tokens: Optional[int] = None,
    ) -> Optional[float]:
        provider_lower = provider.lower()
        model_lower = model.lower()

        if provider_lower not in PRICING_TABLE:
            return None

        provider_prices = PRICING_TABLE[provider_lower]

        pricing: Optional[PricingInfo] = None
        for model_key, pricing_info in provider_prices.items():
            if model_key.lower() == model_lower or model_key in model_lower:
                pricing = pricing_info
                break

        if pricing is None:
            pricing = provider_prices.get("default")

        if pricing is None:
            return None

        if input_tokens is not None and output_tokens is not None:
            input_cost = (input_tokens / 1000) * pricing.price_per_1k_input
            output_cost = (output_tokens / 1000) * pricing.price_per_1k_output
            return round(input_cost + output_cost, 6)

        if tokens_used > 0:
            estimated_input = tokens_used // 2
            estimated_output = tokens_used - estimated_input
            input_cost = (estimated_input / 1000) * pricing.price_per_1k_input
            output_cost = (estimated_output / 1000) * pricing.price_per_1k_output
            return round(input_cost + output_cost, 6)

        return None

    async def log_interaction(
        self,
        agent_type: str,
        provider: str,
        model: str,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
        tokens_used: int,
        latency_ms: int,
        order_id: Optional[int] = None,
        cost: Optional[float] = None,
        meta_info: Optional[Dict[str, Any]] = None,
    ) -> bool:
        try:
            from app.database.models import AIInteraction

            if cost is None:
                cost = self.calculate_cost(provider, model, tokens_used)

            SessionLocal = self._get_session_local()
            db = SessionLocal()

            try:
                interaction = AIInteraction(
                    order_id=order_id,
                    agent_type=agent_type,
                    provider=provider,
                    model=model,
                    input_data=input_data,
                    output_data=output_data,
                    tokens_used=tokens_used,
                    cost=cost,
                    latency_ms=latency_ms,
                    meta_info=meta_info,
                )
                db.add(interaction)
                db.commit()
                logger.debug(
                    f"Logged AI interaction: agent={agent_type}, provider={provider}, "
                    f"model={model}, tokens={tokens_used}, cost=${cost}"
                )
                return True
            except Exception as e:
                db.rollback()
                logger.error(f"Failed to log AI interaction to DB: {e}")
                return False
            finally:
                db.close()

        except Exception as e:
            logger.error(f"Error in AI logger: {e}")
            return False


_ailogger_instance: Optional[AILogger] = None


def get_ai_logger() -> AILogger:
    global _ailogger_instance
    if _ailogger_instance is None:
        _ailogger_instance = AILogger()
    return _ailogger_instance
