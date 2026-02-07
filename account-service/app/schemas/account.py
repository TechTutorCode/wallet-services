from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AccountCreate(BaseModel):
    fullname: str = Field(..., min_length=1, max_length=255)
    wallet_id: UUID


class AccountCreateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    wallet_id: UUID
    fullname: str
    account_no: str


class AccountListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    wallet_id: UUID
    fullname: str
    account_no: str
    sequence_no: int
    is_active: bool
