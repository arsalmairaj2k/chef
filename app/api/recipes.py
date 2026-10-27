from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.recipe import (
    RecipeCreate,
    RecipeRead,
    RecipeStepRead,
    RecipeListResponse,
)
from app.services.recipe_service import (
    RecipeService,
    RecipeNotFoundError,
    DuplicateRecipeSlugError,
)

router = APIRouter(prefix="/recipes", tags=["recipes"])


@router.get("", response_model=RecipeListResponse, status_code=status.HTTP_200_OK)
def list_recipes(
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page (1-100)"),
    search: Optional[str] = Query(None, description="Partial search query on recipe name"),
    cuisine: Optional[str] = Query(None, description="Filter recipes by cuisine"),
    db: Session = Depends(get_db),
) -> RecipeListResponse:
    """Retrieve a paginated list of recipes with optional search and cuisine filtering."""
    return RecipeService.list_recipes(
        db=db,
        page=page,
        page_size=page_size,
        search=search,
        cuisine=cuisine,
    )


@router.post("", response_model=RecipeRead, status_code=status.HTTP_201_CREATED)
def create_recipe(
    recipe_in: RecipeCreate,
    db: Session = Depends(get_db),
) -> RecipeRead:
    """Create a new recipe with canonical ingredients and ordered instructions."""
    try:
        recipe = RecipeService.create_recipe(db=db, recipe_in=recipe_in)
        return recipe
    except DuplicateRecipeSlugError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )


@router.get("/slug/{slug}", response_model=RecipeRead, status_code=status.HTTP_200_OK)
def get_recipe_by_slug(
    slug: str,
    db: Session = Depends(get_db),
) -> RecipeRead:
    """Retrieve recipe details including ingredients and steps by unique slug."""
    try:
        recipe = RecipeService.get_recipe_by_slug(db=db, slug=slug)
        return recipe
    except RecipeNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get("/{recipe_id}", response_model=RecipeRead, status_code=status.HTTP_200_OK)
def get_recipe_by_id(
    recipe_id: int,
    db: Session = Depends(get_db),
) -> RecipeRead:
    """Retrieve recipe details including ingredients and steps by recipe ID."""
    try:
        recipe = RecipeService.get_recipe_by_id(db=db, recipe_id=recipe_id)
        return recipe
    except RecipeNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get("/{recipe_id}/steps", response_model=List[RecipeStepRead], status_code=status.HTTP_200_OK)
def get_recipe_steps(
    recipe_id: int,
    db: Session = Depends(get_db),
) -> List[RecipeStepRead]:
    """Retrieve the ordered instructions for a recipe by recipe ID."""
    try:
        steps = RecipeService.get_recipe_steps(db=db, recipe_id=recipe_id)
        return steps
    except RecipeNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
