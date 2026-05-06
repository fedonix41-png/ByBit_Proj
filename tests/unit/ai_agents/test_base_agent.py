"""Smoke tests for BaseAIAgent."""
import pytest
from unittest.mock import patch, MagicMock
from app.ai_agents.base_agent import BaseAIAgent, AIProvider


class TestBaseAIAgent:
    """Test BaseAIAgent basic functionality."""
    
    def test_provider_enum_values(self):
        """Test AIProvider enum has all expected values."""
        assert AIProvider.OPENAI.value == "openai"
        assert AIProvider.ANTHROPIC.value == "anthropic"
        assert AIProvider.OPENROUTER.value == "openrouter"
        assert AIProvider.MOCK.value == "mock"
    
    @pytest.mark.asyncio
    async def test_mock_provider_initialization(self):
        """Test mock provider initializes correctly."""
        with patch.dict("os.environ", {"USE_AI_MOCK": "true"}):
            agent = ConcreteTestAgent()
            assert agent.provider == AIProvider.MOCK
            assert agent.model == "mock-ai-model"
    
    @pytest.mark.asyncio
    async def test_mock_generate_returns_dict(self):
        """Test mock generate returns expected structure."""
        with patch.dict("os.environ", {"USE_AI_MOCK": "true"}):
            agent = ConcreteTestAgent()
            result = await agent.generate(
                system_prompt="Test system",
                user_prompt="Test user"
            )
            assert "content" in result
            assert "tokens" in result
            assert "model" in result
    
    @pytest.mark.asyncio
    async def test_generate_with_order_id_logs(self):
        """Test generate with order_id triggers logging."""
        with patch.dict("os.environ", {"USE_AI_MOCK": "true"}):
            agent = ConcreteTestAgent(log_to_db=True)
            result = await agent.generate(
                system_prompt="Test",
                user_prompt="Test",
                order_id=123
            )
            assert "latency_ms" in result


class ConcreteTestAgent(BaseAIAgent):
    """Concrete implementation for testing."""
    
    async def process(self, input_data):
        return {"processed": True}
