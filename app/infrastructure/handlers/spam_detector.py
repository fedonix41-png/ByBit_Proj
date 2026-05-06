"""ML-based spam detection using OpenRouter."""
from typing import Dict, Any, Optional
from dataclasses import dataclass
from loguru import logger

from ...ai_agents.openrouter_adapter import OpenRouterClient


@dataclass
class SpamAnalysisResult:
    is_spam: bool
    confidence: float
    categories: list
    explanation: str


SPAM_DETECTION_PROMPT = """Analyze this message for spam/fraud indicators in P2P trading context.

Message: "{message}"

Respond in JSON format:
{{
    "is_spam": true/false,
    "confidence": 0.0-1.0,
    "categories": ["list of detected categories"],
    "explanation": "brief explanation"
}}

Categories to check:
- phishing: attempts to get personal info
- scam: fraudulent schemes
- spam: unsolicited advertising  
- manipulation: pressure tactics
- impersonation: pretending to be someone else
- off_topic: unrelated to P2P trading
- legitimate: normal P2P message

Consider context: this is a P2P cryptocurrency trading bot."""


class SpamDetector:
    """ML-based spam detection using OpenRouter."""
    
    def __init__(self):
        self.client = OpenRouterClient()
        self._enabled = True
    
    async def analyze(self, message: str) -> SpamAnalysisResult:
        """Analyze message for spam indicators."""
        if not self._enabled or not self.client.is_configured:
            return SpamAnalysisResult(
                is_spam=False,
                confidence=0.0,
                categories=[],
                explanation="Spam detection disabled or not configured"
            )
        
        try:
            response = await self.client.generate(
                prompt=SPAM_DETECTION_PROMPT.format(message=message[:500]),
                system="You are a spam detection system. Respond only in valid JSON."
            )
            
            # Parse JSON response
            import json
            result = json.loads(response)
            
            return SpamAnalysisResult(
                is_spam=result.get("is_spam", False),
                confidence=result.get("confidence", 0.0),
                categories=result.get("categories", []),
                explanation=result.get("explanation", "")
            )
            
        except Exception as e:
            logger.warning(f"Spam detection failed: {e}")
            return SpamAnalysisResult(
                is_spam=False,
                confidence=0.0,
                categories=[],
                explanation=f"Error: {str(e)}"
            )
    
    def enable(self):
        self._enabled = True
    
    def disable(self):
        self._enabled = False


# Global instance
spam_detector = SpamDetector()
