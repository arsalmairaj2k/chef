from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.cooking_session import (
    SessionCreate,
    SessionStepActionRequest,
    CookingSessionRead,
    CurrentStepResponse,
)
from app.services.session_service import (
    SessionService,
    SessionNotFoundError,
    RecipeNotFoundError,
    RecipeHasNoStepsError,
    SessionNotActiveError,
    StepNotCurrentError,
    StepNotFoundError,
)

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", response_model=CookingSessionRead, status_code=status.HTTP_201_CREATED)
def create_session(
    payload: SessionCreate,
    db: Session = Depends(get_db),
) -> CookingSessionRead:
    """Start a new persistent cooking session for a recipe."""
    try:
        return SessionService.create_session(
            db=db,
            recipe_id=payload.recipe_id,
            servings=payload.servings,
        )
    except RecipeNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except (RecipeHasNoStepsError, ValueError) as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.get("/{session_id}", response_model=CookingSessionRead, status_code=status.HTTP_200_OK)
def get_session(
    session_id: int,
    db: Session = Depends(get_db),
) -> CookingSessionRead:
    """Retrieve full state and history of a cooking session."""
    try:
        return SessionService.get_session(db=db, session_id=session_id)
    except SessionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{session_id}/current-step", response_model=CurrentStepResponse, status_code=status.HTTP_200_OK)
def get_current_step(
    session_id: int,
    db: Session = Depends(get_db),
) -> CurrentStepResponse:
    """Inspect the active current step without mutating session state."""
    try:
        return SessionService.get_current_step(db=db, session_id=session_id)
    except SessionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{session_id}/complete-step", response_model=CookingSessionRead, status_code=status.HTTP_200_OK)
def complete_step(
    session_id: int,
    payload: SessionStepActionRequest,
    db: Session = Depends(get_db),
) -> CookingSessionRead:
    """Mark the active step completed and advance the session state machine."""
    try:
        return SessionService.complete_step(
            db=db,
            session_id=session_id,
            step_number=payload.step_number,
        )
    except SessionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except StepNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except (SessionNotActiveError, StepNotCurrentError) as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post("/{session_id}/skip-step", response_model=CookingSessionRead, status_code=status.HTTP_200_OK)
def skip_step(
    session_id: int,
    payload: SessionStepActionRequest,
    db: Session = Depends(get_db),
) -> CookingSessionRead:
    """Mark the active step skipped and advance the session state machine."""
    try:
        return SessionService.skip_step(
            db=db,
            session_id=session_id,
            step_number=payload.step_number,
        )
    except SessionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except StepNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except (SessionNotActiveError, StepNotCurrentError) as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post("/{session_id}/cancel", response_model=CookingSessionRead, status_code=status.HTTP_200_OK)
def cancel_session(
    session_id: int,
    db: Session = Depends(get_db),
) -> CookingSessionRead:
    """Cancel an active cooking session."""
    try:
        return SessionService.cancel_session(db=db, session_id=session_id)
    except SessionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except SessionNotActiveError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
