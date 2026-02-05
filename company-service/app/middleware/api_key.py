"""API Gateway trust: reject requests missing X-Internal-API-Key."""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.config import get_settings

HEADER_INTERNAL_API_KEY = "X-Internal-API-Key"


class InternalAPIKeyMiddleware(BaseHTTPMiddleware):
    """
    Service-to-service authentication.
    Rejects requests that do not carry the trusted API key from the API Gateway.
    Does NOT authenticate end-users.
    """

    async def dispatch(self, request: Request, call_next):
        # Skip validation for health and docs (so orchestrators can healthcheck without the key)
        path = request.url.path
        if path in ("/health", "/docs", "/redoc", "/openapi.json"):
            return await call_next(request)

        api_key = request.headers.get(HEADER_INTERNAL_API_KEY)
        expected = get_settings().internal_api_key

        if not api_key or api_key != expected:
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing or invalid internal API key"},
            )
        return await call_next(request)
