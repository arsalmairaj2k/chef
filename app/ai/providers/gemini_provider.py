import json
import logging
from typing import Any, Dict, List, Optional
from pydantic import ValidationError
from google import genai
from google.genai import types
from google.genai.errors import APIError, ClientError, ServerError

from app.ai.providers.base import (
    BaseLLMProvider,
    LLMError,
    LLMTimeoutError,
    LLMRateLimitError,
    LLMAuthenticationError,
    LLMInvalidOutputError,
    LLMProviderUnavailableError,
)
from app.ai.decision_schemas import (
    LLMDecision,
    ExecuteActionDecision,
    AnswerQuestionDecision,
    ClarifyDecision,
)
from app.ai.action_results import ActionResult
from app.schemas.cooking_session import CookingSessionRead


logger = logging.getLogger(__name__)


class GeminiLLMProvider(BaseLLMProvider):
    """Google Gemini LLM provider adapter using official google-genai SDK."""

    def __init__(
        self,
        api_key: Optional[str],
        model: str = "gemini-3.8-flash",
        timeout: float = 30.0,
        max_retries: int = 2,
    ):
        if not api_key:
            raise LLMAuthenticationError(
                "Gemini API key is missing. Set GEMINI_API_KEY environment variable."
            )
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries
        # google-genai HttpOptions timeout is in milliseconds
        timeout_ms = int(timeout * 1000) if timeout < 1000 else int(timeout)
        http_options = types.HttpOptions(timeout=timeout_ms)
        self.client = genai.Client(api_key=api_key, http_options=http_options)

    def _generate_content_resilient(self, contents: str, config: types.GenerateContentConfig):
        """Execute generate_content with automatic fallback for 404 deprecated models, 503 demand spikes, timeouts, and 429 quota exhaustion."""
        primary = self.model
        if primary in ("gemini-2.5-flash", "models/gemini-2.5-flash", "gemini-1.5-flash"):
            primary = "gemini-3.8-flash"

        models = [primary]
        for fallback in ("gemini-3.8-flash", "gemini-3.5-flash-lite", "gemini-3.1-flash-lite"):
            if fallback not in models:
                models.append(fallback)

        last_error = None
        for candidate_model in models:
            try:
                return self.client.models.generate_content(
                    model=candidate_model,
                    contents=contents,
                    config=config,
                )
            except (ServerError, ClientError) as e:
                code = getattr(e, "code", None)
                if code in (404, 408, 429, 503, 504):
                    logger.warning(
                        "Gemini model '%s' hit %s (%s). Attempting fallback...",
                        candidate_model,
                        code,
                        getattr(e, "message", str(e)),
                    )
                    last_error = e
                    continue
                raise
            except Exception as e:
                err_str = str(e).lower()
                if "timed out" in err_str or "timeout" in err_str:
                    logger.warning(
                        "Gemini model '%s' timed out (%s). Attempting fallback...",
                        candidate_model,
                        e,
                    )
                    last_error = e
                    continue
                last_error = e
                raise

        if last_error:
            raise last_error

    def generate_decision(
        self,
        system_prompt: str,
        user_message: str,
        context: Dict[str, Any],
        tool_definitions: List[Dict[str, Any]],
    ) -> LLMDecision:
        """Prompt Gemini for a structured decision JSON adhering strictly to decision schemas."""
        context_str = json.dumps(context, indent=2)
        tools_str = json.dumps(tool_definitions, indent=2)

        prompt_payload = f"""Active Cooking Context:
{context_str}

Allowed Backend Tools:
{tools_str}

User Cooking Message:
"{user_message}"

Respond strictly with a JSON object representing your decision. It MUST match one of these 3 structures:
1. Execute an allowlisted action:
   {{"type": "execute_action", "action": "<action_name>", "arguments": {{...}}}}
2. Answer a general culinary question:
   {{"type": "answer_question", "question": "<question>", "answer": "<concise culinary answer>"}}
3. Ask for clarification on ambiguous statements:
   {{"type": "clarify", "question": "<clarification question>"}}
"""

        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            response_mime_type="application/json",
            temperature=0.0,
        )

        try:
            response = self._generate_content_resilient(
                contents=prompt_payload,
                config=config,
            )
            raw_content = response.text or "{}"
            parsed_json = json.loads(raw_content)

            decision_type = parsed_json.get("type")
            if decision_type == "execute_action":
                return ExecuteActionDecision.model_validate(parsed_json)
            elif decision_type == "answer_question":
                return AnswerQuestionDecision.model_validate(parsed_json)
            elif decision_type == "clarify":
                return ClarifyDecision.model_validate(parsed_json)
            else:
                raise LLMInvalidOutputError(
                    f"Unknown decision type '{decision_type}' received from Gemini model."
                )

        except ClientError as e:
            if e.code in (401, 403):
                raise LLMAuthenticationError(f"Gemini authentication failed: {e.message}") from e
            if e.code == 429:
                raise LLMRateLimitError(f"Gemini rate limit exceeded: {e.message}") from e
            if e.code == 408:
                raise LLMTimeoutError(f"Gemini request timed out: {e.message}") from e
            raise LLMError(f"Gemini client error ({e.code}): {e.message}") from e
        except ServerError as e:
            if e.code == 504:
                raise LLMTimeoutError(f"Gemini gateway timed out: {e.message}") from e
            raise LLMProviderUnavailableError(f"Gemini service unavailable ({e.code}): {e.message}") from e
        except APIError as e:
            raise LLMError(f"Gemini API error ({e.code}): {e.message}") from e
        except (json.JSONDecodeError, ValidationError) as e:
            raise LLMInvalidOutputError(f"Failed to parse structured Gemini decision: {e}") from e
        except TimeoutError as e:
            raise LLMTimeoutError(f"Gemini request timed out: {e}") from e
        except Exception as e:
            err_str = str(e).lower()
            if "timed out" in err_str or "timeout" in err_str:
                raise LLMTimeoutError(f"Gemini request timed out: {e}") from e
            raise LLMError(f"Unexpected error communicating with Gemini: {e}") from e

    def generate_grounded_response(
        self,
        system_prompt: str,
        user_message: str,
        decision: LLMDecision,
        action_result: Optional[ActionResult] = None,
        session_state: Optional[CookingSessionRead] = None,
    ) -> str:
        """Prompt Gemini for a grounded natural language reply based on actual backend results."""
        if decision.type == "answer_question":
            return decision.answer
        if decision.type == "clarify":
            return decision.question

        action_summary = action_result.model_dump(mode="json") if action_result else {}
        session_summary = session_state.model_dump(mode="json") if session_state else {}

        user_content = f"""User Message: "{user_message}"
Action Executed: {decision.action}
Action Execution Result: {json.dumps(action_summary)}
Updated Session State: {json.dumps(session_summary)}

Provide a concise, direct, grounded response to the cook in their language."""

        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.3,
            max_output_tokens=250,
        )

        try:
            response = self._generate_content_resilient(
                contents=user_content,
                config=config,
            )
            return response.text or "Step processed."
        except ClientError as e:
            if e.code in (401, 403):
                raise LLMAuthenticationError(f"Gemini authentication failed: {e.message}") from e
            if e.code == 429:
                raise LLMRateLimitError(f"Gemini rate limit exceeded: {e.message}") from e
            if e.code == 408:
                raise LLMTimeoutError(f"Gemini request timed out: {e.message}") from e
            raise LLMError(f"Gemini client error ({e.code}): {e.message}") from e
        except ServerError as e:
            if e.code == 504:
                raise LLMTimeoutError(f"Gemini gateway timed out: {e.message}") from e
            raise LLMProviderUnavailableError(f"Gemini service unavailable ({e.code}): {e.message}") from e
        except APIError as e:
            raise LLMError(f"Gemini API error ({e.code}): {e.message}") from e
        except TimeoutError as e:
            raise LLMTimeoutError(f"Gemini response timed out: {e}") from e
        except Exception as e:
            err_str = str(e).lower()
            if "timed out" in err_str or "timeout" in err_str:
                raise LLMTimeoutError(f"Gemini response timed out: {e}") from e
            raise LLMError(f"Unexpected error communicating with Gemini: {e}") from e

