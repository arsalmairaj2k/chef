from datetime import datetime
from sqlalchemy import String, Integer, Text, DateTime, CheckConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List
from app.database.base import Base


class Recipe(Base):
    __tablename__ = "recipes"
    __table_args__ = (
        CheckConstraint("default_servings > 0", name="ck_recipes_default_servings_positive"),
        CheckConstraint("prep_time_minutes >= 0", name="ck_recipes_prep_time_non_negative"),
        CheckConstraint("cook_time_minutes >= 0", name="ck_recipes_cook_time_non_negative"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cuisine: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    default_servings: Mapped[int] = mapped_column(Integer, nullable=False, default=4)
    prep_time_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    cook_time_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
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

    ingredients: Mapped[List["RecipeIngredient"]] = relationship(
        "RecipeIngredient",
        back_populates="recipe",
        cascade="all, delete-orphan",
        order_by="RecipeIngredient.id",
    )
    steps: Mapped[List["RecipeStep"]] = relationship(
        "RecipeStep",
        back_populates="recipe",
        cascade="all, delete-orphan",
        order_by="RecipeStep.step_number",
    )
    cooking_sessions = relationship(
        "CookingSession",
        back_populates="recipe",
        passive_deletes="all",
    )

    def __repr__(self) -> str:
        return f"<Recipe(id={self.id}, slug='{self.slug}', name='{self.name}')>"

