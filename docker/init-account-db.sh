#!/bin/bash
# Create account_db for Account Service (idempotent)
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" -d postgres -tc "SELECT 1 FROM pg_database WHERE datname = 'account_db'" | grep -q 1 || \
  psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" -d postgres -c "CREATE DATABASE account_db;"
