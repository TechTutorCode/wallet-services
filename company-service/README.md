# Company Service

Fintech-grade microservice for the wallet platform: **companies** and **wallets**, with M-PESA integration and RabbitMQ domain events.

## Responsibilities

- Create, update, list, and soft-delete **companies**
- Create **wallets** under a company (M-PESA paybills)
- Publish domain events to RabbitMQ: `company.created`, `company.updated`, `company.deleted`, `wallet.created`

## Tech Stack

- **FastAPI** – API
- **SQLAlchemy 2.0** – async ORM
- **PostgreSQL** – database (asyncpg at runtime, psycopg2 for Alembic)
- **Pydantic v2** – validation
- **RabbitMQ** – events (topic exchange `wallet.events`)
- **httpx** – async HTTP client for M-PESA
- **Alembic** – migrations
- **Docker** – container and compose

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | `postgresql+psycopg2://user:pass@host:5432/dbname` |
| `INTERNAL_API_KEY` | Yes | Trusted key; API Gateway sends as `X-Internal-API-Key` |
| `MPESA_BASE_URL` | No | Default: `https://m-pesa.techtutor.co.ke` |
| `COMPANY_CALLBACK_URL` | No | Default: `https://api.myapp.com/mpesa/callback` |
| `RABBITMQ_URL` | No | Default: `amqp://guest:guest@rabbitmq:5672/` |
| `SERVICE_NAME` | No | Default: `company-service` |

## Authentication

- **API Gateway model**: clients authenticate at the gateway; the gateway injects `X-Internal-API-Key`.
- This service **rejects** requests that lack or misuse that header (401).
- End-user auth is **not** handled here (service-to-service trust only).

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/companies` | Create company (M-PESA app + DB + event) |
| `PATCH` | `/companies/{company_id}` | Update company (M-PESA + DB + event) |
| `GET` | `/companies` | List active companies (paginated) |
| `DELETE` | `/companies/{company_id}` | Soft-delete company |
| `POST` | `/companies/{company_id}/wallets` | Create wallet (M-PESA paybill + DB + event) |

OpenAPI: `/docs`, `/redoc` (no API key required for docs).

## Run locally

```bash
# Copy env and set INTERNAL_API_KEY + DATABASE_URL
cp .env.example .env

# Optional: use Docker for DB and RabbitMQ
docker-compose up -d db rabbitmq

# Migrations (sync URL in .env)
alembic upgrade head

# Run app
uvicorn app.main:app --reload --port 8040
```

## Run with Docker

```bash
export INTERNAL_API_KEY=your-key
docker-compose up -d
# Run migrations inside container or from host against db:5432
alembic upgrade head
```

## Project layout

```
app/
  main.py           # FastAPI app, middleware, routers
  config.py         # Settings from env
  dependencies.py   # DB session, optional helpers
  middleware/       # X-Internal-API-Key check
  models/           # SQLAlchemy Company, Wallet
  schemas/           # Pydantic request/response
  routers/           # companies, wallets
  services/          # CompanyService, WalletService
  clients/           # M-PESA httpx client (retries, timeout)
  events/            # RabbitMQ publisher
  db/                # Async engine, session
alembic/             # Migrations
```

## Event format (RabbitMQ)

- **Exchange**: `wallet.events` (topic)
- **Routing keys**: `company.created`, `company.updated`, `company.deleted`, `wallet.created`
- **Body**:
```json
{
  "event_id": "uuid",
  "event_type": "company.created",
  "occurred_at": "ISO8601",
  "payload": { ... }
}
```

## Non-functional

- **Idempotent-friendly** external calls (M-PESA); retries with exponential backoff (max 3).
- **Timeouts** on all HTTP calls (configurable).
- **Async** throughout; RabbitMQ publish runs in thread to avoid blocking.
- **Structured** error handling (4xx/5xx from M-PESA mapped to HTTP responses).
