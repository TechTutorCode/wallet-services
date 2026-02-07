"""Idempotency for M-PESA callbacks: one PaymentReference per trans_id."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class PaymentReference(Base):
    __tablename__ = "payment_references"

    trans_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    account_no: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
