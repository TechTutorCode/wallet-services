"""Company Service - FastAPI application."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.security import APIKeyHeader

from app.config import get_settings
from app.events.publisher import get_event_publisher
from app.middleware.api_key import InternalAPIKeyMiddleware
from app.routers import companies, wallets

# For Swagger UI "Authorize" — same header the middleware checks
INTERNAL_API_KEY_HEADER = APIKeyHeader(name="X-Internal-API-Key", auto_error=False)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: connect to RabbitMQ and declare exchange so it appears in the UI and publish works."""
    import asyncio
    try:
        await asyncio.to_thread(get_event_publisher().declare_exchange)
    except Exception as e:
        import logging
        logging.getLogger("app.events.publisher").warning(
            "RabbitMQ exchange declaration failed at startup: %s. Events will not be published.", e
        )
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
        swagger_ui_init_oauth=None,
        swagger_ui_parameters={"persistAuthorization": True},
    )
    # So /docs shows "Authorize" and sends X-Internal-API-Key on every request
    app.openapi_schema = None  # force rebuild with security

    def custom_openapi():
        if app.openapi_schema is not None:
            return app.openapi_schema
        from fastapi.openapi.utils import get_openapi
        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )
        openapi_schema["components"]["securitySchemes"] = {
            "InternalApiKey": {
                "type": "apiKey",
                "in": "header",
                "name": "X-Internal-API-Key",
                "description": "Internal API key (same as INTERNAL_API_KEY env, e.g. dev-internal-key)",
            }
        }
        openapi_schema["security"] = [{"InternalApiKey": []}]
        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi
    app.add_middleware(InternalAPIKeyMiddleware)
    app.include_router(companies.router)
    app.include_router(wallets.router)

    @app.get("/health")
    async def health():
        return {"status": "ok", "service": settings.service_name}

    return app


app = create_app()
