from decimal import Decimal
import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.recipe import Recipe
from app.models.ingredient import Ingredient
from app.models.recipe_ingredient import RecipeIngredient
from app.models.recipe_step import RecipeStep


def test_create_and_persist_models(db_session: Session):
    """Requirement 1: Each model can be created and persisted."""
    recipe = Recipe(
        name="Chicken Karahi",
        slug="chicken-karahi",
        description="Spicy Pakistani chicken karahi",
        cuisine="Pakistani",
        default_servings=4,
        prep_time_minutes=15,
        cook_time_minutes=30,
    )
    db_session.add(recipe)
    db_session.flush()

    assert recipe.id is not None

    ingredient = Ingredient(name="Chicken")
    db_session.add(ingredient)
    db_session.flush()

    assert ingredient.id is not None

    assoc = RecipeIngredient(
        recipe_id=recipe.id,
        ingredient_id=ingredient.id,
        quantity=Decimal("1000.00"),
        unit="g",
        notes="bone-in",
        is_optional=False,
    )
    db_session.add(assoc)
    db_session.flush()

    assert assoc.id is not None

    step = RecipeStep(
        recipe_id=recipe.id,
        step_number=1,
        instruction="Heat oil in a wok and fry chicken.",
        estimated_duration_seconds=300,
    )
    db_session.add(step)
    db_session.flush()

    assert step.id is not None


def test_recipe_relationships(db_session: Session):
    """Requirement 2: Recipe-to-ingredient and recipe-to-step relationships work."""
    recipe = Recipe(name="Biryani", slug="biryani", default_servings=6)
    db_session.add(recipe)
    db_session.flush()

    rice = Ingredient(name="Basmati Rice")
    db_session.add(rice)
    db_session.flush()

    assoc = RecipeIngredient(
        recipe_id=recipe.id,
        ingredient_id=rice.id,
        quantity=Decimal("500.00"),
        unit="g",
    )
    step1 = RecipeStep(recipe_id=recipe.id, step_number=1, instruction="Wash rice.")
    step2 = RecipeStep(recipe_id=recipe.id, step_number=2, instruction="Boil rice.")

    db_session.add_all([assoc, step1, step2])
    db_session.flush()

    # Verify relationships from recipe side
    assert len(recipe.ingredients) == 1
    assert recipe.ingredients[0].ingredient.name == "Basmati Rice"
    assert len(recipe.steps) == 2

    # Verify back-populates from ingredient side
    assert len(rice.recipe_associations) == 1
    assert rice.recipe_associations[0].recipe.name == "Biryani"


def test_duplicate_recipe_slug_rejected(db_session: Session):
    """Requirement 3: Duplicate recipe slugs are rejected."""
    r1 = Recipe(name="Daal Chawal", slug="daal-chawal", default_servings=2)
    db_session.add(r1)
    db_session.flush()

    r2 = Recipe(name="Another Daal Chawal", slug="daal-chawal", default_servings=4)
    db_session.add(r2)
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_duplicate_step_numbers_rejected(db_session: Session):
    """Requirement 4: Duplicate step numbers within a recipe are rejected."""
    recipe = Recipe(name="Nihari", slug="nihari", default_servings=4)
    db_session.add(recipe)
    db_session.flush()

    step1 = RecipeStep(recipe_id=recipe.id, step_number=1, instruction="Step one.")
    step1_dup = RecipeStep(recipe_id=recipe.id, step_number=1, instruction="Conflicting step one.")
    db_session.add(step1)
    db_session.add(step1_dup)

    with pytest.raises(IntegrityError):
        db_session.flush()


def test_duplicate_recipe_ingredient_rejected(db_session: Session):
    """Requirement 5: Duplicate recipe-ingredient associations are rejected."""
    recipe = Recipe(name="Haleem", slug="haleem", default_servings=6)
    wheat = Ingredient(name="Cracked Wheat")
    db_session.add_all([recipe, wheat])
    db_session.flush()

    assoc1 = RecipeIngredient(recipe_id=recipe.id, ingredient_id=wheat.id, quantity=Decimal("200"))
    assoc2 = RecipeIngredient(recipe_id=recipe.id, ingredient_id=wheat.id, quantity=Decimal("100"))
    db_session.add(assoc1)
    db_session.add(assoc2)

    with pytest.raises(IntegrityError):
        db_session.flush()


def test_recipe_steps_order(db_session: Session):
    """Requirement 7: Recipe steps are returned in the correct order."""
    recipe = Recipe(name="Seekh Kabab", slug="seekh-kabab", default_servings=4)
    db_session.add(recipe)
    db_session.flush()

    # Add steps out of order
    step3 = RecipeStep(recipe_id=recipe.id, step_number=3, instruction="Grill skewers.")
    step1 = RecipeStep(recipe_id=recipe.id, step_number=1, instruction="Mince meat with spices.")
    step2 = RecipeStep(recipe_id=recipe.id, step_number=2, instruction="Shape onto skewers.")

    db_session.add_all([step3, step1, step2])
    db_session.flush()

    # Query recipe and verify steps order
    ordered_numbers = [s.step_number for s in recipe.steps]
    assert ordered_numbers == [1, 2, 3]


def test_database_check_constraints(db_session: Session):
    """Database check constraints for non-negative and positive fields."""
    # Negative default_servings should fail
    r_bad_servings = Recipe(name="Bad", slug="bad-servings", default_servings=0)
    db_session.add(r_bad_servings)
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()

    # Negative prep_time should fail
    r_bad_prep = Recipe(name="Bad", slug="bad-prep", default_servings=2, prep_time_minutes=-5)
    db_session.add(r_bad_prep)
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()

    # Step number <= 0 should fail
    recipe = Recipe(name="Good", slug="good-recipe", default_servings=2)
    db_session.add(recipe)
    db_session.flush()

    bad_step = RecipeStep(recipe_id=recipe.id, step_number=0, instruction="Zero step")
    db_session.add(bad_step)
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()
