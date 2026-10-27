from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Type
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.ai.action_schemas import (
    GetCurrentStateArgs,
    GetCurrentStepArgs,
    CompleteStepArgs,
    SkipStepArgs,
    GetRecipeArgs,
)
from app.services.session_service import SessionService
from app.services.recipe_service import RecipeService
from app.schemas.recipe import RecipeRead


@dataclass(frozen=True)
class ToolDefinition:
    """Explicit definition of an allowlisted cooking tool."""
    name: str
    description: str
    args_schema: Type[BaseModel]
    handler: Callable[[Session, Any], Any]

    def to_dict(self) -> Dict[str, Any]:
        """Return a clean JSON-compatible schema definition suitable for future LLM tool-calling."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.args_schema.model_json_schema(),
        }


def _handle_get_current_state(db: Session, args: GetCurrentStateArgs) -> Dict[str, Any]:
    session_read = SessionService.get_session(db, session_id=args.session_id)
    return session_read.model_dump(mode="json")


def _handle_get_current_step(db: Session, args: GetCurrentStepArgs) -> Dict[str, Any]:
    current_step_resp = SessionService.get_current_step(db, session_id=args.session_id)
    return current_step_resp.model_dump(mode="json")


def _handle_complete_step(db: Session, args: CompleteStepArgs) -> Dict[str, Any]:
    session_read = SessionService.complete_step(
        db,
        session_id=args.session_id,
        step_number=args.step_number,
    )
    return session_read.model_dump(mode="json")


def _handle_skip_step(db: Session, args: SkipStepArgs) -> Dict[str, Any]:
    session_read = SessionService.skip_step(
        db,
        session_id=args.session_id,
        step_number=args.step_number,
    )
    return session_read.model_dump(mode="json")


def _handle_get_recipe(db: Session, args: GetRecipeArgs) -> Dict[str, Any]:
    if args.recipe_id is not None:
        recipe = RecipeService.get_recipe_by_id(db, recipe_id=args.recipe_id)
    elif args.slug is not None:
        recipe = RecipeService.get_recipe_by_slug(db, slug=args.slug)
    else:
        raise ValueError("Either recipe_id or slug must be provided.")

    return RecipeRead.model_validate(recipe).model_dump(mode="json")


class ToolRegistry:
    """Allowlisted registry for cooking tools. Strictly forbids dynamic module loading or code execution."""

    _registry: Dict[str, ToolDefinition] = {
        "get_current_state": ToolDefinition(
            name="get_current_state",
            description="Retrieve the current state of an active cooking session, including status, servings, current step, and full step progress history.",
            args_schema=GetCurrentStateArgs,
            handler=_handle_get_current_state,
        ),
        "get_current_step": ToolDefinition(
            name="get_current_step",
            description="Inspect the current active step in a cooking session without modifying or advancing session state.",
            args_schema=GetCurrentStepArgs,
            handler=_handle_get_current_step,
        ),
        "complete_step": ToolDefinition(
            name="complete_step",
            description="Mark the active step completed in the cooking session and advance to the next pending step.",
            args_schema=CompleteStepArgs,
            handler=_handle_complete_step,
        ),
        "skip_step": ToolDefinition(
            name="skip_step",
            description="Mark the active step skipped in the cooking session and advance to the next pending step.",
            args_schema=SkipStepArgs,
            handler=_handle_skip_step,
        ),
        "get_recipe": ToolDefinition(
            name="get_recipe",
            description="Retrieve recipe information, required ingredients, and ordered instructions using either recipe_id or unique slug.",
            args_schema=GetRecipeArgs,
            handler=_handle_get_recipe,
        ),
    }

    @classmethod
    def get(cls, name: str) -> Optional[ToolDefinition]:
        """Fetch tool definition by allowlisted name."""
        return cls._registry.get(name)

    @classmethod
    def list_tools(cls) -> List[str]:
        """List all supported tool action names."""
        return sorted(cls._registry.keys())

    @classmethod
    def contains(cls, name: str) -> bool:
        """Check whether an action name is registered."""
        return name in cls._registry

    @classmethod
    def get_definitions(cls) -> List[Dict[str, Any]]:
        """Return JSON-serializable list of tool definitions with schemas."""
        return [tool.to_dict() for tool in cls._registry.values()]
