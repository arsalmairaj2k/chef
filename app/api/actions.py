from typing import Any, Dict, List
from fastapi import APIRouter, Depends, Path, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.ai.action_results import ActionResult, ActionError, ActionErrorCode
from app.ai.action_executor import ActionExecutor
from app.ai.tool_registry import ToolRegistry


router = APIRouter(prefix="/sessions", tags=["actions"])


class ActionExecutionRequest(BaseModel):
    """Payload for invoking an action via the development/orchestration endpoint."""
    action: str = Field(..., description="Name of the allowlisted action to execute")
    arguments: Dict[str, Any] = Field(
        default_factory=dict,
        description="Arguments object. For session actions, session_id is inferred from path if omitted.",
    )

    model_config = ConfigDict(extra="forbid")


@router.get(
    "/actions/tools",
    response_model=List[Dict[str, Any]],
    status_code=status.HTTP_200_OK,
    summary="Inspect allowlisted tool definitions and schemas",
)
def get_tool_definitions() -> List[Dict[str, Any]]:
    """Retrieve available tool names, descriptions, and JSON Schema definitions for future tool-calling integrations."""
    return ToolRegistry.get_definitions()


@router.post(
    "/{session_id}/actions",
    response_model=ActionResult,
    status_code=status.HTTP_200_OK,
    summary="Execute a cooking tool action in the context of a session",
)
def execute_session_action(
    session_id: int = Path(..., gt=0, description="Authoritative session identifier from URL path"),
    payload: ActionExecutionRequest = ...,
    db: Session = Depends(get_db),
) -> ActionResult:
    """Development and test interface for dispatching tool actions to the cooking companion engine.

    The session_id in the URL path is authoritative for session operations.
    Conflicting session IDs in the payload body are strictly rejected.
    For get_recipe, session_id is neither required nor injected into recipe lookups.
    """
    exec_args = dict(payload.arguments)

    # Actions that operate on a cooking session
    session_actions = {"get_current_state", "get_current_step", "complete_step", "skip_step"}

    if payload.action in session_actions:
        if "session_id" in exec_args:
            # Reject conflicting session IDs
            if exec_args["session_id"] != session_id:
                return ActionResult(
                    success=False,
                    action=payload.action,
                    error=ActionError(
                        code=ActionErrorCode.INVALID_ARGUMENTS,
                        message=(
                            f"Conflicting session_id: URL path specifies {session_id}, "
                            f"but arguments body specifies {exec_args['session_id']}."
                        ),
                        suggestion="Omit 'session_id' from the request body arguments or ensure it matches the URL path.",
                    ),
                )
        else:
            # Authoritatively supply path session_id
            exec_args["session_id"] = session_id

    # For get_recipe or unknown actions, pass exec_args directly to the executor
    return ActionExecutor.execute_action(
        db=db,
        action_name=payload.action,
        arguments=exec_args,
    )
