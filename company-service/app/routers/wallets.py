"""Wallet API endpoints (under companies)."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.mpesa_client import MpesaClientError
from app.dependencies import get_db
from app.schemas.wallet import WalletCreate, WalletCreateResponse
from app.services.wallet_service import WalletService

router = APIRouter(prefix="/companies", tags=["wallets"])


@router.post("/{company_id}/wallets", response_model=WalletCreateResponse)
async def create_wallet(
    company_id: UUID,
    data: WalletCreate,
    session: AsyncSession = Depends(get_db),
):
    """
    Create a wallet under a company. Calls M-PESA POST /paybills, persists, publishes wallet.created.
    """
    service = WalletService(session=session)
    try:
        result = await service.create(company_id, data)
    except MpesaClientError as e:
        raise HTTPException(
            status_code=502 if e.status_code and e.status_code >= 500 else 422,
            detail=f"M-PESA error: {e!s}",
        )
    if result is None:
        raise HTTPException(status_code=404, detail="Company not found or inactive")
    return result
