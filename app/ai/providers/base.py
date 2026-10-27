from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from app.ai.decision_schemas import LLMDecision
from app.ai.action_results import ActionResult
from app.schemas.cooking_session import CookingSessionRead


# --- Normalized Provider Exception Taxonomy ---

class LLMError(Exception):
    """Base exception for all LLM provider failures."""
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class LLMTimeoutError(LLMError):
    """Raised when an LLM provider request exceeds the configured timeout."""
    pass


class LLMRateLimitError(LLMError):
    """Raised when the LLM provider rate limit / quota is exceeded."""
    pass


class LLMAuthenticationError(LLMError):
    """Raised when the LLM provider rejects credentials (e.g. invalid or missing API key)."""
    pass


class LLMInvalidOutputError(LLMError):
    """Raised when the LLM produces malformed JSON or schema-incompatible decisions."""
    pass


class LLMProviderUnavailableError(LLMError):
    """Raised when the LLM provider is down, experiencing internal server errors, or unreachable."""
    pass


# --- Abstract Base LLM Provider ---

class BaseLLMProvider(ABC):
    """Provider-independent interface for language model interactions."""

    @abstractmethod
    def generate_decision(
        self,
        system_prompt: str,
        user_message: str,
        context: Dict[str, Any],
        tool_definitions: List[Dict[str, Any]],
    ) -> LLMDecision:
        """Interpret user intent and return a validated, structured LLMDecision."""
        pass

    @abstractmethod
    def generate_grounded_response(
        self,
        system_prompt: str,
        user_message: str,
        decision: LLMDecision,
        action_result: Optional[ActionResult] = None,
        session_state: Optional[CookingSessionRead] = None,
    ) -> str:
        """Generate a user-facing natural language reply grounded in actual backend execution results."""
        pass
