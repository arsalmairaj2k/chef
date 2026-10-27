import logging
from typing import Optional
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.ai.prompts import COOKING_ASSISTANT_SYSTEM_PROMPT, GROUNDED_RESPONSE_PROMPT
from app.ai.tool_registry import ToolRegistry
from app.ai.action_executor import ActionExecutor
from app.ai.providers import get_llm_provider
from app.ai.providers.base import (
    BaseLLMProvider,
    LLMError,
    LLMTimeoutError,
    LLMRateLimitError,
    LLMAuthenticationError,
    LLMInvalidOutputError,
    LLMProviderUnavailableError,
)
from app.services.session_service import SessionService, SessionNotFoundError
from app.schemas.chat import ChatMessageResponse, ActionExecutionSummary
from app.schemas.cooking_session import CookingSessionRead


logger = logging.getLogger(__name__)


class ChatService:
    """Orchestrates natural language intent interpretation, backend action dispatching, and grounded responses."""

    @classmethod
    def process_message(
        cls,
        db: Session,
        session_id: int,
        message: str,
        provider: Optional[BaseLLMProvider] = None,
    ) -> ChatMessageResponse:
        """Process a cooking user message safely against an existing session."""
        settings = get_settings()

        # 1. Validate message length
        cleaned_msg = message.strip()
        if not cleaned_msg:
            raise ValueError("Message cannot be empty or whitespace only.")
        if len(cleaned_msg) > settings.llm_max_message_length:
            raise ValueError(
                f"Message length ({len(cleaned_msg)}) exceeds maximum limit of {settings.llm_max_message_length} characters."
            )

        # 2. Authoritative session lookup
        session_read: CookingSessionRead = SessionService.get_session(db, session_id=session_id)

        # 3. Build relevant session context including scaled recipe ingredients
        context = {
            "session_id": session_read.id,
            "recipe_id": session_read.recipe_id,
            "recipe_name": session_read.recipe_name,
            "status": session_read.status,
            "current_step_number": session_read.current_step_number,
            "servings": session_read.servings,
            "current_step": (
                session_read.current_step.model_dump(mode="json")
                if session_read.current_step
                else None
            ),
            "ingredients": [i.model_dump(mode="json") for i in session_read.ingredients],
        }

        # 4. Get allowlisted tool schemas
        tool_definitions = ToolRegistry.get_definitions()

        # 5. Obtain LLM decision
        llm = provider or get_llm_provider()
        decision = llm.generate_decision(
            system_prompt=COOKING_ASSISTANT_SYSTEM_PROMPT,
            user_message=cleaned_msg,
            context=context,
            tool_definitions=tool_definitions,
        )

        # 6. Dispatch based on decision outcome
        if decision.type == "execute_action":
            exec_args = dict(decision.arguments)

            # Inbound session actions must target this authoritative session
            session_actions = {"get_current_state", "get_current_step", "complete_step", "skip_step"}
            if decision.action in session_actions:
                exec_args["session_id"] = session_id

            # Execute action via existing, validated ActionExecutor
            action_result = ActionExecutor.execute_action(
                db=db,
                action_name=decision.action,
                arguments=exec_args,
            )

            # Refresh persisted session state after mutation
            updated_session = SessionService.get_session(db, session_id=session_id)

            # Generate grounded response based on execution result
            reply = llm.generate_grounded_response(
                system_prompt=GROUNDED_RESPONSE_PROMPT,
                user_message=cleaned_msg,
                decision=decision,
                action_result=action_result,
                session_state=updated_session,
            )

            action_summary = ActionExecutionSummary(
                name=decision.action,
                status="success" if action_result.success else "error",
                error=action_result.error.message if action_result.error else None,
                data=action_result.data if action_result.success else None,
            )

            return ChatMessageResponse(
                reply=reply,
                session=updated_session,
                decision_type="execute_action",
                action=action_summary,
            )

        elif decision.type == "answer_question":
            reply = llm.generate_grounded_response(
                system_prompt=GROUNDED_RESPONSE_PROMPT,
                user_message=cleaned_msg,
                decision=decision,
                action_result=None,
                session_state=session_read,
            )
            return ChatMessageResponse(
                reply=reply,
                session=session_read,
                decision_type="answer_question",
                action=None,
            )

        elif decision.type == "clarify":
            reply = llm.generate_grounded_response(
                system_prompt=GROUNDED_RESPONSE_PROMPT,
                user_message=cleaned_msg,
                decision=decision,
                action_result=None,
                session_state=session_read,
            )
            return ChatMessageResponse(
                reply=reply,
                session=session_read,
                decision_type="clarify",
                action=None,
            )

        else:
            raise ValueError(f"Unhandled decision type '{getattr(decision, 'type', None)}'")
