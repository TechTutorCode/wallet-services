"""Wallet request/response schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class WalletCreate(BaseModel):
    """Request body for creating a wallet under a company."""

    name: str = Field(..., min_length=1, max_length=255)
    consumer_key: str = Field(..., min_length=1)
    consumer_secret: str = Field(..., min_length=1)
    business_short_code: str = Field(..., min_length=1, max_length=32)
    passkey: str = Field(..., min_length=1)
    initiator_name: str = Field(..., min_length=1)
    security_credential: str = Field(..., min_length=1)
    environment: str = Field(..., min_length=1, max_length=32)


class WalletCreateResponse(BaseModel):
    """Response after creating a wallet (from M-PESA + stored fields)."""

    model_config = ConfigDict(from_attributes=True)

    credential_id: str
    name: str
    business_short_code: str
    environment: str
    created_at: datetime
    updated_at: datetime
