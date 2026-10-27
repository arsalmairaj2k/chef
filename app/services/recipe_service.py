from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.recipe import Recipe
from app.models.recipe_ingredient import RecipeIngredient
from app.models.recipe_step import RecipeStep
from app.repositories.recipe_repository import RecipeRepository
from app.schemas.recipe import RecipeCreate, RecipeListResponse


class RecipeNotFoundError(Exception):
    """Raised when a recipe is not found by ID or slug."""
    pass


class DuplicateRecipeSlugError(Exception):
    """Raised when attempting to create a recipe with an existing slug."""
    pass


class RecipeService:
    @staticmethod
    def list_recipes(
        db: Session,
        page: int = 1,
        page_size: int = 10,
        search: Optional[str] = None,
        cuisine: Optional[str] = None,
    ) -> RecipeListResponse:
        """Retrieve paginated recipes with database-level search and cuisine filtering."""
        skip = (page - 1) * page_size
        items, total = RecipeRepository.list_recipes(
            db=db,
            skip=skip,
            limit=page_size,
            search=search,
            cuisine=cuisine,
        )
        return RecipeListResponse(
            items=items,
            page=page,
            page_size=page_size,
            total=total,
        )

    @staticmethod
    def get_recipe_by_id(db: Session, recipe_id: int) -> Recipe:
        """Retrieve a single recipe by its primary key ID."""
        recipe = RecipeRepository.get_by_id(db, recipe_id)
        if not recipe:
            raise RecipeNotFoundError(f"Recipe with ID {recipe_id} not found.")
        return recipe

    @staticmethod
    def get_recipe_by_slug(db: Session, slug: str) -> Recipe:
        """Retrieve a single recipe by its unique slug."""
        recipe = RecipeRepository.get_by_slug(db, slug)
        if not recipe:
            raise RecipeNotFoundError(f"Recipe with slug '{slug}' not found.")
        return recipe

    @staticmethod
    def get_recipe_steps(db: Session, recipe_id: int) -> List[RecipeStep]:
        """Retrieve ordered steps for a recipe."""
        steps = RecipeRepository.get_steps_by_recipe_id(db, recipe_id)
        if steps is None:
            raise RecipeNotFoundError(f"Recipe with ID {recipe_id} not found.")
        return steps

    @staticmethod
    def create_recipe(db: Session, recipe_in: RecipeCreate) -> Recipe:
        """Create a recipe with ingredients and steps in a single atomic transaction."""
        # 1. Check for existing slug to prevent duplicates
        existing = RecipeRepository.get_by_slug(db, recipe_in.slug)
        if existing:
            raise DuplicateRecipeSlugError(
                f"Recipe with slug '{recipe_in.slug}' already exists."
            )

        try:
            # 2. Instantiate Recipe entity
            recipe = Recipe(
                name=recipe_in.name,
                slug=recipe_in.slug,
                description=recipe_in.description,
                cuisine=recipe_in.cuisine,
                default_servings=recipe_in.default_servings,
                prep_time_minutes=recipe_in.prep_time_minutes,
                cook_time_minutes=recipe_in.cook_time_minutes,
            )
            db.add(recipe)
            db.flush()

            # 3. Associate Ingredients
            for ing_in in recipe_in.ingredients:
                ingredient = RecipeRepository.get_or_create_ingredient(db, ing_in.name)
                assoc = RecipeIngredient(
                    recipe_id=recipe.id,
                    ingredient_id=ingredient.id,
                    quantity=ing_in.quantity,
                    unit=ing_in.unit,
                    notes=ing_in.notes,
                    is_optional=ing_in.is_optional,
                )
                db.add(assoc)

            # 4. Associate Steps
            for step_in in recipe_in.steps:
                step = RecipeStep(
                    recipe_id=recipe.id,
                    step_number=step_in.step_number,
                    instruction=step_in.instruction,
                    estimated_duration_seconds=step_in.estimated_duration_seconds,
                )
                db.add(step)

            db.commit()
            return RecipeRepository.get_by_id(db, recipe.id)  # return fully loaded ORM entity

        except IntegrityError as e:
            db.rollback()
            # If slug uniqueness was violated concurrently
            if "slug" in str(e).lower() or "unique constraint" in str(e).lower():
                raise DuplicateRecipeSlugError(f"Recipe with slug '{recipe_in.slug}' already exists.") from e
            raise
        except Exception:
            db.rollback()
            raise
