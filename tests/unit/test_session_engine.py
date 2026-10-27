import pytest
from sqlalchemy.orm import Session

from app.models.recipe import Recipe
from app.models.recipe_step import RecipeStep
from app.models.cooking_session import SessionStatus
from app.models.cooking_session_step import StepStatus
from app.services.session_service import (
    SessionService,
    RecipeNotFoundError,
    RecipeHasNoStepsError,
    SessionNotActiveError,
    StepNotCurrentError,
    StepNotFoundError,
)


def create_recipe_with_steps(db: Session, slug: str, step_numbers: list[int]) -> Recipe:
    recipe = Recipe(
        name=f"Recipe {slug}",
        slug=slug,
        default_servings=4,
    )
    db.add(recipe)
    db.flush()

    for num in step_numbers:
        step = RecipeStep(
            recipe_id=recipe.id,
            step_number=num,
            instruction=f"Instruction for step {num}",
            estimated_duration_seconds=120,
        )
        db.add(step)
    db.commit()
    return recipe


def test_start_session_valid_recipe(db_session: Session):
    """Requirement 1 & 4: Starting session with valid recipe & initial current step."""
    recipe = create_recipe_with_steps(db_session, "test-valid-start", [1, 2, 3])

    session_read = SessionService.create_session(db_session, recipe_id=recipe.id)
    assert session_read.id is not None
    assert session_read.status == SessionStatus.ACTIVE.value
    assert session_read.current_step_number == 1
    assert session_read.servings == 4
    assert session_read.current_step is not None
    assert session_read.current_step.step_number == 1
    assert session_read.current_step.status == StepStatus.IN_PROGRESS.value

    # First step IN_PROGRESS, others PENDING
    assert len(session_read.steps) == 3
    assert session_read.steps[0].status == StepStatus.IN_PROGRESS.value
    assert session_read.steps[1].status == StepStatus.PENDING.value
    assert session_read.steps[2].status == StepStatus.PENDING.value


def test_reject_nonexistent_recipe(db_session: Session):
    """Requirement 2: Rejecting nonexistent recipe."""
    with pytest.raises(RecipeNotFoundError):
        SessionService.create_session(db_session, recipe_id=99999)


def test_reject_recipe_with_no_steps(db_session: Session):
    """Requirement 3: Rejecting recipe with no steps."""
    recipe = Recipe(name="No Steps", slug="no-steps", default_servings=2)
    db_session.add(recipe)
    db_session.commit()

    with pytest.raises(RecipeHasNoStepsError):
        SessionService.create_session(db_session, recipe_id=recipe.id)


def test_non_contiguous_step_numbers(db_session: Session):
    """Requirement 17: Sessions work when recipe step numbers are non-contiguous (e.g. 1, 3, 7)."""
    recipe = create_recipe_with_steps(db_session, "non-contiguous", [1, 3, 7])

    session = SessionService.create_session(db_session, recipe_id=recipe.id)
    assert session.current_step_number == 1

    # Complete step 1 -> advances to 3
    session = SessionService.complete_step(db_session, session_id=session.id, step_number=1)
    assert session.current_step_number == 3
    assert session.steps[0].status == StepStatus.COMPLETED.value
    assert session.steps[1].status == StepStatus.IN_PROGRESS.value

    # Skip step 3 -> advances to 7
    session = SessionService.skip_step(db_session, session_id=session.id, step_number=3)
    assert session.current_step_number == 7
    assert session.steps[1].status == StepStatus.SKIPPED.value
    assert session.steps[2].status == StepStatus.IN_PROGRESS.value

    # Complete step 7 -> completes session
    session = SessionService.complete_step(db_session, session_id=session.id, step_number=7)
    assert session.status == SessionStatus.COMPLETED.value
    assert session.current_step_number is None
    assert session.completed_at is not None


def test_completing_and_skipping_steps_history(db_session: Session):
    """Requirements 5, 6, 7, 8, 9: Step transitions, final step completion, and step history preservation."""
    recipe = create_recipe_with_steps(db_session, "step-history", [1, 2, 3])
    session = SessionService.create_session(db_session, recipe_id=recipe.id)

    # Complete step 1
    session = SessionService.complete_step(db_session, session_id=session.id, step_number=1)
    assert session.current_step_number == 2
    assert session.steps[0].status == StepStatus.COMPLETED.value
    assert session.steps[0].completed_at is not None

    # Skip step 2
    session = SessionService.skip_step(db_session, session_id=session.id, step_number=2)
    assert session.current_step_number == 3
    assert session.steps[1].status == StepStatus.SKIPPED.value

    # History preserved
    assert session.steps[0].status == StepStatus.COMPLETED.value
    assert session.steps[1].status == StepStatus.SKIPPED.value
    assert session.steps[2].status == StepStatus.IN_PROGRESS.value

    # Complete final step 3 -> completes session
    session = SessionService.complete_step(db_session, session_id=session.id, step_number=3)
    assert session.status == SessionStatus.COMPLETED.value
    assert session.current_step_number is None
    assert session.steps[2].status == StepStatus.COMPLETED.value


def test_reject_completing_non_current_step(db_session: Session):
    """Requirement 12: Completing a non-current step is rejected."""
    recipe = create_recipe_with_steps(db_session, "non-current-test", [1, 2])
    session = SessionService.create_session(db_session, recipe_id=recipe.id)

    # Current is 1, attempt to complete 2
    with pytest.raises(StepNotCurrentError):
        SessionService.complete_step(db_session, session_id=session.id, step_number=2)

    # Attempt to complete step 999 (not in recipe)
    with pytest.raises(StepNotFoundError):
        SessionService.complete_step(db_session, session_id=session.id, step_number=999)


def test_cancel_session_and_reject_modifications(db_session: Session):
    """Requirements 13, 14, 15: Cancelling session, preserving history, rejecting modifications."""
    recipe = create_recipe_with_steps(db_session, "cancel-test", [1, 2])
    session = SessionService.create_session(db_session, recipe_id=recipe.id)

    # Complete step 1
    SessionService.complete_step(db_session, session_id=session.id, step_number=1)

    # Cancel session
    cancelled = SessionService.cancel_session(db_session, session_id=session.id)
    assert cancelled.status == SessionStatus.CANCELLED.value
    assert cancelled.current_step_number is None
    assert cancelled.steps[0].status == StepStatus.COMPLETED.value

    # Attempt to complete step 2 on cancelled session -> rejected
    with pytest.raises(SessionNotActiveError):
        SessionService.complete_step(db_session, session_id=session.id, step_number=2)

    # Attempt to skip step 2 on cancelled session -> rejected
    with pytest.raises(SessionNotActiveError):
        SessionService.skip_step(db_session, session_id=session.id, step_number=2)

    # Idempotent cancel
    cancelled_again = SessionService.cancel_session(db_session, session_id=session.id)
    assert cancelled_again.status == SessionStatus.CANCELLED.value
