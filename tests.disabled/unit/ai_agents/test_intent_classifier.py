"""Smoke tests for IntentClassifier."""
import pytest
from unittest.mock import patch, MagicMock
from app.ai_agents.intent_classifier import IntentClassifier


class TestIntentClassifier:
    """Test IntentClassifier smoke tests."""
    
    @pytest.mark.asyncio
    async def test_classifier_initialization(self):
        """Test classifier initializes correctly."""
        with patch.dict("os.environ", {"USE_AI_MOCK": "true"}):
            classifier = IntentClassifier()
            assert classifier.agent_type == "IntentClassifier"
    
    @pytest.mark.asyncio
    async def test_process_returns_intent(self):
        """Test process returns intent structure."""
        with patch.dict("os.environ", {"USE_AI_MOCK": "true"}):
            classifier = IntentClassifier()
            result = await classifier.process({"message": "Хочу купить USDT за рубли"})
            assert "intent" in result
            assert "confidence" in result
    
    @pytest.mark.asyncio
    async def test_process_method(self):
        """Test process method exists and works."""
        with patch.dict("os.environ", {"USE_AI_MOCK": "true"}):
            classifier = IntentClassifier()
            result = await classifier.process({"message": "Test message"})
            assert isinstance(result, dict)
