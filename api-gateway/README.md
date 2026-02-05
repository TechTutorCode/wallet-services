# API Gateway

Single entry point for the Wallet Platform. Authenticates clients and proxies requests to backend services.

## Behaviour

- **Port**: 8000
- **Client auth**: Clients must send a valid API key via:
  - `X-API-Key: <key>`, or
  - `Authorization: Bearer <key>`
- **Backend auth**: Gateway adds `X-Internal-API-Key` when forwarding (must match each service’s `INTERNAL_API_KEY`).
- **Routing**:
  - `/companies`, `/companies/*` → Company Service (port 8040)
  - More services can be added by extending `backend_base_url()` and env config.

## Environment

| Variable | Required | Description |
|----------|----------|-------------|
| `CLIENT_API_KEYS` | Yes | Comma-separated valid client API keys |
| `INTERNAL_API_KEY` | Yes | Key injected to backends (must match services) |
| `COMPANY_SERVICE_URL` | No | Default `http://company-service:8040` |

## Run locally

```bash
cp .env.example .env
# Set CLIENT_API_KEYS and INTERNAL_API_KEY (same as company-service INTERNAL_API_KEY)
uvicorn app.main:app --reload --port 8000
```

Then call the **gateway** at `http://localhost:8000/companies` with `X-API-Key: <one of CLIENT_API_KEYS>`.

## Run with Docker (full stack)

From **Wallet Microservices** root:

```bash
docker-compose up -d
```

- Gateway: `http://localhost:8000`
- Company service is only reachable via the gateway (no host port by default).

To add another service later: add a new backend URL in config, extend `backend_base_url()` in `app/main.py`, and add the service to `docker-compose.yml`.
