from typing import Optional, List, Tuple
from sqlalchemy import select, func
from sqlalchemy.orm import Session, selectinload

from app.models.recipe import Recipe
from app.models.ingredient import Ingredient
from app.models.recipe_ingredient import RecipeIngredient
from app.models.recipe_step import RecipeStep


class RecipeRepository:
    @staticmethod
    def get_by_id(db: Session, recipe_id: int) -> Optional[Recipe]:
        """Fetch a single recipe by primary key ID with eager loaded associations."""
        stmt = (
            select(Recipe)
            .options(
                selectinload(Recipe.ingredients).selectinload(RecipeIngredient.ingredient),
                selectinload(Recipe.steps),
            )
            .where(Recipe.id == recipe_id)
        )
        return db.scalar(stmt)

    @staticmethod
    def get_by_slug(db: Session, slug: str) -> Optional[Recipe]:
        """Fetch a single recipe by unique slug with eager loaded associations."""
        stmt = (
            select(Recipe)
            .options(
                selectinload(Recipe.ingredients).selectinload(RecipeIngredient.ingredient),
                selectinload(Recipe.steps),
            )
            .where(Recipe.slug == slug)
        )
        return db.scalar(stmt)

    @staticmethod
    def list_recipes(
        db: Session,
        skip: int = 0,
        limit: int = 10,
        search: Optional[str] = None,
        cuisine: Optional[str] = None,
    ) -> Tuple[List[Recipe], int]:
        """List recipes with database-level filtering, pagination, and stable ordering."""
        query = select(Recipe)
        count_query = select(func.count()).select_from(Recipe)

        if search:
            search_pattern = f"%{search.strip()}%"
            query = query.where(Recipe.name.ilike(search_pattern))
            count_query = count_query.where(Recipe.name.ilike(search_pattern))

        if cuisine:
            cuisine_pattern = cuisine.strip()
            query = query.where(Recipe.cuisine.ilike(cuisine_pattern))
            count_query = count_query.where(Recipe.cuisine.ilike(cuisine_pattern))

        total = db.scalar(count_query) or 0

        # Stable ordering: recipe name followed by ID
        query = query.order_by(Recipe.name.asc(), Recipe.id.asc()).offset(skip).limit(limit)
        items = list(db.scalars(query).all())

        return items, total

    @staticmethod
    def get_steps_by_recipe_id(db: Session, recipe_id: int) -> Optional[List[RecipeStep]]:
        """Fetch steps for a recipe sorted by step_number ascending."""
        # Verify recipe existence first
        exists_stmt = select(func.count()).select_from(Recipe).where(Recipe.id == recipe_id)
        if (db.scalar(exists_stmt) or 0) == 0:
            return None

        stmt = (
            select(RecipeStep)
            .where(RecipeStep.recipe_id == recipe_id)
            .order_by(RecipeStep.step_number.asc())
        )
        return list(db.scalars(stmt).all())

    @staticmethod
    def get_or_create_ingredient(db: Session, name: str) -> Ingredient:
        """Find existing ingredient canonical by name or create a new one."""
        canonical_name = name.strip()
        stmt = select(Ingredient).where(Ingredient.name == canonical_name)
        ingredient = db.scalar(stmt)
        if not ingredient:
            ingredient = Ingredient(name=canonical_name)
            db.add(ingredient)
            db.flush()
        return ingredient
