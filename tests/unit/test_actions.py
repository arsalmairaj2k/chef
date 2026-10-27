import json
import pytest
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.ai.action_results import ActionErrorCode, ActionResult
from app.ai.action_schemas import (
    GetCurrentStateArgs,
    GetCurrentStepArgs,
    CompleteStepArgs,
    SkipStepArgs,
    GetRecipeArgs,
)
from app.ai.tool_registry import ToolRegistry
from app.ai.action_executor import ActionExecutor
from app.services.session_service import SessionService
from app.services.recipe_service import RecipeService
from app.schemas.recipe import RecipeCreate, RecipeIngredientCreate, RecipeStepCreate
from app.models.cooking_session import CookingSession, SessionStatus
from app.models.cooking_session_step import StepStatus


@pytest.fixture
def sample_recipe(db_session: Session):
    """Seed a sample recipe with multiple steps for action testing."""
    recipe_in = RecipeCreate(
        name="Tarka Daal",
        slug="tarka-daal",
        description="Comforting yellow lentils tempered with cumin and garlic.",
        cuisine="Pakistani",
        default_servings=4,
        prep_time_minutes=15,
        cook_time_minutes=30,
        ingredients=[
            RecipeIngredientCreate(name="Yellow Lentils", quantity=250, unit="g"),
            RecipeIngredientCreate(name="Garlic", quantity=4, unit="cloves"),
        ],
        steps=[
            RecipeStepCreate(step_number=1, instruction="Wash and boil lentils until soft.", estimated_duration_seconds=1200),
            RecipeStepCreate(step_number=2, instruction="Prepare tarka with garlic and spices.", estimated_duration_seconds=300),
            RecipeStepCreate(step_number=3, instruction="Pour tarka over daal and serve.", estimated_duration_seconds=60),
        ],
    )
    return RecipeService.create_recipe(db=db_session, recipe_in=recipe_in)


@pytest.fixture
def active_session(db_session: Session, sample_recipe):
    """Create an active cooking session on step 1."""
    return SessionService.create_session(db=db_session, recipe_id=sample_recipe.id)


# --- 1. Tool Registry Allowlist and Schema Serialization Tests ---

def test_registry_contains_only_allowlisted_actions():
    """Verify registry strictly contains only the five allowlisted actions."""
    expected_tools = {
        "get_current_state",
        "get_current_step",
        "complete_step",
        "skip_step",
        "get_recipe",
    }
    registered = set(ToolRegistry.list_tools())
    assert registered == expected_tools, f"Registry contained unexpected tools: {registered ^ expected_tools}"


def test_exported_tool_schemas_are_json_serializable():
    """Verify all tool definitions and their parameter schemas serialize to standard JSON."""
    definitions = ToolRegistry.get_definitions()
    assert len(definitions) == 5

    serialized = json.dumps(definitions)
    assert serialized is not None
    loaded = json.loads(serialized)
    assert len(loaded) == 5

    for tool in loaded:
        assert "name" in tool
        assert "description" in tool
        assert "parameters" in tool
        params = tool["parameters"]
        assert params.get("type") == "object"
        assert "properties" in params


# --- 2. Action Schema Validation Tests ---

def test_get_current_state_args_validation():
    # Valid
    args = GetCurrentStateArgs(session_id=1)
    assert args.session_id == 1

    # Missing session_id
    with pytest.raises(ValidationError):
        GetCurrentStateArgs()

    # Invalid session_id <= 0
    with pytest.raises(ValidationError):
        GetCurrentStateArgs(session_id=0)
    with pytest.raises(ValidationError):
        GetCurrentStateArgs(session_id=-5)

    # Unexpected extra fields
    with pytest.raises(ValidationError):
        GetCurrentStateArgs.model_validate({"session_id": 1, "extra_arg": "forbidden"})


def test_complete_step_args_validation():
    # Valid
    args = CompleteStepArgs(session_id=1, step_number=2)
    assert args.session_id == 1
    assert args.step_number == 2

    # Missing step_number
    with pytest.raises(ValidationError):
        CompleteStepArgs.model_validate({"session_id": 1})

    # Step number <= 0
    with pytest.raises(ValidationError):
        CompleteStepArgs.model_validate({"session_id": 1, "step_number": 0})
    with pytest.raises(ValidationError):
        CompleteStepArgs.model_validate({"session_id": 1, "step_number": -1})

    # Extra fields
    with pytest.raises(ValidationError):
        CompleteStepArgs.model_validate({"session_id": 1, "step_number": 1, "notes": "fast"})


def test_skip_step_args_validation():
    # Valid
    args = SkipStepArgs(session_id=2, step_number=1)
    assert args.step_number == 1

    # Step number 0
    with pytest.raises(ValidationError):
        SkipStepArgs.model_validate({"session_id": 2, "step_number": 0})

    # Extra fields
    with pytest.raises(ValidationError):
        SkipStepArgs.model_validate({"session_id": 2, "step_number": 1, "reason": "no time"})


