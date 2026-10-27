import os
import pytest

from app.ai.providers import get_llm_provider, set_llm_provider
from app.ai.providers.fake import FakeLLMProvider
from app.ai.providers.openai_provider import OpenAILLMProvider
from app.ai.providers.base import (
    LLMTimeoutError,
    LLMRateLimitError,
    LLMAuthenticationError,
    LLMInvalidOutputError,
    LLMProviderUnavailableError,
)
from app.ai.decision_schemas import (
    ExecuteActionDecision,
    AnswerQuestionDecision,
    ClarifyDecision,
)
from app.ai.tool_registry import ToolRegistry


@pytest.fixture(autouse=True)
def reset_custom_provider():
    """Ensure provider override is reset after each test."""
    set_llm_provider(None)
    yield
    set_llm_provider(None)


def test_fake_provider_completes_step_on_done():
    provider = FakeLLMProvider()
    dec = provider.generate_decision(
        system_prompt="",
        user_message="I have finished step 1, it is done.",
        context={"current_step_number": 1},
        tool_definitions=ToolRegistry.get_definitions(),
    )
    assert isinstance(dec, ExecuteActionDecision)
    assert dec.action == "complete_step"
    assert dec.arguments["step_number"] == 1


def test_fake_provider_skips_step():
    provider = FakeLLMProvider()
    dec = provider.generate_decision(
        system_prompt="",
        user_message="Skip step 2 please",
        context={"current_step_number": 2},
        tool_definitions=ToolRegistry.get_definitions(),
    )
    assert isinstance(dec, ExecuteActionDecision)
    assert dec.action == "skip_step"
    assert dec.arguments["step_number"] == 2


def test_fake_provider_answers_culinary_question():
    provider = FakeLLMProvider()
    dec = provider.generate_decision(
        system_prompt="",
        user_message="Why do we brown the meat first?",
        context={"current_step_number": 1},
        tool_definitions=ToolRegistry.get_definitions(),
    )
    assert isinstance(dec, AnswerQuestionDecision)
    assert "caramelizes" in dec.answer.lower()


def test_fake_provider_clarifies_ambiguous_message():
    provider = FakeLLMProvider()
    dec = provider.generate_decision(
        system_prompt="",
        user_message="Chicken daal diya",
        context={"current_step_number": 1},
        tool_definitions=ToolRegistry.get_definitions(),
    )
    assert isinstance(dec, ClarifyDecision)
    assert "add the ingredient" in dec.question


def test_fake_provider_simulated_errors():
    # Timeout
    p_timeout = FakeLLMProvider(force_timeout=True)
    with pytest.raises(LLMTimeoutError):
        p_timeout.generate_decision("", "msg", {}, [])

    # Rate limit
    p_rate = FakeLLMProvider(force_rate_limit=True)
    with pytest.raises(LLMRateLimitError):
        p_rate.generate_decision("", "msg", {}, [])

    # Auth error
    p_auth = FakeLLMProvider(force_auth_error=True)
    with pytest.raises(LLMAuthenticationError):
        p_auth.generate_decision("", "msg", {}, [])

    # Invalid output
    p_inv = FakeLLMProvider(force_invalid_output=True)
    with pytest.raises(LLMInvalidOutputError):
        p_inv.generate_decision("", "msg", {}, [])

    # Provider unavailable
    p_unavail = FakeLLMProvider(force_unavailable=True)
    with pytest.raises(LLMProviderUnavailableError):
        p_unavail.generate_decision("", "msg", {}, [])


from app.ai.providers.gemini_provider import GeminiLLMProvider
from app.core.config import Settings


def test_openai_provider_missing_key_raises_auth_error():
    """Verify initializing OpenAI provider without key raises LLMAuthenticationError."""
    with pytest.raises(LLMAuthenticationError):
        OpenAILLMProvider(api_key=None)


def test_gemini_provider_missing_key_raises_auth_error():
    """Verify initializing Gemini provider without key raises LLMAuthenticationError."""
    with pytest.raises(LLMAuthenticationError):
        GeminiLLMProvider(api_key=None)


def test_default_provider_factory_is_fake():
    """Verify default provider is FakeLLMProvider when no key or settings provided."""
    set_llm_provider(None)
    settings = Settings(llm_provider="fake")
    provider = get_llm_provider(settings=settings)
    assert isinstance(provider, FakeLLMProvider)


def test_gemini_provider_factory_resolution():
    """Verify factory returns GeminiLLMProvider when llm_provider is 'gemini'."""
    settings = Settings(llm_provider="gemini", gemini_api_key="dummy_test_key")
    provider = get_llm_provider(settings=settings)
    assert isinstance(provider, GeminiLLMProvider)
    assert provider.model == settings.llm_model


@pytest.mark.skipif(
    not os.getenv("RUN_LIVE_LLM_TESTS") or not os.getenv("GEMINI_API_KEY"),
    reason="Live tests skipped by default. Set RUN_LIVE_LLM_TESTS=1 and GEMINI_API_KEY to run.",
)
def test_live_gemini_smoke_test():
    """Optional live integration smoke test executed only when RUN_LIVE_LLM_TESTS is explicitly enabled."""
    key = os.getenv("GEMINI_API_KEY")
    provider = GeminiLLMProvider(api_key=key, model="gemini-3.8-flash")
    dec = provider.generate_decision(
        system_prompt="You are a cooking helper. Return a JSON decision.",
        user_message="I have finished cooking step 1.",
        context={"current_step_number": 1},
        tool_definitions=ToolRegistry.get_definitions(),
    )
    assert dec.type in {"execute_action", "answer_question", "clarify"}


@pytest.mark.skipif(
    not os.getenv("RUN_LIVE_LLM_TESTS") or not os.getenv("OPENAI_API_KEY"),
    reason="Live tests skipped by default. Set RUN_LIVE_LLM_TESTS=1 and OPENAI_API_KEY to run.",
)
def test_live_openai_smoke_test():
    """Optional live integration smoke test executed only when OPENAI_API_KEY is configured."""
    key = os.getenv("OPENAI_API_KEY")
    provider = OpenAILLMProvider(api_key=key, model="gpt-4o-mini")
    dec = provider.generate_decision(
        system_prompt="You are a cooking helper. Return a JSON decision.",
        user_message="I have finished cooking step 1.",
        context={"current_step_number": 1},
        tool_definitions=ToolRegistry.get_definitions(),
    )
    assert dec.type in {"execute_action", "answer_question", "clarify"}
