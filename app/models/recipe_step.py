from datetime import datetime
from typing import Optional
from sqlalchemy import Integer, Text, DateTime, ForeignKey, UniqueConstraint, CheckConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base


class RecipeStep(Base):
    __tablename__ = "recipe_steps"
    __table_args__ = (
        UniqueConstraint("recipe_id", "step_number", name="uq_recipe_step_number"),
        CheckConstraint("step_number > 0", name="ck_recipe_steps_step_number_positive"),
        CheckConstraint(
            "estimated_duration_seconds IS NULL OR estimated_duration_seconds > 0",
            name="ck_recipe_steps_duration_positive",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    recipe_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("recipes.id", ondelete="CASCADE"),
        nullable=False,
    )
    step_number: Mapped[int] = mapped_column(Integer, nullable=False)
    instruction: Mapped[str] = mapped_column(Text, nullable=False)
    estimated_duration_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    recipe: Mapped["Recipe"] = relationship("Recipe", back_populates="steps")

    def __repr__(self) -> str:
        return f"<RecipeStep(id={self.id}, recipe_id={self.recipe_id}, step={self.step_number})>"