def test_get_recipe_args_mutual_exclusivity():
    # Valid with ID
    args_id = GetRecipeArgs(recipe_id=1)
    assert args_id.recipe_id == 1
    assert args_id.slug is None

    # Valid with slug
    args_slug = GetRecipeArgs(slug="tarka-daal")
    assert args_slug.slug == "tarka-daal"
    assert args_slug.recipe_id is None

    # Both provided -> rejected
    with pytest.raises(ValidationError, match="Provide either 'recipe_id' or 'slug', but not both"):
        GetRecipeArgs.model_validate({"recipe_id": 1, "slug": "tarka-daal"})

    # Neither provided -> rejected
    with pytest.raises(ValidationError, match="Must provide either 'recipe_id' or 'slug'"):
        GetRecipeArgs.model_validate({})

    # Empty slug -> rejected
    with pytest.raises(ValidationError):
        GetRecipeArgs.model_validate({"slug": ""})
    with pytest.raises(ValidationError):
        GetRecipeArgs.model_validate({"slug": "   "})

    # Malformed slug format -> rejected
    with pytest.raises(ValidationError, match="Invalid slug format"):
        GetRecipeArgs.model_validate({"slug": "Tarka Daal!"})

    # Extra arguments -> rejected
    with pytest.raises(ValidationError):
        GetRecipeArgs.model_validate({"recipe_id": 1, "foo": "bar"})


# --- 3. Action Executor Domain Unit Tests ---

def test_execute_get_current_state(db_session: Session, active_session):
    result = ActionExecutor.execute_action(
        db=db_session,
        action_name="get_current_state",
        arguments={"session_id": active_session.id},
    )
    assert result.success is True
    assert result.action == "get_current_state"
    assert result.error is None
    assert result.data["id"] == active_session.id
    assert result.data["status"] == SessionStatus.ACTIVE.value
    assert result.data["current_step_number"] == 1
    assert len(result.data["steps"]) == 3


def test_execute_get_current_step(db_session: Session, active_session):
    result = ActionExecutor.execute_action(
        db=db_session,
        action_name="get_current_step",
        arguments={"session_id": active_session.id},
    )
    assert result.success is True
    assert result.action == "get_current_step"
    assert result.error is None
    assert result.data["session_id"] == active_session.id
    assert result.data["current_step"]["step_number"] == 1
    assert "boil lentils" in result.data["current_step"]["instruction"].lower()


def test_execute_complete_step(db_session: Session, active_session):
    result = ActionExecutor.execute_action(
        db=db_session,
        action_name="complete_step",
        arguments={"session_id": active_session.id, "step_number": 1},
    )
    assert result.success is True
    assert result.action == "complete_step"
    assert result.data["current_step_number"] == 2

    # Verify step 1 is marked COMPLETED
    step1 = next(s for s in result.data["steps"] if s["step_number"] == 1)
    assert step1["status"] == StepStatus.COMPLETED.value
    assert step1["completed_at"] is not None

    # Verify step 2 is IN_PROGRESS
    step2 = next(s for s in result.data["steps"] if s["step_number"] == 2)
    assert step2["status"] == StepStatus.IN_PROGRESS.value


def test_execute_skip_step(db_session: Session, active_session):
    result = ActionExecutor.execute_action(
        db=db_session,
        action_name="skip_step",
        arguments={"session_id": active_session.id, "step_number": 1},
    )
    assert result.success is True
    assert result.action == "skip_step"
    assert result.data["current_step_number"] == 2

    # Verify step 1 is marked SKIPPED in history
    step1 = next(s for s in result.data["steps"] if s["step_number"] == 1)
    assert step1["status"] == StepStatus.SKIPPED.value


def test_execute_get_recipe_by_id_and_slug(db_session: Session, sample_recipe):
    # Lookup by ID
    res_id = ActionExecutor.execute_action(
        db=db_session,
        action_name="get_recipe",
        arguments={"recipe_id": sample_recipe.id},
    )
    assert res_id.success is True
    assert res_id.data["id"] == sample_recipe.id
    assert res_id.data["name"] == "Tarka Daal"
    assert len(res_id.data["ingredients"]) == 2
    assert len(res_id.data["steps"]) == 3

    # Lookup by Slug
    res_slug = ActionExecutor.execute_action(
        db=db_session,
        action_name="get_recipe",
        arguments={"slug": "tarka-daal"},
    )
    assert res_slug.success is True
    assert res_slug.data["id"] == sample_recipe.id
    assert res_slug.data["slug"] == "tarka-daal"


# --- 4. Error Handling and Domain Boundary Tests ---

def test_unknown_action_name_returns_invalid_action(db_session: Session):
    result = ActionExecutor.execute_action(
        db=db_session,
        action_name="delete_database",
        arguments={"session_id": 1},
    )
    assert result.success is False
    assert result.action == "delete_database"
    assert result.error.code == ActionErrorCode.INVALID_ACTION
    assert "not recognized or not allowed" in result.error.message
    assert result.error.suggestion is not None


