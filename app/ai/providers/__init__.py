from typing import Optional
from app.core.config import get_settings, Settings
from app.ai.providers.base import (
    BaseLLMProvider,
    LLMError,
    LLMTimeoutError,
    LLMRateLimitError,
    LLMAuthenticationError,
    LLMInvalidOutputError,
    LLMProviderUnavailableError,
)
from app.ai.providers.fake import FakeLLMProvider
from app.ai.providers.openai_provider import OpenAILLMProvider
from app.ai.providers.gemini_provider import GeminiLLMProvider


_custom_provider: Optional[BaseLLMProvider] = None


def set_llm_provider(provider: Optional[BaseLLMProvider]) -> None:
    """Override provider globally (useful for unit and integration testing)."""
    global _custom_provider
    _custom_provider = provider


def get_llm_provider(settings: Optional[Settings] = None) -> BaseLLMProvider:
    """Factory creating the configured LLM provider according to application settings."""
    global _custom_provider
    if _custom_provider is not None:
        return _custom_provider

    if settings is None:
        settings = get_settings()

    provider_name = (settings.llm_provider or "fake").lower()

    if provider_name == "gemini":
        return GeminiLLMProvider(
            api_key=settings.gemini_api_key,
            model=settings.llm_model,
            timeout=settings.llm_timeout_seconds,
            max_retries=settings.llm_max_retries,
        )

    if provider_name == "openai":
        return OpenAILLMProvider(
            api_key=settings.openai_api_key,
            model=settings.llm_model,
            timeout=settings.llm_timeout_seconds,
            max_retries=settings.llm_max_retries,
        )

    # Default to deterministic zero-cost Fake provider
    return FakeLLMProvider()
