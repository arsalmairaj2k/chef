import logging
from typing import Any, Dict, Optional
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.ai.action_results import ActionError, ActionErrorCode, ActionResult
from app.ai.tool_registry import ToolRegistry
from app.services.session_service import (
    SessionNotFoundError,
    RecipeNotFoundError as SessionRecipeNotFoundError,
    RecipeHasNoStepsError,
    SessionNotActiveError,
    StepNotCurrentError,
    StepNotFoundError,
)
from app.services.recipe_service import RecipeNotFoundError as ServiceRecipeNotFoundError


logger = logging.getLogger(__name__)


class ActionExecutor:
    """Safe execution engine that bridges untrusted action requests to domain services."""

    @classmethod
    def execute_action(
        cls,
        db: Session,
        action_name: str,
        arguments: Dict[str, Any],
    ) -> ActionResult:
        """Validate and safely execute an allowlisted action against the domain service layer."""
        # 1. Action Name Allowlist Verification
        if not isinstance(action_name, str) or not ToolRegistry.contains(action_name):
            supported = ", ".join(ToolRegistry.list_tools())
            return ActionResult(
                success=False,
                action=str(action_name) if action_name is not None else None,
                error=ActionError(
                    code=ActionErrorCode.INVALID_ACTION,
                    message=f"Action '{action_name}' is not recognized or not allowed.",
                    suggestion=f"Supported actions are: {supported}.",
                ),
            )

        tool = ToolRegistry.get(action_name)
        if tool is None:
            return ActionResult(
                success=False,
                action=action_name,
                error=ActionError(
                    code=ActionErrorCode.INVALID_ACTION,
                    message=f"Action '{action_name}' is unavailable.",
                    suggestion="Please select an allowlisted action.",
                ),
            )

        # 2. Arguments Dictionary Check
        if not isinstance(arguments, dict):
            return ActionResult(
                success=False,
                action=action_name,
                error=ActionError(
                    code=ActionErrorCode.INVALID_ARGUMENTS,
                    message="Arguments must be provided as a dictionary/object.",
                    suggestion="Provide a valid JSON key-value object matching the tool parameters.",
                ),
            )

        # 3. Strict Schema Validation
        try:
            validated_args = tool.args_schema.model_validate(arguments)
        except ValidationError as val_err:
            error_details = []
            for err in val_err.errors():
                loc = " -> ".join(str(p) for p in err.get("loc", []))
                msg = err.get("msg", "Invalid value")
                error_details.append(f"'{loc}': {msg}" if loc else msg)
            summary_msg = "; ".join(error_details)
            return ActionResult(
                success=False,
                action=action_name,
                error=ActionError(
                    code=ActionErrorCode.INVALID_ARGUMENTS,
                    message=f"Argument validation failed for '{action_name}': {summary_msg}",
                    suggestion="Ensure required arguments are present with correct types and no unexpected extra fields.",
                ),
            )

        # 4. Safe Domain Execution
        try:
            result_data = tool.handler(db, validated_args)
            return ActionResult(
                success=True,
                action=action_name,
                data=result_data,
                error=None,
            )

        except SessionNotFoundError as err:
            return ActionResult(
                success=False,
                action=action_name,
                error=ActionError(
                    code=ActionErrorCode.SESSION_NOT_FOUND,
                    message=str(err),
                    suggestion="Verify that the session_id belongs to an active or existing cooking session.",
                ),
            )

        except (SessionRecipeNotFoundError, ServiceRecipeNotFoundError) as err:
            return ActionResult(
                success=False,
                action=action_name,
                error=ActionError(
                    code=ActionErrorCode.RECIPE_NOT_FOUND,
                    message=str(err),
                    suggestion="Verify that the recipe_id or slug exists in the recipe catalog.",
                ),
            )

        except StepNotCurrentError as err:
            return ActionResult(
                success=False,
                action=action_name,
                error=ActionError(
                    code=ActionErrorCode.STEP_CONFLICT,
                    message=str(err),
                    suggestion="You can only complete or skip the current active step in progress.",
                ),
            )

        except StepNotFoundError as err:
            return ActionResult(
                success=False,
                action=action_name,
                error=ActionError(
                    code=ActionErrorCode.STEP_CONFLICT,
                    message=str(err),
                    suggestion="The specified step number does not exist in this recipe.",
                ),
            )

        except RecipeHasNoStepsError as err:
            return ActionResult(
                success=False,
                action=action_name,
                error=ActionError(
                    code=ActionErrorCode.STEP_CONFLICT,
                    message=str(err),
                    suggestion="This recipe does not have any cooking steps defined.",
                ),
            )

        except SessionNotActiveError as err:
            return ActionResult(
                success=False,
                action=action_name,
                error=ActionError(
                    code=ActionErrorCode.SESSION_NOT_ACTIVE,
                    message=str(err),
                    suggestion="The cooking session has already ended (completed or cancelled). No further step modifications are permitted.",
                ),
            )

        except ValueError as err:
            return ActionResult(
                success=False,
                action=action_name,
                error=ActionError(
                    code=ActionErrorCode.INVALID_ARGUMENTS,
                    message=str(err),
                    suggestion="Review the provided argument values.",
                ),
            )

        except Exception as err:
            logger.exception("Unexpected error executing action '%s'", action_name)
            return ActionResult(
                success=False,
                action=action_name,
                error=ActionError(
                    code=ActionErrorCode.INTERNAL_ERROR,
                    message="An unexpected error occurred while executing the action.",
                    suggestion="Please retry the action or check server logs if the problem persists.",
                ),
            )
