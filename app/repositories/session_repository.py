from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.cooking_session import CookingSession
from app.models.cooking_session_step import CookingSessionStep


class SessionRepository:
    @staticmethod
    def get_by_id(db: Session, session_id: int) -> Optional[CookingSession]:
        """Fetch cooking session by ID with eager-loaded recipe and ordered steps."""
        stmt = (
            select(CookingSession)
            .options(
                selectinload(CookingSession.recipe),
                selectinload(CookingSession.steps).selectinload(CookingSessionStep.recipe_step),
            )
            .where(CookingSession.id == session_id)
        )
        return db.scalar(stmt)

    @staticmethod
    def save(db: Session, session: CookingSession) -> CookingSession:
        """Add and flush session to database."""
        db.add(session)
        db.flush()
        return session
