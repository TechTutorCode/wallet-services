from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection

from app.db.session import Base
from app.models import WalletRegistry, Account, PaymentReference  # noqa: F401
from app.config import get_settings

config = context.config
if config.config_file_name:
    fileConfig(config.config_file_name)

settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.database_url)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True, dialect_opts={"paramstyle": "named"})
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    from sqlalchemy import create_engine
    connectable = create_engine(config.get_main_option("sqlalchemy.url", ""), poolclass=pool.NullPool)
    with connectable.connect() as conn:
        do_run_migrations(conn)


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
