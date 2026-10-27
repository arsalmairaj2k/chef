from typing import Any, Dict, List, Optional
import re

from app.ai.providers.base import (
    BaseLLMProvider,
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


class FakeLLMProvider(BaseLLMProvider):
    """Deterministic, zero-cost fake LLM provider for unit and integration testing."""

    def __init__(
        self,
        canned_decisions: Optional[List[LLMDecision]] = None,
        canned_replies: Optional[List[str]] = None,
        force_timeout: bool = False,
        force_rate_limit: bool = False,
        force_auth_error: bool = False,
        force_invalid_output: bool = False,
        force_unavailable: bool = False,
    ):
        self._canned_decisions: List[LLMDecision] = list(canned_decisions or [])
        self._canned_replies: List[str] = list(canned_replies or [])
        self.force_timeout = force_timeout
        self.force_rate_limit = force_rate_limit
        self.force_auth_error = force_auth_error
        self.force_invalid_output = force_invalid_output
        self.force_unavailable = force_unavailable

    def queue_decision(self, decision: LLMDecision) -> None:
        """Enqueue a scripted decision for the next call."""
        self._canned_decisions.append(decision)

    def queue_reply(self, reply: str) -> None:
        """Enqueue a scripted grounded reply for the next call."""
        self._canned_replies.append(reply)

    def generate_decision(
        self,
        system_prompt: str,
        user_message: str,
        context: Dict[str, Any],
        tool_definitions: List[Dict[str, Any]],
    ) -> LLMDecision:
        # Check simulated failure flags
        if self.force_timeout:
            raise LLMTimeoutError("Simulated LLM provider request timeout.")
        if self.force_rate_limit:
            raise LLMRateLimitError("Simulated rate limit exceeded. Please retry later.")
        if self.force_auth_error:
            raise LLMAuthenticationError("Simulated invalid or missing LLM API credentials.")
        if self.force_invalid_output:
            raise LLMInvalidOutputError("Simulated malformed or invalid LLM output.")
        if self.force_unavailable:
            raise LLMProviderUnavailableError("Simulated LLM service temporarily unavailable.")

        # Return queued canned decision if present
        if self._canned_decisions:
            return self._canned_decisions.pop(0)

        # Rule-based heuristic decision engine for realistic offline testing
        msg_lower = user_message.strip().lower()

        # 1. Ambiguous statements trigger clarification
        ambiguous_patterns = ["chicken daal diya", "added onions", "done with something", "maybe"]
        if any(pat in msg_lower for pat in ambiguous_patterns):
            return ClarifyDecision(
                type="clarify",
                question="Did you just add the ingredient to the pan, or has this cooking step finished completely?",
            )

        # 2. General culinary questions (distinguished from step completions)
        question_keywords = ["why do we", "how long", "what temperature", "kitni dair", "kyun"]
        if any(kw in msg_lower for kw in question_keywords):
            return AnswerQuestionDecision(
                type="answer_question",
                question=user_message,
                answer="Browning onions caramelizes natural sugars, creating a rich base flavor for the gravy.",
            )

        # 3. Explicit step completion
        completion_keywords = ["done", "finished", "completed", "ho gaya", "hogaya", "step complete"]
        if any(kw in msg_lower for kw in completion_keywords):
            # Extract step number if mentioned e.g. "step 1 done"
            step_match = re.search(r"step\s*(\d+)", msg_lower)
            step_num = int(step_match.group(1)) if step_match else context.get("current_step_number", 1)
            return ExecuteActionDecision(
                type="execute_action",
                action="complete_step",
                arguments={"step_number": step_num},
            )

        # 4. Explicit step skipping
        if "skip" in msg_lower or "chhor do" in msg_lower:
            step_match = re.search(r"step\s*(\d+)", msg_lower)
            step_num = int(step_match.group(1)) if step_match else context.get("current_step_number", 1)
            return ExecuteActionDecision(
                type="execute_action",
                action="skip_step",
                arguments={"step_number": step_num},
            )

        # 5. Queries asking what to do next or for current step
        if any(phrase in msg_lower for phrase in ["next", "what should i do", "current step", "agla step", "kya karna hai"]):
            return ExecuteActionDecision(
                type="execute_action",
                action="get_current_step",
                arguments={},
            )

        # 6. Fallback clarification
        return ClarifyDecision(
            type="clarify",
            question="Would you like to hear the current step instructions or have you completed it?",
        )

    def generate_grounded_response(
        self,
        system_prompt: str,
        user_message: str,
        decision: LLMDecision,
        action_result: Optional[ActionResult] = None,
        session_state: Optional[CookingSessionRead] = None,
    ) -> str:
        if self._canned_replies:
            return self._canned_replies.pop(0)

        if decision.type == "answer_question":
            return decision.answer

        if decision.type == "clarify":
            return decision.question

        if decision.type == "execute_action":
            if action_result is None:
                return "The requested action has been scheduled."

            if action_result.success:
                if action_result.action == "complete_step":
                    curr_step = session_state.current_step if session_state else None
                    if curr_step:
                        return f"Step marked completed! Next up: Step {curr_step.step_number} - {curr_step.instruction}"
                    return "All cooking steps completed! Enjoy your meal!"

                if action_result.action == "skip_step":
                    curr_step = session_state.current_step if session_state else None
                    if curr_step:
                        return f"Step skipped. Proceed to Step {curr_step.step_number} - {curr_step.instruction}"
                    return "Step skipped. All cooking steps are now finished."

                if action_result.action == "get_current_step":
                    step_data = action_result.data.get("current_step") if action_result.data else None
                    if step_data:
                        return f"Currently on Step {step_data['step_number']}: {step_data['instruction']}"
                    return "No step is currently active in this session."

                return f"Action '{action_result.action}' succeeded."

            # Action failed
            err_msg = action_result.error.message if action_result.error else "Unknown error"
            return f"Action could not be completed: {err_msg}"

        return "I am here to assist with your cooking."
