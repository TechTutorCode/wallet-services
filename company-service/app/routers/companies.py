"""Company API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.mpesa_client import MpesaClientError
from app.dependencies import get_db
from app.schemas.company import (
    CompanyCreate,
    CompanyCreateResponse,
    CompanyListItem,
    CompanyUpdate,
)
from app.services.company_service import CompanyService

router = APIRouter(prefix="/companies", tags=["companies"])


@router.post("", response_model=CompanyCreateResponse)
async def create_company(
    data: CompanyCreate,
    session: AsyncSession = Depends(get_db),
):
    """
    Create a company. Calls M-PESA to register app, persists company, publishes company.created.
    """
    service = CompanyService(session=session)
    try:
        return await service.create(data)
    except MpesaClientError as e:
        raise HTTPException(
            status_code=502 if e.status_code and e.status_code >= 500 else 422,
            detail=f"M-PESA error: {e!s}",
        )


@router.patch("/{company_id}")
async def update_company(
    company_id: UUID,
    data: CompanyUpdate,
    session: AsyncSession = Depends(get_db),
):
    """
    Update a company. Syncs to M-PESA, updates DB, publishes company.updated.
    """
    service = CompanyService(session=session)
    try:
        company = await service.update(company_id, data)
    except MpesaClientError as e:
        raise HTTPException(
            status_code=502 if e.status_code and e.status_code >= 500 else 422,
            detail=f"M-PESA error: {e!s}",
        )
    if company is None:
        raise HTTPException(status_code=404, detail="Company not found")
    return {
        "id": str(company.id),
        "name": company.name,
        "account_number": company.account_number,
        "callback_url": company.callback_url,
        "is_active": company.is_active,
        "updated_at": company.updated_at.isoformat(),
    }


@router.get("", response_model=dict)
async def list_companies(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_db),
):
    """
    List active companies (is_active=true), paginated.
    """
    service = CompanyService(session=session)
    items = await service.list_active(skip=skip, limit=limit)
    total = await service.count_active()
    return {
        "items": [CompanyListItem.model_validate(c) for c in items],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.delete("/{company_id}")
async def soft_delete_company(
    company_id: UUID,
    session: AsyncSession = Depends(get_db),
):
    """
    Soft-delete a company (is_active=false, deleted_at=NOW). Publishes company.deleted.
    """
    service = CompanyService(session=session)
    company = await service.soft_delete(company_id)
    if company is None:
        raise HTTPException(status_code=404, detail="Company not found")
    return {"message": "Company deleted", "company_id": str(company.id)}
