from decimal import Decimal
import pytest
from pydantic import ValidationError

from app.schemas.recipe import (
    RecipeCreate,
    RecipeIngredientCreate,
    RecipeStepCreate,
    IngredientCreate,
)


def test_valid_recipe_create_schema():
    """Valid recipe creation schema passes validation."""
    data = {
        "name": "Chicken Karahi",
        "slug": "chicken-karahi",
        "description": "Authentic Pakistani dish",
        "cuisine": "Pakistani",
        "default_servings": 4,
        "prep_time_minutes": 15,
        "cook_time_minutes": 30,
        "ingredients": [
            {
                "name": "Chicken",
                "quantity": Decimal("1000"),
                "unit": "g",
                "notes": "bone-in",
                "is_optional": False,
            }
        ],
        "steps": [
            {
                "step_number": 1,
                "instruction": "Fry chicken in hot oil.",
                "estimated_duration_seconds": 300,
            },
            {
                "step_number": 2,
                "instruction": "Add ginger garlic paste.",
                "estimated_duration_seconds": 120,
            },
        ],
    }
    recipe_in = RecipeCreate(**data)
    assert recipe_in.name == "Chicken Karahi"
    assert recipe_in.slug == "chicken-karahi"
    assert len(recipe_in.ingredients) == 1
    assert len(recipe_in.steps) == 2


def test_invalid_servings_fails_validation():
    """Requirement 6: Invalid serving counts fail validation."""
    with pytest.raises(ValidationError) as exc:
        RecipeCreate(name="Daal", slug="daal", default_servings=0)
    assert "default_servings" in str(exc.value)

    with pytest.raises(ValidationError) as exc:
        RecipeCreate(name="Daal", slug="daal", default_servings=-2)
    assert "default_servings" in str(exc.value)


def test_invalid_quantities_fail_validation():
    """Requirement 6: Invalid quantities fail validation."""
    with pytest.raises(ValidationError) as exc:
        RecipeIngredientCreate(name="Salt", quantity=Decimal("-1.5"))
    assert "quantity" in str(exc.value)


def test_empty_recipe_name_fails_validation():
    """Empty or whitespace-only recipe name fails validation."""
    with pytest.raises(ValidationError):
        RecipeCreate(name="", slug="valid-slug")

    with pytest.raises(ValidationError):
        RecipeCreate(name="   ", slug="valid-slug")


def test_invalid_slug_fails_validation():
    """Invalid slug characters fail validation."""
    with pytest.raises(ValidationError):
        RecipeCreate(name="Recipe", slug="")

    with pytest.raises(ValidationError):
        RecipeCreate(name="Recipe", slug="Invalid Slug With Spaces")

    with pytest.raises(ValidationError):
        RecipeCreate(name="Recipe", slug="invalid_slug_with_underscores")


def test_negative_times_fail_validation():
    """Negative preparation and cooking times fail validation."""
    with pytest.raises(ValidationError):
        RecipeCreate(name="Recipe", slug="test-recipe", prep_time_minutes=-5)

    with pytest.raises(ValidationError):
        RecipeCreate(name="Recipe", slug="test-recipe", cook_time_minutes=-10)


def test_invalid_step_numbers_and_instructions_fail_validation():
    """Step numbers must be > 0 and instruction cannot be empty."""
    with pytest.raises(ValidationError):
        RecipeStepCreate(step_number=0, instruction="Do something")

    with pytest.raises(ValidationError):
        RecipeStepCreate(step_number=1, instruction="")

    with pytest.raises(ValidationError):
        RecipeStepCreate(step_number=1, instruction="   ")


def test_duplicate_step_numbers_in_recipe_fails_validation():
    """Duplicate step numbers within submitted recipe fail validation."""
    with pytest.raises(ValidationError) as exc:
        RecipeCreate(
            name="Recipe",
            slug="test-slug",
            steps=[
                RecipeStepCreate(step_number=1, instruction="Step one"),
                RecipeStepCreate(step_number=1, instruction="Step one duplicate"),
            ],
        )
    assert "Duplicate step numbers" in str(exc.value)


def test_empty_ingredient_name_fails_validation():
    """Empty or whitespace ingredient name fails validation."""
    with pytest.raises(ValidationError):
        IngredientCreate(name="")

    with pytest.raises(ValidationError):
        RecipeIngredientCreate(name="   ")
