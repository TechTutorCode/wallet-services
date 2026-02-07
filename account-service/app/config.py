"""Application configuration."""

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

    service_name: str = Field(default="account-service", alias="SERVICE_NAME")

    database_url: str = Field(..., alias="DATABASE_URL")

    rabbitmq_url: str = Field(
        default="amqp://guest:guest@rabbitmq:5672/",
        alias="RABBITMQ_URL",
    )
    rabbitmq_exchange: str = Field(default="wallet.events", alias="RABBITMQ_EXCHANGE")

    account_no_padding: int = Field(default=6, ge=1, le=12, alias="ACCOUNT_NO_PADDING")

    internal_api_key: str = Field(..., min_length=1, alias="INTERNAL_API_KEY")


@lru_cache
def get_settings() -> Settings:
    return Settings()
