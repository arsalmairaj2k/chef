from starlette.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.recipe import Recipe
from app.models.recipe_step import RecipeStep


def seed_recipe(db: Session, slug: str = "karahi-session", step_count: int = 3) -> Recipe:
    recipe = Recipe(
        name="Chicken Karahi",
        slug=slug,
        cuisine="Pakistani",
        default_servings=4,
    )
    db.add(recipe)
    db.flush()

    for i in range(1, step_count + 1):
        step = RecipeStep(
            recipe_id=recipe.id,
            step_number=i,
            instruction=f"Step instruction {i}",
            estimated_duration_seconds=120 * i,
        )
        db.add(step)
    db.commit()
    return recipe


def test_api_start_session_valid(client: TestClient, db_session: Session):
    """Requirement 1, 4: POST /api/v1/sessions creates active session with initial step."""
    recipe = seed_recipe(db_session, "api-start-valid")

    response = client.post("/api/v1/sessions", json={"recipe_id": recipe.id})
    assert response.status_code == 201
    data = response.json()
    assert data["recipe_id"] == recipe.id
    assert data["recipe_name"] == "Chicken Karahi"
    assert data["status"] == "ACTIVE"
    assert data["current_step_number"] == 1
    assert data["servings"] == 4
    assert data["current_step"]["step_number"] == 1
    assert data["current_step"]["status"] == "IN_PROGRESS"
    assert len(data["steps"]) == 3


def test_api_start_session_custom_servings(client: TestClient, db_session: Session):
    """POST /api/v1/sessions with custom servings overrides default."""
    recipe = seed_recipe(db_session, "api-custom-servings")

    response = client.post("/api/v1/sessions", json={"recipe_id": recipe.id, "servings": 8})
    assert response.status_code == 201
    assert response.json()["servings"] == 8


def test_api_start_session_nonexistent_recipe(client: TestClient):
    """Requirement 2: Reject nonexistent recipe with HTTP 404."""
    response = client.post("/api/v1/sessions", json={"recipe_id": 99999})
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_api_start_session_recipe_no_steps(client: TestClient, db_session: Session):
    """Requirement 3: Reject recipe with no steps with HTTP 422."""
    recipe = Recipe(name="Empty Recipe", slug="empty-recipe", default_servings=4)
    db_session.add(recipe)
    db_session.commit()

    response = client.post("/api/v1/sessions", json={"recipe_id": recipe.id})
    assert response.status_code == 422
    assert "no cooking steps" in response.json()["detail"].lower()


def test_api_get_session_and_current_step_idempotent(client: TestClient, db_session: Session):
    """Requirement 10 & 11: Retrieving session and current step does NOT advance state."""
    recipe = seed_recipe(db_session, "api-read-idempotent")
    create_res = client.post("/api/v1/sessions", json={"recipe_id": recipe.id})
    session_id = create_res.json()["id"]

    # Read session
    res1 = client.get(f"/api/v1/sessions/{session_id}")
    assert res1.status_code == 200
    assert res1.json()["current_step_number"] == 1

    # Read current step multiple times
    res_step1 = client.get(f"/api/v1/sessions/{session_id}/current-step")
    res_step2 = client.get(f"/api/v1/sessions/{session_id}/current-step")
    assert res_step1.status_code == 200
    assert res_step2.status_code == 200
    assert res_step1.json() == res_step2.json()
    assert res_step1.json()["current_step"]["step_number"] == 1

    # Verify session is still at step 1
    res_check = client.get(f"/api/v1/sessions/{session_id}")
    assert res_check.json()["current_step_number"] == 1


