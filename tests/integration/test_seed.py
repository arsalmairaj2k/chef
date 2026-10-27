from sqlalchemy.orm import Session

from app.models.recipe import Recipe
from app.models.ingredient import Ingredient
from app.models.recipe_ingredient import RecipeIngredient
from app.models.recipe_step import RecipeStep
from scripts.seed_recipes import seed_database, SAMPLE_RECIPES


def test_seed_script_is_idempotent(db_session: Session):
    """Requirement 8: The seed script can run more than once without duplicating data."""
    # First execution
    result1 = seed_database(db_session)
    assert result1["recipes_processed"] == len(SAMPLE_RECIPES)
    assert result1["new_recipes_added"] == len(SAMPLE_RECIPES)
    assert result1["new_ingredients_added"] > 0

    initial_recipe_count = db_session.query(Recipe).count()
    initial_ingredient_count = db_session.query(Ingredient).count()
    initial_assoc_count = db_session.query(RecipeIngredient).count()
    initial_step_count = db_session.query(RecipeStep).count()

    assert initial_recipe_count == 2
    assert initial_ingredient_count > 0
    assert initial_step_count > 0

    # Second execution (must not create duplicates)
    result2 = seed_database(db_session)
    assert result2["recipes_processed"] == len(SAMPLE_RECIPES)
    assert result2["new_recipes_added"] == 0
    assert result2["new_ingredients_added"] == 0

    final_recipe_count = db_session.query(Recipe).count()
    final_ingredient_count = db_session.query(Ingredient).count()
    final_assoc_count = db_session.query(RecipeIngredient).count()
    final_step_count = db_session.query(RecipeStep).count()

    assert final_recipe_count == initial_recipe_count
    assert final_ingredient_count == initial_ingredient_count
    assert final_assoc_count == initial_assoc_count
    assert final_step_count == initial_step_count

    # Verify both recipes are present by slug with expected steps and ingredients
    chicken_karahi = db_session.query(Recipe).filter(Recipe.slug == "chicken-karahi").first()
    assert chicken_karahi is not None
    assert len(chicken_karahi.steps) == 7
    assert len(chicken_karahi.ingredients) == 12

    tarka_daal = db_session.query(Recipe).filter(Recipe.slug == "tarka-daal").first()
    assert tarka_daal is not None
    assert len(tarka_daal.steps) == 7
    assert len(tarka_daal.ingredients) == 10
