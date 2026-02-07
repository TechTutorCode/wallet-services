from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.config import get_settings

SKIP_PATHS = ("/health", "/docs", "/redoc", "/openapi.json", "/callbacks/mpesa")


class InternalAPIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path.rstrip("/") in SKIP_PATHS or request.url.path.startswith("/callbacks/"):
            return await call_next(request)
        key = request.headers.get("X-Internal-API-Key")
        if not key or key != get_settings().internal_api_key:
            return JSONResponse(status_code=401, content={"detail": "Missing or invalid internal API key"})
        return await call_next(request)
