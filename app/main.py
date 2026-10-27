from fastapi import FastAPI
from app.core.config import get_settings
from app.api.health import router as health_router
from app.api.recipes import router as recipes_router
from app.api.sessions import router as sessions_router
from app.api.actions import router as actions_router
from app.api.chat import router as chat_router


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        description="Pakistan-first, voice-first AI Cooking Companion backend API",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # Health check available directly at /health and under the API v1 prefix
    app.include_router(health_router)
    app.include_router(health_router, prefix=settings.api_v1_prefix)

    # Recipes API under /api/v1/recipes
    app.include_router(recipes_router, prefix=settings.api_v1_prefix)

    # Sessions API under /api/v1/sessions
    app.include_router(sessions_router, prefix=settings.api_v1_prefix)

    # Actions API under /api/v1/sessions
    app.include_router(actions_router, prefix=settings.api_v1_prefix)

    # Chat Interaction API under /api/v1/sessions
    app.include_router(chat_router, prefix=settings.api_v1_prefix)



    @app.get("/", tags=["root"])
    async def root():
        return {
            "message": "Welcome to AI Cooking Companion API",
            "docs": "/docs",
            "health": "/health",
        }

    return app


app = create_app()
