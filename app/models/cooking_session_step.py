from datetime import datetime
from enum import Enum
from typing import Optional
from sqlalchemy import Integer, String, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base


class StepStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    SKIPPED = "SKIPPED"


class CookingSessionStep(Base):
    __tablename__ = "cooking_session_steps"
    __table_args__ = (
        UniqueConstraint("session_id", "recipe_step_id", name="uq_session_recipe_step"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("cooking_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    recipe_step_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("recipe_steps.id", ondelete="RESTRICT"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=StepStatus.PENDING.value,
        index=True,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    session = relationship("CookingSession", back_populates="steps")
    recipe_step = relationship("RecipeStep")

    @property
    def step_number(self) -> int:
        return self.recipe_step.step_number if self.recipe_step else 0

    @property
    def instruction(self) -> str:
        return self.recipe_step.instruction if self.recipe_step else ""

    @property
    def estimated_duration_seconds(self) -> Optional[int]:
        return self.recipe_step.estimated_duration_seconds if self.recipe_step else None

    def __repr__(self) -> str:
        return f"<CookingSessionStep(id={self.id}, session_id={self.session_id}, step_id={self.recipe_step_id}, status='{self.status}')>"
