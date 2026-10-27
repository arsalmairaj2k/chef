from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List
from sqlalchemy.orm import Session

from app.models.cooking_session import CookingSession, SessionStatus
from app.models.cooking_session_step import CookingSessionStep, StepStatus
from app.repositories.recipe_repository import RecipeRepository
from app.repositories.session_repository import SessionRepository
from app.schemas.recipe import RecipeIngredientRead
from app.schemas.cooking_session import (
    CookingSessionRead,
    CookingSessionStepRead,
    CurrentStepInfo,
    CurrentStepResponse,
)


class SessionNotFoundError(Exception):
    """Raised when a cooking session is not found."""
    pass


class RecipeNotFoundError(Exception):
    """Raised when the requested recipe is not found."""
    pass


class RecipeHasNoStepsError(Exception):
    """Raised when attempting to start a cooking session for a recipe with no steps."""
    pass


class SessionNotActiveError(Exception):
    """Raised when attempting to modify a session that is completed or cancelled."""
    pass


class StepNotCurrentError(Exception):
    """Raised when completing or skipping a step that is not currently in progress."""
    pass


class StepNotFoundError(Exception):
    """Raised when the step does not exist or does not belong to the recipe."""
    pass


class SessionService:
    @staticmethod
    def _to_session_read(session: CookingSession) -> CookingSessionRead:
        """Convert CookingSession ORM model to CookingSessionRead schema."""
        # Find active current step info if session is active
        current_step_info: Optional[CurrentStepInfo] = None
        sorted_steps = sorted(
            session.steps,
            key=lambda s: s.recipe_step.step_number if s.recipe_step else 0,
        )

        if session.status == SessionStatus.ACTIVE.value and session.current_step_number is not None:
            for step in sorted_steps:
                if step.recipe_step and step.recipe_step.step_number == session.current_step_number:
                    current_step_info = CurrentStepInfo(
                        step_number=step.recipe_step.step_number,
                        instruction=step.recipe_step.instruction,
                        estimated_duration_seconds=step.recipe_step.estimated_duration_seconds,
                        status=step.status,
                    )
                    break

        steps_read = [
            CookingSessionStepRead(
                id=s.id,
                session_id=s.session_id,
                recipe_step_id=s.recipe_step_id,
                step_number=s.step_number,
                instruction=s.instruction,
                estimated_duration_seconds=s.estimated_duration_seconds,
                status=s.status,
                completed_at=s.completed_at,
                updated_at=s.updated_at,
            )
            for s in sorted_steps
        ]

        # Calculate scaled ingredient quantities for this session
        ingredients_read = []
        if session.recipe and session.recipe.ingredients:
            default_servings = Decimal(session.recipe.default_servings or 1)
            ratio = Decimal(session.servings) / default_servings
            for ri in session.recipe.ingredients:
                scaled_qty = round(ri.quantity * ratio, 2) if ri.quantity is not None else None
                ingredients_read.append(
                    RecipeIngredientRead(
                        id=ri.id,
                        recipe_id=ri.recipe_id,
                        ingredient_id=ri.ingredient_id,
                        ingredient_name=ri.ingredient.name if ri.ingredient else None,
                        quantity=scaled_qty,
                        unit=ri.unit,
                        notes=ri.notes,
                        is_optional=ri.is_optional,
                    )
                )

        return CookingSessionRead(
            id=session.id,
            recipe_id=session.recipe_id,
            recipe_name=session.recipe.name if session.recipe else "",
            status=session.status,
            current_step_number=session.current_step_number,
            servings=session.servings,
            version=session.version,
            started_at=session.started_at,
            updated_at=session.updated_at,
            completed_at=session.completed_at,
            current_step=current_step_info,
            steps=steps_read,
            ingredients=ingredients_read,
        )

    @classmethod
    def create_session(
        cls,
        db: Session,
        recipe_id: int,
        servings: Optional[int] = None,
    ) -> CookingSessionRead:
        """Start a new persistent cooking session."""
        recipe = RecipeRepository.get_by_id(db, recipe_id)
        if not recipe:
            raise RecipeNotFoundError(f"Recipe with ID {recipe_id} not found.")

        if not recipe.steps:
            raise RecipeHasNoStepsError(
                f"Recipe '{recipe.name}' has no cooking steps and cannot be started."
            )

        serving_count = servings if servings is not None else recipe.default_servings
        if serving_count <= 0:
            raise ValueError("Servings count must be positive.")

        # Sort recipe steps by step_number ascending
        sorted_recipe_steps = sorted(recipe.steps, key=lambda s: s.step_number)
        first_step = sorted_recipe_steps[0]

        try:
            session = CookingSession(
                recipe_id=recipe.id,
                status=SessionStatus.ACTIVE.value,
                current_step_number=first_step.step_number,
                servings=serving_count,
                version=1,
            )
            db.add(session)
            db.flush()

            for idx, r_step in enumerate(sorted_recipe_steps):
                step_status = (
                    StepStatus.IN_PROGRESS.value
                    if idx == 0
                    else StepStatus.PENDING.value
                )
                session_step = CookingSessionStep(
                    session_id=session.id,
                    recipe_step_id=r_step.id,
                    status=step_status,
                )
                db.add(session_step)

            db.commit()
            loaded_session = SessionRepository.get_by_id(db, session.id)
            return cls._to_session_read(loaded_session)

        except Exception:
            db.rollback()
            raise

    @classmethod
    def get_session(cls, db: Session, session_id: int) -> CookingSessionRead:
        """Retrieve the persisted state of a cooking session."""
        session = SessionRepository.get_by_id(db, session_id)
        if not session:
            raise SessionNotFoundError(f"Cooking session with ID {session_id} not found.")
        return cls._to_session_read(session)

    @classmethod
    def get_current_step(cls, db: Session, session_id: int) -> CurrentStepResponse:
        """Inspect the current step and status without changing state."""
        session = SessionRepository.get_by_id(db, session_id)
        if not session:
            raise SessionNotFoundError(f"Cooking session with ID {session_id} not found.")

        current_step_info: Optional[CurrentStepInfo] = None
        if session.status == SessionStatus.ACTIVE.value and session.current_step_number is not None:
            for s in session.steps:
                if s.recipe_step and s.recipe_step.step_number == session.current_step_number:
                    current_step_info = CurrentStepInfo(
                        step_number=s.recipe_step.step_number,
                        instruction=s.recipe_step.instruction,
                        estimated_duration_seconds=s.recipe_step.estimated_duration_seconds,
                        status=s.status,
                    )
                    break

        return CurrentStepResponse(
            session_id=session.id,
            session_status=session.status,
            recipe_id=session.recipe_id,
            recipe_name=session.recipe.name if session.recipe else "",
            current_step=current_step_info,
        )

    @classmethod
    def complete_step(
        cls,
        db: Session,
        session_id: int,
        step_number: int,
    ) -> CookingSessionRead:
        """Complete the current step and advance the state machine to the next pending step."""
        session = SessionRepository.get_by_id(db, session_id)
        if not session:
            raise SessionNotFoundError(f"Cooking session with ID {session_id} not found.")

        if session.status != SessionStatus.ACTIVE.value:
            raise SessionNotActiveError(
                f"Cannot modify session: session status is '{session.status}'."
            )

        # Check if the requested step number exists in recipe
        recipe_step_numbers = [s.recipe_step.step_number for s in session.steps if s.recipe_step]
        if step_number not in recipe_step_numbers:
            raise StepNotFoundError(
                f"Step number {step_number} does not belong to this recipe."
            )

        if step_number != session.current_step_number:
            raise StepNotCurrentError(
                f"Step {step_number} is not the current active step (current active step is {session.current_step_number})."
            )

        try:
            now = datetime.now(timezone.utc)
            sorted_steps = sorted(
                session.steps,
                key=lambda s: s.recipe_step.step_number if s.recipe_step else 0,
            )

            # Mark current step COMPLETED
            for step in sorted_steps:
                if step.recipe_step and step.recipe_step.step_number == step_number:
                    step.status = StepStatus.COMPLETED.value
                    step.completed_at = now
                    break

            # Find next PENDING step
            next_step: Optional[CookingSessionStep] = None
            for step in sorted_steps:
                if step.status == StepStatus.PENDING.value:
                    next_step = step
                    break

            if next_step is not None:
                next_step.status = StepStatus.IN_PROGRESS.value
                session.current_step_number = next_step.recipe_step.step_number
            else:
                # All steps finished -> complete session
                session.status = SessionStatus.COMPLETED.value
                session.current_step_number = None
                session.completed_at = now

            session.version += 1
            db.commit()

            loaded = SessionRepository.get_by_id(db, session.id)
            return cls._to_session_read(loaded)

        except Exception:
            db.rollback()
            raise

    @classmethod
    def skip_step(
        cls,
        db: Session,
        session_id: int,
        step_number: int,
    ) -> CookingSessionRead:
        """Skip the current step and advance the state machine to the next pending step."""
        session = SessionRepository.get_by_id(db, session_id)
        if not session:
            raise SessionNotFoundError(f"Cooking session with ID {session_id} not found.")

        if session.status != SessionStatus.ACTIVE.value:
            raise SessionNotActiveError(
                f"Cannot modify session: session status is '{session.status}'."
            )

        recipe_step_numbers = [s.recipe_step.step_number for s in session.steps if s.recipe_step]
        if step_number not in recipe_step_numbers:
            raise StepNotFoundError(
                f"Step number {step_number} does not belong to this recipe."
            )

        if step_number != session.current_step_number:
            raise StepNotCurrentError(
                f"Step {step_number} is not the current active step (current active step is {session.current_step_number})."
            )

        try:
            now = datetime.now(timezone.utc)
            sorted_steps = sorted(
                session.steps,
                key=lambda s: s.recipe_step.step_number if s.recipe_step else 0,
            )

            # Mark current step SKIPPED
            for step in sorted_steps:
                if step.recipe_step and step.recipe_step.step_number == step_number:
                    step.status = StepStatus.SKIPPED.value
                    break

            # Find next PENDING step
            next_step: Optional[CookingSessionStep] = None
            for step in sorted_steps:
                if step.status == StepStatus.PENDING.value:
                    next_step = step
                    break

            if next_step is not None:
                next_step.status = StepStatus.IN_PROGRESS.value
                session.current_step_number = next_step.recipe_step.step_number
            else:
                session.status = SessionStatus.COMPLETED.value
                session.current_step_number = None
                session.completed_at = now

            session.version += 1
            db.commit()

            loaded = SessionRepository.get_by_id(db, session.id)
            return cls._to_session_read(loaded)

        except Exception:
            db.rollback()
            raise

    @classmethod
    def cancel_session(cls, db: Session, session_id: int) -> CookingSessionRead:
        """Cancel an active cooking session."""
        session = SessionRepository.get_by_id(db, session_id)
        if not session:
            raise SessionNotFoundError(f"Cooking session with ID {session_id} not found.")

        # Idempotent: if already cancelled, return state
        if session.status == SessionStatus.CANCELLED.value:
            return cls._to_session_read(session)

        if session.status == SessionStatus.COMPLETED.value:
            raise SessionNotActiveError(
                "Cannot cancel a session that is already completed."
            )

        try:
            session.status = SessionStatus.CANCELLED.value
            session.current_step_number = None
            session.version += 1
            db.commit()

            loaded = SessionRepository.get_by_id(db, session.id)
            return cls._to_session_read(loaded)

        except Exception:
            db.rollback()
            raise
