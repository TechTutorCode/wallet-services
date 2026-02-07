# Account Service

Customer accounts under wallets; account number generation; M-PESA callback handling.

## Responsibilities

- **Account creation** under a wallet (with DB-locked sequence for safe account numbers).
- **Account number format**: `<company_prefix>-<zero_padded_sequence>` (e.g. `873-000001`).
- **WalletRegistry** read model: populated from `wallet.created` events (company prefix from first 3 chars of company account number).
- **M-PESA callback** `POST /callbacks/mpesa`: match BillRefNumber → account_no, idempotent, emit `ledger.credit.requested`.
- **Events published**: `account.created`, `ledger.credit.requested`.
- **Events consumed**: `wallet.created`.

## Environment

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL (postgresql+psycopg2://...) |
| `RABBITMQ_URL` | No | Default amqp://guest:guest@rabbitmq:5672/ |
| `INTERNAL_API_KEY` | Yes | Same as gateway/company-service |
| `ACCOUNT_NO_PADDING` | No | Default 6 (e.g. 000001) |

## API

- `POST /accounts` — Create account `{ "fullname": "...", "wallet_id": "uuid" }`.
- `GET /wallets/{wallet_id}/accounts` — List accounts by wallet.
- `DELETE /accounts/{account_id}` — Soft delete.
- `POST /callbacks/mpesa` — M-PESA webhook (no internal API key required).

## Wallet sync

Ensure **company-service** sends `company_account_number` in the `wallet.created` event (company’s `account_number`). Account-service consumes it and stores the first 3 characters as `company_account_prefix` in WalletRegistry. New wallets must have a `wallet.created` event before accounts can be created.

## Database

- **account_db**: create manually if your Postgres volume already existed before adding the init script:  
  `CREATE DATABASE account_db;`
- Migrations: `alembic upgrade head` (from account-service directory with `DATABASE_URL` set).

## Run

- With root docker-compose: `docker-compose up -d account-service` (after db and rabbitmq).
- Migrations:  
  `docker-compose exec account-service alembic upgrade head`  
  (or from host: `DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5433/account_db alembic upgrade head` from `account-service/`).
