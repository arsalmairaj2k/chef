import json
import logging
from typing import Any, Dict, List, Optional
import openai
from openai import OpenAI
from pydantic import ValidationError

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


class OpenAILLMProvider(BaseLLMProvider):
    """Production LLM adapter leveraging OpenAI with structured output and error normalization."""

    def __init__(
        self,
        api_key: Optional[str],
        model: str = "gpt-4o-mini",
        timeout: float = 30.0,
        max_retries: int = 2,
    ):
        if not api_key:
            raise LLMAuthenticationError(
                "OpenAI API key is missing. Set OPENAI_API_KEY environment variable."
            )
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries
        self.client = OpenAI(
            api_key=api_key,
            timeout=timeout,
            max_retries=max_retries,
        )

    def generate_decision(
        self,
        system_prompt: str,
        user_message: str,
        context: Dict[str, Any],
        tool_definitions: List[Dict[str, Any]],
    ) -> LLMDecision:
        """Prompt OpenAI for a structured decision JSON conforming to LLMDecision schemas."""
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

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt_payload},
        ]

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.0,
            )
            raw_content = response.choices[0].message.content or "{}"
            parsed_json = json.loads(raw_content)

            # Determine decision type and validate with strict Pydantic models
            decision_type = parsed_json.get("type")
            if decision_type == "execute_action":
                return ExecuteActionDecision.model_validate(parsed_json)
            elif decision_type == "answer_question":
                return AnswerQuestionDecision.model_validate(parsed_json)
            elif decision_type == "clarify":
                return ClarifyDecision.model_validate(parsed_json)
            else:
                raise LLMInvalidOutputError(
                    f"Unknown decision type '{decision_type}' received from model."
                )

        except openai.APITimeoutError as e:
            raise LLMTimeoutError(f"OpenAI request timed out: {e}") from e
        except openai.RateLimitError as e:
            raise LLMRateLimitError(f"OpenAI rate limit exceeded: {e}") from e
        except openai.AuthenticationError as e:
            raise LLMAuthenticationError(f"OpenAI authentication failed: {e}") from e
        except (openai.APIConnectionError, openai.InternalServerError) as e:
            raise LLMProviderUnavailableError(f"OpenAI service unavailable: {e}") from e
        except (json.JSONDecodeError, ValidationError) as e:
            raise LLMInvalidOutputError(f"Failed to parse structured model decision: {e}") from e
        except openai.APIError as e:
            raise LLMError(f"OpenAI API error occurred: {e}") from e

    def generate_grounded_response(
        self,
        system_prompt: str,
        user_message: str,
        decision: LLMDecision,
        action_result: Optional[ActionResult] = None,
        session_state: Optional[CookingSessionRead] = None,
    ) -> str:
        """Prompt OpenAI for a grounded natural language reply based on actual backend results."""
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

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,
                max_tokens=250,
            )
            return response.choices[0].message.content or "Step processed."
        except openai.APITimeoutError as e:
            raise LLMTimeoutError(f"OpenAI response generation timed out: {e}") from e
        except openai.RateLimitError as e:
            raise LLMRateLimitError(f"OpenAI rate limit exceeded: {e}") from e
        except openai.AuthenticationError as e:
            raise LLMAuthenticationError(f"OpenAI authentication failed: {e}") from e
        except (openai.APIConnectionError, openai.InternalServerError) as e:
            raise LLMProviderUnavailableError(f"OpenAI service unavailable: {e}") from e
        except openai.APIError as e:
            raise LLMError(f"OpenAI API error occurred: {e}") from e
