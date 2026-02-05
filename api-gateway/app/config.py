"""Gateway configuration."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Gateway
    service_name: str = Field(default="api-gateway", alias="SERVICE_NAME")
    port: int = Field(default=8000, ge=1, le=65535)

    # Client auth: keys that external clients must send (e.g. X-API-Key)
    # Comma-separated list for multiple keys
    client_api_keys: str = Field(
        ...,
        min_length=1,
        description="Valid client API keys (comma-separated)",
        alias="CLIENT_API_KEYS",
    )

    # Internal key to inject when calling backend services (must match INTERNAL_API_KEY on services)
    internal_api_key: str = Field(
        ...,
        min_length=1,
        alias="INTERNAL_API_KEY",
    )

    # Backend service URLs (used when running in Docker / same network)
    company_service_url: str = Field(
        default="http://company-service:8040",
        alias="COMPANY_SERVICE_URL",
    )

    # Timeout for proxy requests
    proxy_timeout_seconds: float = Field(default=30.0, ge=1.0, le=120.0)


@lru_cache
def get_settings() -> Settings:
    return Settings()
