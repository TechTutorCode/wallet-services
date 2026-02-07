"""API Gateway - proxy to backend services with client auth."""

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
import httpx

from app.config import get_settings

# Header names
HEADER_CLIENT_API_KEY = "X-API-Key"
HEADER_INTERNAL_API_KEY = "X-Internal-API-Key"
AUTH_BEARER_PREFIX = "Bearer "


def create_app() -> FastAPI:
    settings = get_settings()
    valid_client_keys = {k.strip() for k in settings.client_api_keys.split(",") if k.strip()}

    app = FastAPI(
        title="Wallet Platform API Gateway",
        description="Single entry point; authenticates clients and proxies to backend services.",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    def get_client_key(request: Request) -> str | None:
        # Prefer X-API-Key, then Authorization: Bearer <key>
        key = request.headers.get(HEADER_CLIENT_API_KEY)
        if key:
            return key
        auth = request.headers.get("Authorization")
        if auth and auth.startswith(AUTH_BEARER_PREFIX):
            return auth[len(AUTH_BEARER_PREFIX) :].strip()
        return None

    def backend_base_url(path: str) -> str | None:
        """Return base URL of the backend that should handle this path, or None."""
        path = path.strip("/")
        if path.startswith("companies") or path == "companies":
            return settings.company_service_url.rstrip("/")
        if path.startswith("accounts") or path == "accounts":
            return settings.account_service_url.rstrip("/")
        if path.startswith("wallets") or path == "wallets":
            return settings.account_service_url.rstrip("/")
        if path.startswith("callbacks") or path == "callbacks":
            return settings.account_service_url.rstrip("/")
        return None

    @app.get("/health")
    async def health():
        return {"status": "ok", "service": settings.service_name}

    @app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"])
    async def proxy(path: str, request: Request):
        if path in ("docs", "redoc", "openapi.json", "health"):
            return JSONResponse(status_code=404, content={"detail": "Not found"})

        client_key = get_client_key(request)
        if not client_key or client_key not in valid_client_keys:
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing or invalid API key. Use X-API-Key or Authorization: Bearer <key>."},
            )

        base = backend_base_url(path)
        if not base:
            return JSONResponse(status_code=404, content={"detail": "No backend for this path"})

        # Build target URL: same path and query as request
        target_full = f"{base}/{path}" if path else base
        if request.url.query:
            target_full += "?" + request.url.query

        headers = dict(request.headers)
        # Remove client-facing and hop-by-hop headers
        for h in ("host", "x-api-key", "content-length", "connection", "transfer-encoding"):
            headers.pop(h.lower(), None)
        headers[HEADER_INTERNAL_API_KEY] = settings.internal_api_key

        try:
            body = await request.body()
            async with httpx.AsyncClient(timeout=settings.proxy_timeout_seconds) as client:
                resp = await client.request(
                    request.method,
                    target_full,
                    content=body,
                    headers=headers,
                )
            response_content = resp.content
            response_headers = [(k, v) for k, v in resp.headers.items() if k.lower() not in ("transfer-encoding", "connection", "content-encoding")]
            return Response(
                content=response_content,
                status_code=resp.status_code,
                headers=dict(response_headers),
            )
        except httpx.TimeoutException:
            return JSONResponse(status_code=504, content={"detail": "Backend timeout"})
        except httpx.ConnectError as e:
            return JSONResponse(status_code=502, content={"detail": f"Backend unreachable: {e!s}"})

    return app


app = create_app()
