from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel


class OrganizationBase(BaseModel):
    name: str
    industry: str | None = None
    size: str | None = None
    website: str | None = None
    segment: str | None = None
    source: str | None = None
    tags: list[str] = []


class OrganizationCreate(OrganizationBase):
    pass


class OrganizationUpdate(BaseModel):
    name: str | None = None
    industry: str | None = None
    size: str | None = None
    website: str | None = None
    segment: str | None = None
    source: str | None = None
    tags: list[str] | None = None
    status: str | None = None
    primary_contact_id: str | None = None
    billing_contact_id: str | None = None


class ContactSummary(BaseModel):
    id: str
    first_name: str
    last_name: str | None = None
    email: str | None = None

    class Config:
        from_attributes = True


class OrganizationResponse(OrganizationBase):
    id: str
    status: str
    lifetime_value: Decimal
    primary_contact_id: str | None = None
    billing_contact_id: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OrganizationWithContacts(OrganizationResponse):
    primary_contact: ContactSummary | None = None
    billing_contact: ContactSummary | None = None
    contact_count: int = 0


class OrganizationList(BaseModel):
    items: list[OrganizationResponse]
    total: int
    page: int
    size: int
