from decimal import Decimal
from starlette.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.recipe import Recipe
from app.models.ingredient import Ingredient
from app.models.recipe_ingredient import RecipeIngredient
from app.models.recipe_step import RecipeStep


def test_recipe_list_empty(client: TestClient):
    """Requirement 2: Recipe list returns an empty collection when no recipes exist."""
    response = client.get("/api/v1/recipes")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0
    assert data["page"] == 1
    assert data["page_size"] == 10


def test_recipe_pagination(client: TestClient, db_session: Session):
    """Requirement 3: Pagination returns the correct page and total."""
    for i in range(1, 6):
        r = Recipe(name=f"Recipe {i}", slug=f"recipe-{i}", default_servings=4)
        db_session.add(r)
    db_session.commit()

    # Request page 2 with page_size 2
    response = client.get("/api/v1/recipes?page=2&page_size=2")
    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 2
    assert data["page_size"] == 2
    assert data["total"] == 5
    assert len(data["items"]) == 2


def test_recipe_search_case_insensitive(client: TestClient, db_session: Session):
    """Requirement 4: Search works without case sensitivity."""
    r1 = Recipe(name="Chicken Karahi", slug="chicken-karahi", default_servings=4)
    r2 = Recipe(name="Mutton Qorma", slug="mutton-qorma", default_servings=4)
    r3 = Recipe(name="Chicken Biryani", slug="chicken-biryani", default_servings=6)
    db_session.add_all([r1, r2, r3])
    db_session.commit()

    # Search lowercase "chicken"
    response = client.get("/api/v1/recipes?search=chicken")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    names = [item["name"] for item in data["items"]]
    assert "Chicken Karahi" in names
    assert "Chicken Biryani" in names
    assert "Mutton Qorma" not in names

    # Search uppercase "KARAHI"
    response2 = client.get("/api/v1/recipes?search=KARAHI")
    assert response2.status_code == 200
    data2 = response2.json()
    assert data2["total"] == 1
    assert data2["items"][0]["slug"] == "chicken-karahi"


def test_recipe_cuisine_filtering(client: TestClient, db_session: Session):
    """Requirement 5: Cuisine filtering works."""
    r1 = Recipe(name="Nihari", slug="nihari", cuisine="Pakistani", default_servings=4)
    r2 = Recipe(name="Pizza", slug="pizza", cuisine="Italian", default_servings=2)
    db_session.add_all([r1, r2])
    db_session.commit()

    response = client.get("/api/v1/recipes?cuisine=Pakistani")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "Nihari"


