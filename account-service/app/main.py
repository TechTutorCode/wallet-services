"""Account Service - customer accounts under wallets."""

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import get_settings
from app.events.consumer import start_wallet_consumer, stop_wallet_consumer
from app.events.publisher import get_event_publisher
from app.middleware.api_key import InternalAPIKeyMiddleware
from app.routers import accounts, callbacks

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await asyncio.to_thread(get_event_publisher().declare_exchange)
    except Exception as e:
        import logging
        logging.getLogger("app.events.publisher").warning("RabbitMQ declare failed: %s", e)
    start_wallet_consumer()
    yield
    stop_wallet_consumer()
    get_event_publisher().close()


app = FastAPI(
    title="Account Service",
    description="Customer accounts under wallets; account number generation; M-PESA callback",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(InternalAPIKeyMiddleware)
app.include_router(accounts.router)
app.include_router(callbacks.router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": get_settings().service_name}
