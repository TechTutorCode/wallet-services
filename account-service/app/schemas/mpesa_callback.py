"""M-PESA callback body - adapt fields to your actual M-PESA payload."""

from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field


class MpesaCallbackPayload(BaseModel):
    """Typical M-PESA callback structure. Adjust to match your provider's schema."""

    # Common fields; M-PESA often nests under Body.stkCallback or similar
    BillRefNumber: str | None = Field(None, description="Account number (our account_no)")
    TransID: str | None = Field(None, description="Transaction id for idempotency")
    Amount: Decimal | None = None

    # Allow extra for flexibility
    model_config = {"extra": "allow"}

    def get_trans_id(self) -> str | None:
        return self.TransID

    def get_account_no(self) -> str | None:
        return self.BillRefNumber

    def get_amount(self) -> Decimal | None:
        return self.Amount


def parse_mpesa_callback(body: dict[str, Any]) -> tuple[str | None, str | None, Decimal | None]:
    """Extract trans_id, account_no, amount. Handles top-level or Body.stkCallback.CallbackMetadata.Item."""
    trans_id = body.get("TransID")
    account_no = body.get("BillRefNumber")
    amount = body.get("Amount")

    b = body.get("Body") if isinstance(body.get("Body"), dict) else None
    if b:
        sc = b.get("stkCallback") or b.get("CallbackMetadata")
        if isinstance(sc, dict):
            trans_id = trans_id or sc.get("TransID")
            account_no = account_no or b.get("BillRefNumber")
            meta = sc.get("CallbackMetadata") if isinstance(sc.get("CallbackMetadata"), dict) else None
            if meta:
                for item in (meta.get("Item") or []):
                    if not isinstance(item, dict):
                        continue
                    name, val = item.get("Name"), item.get("Value")
                    if name == "TransactionId":
                        trans_id = trans_id or (str(val) if val is not None else None)
                    elif name == "Amount":
                        amount = amount if amount is not None else val
                    elif name == "BillRefNumber":
                        account_no = account_no or (str(val) if val is not None else None)

    if amount is not None and not isinstance(amount, Decimal):
        amount = Decimal(str(amount))
    return (trans_id, account_no, amount)
