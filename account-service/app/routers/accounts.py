from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.schemas.account import AccountCreate, AccountCreateResponse, AccountListItem
from app.services.account_service import AccountService

router = APIRouter(tags=["accounts"])


@router.post("/accounts", response_model=AccountCreateResponse)
async def create_account(data: AccountCreate, session: AsyncSession = Depends(get_db)):
    try:
        svc = AccountService(session)
        return await svc.create_account(data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/wallets/{wallet_id}/accounts", response_model=list[AccountListItem])
async def list_accounts_by_wallet(wallet_id: UUID, session: AsyncSession = Depends(get_db)):
    svc = AccountService(session)
    return await svc.list_by_wallet(wallet_id)


@router.delete("/accounts/{account_id}")
async def soft_delete_account(account_id: UUID, session: AsyncSession = Depends(get_db)):
    svc = AccountService(session)
    account = await svc.soft_delete(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return {"message": "Account deactivated", "account_id": str(account.id)}
