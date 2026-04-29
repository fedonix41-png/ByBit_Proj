"""Fraud risk analysis AI agent."""
import json
import logging
from typing import Dict, Any
from datetime import datetime
from .base_agent import BaseAIAgent

logger = logging.getLogger(__name__)

class FraudAnalyzer(BaseAIAgent):
    """Analyze fraud risk for P2P transactions."""
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze fraud risk.
        
        Args:
            input_data: {
                "payment_data": {
                    "amount": 10000,
                    "currency": "RUB",
                    "card_number": "1234****5678",
                    "timestamp": "2024-01-15 14:30",
                    "bank": "Сбербанк"
                },
                "order_data": {
                    "order_id": "ORD123",
                    "expected_amount": 10000,
                    "currency": "RUB",
                    "created_at": "2024-01-15 14:00"
                },
                "counterparty_history": {
                    "total_trades": 5,
                    "successful_trades": 5,
                    "disputes": 0
                }
            }
        
        Returns:
            {
                "risk_score": 0.15,
                "risk_level": "low",
                "flags": [],
                "checks": {
                    "amount_match": true,
                    "timing_reasonable": true,
                    "card_format_valid": true
                },
                "recommendation": "approve"
            }
        """
        payment_data = input_data.get("payment_data", {})
        order_data = input_data.get("order_data", {})
        counterparty_history = input_data.get("counterparty_history", {})
        
        # Rule-based checks first
        rule_checks = self._rule_based_checks(payment_data, order_data)
        
        # AI analysis
        ai_analysis = await self._ai_analysis(payment_data, order_data, counterparty_history, rule_checks)
        
        # Combine results
        final_score = self._calculate_final_score(rule_checks, ai_analysis)
        
        return {
            **ai_analysis,
            "risk_score": final_score,
            "risk_level": self._get_risk_level(final_score),
            "checks": rule_checks,
            "recommendation": self._get_recommendation(final_score)
        }
    
    def _rule_based_checks(self, payment_data: Dict, order_data: Dict) -> Dict[str, bool]:
        """Perform rule-based checks."""
        checks = {}
        
        # Amount match
        payment_amount = payment_data.get("amount")
        expected_amount = order_data.get("expected_amount")
        checks["amount_match"] = (
            payment_amount is not None and 
            expected_amount is not None and
            abs(payment_amount - expected_amount) < 1.0
        )
        
        # Card format
        card_number = payment_data.get("card_number", "")
        checks["card_format_valid"] = (
            len(card_number) >= 13 and
            "****" in card_number
        )
        
        # Timing reasonable (within 24 hours)
        try:
            payment_time = datetime.fromisoformat(payment_data.get("timestamp", ""))
            order_time = datetime.fromisoformat(order_data.get("created_at", ""))
            time_diff = (payment_time - order_time).total_seconds()
            checks["timing_reasonable"] = 0 < time_diff < 86400  # 24 hours
        except:
            checks["timing_reasonable"] = False
        
        # Currency match
        checks["currency_match"] = (
            payment_data.get("currency") == order_data.get("currency")
        )
        
        return checks
    
    async def _ai_analysis(self, payment_data: Dict, order_data: Dict, 
                          counterparty_history: Dict, rule_checks: Dict) -> Dict[str, Any]:
        """AI-based fraud analysis."""
        system_prompt = self._get_system_prompt()
        user_prompt = self._build_prompt(payment_data, order_data, counterparty_history, rule_checks)
        
        try:
            result = await self.generate(system_prompt, user_prompt, temperature=0.2, json_mode=True)
            parsed = json.loads(result["content"])
            
            logger.info(f"AI fraud analysis: risk_score={parsed.get('ai_risk_score')}")
            
            return {
                "ai_risk_score": parsed.get("ai_risk_score", 0.5),
                "flags": parsed.get("flags", []),
                "explanation": parsed.get("explanation", ""),
                "tokens_used": result.get("tokens", 0),
                "model": result.get("model")
            }
        
        except Exception as e:
            logger.error(f"AI fraud analysis failed: {e}")
            return {
                "ai_risk_score": 0.5,
                "flags": ["ai_analysis_failed"],
                "explanation": f"AI analysis error: {str(e)}",
                "error": str(e)
            }
    
    def _get_system_prompt(self) -> str:
        return """Ты - эксперт по выявлению мошенничества в P2P торговле криптовалютой.

Анализируй данные платежа и определи уровень риска мошенничества.

Красные флаги (высокий риск):
- Несоответствие суммы
- Подозрительное время платежа (слишком быстро или слишком долго)
- Неправильный формат карты
- Несоответствие валюты
- История споров у контрагента
- Странные паттерны в данных

Зелёные флаги (низкий риск):
- Точное совпадение суммы
- Разумное время платежа
- Корректный формат данных
- Хорошая история контрагента
- Известный банк

Верни JSON:
{
    "ai_risk_score": 0.0-1.0,
    "flags": ["список подозрительных моментов"],
    "explanation": "краткое объяснение оценки риска"
}"""
    
    def _build_prompt(self, payment_data: Dict, order_data: Dict, 
                     counterparty_history: Dict, rule_checks: Dict) -> str:
        prompt = "Данные платежа:\n"
        prompt += json.dumps(payment_data, ensure_ascii=False, indent=2)
        prompt += "\n\nДанные ордера:\n"
        prompt += json.dumps(order_data, ensure_ascii=False, indent=2)
        prompt += "\n\nИстория контрагента:\n"
        prompt += json.dumps(counterparty_history, ensure_ascii=False, indent=2)
        prompt += "\n\nАвтоматические проверки:\n"
        prompt += json.dumps(rule_checks, ensure_ascii=False, indent=2)
        prompt += "\n\nОцени риск мошенничества."
        return prompt
    
    def _calculate_final_score(self, rule_checks: Dict, ai_analysis: Dict) -> float:
        """Calculate final risk score combining rules and AI."""
        # Rule-based score (0.0 = all pass, 1.0 = all fail)
        failed_checks = sum(1 for passed in rule_checks.values() if not passed)
        rule_score = failed_checks / len(rule_checks) if rule_checks else 0.5
        
        # AI score
        ai_score = ai_analysis.get("ai_risk_score", 0.5)
        
        # Weighted average (60% AI, 40% rules)
        final_score = (ai_score * 0.6) + (rule_score * 0.4)
        
        return round(final_score, 2)
    
    def _get_risk_level(self, risk_score: float) -> str:
        """Convert risk score to level."""
        if risk_score < 0.3:
            return "low"
        elif risk_score < 0.7:
            return "medium"
        else:
            return "high"
    
    def _get_recommendation(self, risk_score: float) -> str:
        """Get recommendation based on risk score."""
        if risk_score < 0.3:
            return "approve"
        elif risk_score < 0.7:
            return "manual_review"
        else:
            return "reject"
