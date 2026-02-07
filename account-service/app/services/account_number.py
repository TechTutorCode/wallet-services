"""Account number generation with DB-level locking. Format: <company_prefix>-<zero_padded_sequence>."""

import uuid
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import with_for_update

from app.config import get_settings
from app.models.wallet_registry import WalletRegistry

logger = logging.getLogger(__name__)


async def generate_account_number(session: AsyncSession, wallet_id: uuid.UUID) -> tuple[str, int]:
    """
    Lock wallet row, increment sequence_no, return (account_no, sequence_no).
    Raises if wallet_id not in WalletRegistry.
    """
    settings = get_settings()
    padding = settings.account_no_padding

    # SELECT FOR UPDATE: lock the row until we commit
    result = await session.execute(
        select(WalletRegistry)
        .where(WalletRegistry.wallet_id == wallet_id)
        .with_for_update(nowait=False)
    )
    reg: WalletRegistry | None = result.scalar_one_or_none()
    if not reg:
        raise ValueError(f"Wallet {wallet_id} not found in registry. Consume wallet.created first.")

    next_seq = reg.sequence_no + 1
    reg.sequence_no = next_seq
    await session.flush()

    prefix = reg.company_account_prefix
    account_no = f"{prefix}-{str(next_seq).zfill(padding)}"
    return account_no, next_seq
