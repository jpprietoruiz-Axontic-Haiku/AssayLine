from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "development"
    database_url: str = "postgresql+psycopg://assayline:assayline@localhost:5432/assayline"
    redis_url: str = "redis://localhost:6379/0"
    anthropic_api_key: str = ""
    max_upload_mb: int = 25
    storage_dir: str = "./data/reports"
    min_embedded_text_chars: int = 40
    anthropic_vision_model: str = "claude-sonnet-5"
    anthropic_agent_model: str = "claude-sonnet-5"
    cors_allow_origins: str = "http://localhost:5173"

    @property
    def cors_allow_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allow_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
