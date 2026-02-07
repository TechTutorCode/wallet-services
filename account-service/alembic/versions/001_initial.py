"""Initial wallet_registry, accounts, payment_references.

Revision ID: 001
Revises:
Create Date: 2025-02-05

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "wallet_registry",
        sa.Column("wallet_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_account_prefix", sa.String(3), nullable=False),
        sa.Column("sequence_no", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("wallet_id"),
    )
    op.create_index("ix_wallet_registry_company_id", "wallet_registry", ["company_id"], unique=False)

    op.create_table(
        "accounts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("wallet_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("fullname", sa.String(255), nullable=False),
        sa.Column("account_no", sa.String(32), nullable=False),
        sa.Column("sequence_no", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["wallet_id"], ["wallet_registry.wallet_id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_accounts_account_no", "accounts", ["account_no"], unique=True)
    op.create_index("ix_accounts_wallet_id", "accounts", ["wallet_id"], unique=False)

    op.create_table(
        "payment_references",
        sa.Column("trans_id", sa.String(64), nullable=False),
        sa.Column("account_no", sa.String(32), nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("trans_id"),
    )
    op.create_index("ix_payment_references_account_no", "payment_references", ["account_no"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_payment_references_account_no", table_name="payment_references")
    op.drop_table("payment_references")
    op.drop_index("ix_accounts_wallet_id", table_name="accounts")
    op.drop_index("ix_accounts_account_no", table_name="accounts")
    op.drop_table("accounts")
    op.drop_index("ix_wallet_registry_company_id", table_name="wallet_registry")
    op.drop_table("wallet_registry")
