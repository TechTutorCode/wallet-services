"""Application configuration from environment variables."""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Service
    service_name: str = Field(default="company-service", alias="SERVICE_NAME")

    # Database
    database_url: str = Field(
        ...,
        description="PostgreSQL connection URL (postgresql+psycopg2://...)",
        alias="DATABASE_URL",
    )

    # M-PESA integration
    mpesa_base_url: str = Field(
        default="https://m-pesa.techtutor.co.ke",
        alias="MPESA_BASE_URL",
    )
    company_callback_url: str = Field(
        default="https://api.myapp.com/mpesa/callback",
        alias="COMPANY_CALLBACK_URL",
    )

    # RabbitMQ
    rabbitmq_url: str = Field(
        default="amqp://guest:guest@rabbitmq:5672/",
        alias="RABBITMQ_URL",
    )
    rabbitmq_exchange: str = Field(
        default="wallet.events",
        description="Topic exchange for domain events",
    )

    # API Gateway auth (service-to-service)
    internal_api_key: str = Field(
        ...,
        min_length=1,
        description="Trusted key from API Gateway (X-Internal-API-Key)",
        alias="INTERNAL_API_KEY",
    )

    # HTTP client
    http_timeout_seconds: float = Field(default=30.0, ge=1.0, le=120.0)
    http_max_retries: int = Field(default=3, ge=1, le=10)


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()
