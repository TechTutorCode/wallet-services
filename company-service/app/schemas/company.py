"""Company request/response schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CompanyCreate(BaseModel):
    """Request body for creating a company."""

    name: str = Field(..., min_length=1, max_length=255)


class CompanyCreateResponse(BaseModel):
    """Response after creating a company."""

    model_config = ConfigDict(from_attributes=True)

    name: str
    account_number: str
    api_key: str
    callback_url: str
    created_at: datetime


class CompanyUpdate(BaseModel):
    """Request body for updating a company."""

    name: str | None = Field(None, min_length=1, max_length=255)


class CompanyListItem(BaseModel):
    """Company item in list response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    account_number: str
    callback_url: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
