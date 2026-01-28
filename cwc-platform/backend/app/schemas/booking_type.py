from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator
import re


class BookingTypeBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    slug: str = Field(..., min_length=1, max_length=100)
    description: str | None = None
    duration_minutes: int = Field(default=60, ge=15, le=480)
    color: str = Field(default="#3B82F6", pattern=r"^#[0-9A-Fa-f]{6}$")
    price: Decimal | None = None
    buffer_before: int = Field(default=0, ge=0, le=120)
    buffer_after: int = Field(default=15, ge=0, le=120)
    min_notice_hours: int = Field(default=24, ge=0, le=720)
    max_advance_days: int = Field(default=60, ge=1, le=365)
    max_per_day: int | None = Field(default=None, ge=1, le=20)
    requires_confirmation: bool = False
    is_active: bool = True

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        if not re.match(r"^[a-z0-9-]+$", v):
            raise ValueError("Slug must contain only lowercase letters, numbers, and hyphens")
        return v


class BookingTypeCreate(BookingTypeBase):
    pass


class BookingTypeUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    slug: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None
    duration_minutes: int | None = Field(default=None, ge=15, le=480)
    color: str | None = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")
    price: Decimal | None = None
    buffer_before: int | None = Field(default=None, ge=0, le=120)
    buffer_after: int | None = Field(default=None, ge=0, le=120)
    min_notice_hours: int | None = Field(default=None, ge=0, le=720)
    max_advance_days: int | None = Field(default=None, ge=1, le=365)
    max_per_day: int | None = Field(default=None, ge=1, le=20)
    requires_confirmation: bool | None = None
    is_active: bool | None = None

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str | None) -> str | None:
        if v is not None and not re.match(r"^[a-z0-9-]+$", v):
            raise ValueError("Slug must contain only lowercase letters, numbers, and hyphens")
        return v


class BookingTypeResponse(BookingTypeBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BookingTypeList(BaseModel):
    items: list[BookingTypeResponse]
    total: int
