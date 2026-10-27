import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def seeded_recipe_id(client: TestClient) -> int:
    """Create a recipe via API for testing actions."""
    payload = {
        "name": "Aloo Gosht",
        "slug": "aloo-gosht",
        "description": "Traditional Pakistani mutton and potato curry.",
        "cuisine": "Pakistani",
        "default_servings": 4,
        "prep_time_minutes": 20,
        "cook_time_minutes": 45,
        "ingredients": [
            {"name": "Mutton", "quantity": 500, "unit": "g"},
            {"name": "Potatoes", "quantity": 3, "unit": "medium"},
        ],
        "steps": [
            {"step_number": 1, "instruction": "Sear mutton with onions and spices.", "estimated_duration_seconds": 600},
            {"step_number": 2, "instruction": "Add potatoes and water, simmer until tender.", "estimated_duration_seconds": 1800},
            {"step_number": 3, "instruction": "Garnish with fresh coriander and serve.", "estimated_duration_seconds": 120},
        ],
    }
    resp = client.post("/api/v1/recipes", json=payload)
    assert resp.status_code == 201
    return resp.json()["id"]


@pytest.fixture
def seeded_session_id(client: TestClient, seeded_recipe_id: int) -> int:
    """Create an active session via API."""
    resp = client.post("/api/v1/sessions", json={"recipe_id": seeded_recipe_id, "servings": 4})
    assert resp.status_code == 201
    return resp.json()["id"]


def test_api_get_tool_definitions(client: TestClient):
    """Verify tool discovery endpoint exposes all 5 tool definitions."""
    resp = client.get("/api/v1/sessions/actions/tools")
    assert resp.status_code == 200
    tools = resp.json()
    assert isinstance(tools, list)
    assert len(tools) == 5

    names = [t["name"] for t in tools]
    assert "get_current_state" in names
    assert "get_current_step" in names
    assert "complete_step" in names
    assert "skip_step" in names
    assert "get_recipe" in names


