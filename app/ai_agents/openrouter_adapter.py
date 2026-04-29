"""OpenRouter.ai adapter for AI generation."""
import os
from typing import Optional
from loguru import logger
from openai import APIConnectionError, AuthenticationError, APIError


class OpenRouterClient:
    """OpenRouter.ai client using OpenAI-compatible interface."""
    
    OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
    DEFAULT_MODEL = "openai/gpt-4o-mini"
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.model = model or os.getenv("OPENROUTER_MODEL", self.DEFAULT_MODEL)
        self._client = None
        
        if not self.api_key:
            logger.warning("OPENROUTER_API_KEY not configured")
    
    def _get_client(self):
        """Lazy initialization of LangChain ChatOpenAI client."""
        if self._client is not None:
            return self._client
        
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not configured")
        
        from langchain_openai import ChatOpenAI
        
        self._client = ChatOpenAI(
            base_url=self.OPENROUTER_BASE_URL,
            api_key=self.api_key,
            model=self.model,
            temperature=0.3
        )
        
        return self._client
    
    async def generate(self, prompt: str, system: Optional[str] = None) -> str:
        """
        Generate AI response asynchronously.
        
        Args:
            prompt: User message
            system: System prompt (optional)
        
        Returns:
            Generated text response
        
        Raises:
            ValueError: API key not configured
        """
        if not self.api_key:
            return "API-ключ OpenRouter не настроен. Добавьте OPENROUTER_API_KEY в .env"
        
        try:
            client = self._get_client()
            
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})
            
            response = await client.ainvoke(messages)
            
            return response.content
        
        except AuthenticationError:
            logger.error("OpenRouter authentication failed: invalid API key")
            return "Неверный API-ключ OpenRouter. Проверьте OPENROUTER_API_KEY"
        
        except APIConnectionError as e:
            logger.error(f"OpenRouter connection error: {type(e).__name__}")
            return "Сервис временно недоступен. Попробуйте позже"
        
        except APIError as e:
            logger.error(f"OpenRouter API error: {type(e).__name__}")
            return "Ошибка сервиса. Попробуйте позже"
        
        except Exception as e:
            logger.error(f"OpenRouter unexpected error: {type(e).__name__}")
            return "Произошла ошибка. Попробуйте позже"
    
    @property
    def is_configured(self) -> bool:
        """Check if client is properly configured."""
        return bool(self.api_key)
