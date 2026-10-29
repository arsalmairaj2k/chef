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
        """Execute generate_content with automatic fallback across models, demand spikes, and thinking configs."""
        primary = self.model
        if primary in ("gemini-2.5-flash", "models/gemini-2.5-flash", "gemini-1.5-flash", "models/gemini-1.5-flash"):
            primary = "gemini-3.5-flash"

        # Robust priority list of operational Gemini models
        candidate_pool = [
            primary,
            "gemini-3.5-flash",
            "gemini-3.8-flash",
            "gemini-3-flash-preview",
            "gemini-3.5-flash-lite",
            "gemini-flash-latest",
        ]
        models = []
        for m in candidate_pool:
            if m not in models:
                models.append(m)

        last_error = None
        for candidate_model in models:
            # First attempt with provided config
            try:
                return self.client.models.generate_content(
                    model=candidate_model,
                    contents=contents,
                    config=config,
                )
            except ClientError as e:
                code = getattr(e, "code", None)
                msg = getattr(e, "message", str(e)).lower()
                # If thinking config is unsupported for this specific model, retry without it
                if code == 400 and ("thinking" in msg or "thinking_level" in msg or "budget" in msg):
                    logger.warning(
                        "Model '%s' rejected thinking config (%s). Retrying without thinking config...",
                        candidate_model,
                        msg,
                    )
                    safe_config = config.model_copy() if hasattr(config, "model_copy") else config
                    safe_config.thinking_config = None
                    try:
                        return self.client.models.generate_content(
                            model=candidate_model,
                            contents=contents,
                            config=safe_config,
                        )
                    except Exception as inner_e:
                        last_error = inner_e
                        continue

                if code in (404, 408, 429):
                    logger.warning(
                        "Gemini model '%s' hit %s (%s). Attempting fallback...",
                        candidate_model,
                        code,
                        getattr(e, "message", str(e)),
                    )
                    last_error = e
                    continue
                last_error = e
                raise
            except ServerError as e:
                # Catch 500, 502, 503 (demand spike), 504 (timeout) and fallback
                logger.warning(
                    "Gemini model '%s' hit server error %s (%s). Attempting fallback...",
                    candidate_model,
                    getattr(e, "code", 500),
                    getattr(e, "message", str(e)),
                )
                last_error = e
                continue
            except Exception as e:
                err_str = str(e).lower()
                if "timed out" in err_str or "timeout" in err_str or "connection" in err_str or "reset" in err_str:
                    logger.warning(
                        "Gemini model '%s' hit connection issue (%s). Attempting fallback...",
                        candidate_model,
                        e,
                    )
                    last_error = e
                    continue
                last_error = e
                raise

        if last_error:
            raise last_error

    def _extract_response_text(self, response: Any) -> str:
        """Safely extract text content from response across all candidate formats and parts."""
        if not response:
            return ""
        try:
            if getattr(response, "text", None):
                return response.text.strip()
        except Exception:
            pass

        # Fallback to candidates structure if response.text raised
        try:
            if hasattr(response, "candidates") and response.candidates:
                for c in response.candidates:
                    if hasattr(c, "content") and c.content and hasattr(c.content, "parts") and c.content.parts:
                        parts_text = []
                        for p in c.content.parts:
                            if hasattr(p, "text") and p.text:
                                parts_text.append(p.text)
                        if parts_text:
                            return "".join(parts_text).strip()
        except Exception:
            pass
        return ""

    def _clean_json_payload(self, text: str) -> str:
        """Strip markdown fences, thoughts, or comments and extract the JSON envelope."""
        cleaned = text.strip()
        if cleaned.startswith("```"):
            lines = cleaned.splitlines()
            if len(lines) >= 2:
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                cleaned = "\n".join(lines).strip()

        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            cleaned = cleaned[start : end + 1]
        return cleaned

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
            max_output_tokens=600,
        )

        raw_content = ""
        try:
            response = self._generate_content_resilient(
                contents=prompt_payload,
                config=config,
            )
            raw_content = self._extract_response_text(response)
            cleaned_json = self._clean_json_payload(raw_content)
            parsed_json = json.loads(cleaned_json)

            decision_type = parsed_json.get("type")
            if decision_type == "execute_action":
                action_name = parsed_json.get("action", "")
                # Normalize common action synonyms
                synonyms = {
                    "next": "complete_step",
                    "next_step": "complete_step",
                    "complete": "complete_step",
                    "complete_current_step": "complete_step",
                    "finish_step": "complete_step",
                    "skip": "skip_step",
                    "skip_current_step": "skip_step",
                    "get_step": "get_current_step",
                    "step": "get_current_step",
                    "state": "get_current_state",
                    "status": "get_current_state",
                }
                action_name = synonyms.get(action_name, action_name)
                parsed_json["action"] = action_name
                if "arguments" not in parsed_json or not isinstance(parsed_json["arguments"], dict):
                    parsed_json["arguments"] = {}
                return ExecuteActionDecision.model_validate(parsed_json)

            elif decision_type == "answer_question":
                if "question" not in parsed_json or not parsed_json["question"]:
                    parsed_json["question"] = user_message
                if "answer" not in parsed_json or not parsed_json["answer"]:
                    parsed_json["answer"] = (
                        parsed_json.get("text")
                        or parsed_json.get("response")
                        or "Here is the culinary guidance for your current step."
                    )
                return AnswerQuestionDecision.model_validate(parsed_json)

            elif decision_type == "clarify":
                if "question" not in parsed_json or not parsed_json["question"]:
                    parsed_json["question"] = (
                        parsed_json.get("clarification")
                        or parsed_json.get("text")
                        or "Could you please clarify what you would like to do next?"
                    )
                return ClarifyDecision.model_validate(parsed_json)

            else:
                # Fall back gracefully to question answer rather than raising invalid output error
                return AnswerQuestionDecision(
                    question=user_message,
                    answer=raw_content or "Main aapki recipe mein agle step par chalne ke liye tayyar hoon.",
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
            logger.warning("JSON decode failed for raw output '%s': %s. Applying smart fallback.", raw_content, e)
            lower_msg = user_message.lower()
            # Smart intent fallback based on culinary phrases
            if any(w in lower_msg for w in ("next", "done", "ho gaya", "kar liya", "finish", "tayyar", "agla", "completed")):
                return ExecuteActionDecision(action="complete_step", arguments={})
            if any(w in lower_msg for w in ("skip", "chhor do", "aage chalo")):
                return ExecuteActionDecision(action="skip_step", arguments={})
            fallback_answer = raw_content.strip() if raw_content else ""
            if not fallback_answer or fallback_answer.startswith("{") or '"type"' in fallback_answer:
                fallback_answer = "Aap agle step par chalna chahte hain ya is step ke bare mein kuch poochna chahte hain?"
            return AnswerQuestionDecision(
                question=user_message,
                answer=fallback_answer,
            )
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
            max_output_tokens=300,
        )

        try:
            response = self._generate_content_resilient(
                contents=user_content,
                config=config,
            )
            extracted = self._extract_response_text(response)
            if extracted:
                return extracted
            if session_state and session_state.current_step:
                return f"Step {session_state.current_step_number}: {session_state.current_step.instruction}"
            return "Step processed successfully."
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

