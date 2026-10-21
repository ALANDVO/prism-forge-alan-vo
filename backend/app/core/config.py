from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    app_name: str = "Prism Forge"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = "development"  # development, production

    # Database
    database_url: str = "sqlite+aiosqlite:///./data/prism.db"

    # Auth / OIDC
    oidc_enabled: bool = False
    oidc_issuer_url: str = ""
    oidc_client_id: str = ""
    oidc_client_secret: str = ""
    oidc_redirect_uri: str = ""
    oidc_scopes: str = "openid profile email"
    demo_mode: bool = True  # Only allowed on localhost

    # LLM
    llm_api_key: str = ""
    llm_provider: str = "openai-compatible"
    llm_model: str = ""
    llm_base_url: str = ""

    # Security
    secret_key: str = "dev-secret-change-in-production"
    access_token_expire_minutes: int = 30

    # CORS
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def is_demo_allowed(self) -> bool:
        return self.demo_mode and not self.is_production


@lru_cache
def get_settings() -> Settings:
    return Settings()