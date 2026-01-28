from datetime import datetime
from pydantic import BaseModel, EmailStr
from typing import Literal


ContactType = Literal["lead", "client", "past_client", "partner"]
CoachingType = Literal["executive", "life", "group"]


class ContactBase(BaseModel):
    first_name: str
    last_name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    role: str | None = None
    title: str | None = None
    contact_type: ContactType = "lead"
    coaching_type: CoachingType | None = None
    tags: list[str] = []
    source: str | None = None


class ContactCreate(ContactBase):
    organization_id: str | None = None


class ContactUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    organization_id: str | None = None
    role: str | None = None
    title: str | None = None
    contact_type: ContactType | None = None
    coaching_type: CoachingType | None = None
    tags: list[str] | None = None
    source: str | None = None


class OrganizationSummary(BaseModel):
    id: str
    name: str

    class Config:
        from_attributes = True


class ContactResponse(ContactBase):
    id: str
    organization_id: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ContactWithOrganization(ContactResponse):
    organization: OrganizationSummary | None = None


class ContactList(BaseModel):
    items: list[ContactResponse]
    total: int
    page: int
    size: int