def test_missing_and_unexpected_arguments(db_session: Session, active_session):
    # Missing required argument
    res_missing = ActionExecutor.execute_action(
        db=db_session,
        action_name="complete_step",
        arguments={"session_id": active_session.id},
    )
    assert res_missing.success is False
    assert res_missing.error.code == ActionErrorCode.INVALID_ARGUMENTS

    # Unexpected extra argument
    res_extra = ActionExecutor.execute_action(
        db=db_session,
        action_name="get_current_state",
        arguments={"session_id": active_session.id, "extra": "unauthorized"},
    )
    assert res_extra.success is False
    assert res_extra.error.code == ActionErrorCode.INVALID_ARGUMENTS
    assert "Extra inputs are not permitted" in res_extra.error.message


def test_malformed_arguments_payload(db_session: Session):
    result = ActionExecutor.execute_action(
        db=db_session,
        action_name="get_current_state",
        arguments="not-a-dict",  # type: ignore
    )
    assert result.success is False
    assert result.error.code == ActionErrorCode.INVALID_ARGUMENTS
    assert "Arguments must be provided as a dictionary/object" in result.error.message


def test_nonexistent_session_returns_session_not_found(db_session: Session):
    result = ActionExecutor.execute_action(
        db=db_session,
        action_name="get_current_state",
        arguments={"session_id": 99999},
    )
    assert result.success is False
    assert result.error.code == ActionErrorCode.SESSION_NOT_FOUND
    assert "99999 not found" in result.error.message


def test_nonexistent_recipe_returns_recipe_not_found(db_session: Session):
    # Nonexistent ID
    res_id = ActionExecutor.execute_action(
        db=db_session,
        action_name="get_recipe",
        arguments={"recipe_id": 99999},
    )
    assert res_id.success is False
    assert res_id.error.code == ActionErrorCode.RECIPE_NOT_FOUND

    # Nonexistent slug
    res_slug = ActionExecutor.execute_action(
        db=db_session,
        action_name="get_recipe",
        arguments={"slug": "nonexistent-recipe"},
    )
    assert res_slug.success is False
    assert res_slug.error.code == ActionErrorCode.RECIPE_NOT_FOUND


def test_out_of_order_step_completion_returns_step_conflict(db_session: Session, active_session):
    # Session is on step 1; attempt to complete step 2
    result = ActionExecutor.execute_action(
        db=db_session,
        action_name="complete_step",
        arguments={"session_id": active_session.id, "step_number": 2},
    )
    assert result.success is False
    assert result.error.code == ActionErrorCode.STEP_CONFLICT
    assert "not the current active step" in result.error.message


def test_action_on_cancelled_session_returns_session_not_active(db_session: Session, active_session):
    # Cancel session
    SessionService.cancel_session(db=db_session, session_id=active_session.id)

    # Attempt to complete step
    result = ActionExecutor.execute_action(
        db=db_session,
        action_name="complete_step",
        arguments={"session_id": active_session.id, "step_number": 1},
    )
    assert result.success is False
    assert result.error.code == ActionErrorCode.SESSION_NOT_ACTIVE
    assert "CANCELLED" in result.error.message.upper()


# --- 5. State Immutability and Transaction Isolation Tests ---

def test_read_only_actions_do_not_mutate_state(db_session: Session, active_session, sample_recipe):
    """Verify that read-only tools make zero database mutations."""
    # Record initial state
    session_before = db_session.get(CookingSession, active_session.id)
    initial_version = session_before.version
    initial_updated_at = session_before.updated_at
    initial_step = session_before.current_step_number

    # Execute read-only actions
    ActionExecutor.execute_action(db=db_session, action_name="get_current_state", arguments={"session_id": active_session.id})
    ActionExecutor.execute_action(db=db_session, action_name="get_current_step", arguments={"session_id": active_session.id})
    ActionExecutor.execute_action(db=db_session, action_name="get_recipe", arguments={"recipe_id": sample_recipe.id})

    # Reload from DB and verify zero modification
    db_session.expire_all()
    session_after = db_session.get(CookingSession, active_session.id)
    assert session_after.version == initial_version
    assert session_after.updated_at == initial_updated_at
    assert session_after.current_step_number == initial_step


def test_failed_mutations_do_not_partially_mutate_state(db_session: Session, active_session):
    """Verify that a rejected mutation rolls back completely and leaves state unchanged."""
    session_before = db_session.get(CookingSession, active_session.id)
    initial_version = session_before.version
    initial_step = session_before.current_step_number

    # Try invalid out-of-order completion
    result = ActionExecutor.execute_action(
        db=db_session,
        action_name="complete_step",
        arguments={"session_id": active_session.id, "step_number": 3},
    )
    assert result.success is False

    db_session.expire_all()
    session_after = db_session.get(CookingSession, active_session.id)
    assert session_after.version == initial_version
    assert session_after.current_step_number == initial_step
    # Step 1 must still be IN_PROGRESS
    step1 = next(s for s in session_after.steps if s.recipe_step.step_number == 1)
    assert step1.status == StepStatus.IN_PROGRESS.value
