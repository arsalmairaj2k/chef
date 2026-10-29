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
from app.models.chat_message import ChatMessage
from app.schemas.chat import ChatMessageResponse, ActionExecutionSummary, ChatMessageRead
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
            raw_args = dict(decision.arguments)
            exec_args: dict = {}

            # Inbound session actions must target this authoritative session
            session_actions = {"get_current_state", "get_current_step", "complete_step", "skip_step"}
            if decision.action in session_actions:
                exec_args["session_id"] = session_id

            if decision.action in ("complete_step", "skip_step"):
                step_num = raw_args.get("step_number")
                if step_num is None:
                    exec_args["step_number"] = session_read.current_step_number
                else:
                    try:
                        exec_args["step_number"] = int(step_num)
                    except (ValueError, TypeError):
                        exec_args["step_number"] = session_read.current_step_number
            elif decision.action == "get_recipe":
                if "recipe_id" in raw_args and raw_args["recipe_id"] is not None:
                    exec_args["recipe_id"] = int(raw_args["recipe_id"])
                elif "slug" in raw_args and raw_args["slug"]:
                    exec_args["slug"] = str(raw_args["slug"]).strip()
                else:
                    exec_args["recipe_id"] = session_read.recipe_id
            else:
                exec_args.update(raw_args)

            # Execute action via existing, validated ActionExecutor
            action_result = ActionExecutor.execute_action(
                db=db,
                action_name=decision.action,
                arguments=exec_args,
            )

            # Refresh persisted session state after mutation
            updated_session = SessionService.get_session(db, session_id=session_id)

            # Format authoritative grounded response directly from session state (0s latency, zero truncation risk)
            if not action_result.success:
                err_msg = action_result.error.message if action_result.error else "Unknown error"
                reply = f"Action could not be completed: {err_msg}"
            elif decision.action == "complete_step":
                if updated_session.status == "COMPLETED":
                    reply = "🎉 Bohat khoob! All cooking steps completed! Nosh-e-Jaan / Enjoy your meal!"
                elif updated_session.current_step:
                    curr = updated_session.current_step
                    reply = f"✅ Step marked completed! Next up: Step {curr.step_number} - {curr.instruction}"
                else:
                    reply = "Step marked completed!"
            elif decision.action == "skip_step":
                if updated_session.status == "COMPLETED":
                    reply = "⏭️ Step skipped. All cooking steps are now finished."
                elif updated_session.current_step:
                    curr = updated_session.current_step
                    reply = f"⏭️ Step skipped. Proceed to Step {curr.step_number} - {curr.instruction}"
                else:
                    reply = "Step skipped."
            elif decision.action in ("get_current_step", "get_current_state"):
                if updated_session.current_step:
                    curr = updated_session.current_step
                    reply = f"Currently on Step {curr.step_number}: {curr.instruction}"
                else:
                    reply = f"Session status: {updated_session.status}"
            else:
                try:
                    reply = llm.generate_grounded_response(
                        system_prompt=GROUNDED_RESPONSE_PROMPT,
                        user_message=cleaned_msg,
                        decision=decision,
                        action_result=action_result,
                        session_state=updated_session,
                    )
                except Exception as e:
                    logger.warning("Grounded fallback after action: %s", e)
                    if updated_session.current_step:
                        reply = f"Step {updated_session.current_step_number}: {updated_session.current_step.instruction}"
                    else:
                        reply = "Action completed successfully."

            action_summary = ActionExecutionSummary(
                name=decision.action,
                status="success" if action_result.success else "error",
                error=action_result.error.message if action_result.error else None,
                data=action_result.data if action_result.success else None,
            )

            response_obj = ChatMessageResponse(
                reply=reply,
                session=updated_session,
                decision_type="execute_action",
                action=action_summary,
            )

        elif decision.type == "answer_question":
            # Direct response from decision without redundant second roundtrip
            reply = decision.answer if getattr(decision, "answer", None) else "Here is the guidance for your recipe."
            response_obj = ChatMessageResponse(
                reply=reply,
                session=session_read,
                decision_type="answer_question",
                action=None,
            )

        elif decision.type == "clarify":
            # Direct response from decision without redundant second roundtrip
            reply = decision.question if getattr(decision, "question", None) else "Could you please clarify what you would like to do?"
            response_obj = ChatMessageResponse(
                reply=reply,
                session=session_read,
                decision_type="clarify",
                action=None,
            )

        else:
            raise ValueError(f"Unhandled decision type '{getattr(decision, 'type', None)}'")

        # Persist conversation exchange to database for page refresh & history recovery
        try:
            user_msg_record = ChatMessage(session_id=session_id, role="user", content=cleaned_msg)
            assistant_msg_record = ChatMessage(
                session_id=session_id,
                role="assistant",
                content=response_obj.reply,
                decision_type=response_obj.decision_type,
            )
            db.add(user_msg_record)
            db.add(assistant_msg_record)
            db.commit()
        except Exception as e:
            logger.warning("Could not persist chat message to database: %s", e)
            try:
                db.rollback()
            except Exception:
                pass

        return response_obj

    @classmethod
    def get_session_messages(cls, db: Session, session_id: int) -> list[ChatMessageRead]:
        """Retrieve full chronological conversation transcript for an authoritative session."""
        SessionService.get_session(db, session_id=session_id)
        records = (
            db.query(ChatMessage)
            .filter(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc(), ChatMessage.id.asc())
            .all()
        )
        return [ChatMessageRead.model_validate(r) for r in records]
