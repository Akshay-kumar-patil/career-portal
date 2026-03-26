"""
Hybrid Multi-Model Router — the brain of the AI system.
Routes requests to OpenAI or Ollama based on connectivity, preference, and task.
"""
import socket
import logging
from typing import Optional
from langchain_core.language_models import BaseChatModel

from backend.config import settings

logger = logging.getLogger(__name__)


class ModelRouter:
    """
    Intelligent model routing with:
    - Auto-detection of available models
    - Internet connectivity check
    - Graceful fallback (OpenAI → Ollama or vice versa)
    - Cost-aware execution tracking
    """

    def __init__(self):
        self._openai_available: Optional[bool] = None
        self._ollama_available: Optional[bool] = None
        self._total_tokens_used: int = 0
        self._estimated_cost_usd: float = 0.0

    def check_internet(self) -> bool:
        """Check if internet is available by probing OpenAI's API endpoint."""
        try:
            socket.create_connection(("api.openai.com", 443), timeout=3)
            return True
        except (socket.timeout, socket.error, OSError):
            return False

    def check_ollama(self) -> bool:
        """Check if Ollama is running locally."""
        try:
            host = settings.OLLAMA_BASE_URL.replace("http://", "").replace("https://", "")
            if ":" in host:
                hostname, port = host.split(":")
                port = int(port)
            else:
                hostname, port = host, 11434
            socket.create_connection((hostname, port), timeout=2)
            return True
        except (socket.timeout, socket.error, OSError):
            return False

    def get_llm(
        self,
        provider: Optional[str] = None,
        task_type: str = "general",
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> BaseChatModel:
        """
        Get the best available LLM based on provider preference and availability.

        Args:
            provider: "openai", "ollama", or "auto" (None = use settings default)
            task_type: Task hint for model selection — "generation", "analysis", "chat"
            temperature: Sampling temperature
            max_tokens: Maximum output tokens

        Returns:
            A LangChain chat model instance
        """
        provider = provider or settings.DEFAULT_MODEL_PROVIDER

        if provider == "auto":
            return self._auto_route(task_type, temperature, max_tokens)
        elif provider == "openai":
            return self._get_openai(temperature, max_tokens)
        elif provider == "ollama":
            return self._get_ollama(temperature, max_tokens)
        else:
            return self._auto_route(task_type, temperature, max_tokens)

    def _auto_route(
        self, task_type: str, temperature: float, max_tokens: int
    ) -> BaseChatModel:
        """Auto-route to the best available model."""
        has_internet = self.check_internet()
        has_ollama = self.check_ollama()
        has_api_key = bool(settings.OPENAI_API_KEY)

        # Priority: OpenAI (if available + key) → Ollama → raise error
        if has_internet and has_api_key:
            try:
                llm = self._get_openai(temperature, max_tokens)
                if has_ollama:
                    # Add Ollama as fallback
                    fallback = self._get_ollama(temperature, max_tokens)
                    return llm.with_fallbacks([fallback])
                return llm
            except Exception:
                if has_ollama:
                    return self._get_ollama(temperature, max_tokens)
                raise

        if has_ollama:
            logger.info("Using Ollama (no internet or no API key)")
            return self._get_ollama(temperature, max_tokens)

        # Last resort: try OpenAI anyway
        if has_api_key:
            return self._get_openai(temperature, max_tokens)

        raise RuntimeError(
            "No AI model available. Please either:\n"
            "1. Set OPENAI_API_KEY in .env for cloud AI, or\n"
            "2. Install and run Ollama (https://ollama.ai) for local AI"
        )

    def _get_openai(self, temperature: float, max_tokens: int) -> BaseChatModel:
        """Get OpenAI ChatModel."""
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=settings.OPENAI_MODEL,
            api_key=settings.OPENAI_API_KEY,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    def _get_ollama(self, temperature: float, max_tokens: int) -> BaseChatModel:
        """Get Ollama ChatModel."""
        from langchain_community.chat_models import ChatOllama

        return ChatOllama(
            model=settings.OLLAMA_MODEL,
            base_url=settings.OLLAMA_BASE_URL,
            temperature=temperature,
            num_predict=max_tokens,
        )

    def get_status(self) -> dict:
        """Get current AI system status."""
        return {
            "internet_available": self.check_internet(),
            "ollama_available": self.check_ollama(),
            "openai_configured": bool(settings.OPENAI_API_KEY),
            "default_provider": settings.DEFAULT_MODEL_PROVIDER,
            "openai_model": settings.OPENAI_MODEL,
            "ollama_model": settings.OLLAMA_MODEL,
            "tokens_used": self._total_tokens_used,
            "estimated_cost_usd": round(self._estimated_cost_usd, 4),
        }

    def track_usage(self, tokens: int, model: str = "gpt-3.5-turbo"):
        """Track token usage and estimated cost."""
        self._total_tokens_used += tokens
        # Rough pricing
        cost_per_1k = {
            "gpt-3.5-turbo": 0.002,
            "gpt-4": 0.06,
            "gpt-4-turbo": 0.03,
            "gpt-4o": 0.015,
            "gpt-4o-mini": 0.00015,
        }
        rate = cost_per_1k.get(model, 0.002)
        self._estimated_cost_usd += (tokens / 1000) * rate


# Singleton instance
model_router = ModelRouter()
