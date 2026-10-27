from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, Field


class ActionErrorCode(str, Enum):
    INVALID_ACTION = "INVALID_ACTION"
    INVALID_ARGUMENTS = "INVALID_ARGUMENTS"
    SESSION_NOT_FOUND = "SESSION_NOT_FOUND"
    RECIPE_NOT_FOUND = "RECIPE_NOT_FOUND"
    STEP_CONFLICT = "STEP_CONFLICT"
    SESSION_NOT_ACTIVE = "SESSION_NOT_ACTIVE"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class ActionError(BaseModel):
    """Structured error object designed for safe model consumption."""
    code: ActionErrorCode = Field(..., description="Machine-readable error category code")
    message: str = Field(..., description="Safe human-readable explanation of why the action failed")
    suggestion: Optional[str] = Field(
        None,
        description="Actionable suggestion or clarification prompt suitable for model or user response",
    )

    model_config = ConfigDict(from_attributes=True)


class ActionResult(BaseModel):
    """Predictable result envelope for all action invocations."""
    success: bool = Field(..., description="Whether the action completed successfully")
    action: Optional[str] = Field(None, description="The action name executed or attempted")
    data: Optional[Any] = Field(None, description="Structured payload returned on success")
    error: Optional[ActionError] = Field(None, description="Structured error payload on failure")

    model_config = ConfigDict(from_attributes=True)
