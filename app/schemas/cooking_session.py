from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.recipe import RecipeIngredientRead


class SessionCreate(BaseModel):
    recipe_id: int = Field(..., description="ID of the recipe to cook")
    servings: Optional[int] = Field(None, gt=0, description="Optional custom serving count (positive integer)")


class SessionStepActionRequest(BaseModel):
    step_number: int = Field(..., gt=0, description="Recipe step number to complete or skip")


class CurrentStepInfo(BaseModel):
    step_number: int
    instruction: str
    estimated_duration_seconds: Optional[int] = None
    status: str
    model_config = ConfigDict(from_attributes=True)


class CurrentStepResponse(BaseModel):
    session_id: int
    session_status: str
    recipe_id: int
    recipe_name: str
    current_step: Optional[CurrentStepInfo] = None
    model_config = ConfigDict(from_attributes=True)


class CookingSessionStepRead(BaseModel):
    id: int
    session_id: int
    recipe_step_id: int
    step_number: int
    instruction: str
    estimated_duration_seconds: Optional[int] = None
    status: str
    completed_at: Optional[datetime] = None
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CookingSessionRead(BaseModel):
    id: int
    recipe_id: int
    recipe_name: str
    status: str
    current_step_number: Optional[int] = None
    servings: int
    version: int
    started_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    current_step: Optional[CurrentStepInfo] = None
    steps: List[CookingSessionStepRead] = Field(default_factory=list)
    ingredients: List[RecipeIngredientRead] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)

