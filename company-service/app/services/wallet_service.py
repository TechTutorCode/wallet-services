"""Wallet domain service: create wallet under company."""

import asyncio
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.mpesa_client import MpesaClient
from app.events.publisher import get_event_publisher
from app.models.company import Company
from app.models.wallet import Wallet
from app.schemas.wallet import WalletCreate, WalletCreateResponse


class WalletService:
    """Creates wallets (M-PESA paybills) under a company."""

    def __init__(
        self,
        session: AsyncSession,
        mpesa_client: MpesaClient | None = None,
    ):
        self.session = session
        self.mpesa = mpesa_client or MpesaClient()

    def _publish(self, event_type: str, payload: dict) -> None:
        """Publish event in thread so we don't block async loop."""
        pub = get_event_publisher()
        asyncio.to_thread(pub.publish, event_type, payload)

    async def create(self, company_id: UUID, data: WalletCreate) -> WalletCreateResponse | None:
        """
        Create wallet: call M-PESA POST /paybills, persist, publish wallet.created.
        """
        result = await self.session.execute(
            select(Company).where(Company.id == company_id).where(Company.is_active.is_(True)),
        )
        company = result.scalar_one_or_none()
        if not company:
            return None

        mpesa_resp = await self.mpesa.create_paybill(
            api_key=company.api_key,
            name=data.name,
            consumer_key=data.consumer_key,
            consumer_secret=data.consumer_secret,
            business_short_code=data.business_short_code,
            passkey=data.passkey,
            initiator_name=data.initiator_name,
            security_credential=data.security_credential,
            environment=data.environment,
        )
        credential_id = mpesa_resp.get("credential_id") or ""
        name = mpesa_resp.get("name") or data.name
        business_short_code = mpesa_resp.get("business_short_code") or data.business_short_code
        environment = mpesa_resp.get("environment") or data.environment

        wallet = Wallet(
            company_id=company_id,
            credential_id=credential_id,
            name=name,
            business_short_code=business_short_code,
            environment=environment,
        )
        self.session.add(wallet)
        await self.session.flush()
        await self.session.refresh(wallet)

        self._publish("wallet.created", {
            "wallet_id": str(wallet.id),
            "company_id": str(company_id),
            "credential_id": wallet.credential_id,
            "name": wallet.name,
            "business_short_code": wallet.business_short_code,
            "environment": wallet.environment,
            "created_at": wallet.created_at.isoformat(),
        })

        return WalletCreateResponse(
            credential_id=wallet.credential_id,
            name=wallet.name,
            business_short_code=wallet.business_short_code,
            environment=wallet.environment,
            created_at=wallet.created_at,
            updated_at=wallet.updated_at,
        )
