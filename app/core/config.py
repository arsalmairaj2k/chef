from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Cooking Companion API"
    app_env: str = "development"
    debug: bool = True
    api_v1_prefix: str = "/api/v1"

    host: str = "127.0.0.1"
    port: int = 8000

    # Database settings
    database_url: str = "postgresql://chef_user:chef_password@127.0.0.1:5432/chef_db"

    # LLM Settings
    llm_provider: str = "fake"  # 'fake', 'gemini', or 'openai'
    llm_model: str = "gemini-3.8-flash"
    gemini_api_key: str | None = None
    openai_api_key: str | None = None
    llm_timeout_seconds: float = 30.0
    llm_max_retries: int = 2
    llm_max_message_length: int = 1000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