def test_api_action_get_current_state_infers_path_session_id(client: TestClient, seeded_session_id: int):
    """Verify session_id is automatically inferred from path when omitted from arguments."""
    resp = client.post(
        f"/api/v1/sessions/{seeded_session_id}/actions",
        json={"action": "get_current_state", "arguments": {}},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["action"] == "get_current_state"
    assert data["error"] is None
    assert data["data"]["id"] == seeded_session_id
    assert data["data"]["status"] == "ACTIVE"
    assert data["data"]["current_step_number"] == 1


def test_api_action_get_current_step_infers_path_session_id(client: TestClient, seeded_session_id: int):
    """Verify get_current_step succeeds and returns step 1 without state mutation."""
    resp = client.post(
        f"/api/v1/sessions/{seeded_session_id}/actions",
        json={"action": "get_current_step", "arguments": {}},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["data"]["current_step"]["step_number"] == 1
    assert data["data"]["session_status"] == "ACTIVE"


def test_api_action_complete_step_advances_state(client: TestClient, seeded_session_id: int):
    """Verify complete_step transitions step 1 to completed and advances to step 2."""
    resp = client.post(
        f"/api/v1/sessions/{seeded_session_id}/actions",
        json={"action": "complete_step", "arguments": {"step_number": 1}},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["data"]["current_step_number"] == 2

    # Verify step statuses in returned session data
    step1 = next(s for s in data["data"]["steps"] if s["step_number"] == 1)
    step2 = next(s for s in data["data"]["steps"] if s["step_number"] == 2)
    assert step1["status"] == "COMPLETED"
    assert step2["status"] == "IN_PROGRESS"


def test_api_action_skip_step_advances_state(client: TestClient, seeded_session_id: int):
    """Verify skip_step transitions active step to skipped and advances to next."""
    # First advance to step 2
    client.post(
        f"/api/v1/sessions/{seeded_session_id}/actions",
        json={"action": "complete_step", "arguments": {"step_number": 1}},
    )

    # Now skip step 2
    resp = client.post(
        f"/api/v1/sessions/{seeded_session_id}/actions",
        json={"action": "skip_step", "arguments": {"step_number": 2}},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["data"]["current_step_number"] == 3

    step2 = next(s for s in data["data"]["steps"] if s["step_number"] == 2)
    step3 = next(s for s in data["data"]["steps"] if s["step_number"] == 3)
    assert step2["status"] == "SKIPPED"
    assert step3["status"] == "IN_PROGRESS"


def test_api_action_get_recipe(client: TestClient, seeded_session_id: int, seeded_recipe_id: int):
    """Verify get_recipe executes properly via actions endpoint using ID or slug."""
    # By ID
    resp_id = client.post(
        f"/api/v1/sessions/{seeded_session_id}/actions",
        json={"action": "get_recipe", "arguments": {"recipe_id": seeded_recipe_id}},
    )
    assert resp_id.status_code == 200
    data_id = resp_id.json()
    assert data_id["success"] is True
    assert data_id["data"]["name"] == "Aloo Gosht"

    # By slug
    resp_slug = client.post(
        f"/api/v1/sessions/{seeded_session_id}/actions",
        json={"action": "get_recipe", "arguments": {"slug": "aloo-gosht"}},
    )
    assert resp_slug.status_code == 200
    data_slug = resp_slug.json()
    assert data_slug["success"] is True
    assert data_slug["data"]["slug"] == "aloo-gosht"


def test_api_action_rejects_conflicting_session_id(client: TestClient, seeded_session_id: int):
    """Verify that if arguments contains a conflicting session_id, it is rejected."""
    conflicting_id = seeded_session_id + 999
    resp = client.post(
        f"/api/v1/sessions/{seeded_session_id}/actions",
        json={"action": "complete_step", "arguments": {"session_id": conflicting_id, "step_number": 1}},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is False
    assert data["error"]["code"] == "INVALID_ARGUMENTS"
    assert f"Conflicting session_id" in data["error"]["message"]


def test_api_action_matching_session_id_succeeds(client: TestClient, seeded_session_id: int):
    """Verify that explicitly providing the matching session_id in arguments succeeds."""
    resp = client.post(
        f"/api/v1/sessions/{seeded_session_id}/actions",
        json={"action": "get_current_step", "arguments": {"session_id": seeded_session_id}},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["data"]["session_id"] == seeded_session_id


def test_api_action_unknown_action(client: TestClient, seeded_session_id: int):
    """Verify unknown action returns structured error with INVALID_ACTION."""
    resp = client.post(
        f"/api/v1/sessions/{seeded_session_id}/actions",
        json={"action": "modify_temperature", "arguments": {"temp": 200}},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is False
    assert data["error"]["code"] == "INVALID_ACTION"
    assert "not recognized or not allowed" in data["error"]["message"]


def test_api_action_step_conflict(client: TestClient, seeded_session_id: int):
    """Verify completing non-current step returns STEP_CONFLICT."""
    resp = client.post(
        f"/api/v1/sessions/{seeded_session_id}/actions",
        json={"action": "complete_step", "arguments": {"step_number": 3}},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is False
    assert data["error"]["code"] == "STEP_CONFLICT"
    assert "not the current active step" in data["error"]["message"]


def test_api_action_nonexistent_session(client: TestClient):
    """Verify action on nonexistent session returns SESSION_NOT_FOUND."""
    resp = client.post(
        "/api/v1/sessions/99999/actions",
        json={"action": "get_current_state", "arguments": {}},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is False
    assert data["error"]["code"] == "SESSION_NOT_FOUND"


def test_api_action_unexpected_payload_fields_rejected(client: TestClient, seeded_session_id: int):
    """Verify extra payload fields in the outer request are rejected with 422."""
    resp = client.post(
        f"/api/v1/sessions/{seeded_session_id}/actions",
        json={"action": "get_current_state", "arguments": {}, "unsupported_field": True},
    )
    assert resp.status_code == 422
