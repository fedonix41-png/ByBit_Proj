"""Base AI agent with multi-provider support."""
import os
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)

class AIProvider(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"
    GROQ = "groq"
    TOGETHER = "together"
    MISTRAL = "mistral"
    MOCK = "mock"

class BaseAIAgent(ABC):
    """Base class for AI agents with multi-provider support."""
    
    def __init__(self, provider: str = None, model: str = None):
        # Check if mock mode is enabled
        self.use_mock = os.getenv("USE_AI_MOCK", "false").lower() == "true"

        if self.use_mock:
            self.provider = AIProvider.MOCK
            self.model = "mock-ai-model"
            self.client = None
        else:
            self.provider = AIProvider(provider or os.getenv("AI_PROVIDER", "openai"))
            self.model = model or self._get_default_model()
            self.client = self._init_client()
    
    def _get_default_model(self) -> str:
        """Get default model for provider."""
        defaults = {
            AIProvider.OPENAI: "gpt-4-turbo-preview",
            AIProvider.ANTHROPIC: "claude-3-sonnet-20240229",
            AIProvider.LOCAL: "llama-3-8b",
            AIProvider.GROQ: "mixtral-8x7b-32768",
            AIProvider.TOGETHER: "mistralai/Mixtral-8x7B-Instruct-v0.1",
            AIProvider.MISTRAL: "mistral-large-latest"
        }
        return defaults.get(self.provider, "gpt-4-turbo-preview")
    
    def _init_client(self):
        """Initialize AI client based on provider."""
        if self.provider == AIProvider.OPENAI:
            from openai import OpenAI
            return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        elif self.provider == AIProvider.ANTHROPIC:
            from anthropic import Anthropic
            return Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        
        elif self.provider == AIProvider.GROQ:
            from groq import Groq
            return Groq(api_key=os.getenv("GROQ_API_KEY"))
        
        elif self.provider == AIProvider.TOGETHER:
            from together import Together
            return Together(api_key=os.getenv("TOGETHER_API_KEY"))
        
        elif self.provider == AIProvider.MISTRAL:
            from mistralai.client import MistralClient
            return MistralClient(api_key=os.getenv("MISTRAL_API_KEY"))
        
        elif self.provider == AIProvider.LOCAL:
            # Ollama or local LLM
            import httpx
            return httpx.AsyncClient(base_url=os.getenv("LOCAL_LLM_URL", "http://localhost:11434"))
        
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    async def generate(self, system_prompt: str, user_prompt: str,
                       temperature: float = 0.3, json_mode: bool = False) -> Dict[str, Any]:
        """Generate response from AI."""
        try:
            if self.provider == AIProvider.MOCK:
                return await self._generate_mock(system_prompt, user_prompt, temperature, json_mode)

            if self.provider == AIProvider.OPENAI:
                return await self._generate_openai(system_prompt, user_prompt, temperature, json_mode)

            elif self.provider == AIProvider.ANTHROPIC:
                return await self._generate_anthropic(system_prompt, user_prompt, temperature, json_mode)

            elif self.provider == AIProvider.GROQ:
                return await self._generate_groq(system_prompt, user_prompt, temperature, json_mode)

            elif self.provider == AIProvider.TOGETHER:
                return await self._generate_together(system_prompt, user_prompt, temperature, json_mode)

            elif self.provider == AIProvider.MISTRAL:
                return await self._generate_mistral(system_prompt, user_prompt, temperature, json_mode)

            elif self.provider == AIProvider.LOCAL:
                return await self._generate_local(system_prompt, user_prompt, temperature, json_mode)

        except Exception as e:
            logger.error(f"AI generation error ({self.provider.value}): {e}")
            raise
    
    async def _generate_openai(self, system_prompt: str, user_prompt: str, 
                               temperature: float, json_mode: bool) -> Dict[str, Any]:
        """Generate with OpenAI."""
        kwargs = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": temperature
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        
        response = self.client.chat.completions.create(**kwargs)
        
        return {
            "content": response.choices[0].message.content,
            "tokens": response.usage.total_tokens,
            "model": response.model
        }
    
    async def _generate_anthropic(self, system_prompt: str, user_prompt: str, 
                                  temperature: float, json_mode: bool) -> Dict[str, Any]:
        """Generate with Anthropic."""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            temperature=temperature,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )
        
        return {
            "content": response.content[0].text,
            "tokens": response.usage.input_tokens + response.usage.output_tokens,
            "model": response.model
        }
    
    async def _generate_groq(self, system_prompt: str, user_prompt: str, 
                            temperature: float, json_mode: bool) -> Dict[str, Any]:
        """Generate with Groq."""
        kwargs = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": temperature
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        
        response = self.client.chat.completions.create(**kwargs)
        
        return {
            "content": response.choices[0].message.content,
            "tokens": response.usage.total_tokens,
            "model": response.model
        }
    
    async def _generate_together(self, system_prompt: str, user_prompt: str, 
                                 temperature: float, json_mode: bool) -> Dict[str, Any]:
        """Generate with Together AI."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=temperature
        )
        
        return {
            "content": response.choices[0].message.content,
            "tokens": response.usage.total_tokens,
            "model": response.model
        }
    
    async def _generate_mistral(self, system_prompt: str, user_prompt: str, 
                               temperature: float, json_mode: bool) -> Dict[str, Any]:
        """Generate with Mistral."""
        response = self.client.chat(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=temperature
        )
        
        return {
            "content": response.choices[0].message.content,
            "tokens": response.usage.total_tokens,
            "model": response.model
        }
    
    async def _generate_local(self, system_prompt: str, user_prompt: str, 
                             temperature: float, json_mode: bool) -> Dict[str, Any]:
        """Generate with local LLM (Ollama)."""
        response = await self.client.post("/api/generate", json={
            "model": self.model,
            "prompt": f"{system_prompt}\n\n{user_prompt}",
            "temperature": temperature,
            "stream": False
        })
        data = response.json()
        
        return {
            "content": data["response"],
            "tokens": 0,  # Ollama doesn't return token count
            "model": self.model
        }

    async def _generate_mock(self, system_prompt: str, user_prompt: str,
                            temperature: float, json_mode: bool) -> Dict[str, Any]:
        """Generate mock response for testing."""
        import json
        import asyncio
        import random

        # Simulate API delay
        await asyncio.sleep(0.1)

        # Generate mock response based on the request type
        if "classify" in system_prompt.lower() or "intent" in system_prompt.lower():
            # Mock intent classification
            mock_response = {
                "intent": "BUY_CRYPTO",
                "confidence": 0.85,
                "entities": {"crypto": "USDT", "currency": "RUB", "amount": "1000"}
            }
        elif "analyze" in system_prompt.lower() or "fraud" in system_prompt.lower():
            # Mock fraud analysis
            mock_response = {
                "is_fraud": False,
                "risk_score": 0.15,
                "reasons": [],
                "recommendation": "APPROVE"
            }
        elif "generate" in system_prompt.lower() and "response" in system_prompt.lower():
            # Mock response generation
            mock_response = "Здравствуйте! Я готов помочь вам с покупкой USDT. Пожалуйста, предоставьте детали сделки."
        elif json_mode:
            # Mock JSON response
            mock_response = {"status": "success", "message": "Mock AI response"}
        else:
            # Generic mock response
            mock_response = "Это mock-ответ ИИ для тестирования. Реальный API не используется."

        # Convert to JSON string if json_mode
        if json_mode and isinstance(mock_response, dict):
            content = json.dumps(mock_response, ensure_ascii=False)
        elif isinstance(mock_response, dict):
            content = str(mock_response)
        else:
            content = mock_response

        return {
            "content": content,
            "tokens": random.randint(50, 200),
            "model": "mock-ai-model"
        }

    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process input and return result."""
        pass
