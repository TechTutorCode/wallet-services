"""Read model: populated from wallet.created events. Holds prefix + sequence for account number generation."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Integer, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class WalletRegistry(Base):
    __tablename__ = "wallet_registry"

    wallet_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
    )
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    company_account_prefix: Mapped[str] = mapped_column(String(3), nullable=False)
    sequence_no: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
