from typing import Annotated, Any, Dict, Literal, Union
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.ai.tool_registry import ToolRegistry


class ExecuteActionDecision(BaseModel):
    """The model selects an allowlisted backend action to execute."""
    type: Literal["execute_action"] = "execute_action"
    action: str = Field(..., description="Name of the allowlisted action to execute")
    arguments: Dict[str, Any] = Field(
        default_factory=dict,
        description="Key-value arguments matching the action parameters schema",
    )

    model_config = ConfigDict(extra="forbid")

    @field_validator("action")
    @classmethod
    def validate_action_allowlist(cls, v: str) -> str:
        if not ToolRegistry.contains(v):
            supported = ", ".join(ToolRegistry.list_tools())
            raise ValueError(
                f"Action '{v}' is not recognized or not allowlisted. Supported actions: {supported}"
            )
        return v


class AnswerQuestionDecision(BaseModel):
    """The model answers a general culinary or informational question without mutating state."""
    type: Literal["answer_question"] = "answer_question"
    question: str = Field(..., description="The user's question being addressed")
    answer: str = Field(..., description="Helpful, practical, concise cooking explanation")

    model_config = ConfigDict(extra="forbid")


class ClarifyDecision(BaseModel):
    """The user's intent is ambiguous or requires clarification before proceeding."""
    type: Literal["clarify"] = "clarify"
    question: str = Field(
        ...,
        description="Clarification question prompt to resolve ambiguity safely",
    )

    model_config = ConfigDict(extra="forbid")


LLMDecision = Annotated[
    Union[ExecuteActionDecision, AnswerQuestionDecision, ClarifyDecision],
    Field(discriminator="type"),
]
