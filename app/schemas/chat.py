from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.schemas.cooking_session import CookingSessionRead


class ChatMessageRequest(BaseModel):
    """Inbound cooking message payload."""
    message: str = Field(..., min_length=1, max_length=1000, description="User's cooking statement or question")

    model_config = ConfigDict(extra="forbid")

    @field_validator("message")
    @classmethod
    def validate_message_not_empty(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Message cannot be empty or whitespace only.")
        return stripped


class ActionExecutionSummary(BaseModel):
    """Summary of any action executed in response to the user's message."""
    name: str = Field(..., description="Action name executed")
    status: str = Field(..., description="'success' or 'error'")
    error: Optional[str] = Field(None, description="Error message if the action failed")
    data: Optional[Any] = Field(None, description="Action result data if successful")

    model_config = ConfigDict(from_attributes=True)


class ChatMessageResponse(BaseModel):
    """Grounded response returned to the conversational client."""
    reply: str = Field(..., description="Grounded natural language response for the user")
    session: CookingSessionRead = Field(..., description="Authoritative cooking session state after processing")
    decision_type: str = Field(..., description="Type of decision made: 'execute_action', 'answer_question', 'clarify'")
    action: Optional[ActionExecutionSummary] = Field(None, description="Details of executed action if applicable")

    model_config = ConfigDict(from_attributes=True)


class ChatMessageRead(BaseModel):
    """Persisted conversation record."""
    id: int
    session_id: int
    role: str
    content: str
    decision_type: Optional[str] = None
    created_at: Any

    model_config = ConfigDict(from_attributes=True)