def test_api_complete_step_lifecycle(client: TestClient, db_session: Session):
    """Requirements 5 & 6: Completing step advances to next, and final step completes session."""
    recipe = seed_recipe(db_session, "api-complete-cycle", step_count=2)
    session_id = client.post("/api/v1/sessions", json={"recipe_id": recipe.id}).json()["id"]

    # Complete step 1
    res_step1 = client.post(
        f"/api/v1/sessions/{session_id}/complete-step",
        json={"step_number": 1},
    )
    assert res_step1.status_code == 200
    data1 = res_step1.json()
    assert data1["current_step_number"] == 2
    assert data1["steps"][0]["status"] == "COMPLETED"
    assert data1["steps"][0]["completed_at"] is not None
    assert data1["steps"][1]["status"] == "IN_PROGRESS"

    # Complete final step 2 -> Session completes
    res_step2 = client.post(
        f"/api/v1/sessions/{session_id}/complete-step",
        json={"step_number": 2},
    )
    assert res_step2.status_code == 200
    data2 = res_step2.json()
    assert data2["status"] == "COMPLETED"
    assert data2["current_step_number"] is None
    assert data2["completed_at"] is not None
    assert data2["current_step"] is None

    # Current step inspection on completed session
    cur_step = client.get(f"/api/v1/sessions/{session_id}/current-step").json()
    assert cur_step["session_status"] == "COMPLETED"
    assert cur_step["current_step"] is None


def test_api_skip_step_lifecycle(client: TestClient, db_session: Session):
    """Requirements 7 & 8: Skipping step preserves SKIPPED status, final skip completes session."""
    recipe = seed_recipe(db_session, "api-skip-cycle", step_count=2)
    session_id = client.post("/api/v1/sessions", json={"recipe_id": recipe.id}).json()["id"]

    # Skip step 1
    res_skip1 = client.post(
        f"/api/v1/sessions/{session_id}/skip-step",
        json={"step_number": 1},
    )
    assert res_skip1.status_code == 200
    data1 = res_skip1.json()
    assert data1["current_step_number"] == 2
    assert data1["steps"][0]["status"] == "SKIPPED"
    assert data1["steps"][1]["status"] == "IN_PROGRESS"

    # Skip final step 2 -> Session completes
    res_skip2 = client.post(
        f"/api/v1/sessions/{session_id}/skip-step",
        json={"step_number": 2},
    )
    assert res_skip2.status_code == 200
    data2 = res_skip2.json()
    assert data2["status"] == "COMPLETED"
    assert data2["current_step_number"] is None
    assert data2["steps"][1]["status"] == "SKIPPED"


def test_api_reject_completing_non_current_step(client: TestClient, db_session: Session):
    """Requirement 12: Completing a non-current step returns HTTP 409 Conflict."""
    recipe = seed_recipe(db_session, "api-non-current", step_count=3)
    session_id = client.post("/api/v1/sessions", json={"recipe_id": recipe.id}).json()["id"]

    # Current is 1, attempt to complete 2
    res = client.post(
        f"/api/v1/sessions/{session_id}/complete-step",
        json={"step_number": 2},
    )
    assert res.status_code == 409
    assert "not the current active step" in res.json()["detail"].lower()

    # Step not in recipe
    res_bad = client.post(
        f"/api/v1/sessions/{session_id}/complete-step",
        json={"step_number": 99},
    )
    assert res_bad.status_code == 404


def test_api_cancel_session_and_reject_modifications(client: TestClient, db_session: Session):
    """Requirements 13, 14, 15: Cancelling session, rejecting modifications on cancelled/completed."""
    recipe = seed_recipe(db_session, "api-cancel-cycle", step_count=2)
    session_id = client.post("/api/v1/sessions", json={"recipe_id": recipe.id}).json()["id"]

    # Cancel session
    res_cancel = client.post(f"/api/v1/sessions/{session_id}/cancel")
    assert res_cancel.status_code == 200
    assert res_cancel.json()["status"] == "CANCELLED"

    # Attempt to complete step on cancelled session -> 409
    res_fail = client.post(
        f"/api/v1/sessions/{session_id}/complete-step",
        json={"step_number": 1},
    )
    assert res_fail.status_code == 409
    assert "cannot modify" in res_fail.json()["detail"].lower()


def test_api_unknown_session_404(client: TestClient):
    """Unknown session returns 404."""
    assert client.get("/api/v1/sessions/99999").status_code == 404
    assert client.get("/api/v1/sessions/99999/current-step").status_code == 404
    assert client.post("/api/v1/sessions/99999/complete-step", json={"step_number": 1}).status_code == 404
    assert client.post("/api/v1/sessions/99999/skip-step", json={"step_number": 1}).status_code == 404
    assert client.post("/api/v1/sessions/99999/cancel").status_code == 404
