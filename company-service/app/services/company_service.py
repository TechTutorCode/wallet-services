"""Company domain service: create, update, list, soft-delete."""

import asyncio
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.mpesa_client import MpesaClient, MpesaClientError
from app.events.publisher import get_event_publisher
from app.models.company import Company
from app.schemas.company import CompanyCreate, CompanyCreateResponse, CompanyUpdate


class CompanyServiceError(Exception):
    """Company service error."""

    pass


class CompanyService:
    """Handles company CRUD and M-PESA app sync."""

    def __init__(
        self,
        session: AsyncSession,
        mpesa_client: MpesaClient | None = None,
    ):
        self.session = session
        self.mpesa = mpesa_client or MpesaClient()

    async def _publish(self, event_type: str, payload: dict) -> None:
        """Publish event in thread so we don't block async loop."""
        pub = get_event_publisher()
        await asyncio.to_thread(pub.publish, event_type, payload)

    async def create(self, data: CompanyCreate) -> CompanyCreateResponse:
        """
        Create company: call M-PESA POST /apps, persist, publish company.created.
        """
        mpesa_resp = await self.mpesa.create_app(name=data.name)
        account_number = mpesa_resp.get("account_number") or ""
        api_key = mpesa_resp.get("api_key") or ""
        callback_url = mpesa_resp.get("callback_url") or ""

        company = Company(
            name=data.name,
            account_number=account_number,
            api_key=api_key,
            callback_url=callback_url,
        )
        self.session.add(company)
        await self.session.flush()
        await self.session.refresh(company)

        await self._publish("company.created", {
            "company_id": str(company.id),
            "name": company.name,
            "account_number": company.account_number,
            "callback_url": company.callback_url,
            "created_at": company.created_at.isoformat(),
        })

        return CompanyCreateResponse(
            name=company.name,
            account_number=company.account_number,
            api_key=company.api_key,
            callback_url=company.callback_url,
            created_at=company.created_at,
        )

    async def update(self, company_id: UUID, data: CompanyUpdate) -> Company | None:
        """
        Update company: call M-PESA PATCH /apps, update DB, publish company.updated.
        """
        result = await self.session.execute(
            select(Company).where(Company.id == company_id).where(Company.is_active.is_(True)),
        )
        company = result.scalar_one_or_none()
        if not company:
            return None
        if data.name is None:
            return company

        await self.mpesa.update_app(api_key=company.api_key, name=data.name)
        company.name = data.name
        await self.session.flush()
        await self.session.refresh(company)

        await self._publish("company.updated", {
            "company_id": str(company.id),
            "name": company.name,
            "account_number": company.account_number,
            "callback_url": company.callback_url,
            "updated_at": company.updated_at.isoformat(),
        })
        return company

    async def list_active(
        self,
        skip: int = 0,
        limit: int = 20,
    ) -> list[Company]:
        """List companies with is_active=True, paginated."""
        result = await self.session.execute(
            select(Company)
            .where(Company.is_active.is_(True))
            .order_by(Company.created_at.desc())
            .offset(skip)
            .limit(limit),
        )
        return list(result.scalars().all())

    async def count_active(self) -> int:
        """Count active companies (for pagination total)."""
        from sqlalchemy import func
        result = await self.session.execute(
            select(func.count()).select_from(Company).where(Company.is_active.is_(True)),
        )
        return result.scalar() or 0

    async def soft_delete(self, company_id: UUID) -> Company | None:
        """Set is_active=False, deleted_at=NOW(), publish company.deleted."""
        result = await self.session.execute(
            select(Company).where(Company.id == company_id).where(Company.is_active.is_(True)),
        )
        company = result.scalar_one_or_none()
        if not company:
            return None
        now = datetime.now(timezone.utc)
        company.is_active = False
        company.deleted_at = now
        await self.session.flush()
        await self.session.refresh(company)

        await self._publish("company.deleted", {
            "company_id": str(company.id),
            "name": company.name,
            "deleted_at": now.isoformat(),
        })
        return company
