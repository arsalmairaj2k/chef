import re
from typing import Optional, Literal, Union
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


SLUG_REGEX = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class GetCurrentStateArgs(BaseModel):
    """Arguments for retrieving full cooking session state."""
    session_id: int = Field(..., gt=0, description="Unique primary key of the cooking session (must be > 0)")

    model_config = ConfigDict(extra="forbid", strict=True)


class GetCurrentStepArgs(BaseModel):
    """Arguments for retrieving the current active step without state change."""
    session_id: int = Field(..., gt=0, description="Unique primary key of the cooking session (must be > 0)")

    model_config = ConfigDict(extra="forbid", strict=True)


class CompleteStepArgs(BaseModel):
    """Arguments for marking the active step completed and advancing state."""
    session_id: int = Field(..., gt=0, description="Unique primary key of the cooking session (must be > 0)")
    step_number: int = Field(..., gt=0, description="Recipe step number to complete (1-indexed, positive integer)")

    model_config = ConfigDict(extra="forbid", strict=True)


class SkipStepArgs(BaseModel):
    """Arguments for marking the active step skipped and advancing state."""
    session_id: int = Field(..., gt=0, description="Unique primary key of the cooking session (must be > 0)")
    step_number: int = Field(..., gt=0, description="Recipe step number to skip (1-indexed, positive integer)")

    model_config = ConfigDict(extra="forbid", strict=True)


class GetRecipeArgs(BaseModel):
    """Arguments for retrieving full recipe details. Exactly one of recipe_id or slug is required."""
    recipe_id: Optional[int] = Field(None, gt=0, description="Primary key ID of the recipe (must be > 0)")
    slug: Optional[str] = Field(None, description="Unique URL-friendly slug of the recipe (e.g. 'chicken-karahi')")

    model_config = ConfigDict(extra="forbid", strict=True)

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            stripped = v.strip().lower()
            if not stripped:
                raise ValueError("Recipe slug cannot be empty or whitespace only.")
            if not SLUG_REGEX.match(stripped):
                raise ValueError(
                    "Invalid slug format. Use lowercase alphanumeric characters and single hyphens (e.g. 'chicken-karahi')."
                )
            return stripped
        return None

    @model_validator(mode="after")
    def validate_exclusive_identifiers(self) -> "GetRecipeArgs":
        has_id = self.recipe_id is not None
        has_slug = self.slug is not None

        if has_id and has_slug:
            raise ValueError("Provide either 'recipe_id' or 'slug', but not both.")
        if not has_id and not has_slug:
            raise ValueError("Must provide either 'recipe_id' or 'slug'.")
        return self


# --- Typed Action Envelopes (Discriminated Union) ---

class GetCurrentStateAction(BaseModel):
    action: Literal["get_current_state"] = "get_current_state"
    arguments: GetCurrentStateArgs
    model_config = ConfigDict(extra="forbid")


class GetCurrentStepAction(BaseModel):
    action: Literal["get_current_step"] = "get_current_step"
    arguments: GetCurrentStepArgs
    model_config = ConfigDict(extra="forbid")


class CompleteStepAction(BaseModel):
    action: Literal["complete_step"] = "complete_step"
    arguments: CompleteStepArgs
    model_config = ConfigDict(extra="forbid")


class SkipStepAction(BaseModel):
    action: Literal["skip_step"] = "skip_step"
    arguments: SkipStepArgs
    model_config = ConfigDict(extra="forbid")


class GetRecipeAction(BaseModel):
    action: Literal["get_recipe"] = "get_recipe"
    arguments: GetRecipeArgs
    model_config = ConfigDict(extra="forbid")


CookingAction = Union[
    GetCurrentStateAction,
    GetCurrentStepAction,
    CompleteStepAction,
    SkipStepAction,
    GetRecipeAction,
]
