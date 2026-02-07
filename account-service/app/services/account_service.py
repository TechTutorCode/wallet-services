"""Account creation, list, soft-delete; M-PESA callback handling."""

import asyncio
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.events.publisher import get_event_publisher
from app.models.account import Account
from app.models.payment_reference import PaymentReference
from app.schemas.account import AccountCreate, AccountCreateResponse, AccountListItem
from app.services.account_number import generate_account_number


class AccountService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def _publish(self, event_type: str, payload: dict) -> None:
        pub = get_event_publisher()
        await asyncio.to_thread(pub.publish, event_type, payload)

    async def create_account(self, data: AccountCreate) -> AccountCreateResponse:
        account_no, sequence_no = await generate_account_number(self.session, data.wallet_id)
        account = Account(
            wallet_id=data.wallet_id,
            fullname=data.fullname,
            account_no=account_no,
            sequence_no=sequence_no,
            is_active=True,
        )
        self.session.add(account)
        await self.session.flush()
        await self.session.refresh(account)

        await self._publish("account.created", {
            "account_id": str(account.id),
            "wallet_id": str(account.wallet_id),
            "fullname": account.fullname,
            "account_no": account.account_no,
        })

        return AccountCreateResponse(
            id=account.id,
            wallet_id=account.wallet_id,
            fullname=account.fullname,
            account_no=account.account_no,
        )

    async def list_by_wallet(self, wallet_id: UUID) -> list[AccountListItem]:
        result = await self.session.execute(
            select(Account).where(Account.wallet_id == wallet_id).order_by(Account.sequence_no)
        )
        accounts = result.scalars().all()
        return [AccountListItem.model_validate(a) for a in accounts]

    async def soft_delete(self, account_id: UUID) -> Account | None:
        result = await self.session.execute(
            select(Account).where(Account.id == account_id).where(Account.is_active.is_(True))
        )
        account = result.scalar_one_or_none()
        if not account:
            return None
        account.is_active = False
        await self.session.flush()
        await self.session.refresh(account)
        return account

    async def record_payment_and_emit_credit(
        self,
        trans_id: str,
        account_no: str,
        amount: Decimal,
    ) -> bool:
        """Idempotent: if trans_id exists, return False (already processed). Else insert and return True."""
        existing = await self.session.execute(
            select(PaymentReference).where(PaymentReference.trans_id == trans_id)
        )
        if existing.scalar_one_or_none():
            return False

        ref = PaymentReference(trans_id=trans_id, account_no=account_no, amount=amount)
        self.session.add(ref)
        await self.session.flush()

        await self._publish("ledger.credit.requested", {
            "trans_id": trans_id,
            "account_no": account_no,
            "amount": str(amount),
        })
        return True