def test_recipe_detail_by_id(client: TestClient, db_session: Session):
    """Requirement 6: Recipe detail includes its ingredients and ordered steps."""
    recipe = Recipe(
        name="Tarka Daal",
        slug="tarka-daal",
        description="Lentils with tempering",
        cuisine="Pakistani",
        default_servings=4,
        prep_time_minutes=10,
        cook_time_minutes=20,
    )
    db_session.add(recipe)
    db_session.flush()

    daal = Ingredient(name="Daal Masoor")
    db_session.add(daal)
    db_session.flush()

    assoc = RecipeIngredient(
        recipe_id=recipe.id,
        ingredient_id=daal.id,
        quantity=Decimal("250.00"),
        unit="g",
        notes="washed",
        is_optional=False,
    )
    step1 = RecipeStep(recipe_id=recipe.id, step_number=1, instruction="Boil daal.", estimated_duration_seconds=600)
    step2 = RecipeStep(recipe_id=recipe.id, step_number=2, instruction="Prepare tarka.", estimated_duration_seconds=180)
    db_session.add_all([assoc, step1, step2])
    db_session.commit()

    response = client.get(f"/api/v1/recipes/{recipe.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Tarka Daal"
    assert data["slug"] == "tarka-daal"
    assert len(data["ingredients"]) == 1
    assert data["ingredients"][0]["ingredient_name"] == "Daal Masoor"
    assert float(data["ingredients"][0]["quantity"]) == 250.00
    assert len(data["steps"]) == 2
    assert data["steps"][0]["step_number"] == 1
    assert data["steps"][1]["step_number"] == 2


def test_recipe_retrieval_by_slug(client: TestClient, db_session: Session):
    """Requirement 7: Recipe retrieval by slug works."""
    recipe = Recipe(name="Chapli Kabab", slug="chapli-kabab", default_servings=4)
    db_session.add(recipe)
    db_session.commit()

    response = client.get("/api/v1/recipes/slug/chapli-kabab")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Chapli Kabab"
    assert data["slug"] == "chapli-kabab"


def test_unknown_id_and_slug_return_404(client: TestClient):
    """Requirement 8: Unknown IDs and slugs return HTTP 404."""
    # Unknown ID
    res1 = client.get("/api/v1/recipes/999999")
    assert res1.status_code == 404
    assert "not found" in res1.json()["detail"].lower()

    # Unknown slug
    res2 = client.get("/api/v1/recipes/slug/non-existent-slug")
    assert res2.status_code == 404
    assert "not found" in res2.json()["detail"].lower()

    # Unknown ID steps
    res3 = client.get("/api/v1/recipes/999999/steps")
    assert res3.status_code == 404
    assert "not found" in res3.json()["detail"].lower()


def test_valid_recipe_creation(client: TestClient, db_session: Session):
    """Requirement 9: Valid recipe creation returns HTTP 201."""
    payload = {
        "name": "Aloo Keema",
        "slug": "aloo-keema",
        "description": "Ground minced beef with potatoes",
        "cuisine": "Pakistani",
        "default_servings": 4,
        "prep_time_minutes": 15,
        "cook_time_minutes": 35,
        "ingredients": [
            {"name": "Minced Beef", "quantity": 500, "unit": "g", "notes": "lean", "is_optional": False},
            {"name": "Potatoes", "quantity": 2, "unit": "piece", "notes": "cubed", "is_optional": False},
        ],
        "steps": [
            {"step_number": 1, "instruction": "Brown onions and add spices.", "estimated_duration_seconds": 300},
            {"step_number": 2, "instruction": "Add mince and fry thoroughly.", "estimated_duration_seconds": 600},
            {"step_number": 3, "instruction": "Add potatoes and simmer until tender.", "estimated_duration_seconds": 900},
        ],
    }

    response = client.post("/api/v1/recipes", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Aloo Keema"
    assert data["slug"] == "aloo-keema"
    assert len(data["ingredients"]) == 2
    assert len(data["steps"]) == 3
    assert data["id"] is not None

    # Verify canonical ingredient reuse in db
    mince_count = db_session.query(Ingredient).filter(Ingredient.name == "Minced Beef").count()
    assert mince_count == 1


def test_invalid_recipe_input_returns_422(client: TestClient):
    """Requirement 10: Invalid recipe input returns HTTP 422."""
    # Empty name
    bad_name = {"name": "   ", "slug": "bad-name", "default_servings": 4}
    res1 = client.post("/api/v1/recipes", json=bad_name)
    assert res1.status_code == 422

    # Invalid slug format
    bad_slug = {"name": "Bad Slug", "slug": "Invalid Slug With Spaces!", "default_servings": 4}
    res2 = client.post("/api/v1/recipes", json=bad_slug)
    assert res2.status_code == 422

    # Zero servings
    bad_servings = {"name": "Bad Servings", "slug": "bad-servings", "default_servings": 0}
    res3 = client.post("/api/v1/recipes", json=bad_servings)
    assert res3.status_code == 422

    # Duplicate step numbers within payload
    duplicate_steps = {
        "name": "Dup Steps",
        "slug": "dup-steps",
        "steps": [
            {"step_number": 1, "instruction": "First"},
            {"step_number": 1, "instruction": "Duplicate first"},
        ],
    }
    res4 = client.post("/api/v1/recipes", json=duplicate_steps)
    assert res4.status_code == 422


def test_duplicate_slug_returns_409(client: TestClient, db_session: Session):
    """Requirement 11: Duplicate slugs return HTTP 409."""
    existing = Recipe(name="Existing Recipe", slug="existing-slug", default_servings=4)
    db_session.add(existing)
    db_session.commit()

    payload = {
        "name": "New Recipe with same slug",
        "slug": "existing-slug",
        "default_servings": 2,
    }
    response = client.post("/api/v1/recipes", json=payload)
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"].lower()


def test_failed_creation_rollback(client: TestClient, db_session: Session):
    """Requirement 12: Failed recipe creation does not leave partial recipe data."""
    initial_recipe_count = db_session.query(Recipe).count()
    initial_assoc_count = db_session.query(RecipeIngredient).count()

    # Pre-insert a recipe to cause 409 conflict
    r = Recipe(name="Existing Dish", slug="existing-dish", default_servings=4)
    db_session.add(r)
    db_session.commit()

    # Attempt to create with duplicate slug and some ingredients
    payload = {
        "name": "Conflict Dish",
        "slug": "existing-dish",
        "ingredients": [{"name": "Unique Never Seen Before Ingredient", "quantity": 100}],
    }
    response = client.post("/api/v1/recipes", json=payload)
    assert response.status_code == 409

    # Assert no new recipes or associations were added
    assert db_session.query(Recipe).count() == initial_recipe_count + 1  # only pre-inserted
    assert db_session.query(RecipeIngredient).count() == initial_assoc_count


def test_step_retrieval_ascending_order(client: TestClient, db_session: Session):
    """Requirement 13: Step retrieval returns steps in ascending order."""
    recipe = Recipe(name="Pulao", slug="pulao", default_servings=4)
    db_session.add(recipe)
    db_session.flush()

    # Add steps out of order
    s3 = RecipeStep(recipe_id=recipe.id, step_number=3, instruction="Dum par rakhain.")
    s1 = RecipeStep(recipe_id=recipe.id, step_number=1, instruction="Yakhni banayain.")
    s2 = RecipeStep(recipe_id=recipe.id, step_number=2, instruction="Chawal shamil karein.")
    db_session.add_all([s3, s1, s2])
    db_session.commit()

    response = client.get(f"/api/v1/recipes/{recipe.id}/steps")
    assert response.status_code == 200
    steps = response.json()
    assert len(steps) == 3
    assert [s["step_number"] for s in steps] == [1, 2, 3]
    assert steps[0]["instruction"] == "Yakhni banayain."
    assert steps[1]["instruction"] == "Chawal shamil karein."
    assert steps[2]["instruction"] == "Dum par rakhain."
