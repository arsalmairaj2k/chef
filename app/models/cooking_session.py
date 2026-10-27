from datetime import datetime
from enum import Enum
from typing import Optional, List
from sqlalchemy import Integer, String, DateTime, ForeignKey, CheckConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base


class SessionStatus(str, Enum):
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class CookingSession(Base):
    __tablename__ = "cooking_sessions"
    __table_args__ = (
        CheckConstraint("servings > 0", name="ck_cooking_sessions_servings_positive"),
        CheckConstraint("version > 0", name="ck_cooking_sessions_version_positive"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    recipe_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("recipes.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=SessionStatus.ACTIVE.value,
        index=True,
    )
    current_step_number: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    servings: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    recipe = relationship("Recipe", back_populates="cooking_sessions")
    steps: Mapped[List["CookingSessionStep"]] = relationship(
        "CookingSessionStep",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="CookingSessionStep.id",
    )

    def __repr__(self) -> str:
        return f"<CookingSession(id={self.id}, recipe_id={self.recipe_id}, status='{self.status}', step={self.current_step_number})>"
