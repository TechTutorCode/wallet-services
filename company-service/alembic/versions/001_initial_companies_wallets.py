"""Initial companies and wallets tables.

Revision ID: 001
Revises:
Create Date: 2025-02-05

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "companies",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("account_number", sa.String(64), nullable=False),
        sa.Column("api_key", sa.String(255), nullable=False),
        sa.Column("callback_url", sa.String(512), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_companies_account_number", "companies", ["account_number"], unique=True)
    op.create_index("ix_companies_api_key", "companies", ["api_key"], unique=True)
    op.create_index("ix_companies_name", "companies", ["name"], unique=True)

    op.create_table(
        "wallets",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("credential_id", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("business_short_code", sa.String(32), nullable=False),
        sa.Column("environment", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_wallets_company_id", "wallets", ["company_id"], unique=False)
    op.create_index("ix_wallets_credential_id", "wallets", ["credential_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_wallets_credential_id", table_name="wallets")
    op.drop_index("ix_wallets_company_id", table_name="wallets")
    op.drop_table("wallets")
    op.drop_index("ix_companies_name", table_name="companies")
    op.drop_index("ix_companies_api_key", table_name="companies")
    op.drop_index("ix_companies_account_number", table_name="companies")
    op.drop_table("companies")
