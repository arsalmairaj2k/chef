import re
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


SLUG_REGEX = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


# --- Ingredient Schemas ---

class IngredientBase(BaseModel):
    name: str = Field(..., min_length=1, description="Canonical name of the ingredient")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Ingredient name cannot be empty or whitespace only")
        return stripped


class IngredientCreate(IngredientBase):
    pass


class IngredientRead(IngredientBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# --- Recipe Ingredient Schemas ---

class RecipeIngredientCreate(BaseModel):
    name: str = Field(..., min_length=1, description="Canonical name of the ingredient")
    quantity: Optional[Decimal] = Field(None, ge=0, description="Quantity of the ingredient")
    unit: Optional[str] = Field(None, description="Unit of measurement (e.g., g, ml, tsp, tbsp, piece)")
    notes: Optional[str] = Field(None, description="Optional preparation note")
    is_optional: bool = Field(False, description="Whether this ingredient is optional")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Ingredient name cannot be empty")
        return stripped

    @field_validator("unit", "notes")
    @classmethod
    def clean_strings(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            stripped = v.strip()
            return stripped if stripped else None
        return None


class RecipeIngredientRead(BaseModel):
    id: int
    recipe_id: int
    ingredient_id: int
    ingredient_name: Optional[str] = None
    quantity: Optional[Decimal] = None
    unit: Optional[str] = None
    notes: Optional[str] = None
    is_optional: bool = False

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_orm_model(cls, ri) -> "RecipeIngredientRead":
        return cls(
            id=ri.id,
            recipe_id=ri.recipe_id,
            ingredient_id=ri.ingredient_id,
            ingredient_name=ri.ingredient.name if ri.ingredient else None,
            quantity=ri.quantity,
            unit=ri.unit,
            notes=ri.notes,
            is_optional=ri.is_optional,
        )


# --- Recipe Step Schemas ---

class RecipeStepCreate(BaseModel):
    step_number: int = Field(..., gt=0, description="Step sequence number (1-indexed)")
    instruction: str = Field(..., min_length=1, description="Step instruction text")
    estimated_duration_seconds: Optional[int] = Field(None, gt=0, description="Duration in seconds if timed")

    @field_validator("instruction")
    @classmethod
    def validate_instruction(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Instruction cannot be empty or whitespace only")
        return stripped


class RecipeStepRead(BaseModel):
    id: int
    recipe_id: int
    step_number: int
    instruction: str
    estimated_duration_seconds: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Recipe Schemas ---

class RecipeBase(BaseModel):
    name: str = Field(..., min_length=1, description="Recipe name")
    slug: str = Field(..., min_length=1, description="URL-friendly slug")
    description: Optional[str] = None
    cuisine: Optional[str] = None
    default_servings: int = Field(4, gt=0, description="Default number of servings")
    prep_time_minutes: Optional[int] = Field(None, ge=0, description="Preparation time in minutes")
    cook_time_minutes: Optional[int] = Field(None, ge=0, description="Cooking time in minutes")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Recipe name cannot be empty")
        return stripped

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        stripped = v.strip().lower()
        if not stripped:
            raise ValueError("Recipe slug cannot be empty")
        if not SLUG_REGEX.match(stripped):
            raise ValueError(
                "Invalid slug format. Use lowercase alphanumeric characters and single hyphens (e.g. 'chicken-karahi')."
            )
        return stripped


class RecipeCreate(RecipeBase):
    ingredients: List[RecipeIngredientCreate] = Field(default_factory=list)
    steps: List[RecipeStepCreate] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_steps_uniqueness(self) -> "RecipeCreate":
        step_numbers = [step.step_number for step in self.steps]
        if len(step_numbers) != len(set(step_numbers)):
            duplicates = [num for num in step_numbers if step_numbers.count(num) > 1]
            raise ValueError(f"Duplicate step numbers detected within recipe: {sorted(set(duplicates))}")
        return self


class RecipeRead(RecipeBase):
    id: int
    created_at: datetime
    updated_at: datetime
    ingredients: List[RecipeIngredientRead] = Field(default_factory=list)
    steps: List[RecipeStepRead] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class RecipeSummaryRead(RecipeBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RecipeListResponse(BaseModel):
    items: List[RecipeSummaryRead]
    page: int
    page_size: int
    total: int

