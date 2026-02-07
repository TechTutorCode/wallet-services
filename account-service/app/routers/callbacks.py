"""M-PESA callback: match BillRefNumber to account_no, idempotent, emit ledger.credit.requested."""

from decimal import Decimal

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.models.account import Account
from app.schemas.mpesa_callback import parse_mpesa_callback
from app.services.account_service import AccountService

router = APIRouter(prefix="/callbacks", tags=["callbacks"])


@router.post("/mpesa")
async def mpesa_callback(request: Request, session: AsyncSession = Depends(get_db)):
    body = await request.json()
    trans_id, account_no, amount = parse_mpesa_callback(body)
    if not trans_id or not account_no:
        return {"ResultCode": 1, "ResultDesc": "Missing TransID or BillRefNumber"}
    if amount is None:
        amount = Decimal("0")

    # Verify account exists
    r = await session.execute(select(Account).where(Account.account_no == account_no).where(Account.is_active.is_(True)))
    if not r.scalar_one_or_none():
        return {"ResultCode": 1, "ResultDesc": "Account not found"}

    svc = AccountService(session)
    recorded = await svc.record_payment_and_emit_credit(trans_id=trans_id, account_no=account_no, amount=amount)
    if not recorded:
        return {"ResultCode": 0, "ResultDesc": "Already processed"}

    return {"ResultCode": 0, "ResultDesc": "Success"}
