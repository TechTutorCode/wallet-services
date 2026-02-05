"""Company Service - FastAPI application."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import get_settings
from app.events.publisher import get_event_publisher
from app.middleware.api_key import InternalAPIKeyMiddleware
from app.routers import companies, wallets


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: ensure exchange exists. Shutdown: close RabbitMQ."""
    yield
    get_event_publisher().close()


def create_app() -> FastAPI:
    """Application factory."""
    settings = get_settings()
    app = FastAPI(
        title="Company Service",
        description="Wallet platform - companies and wallets (M-PESA integration)",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )
    app.add_middleware(InternalAPIKeyMiddleware)
    app.include_router(companies.router)
    app.include_router(wallets.router)

    @app.get("/health")
    async def health():
        return {"status": "ok", "service": settings.service_name}

    return app


app = create_app()
