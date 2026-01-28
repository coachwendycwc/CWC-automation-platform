from datetime import datetime
from pydantic import BaseModel, Field, EmailStr
from typing import Literal

from app.schemas.booking_type import BookingTypeResponse
from app.schemas.contact import ContactResponse


class BookingBase(BaseModel):
    notes: str | None = None


class BookingCreate(BookingBase):
    """For admin creating bookings."""
    booking_type_id: str
    contact_id: str
    start_time: datetime


class PublicBookingCreate(BaseModel):
    """For public booking flow (creates contact if needed)."""
    start_time: datetime
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=50)
    notes: str | None = None


class BookingUpdate(BaseModel):
    notes: str | None = None
    status: Literal["pending", "confirmed", "completed", "cancelled", "no_show"] | None = None


class BookingResponse(BookingBase):
    id: str
    booking_type_id: str
    contact_id: str
    start_time: datetime
    end_time: datetime
    status: str
    google_event_id: str | None
    zoom_meeting_id: str | None = None
    zoom_meeting_url: str | None = None
    zoom_meeting_password: str | None = None
    cancellation_reason: str | None
    cancelled_at: datetime | None
    cancelled_by: str | None
    confirmation_token: str
    reminder_24h_sent_at: datetime | None = None
    reminder_1h_sent_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BookingDetailResponse(BookingResponse):
    """Booking with related booking type and contact info."""
    booking_type: BookingTypeResponse
    contact: ContactResponse


class BookingList(BaseModel):
    items: list[BookingDetailResponse]
    total: int


# Public booking management (token-based)

class PublicBookingResponse(BaseModel):
    """Limited info for public view."""
    id: str
    start_time: datetime
    end_time: datetime
    status: str
    booking_type_name: str
    booking_type_duration: int
    can_cancel: bool  # Based on 24hr policy
    can_reschedule: bool


class RescheduleRequest(BaseModel):
    new_start_time: datetime


class CancelRequest(BaseModel):
    reason: str | None = None


# Available slots

class TimeSlot(BaseModel):
    start_time: datetime
    end_time: datetime
    available: bool = True


class AvailableSlotsResponse(BaseModel):
    date: str  # ISO date string
    slots: list[TimeSlot]


class PublicBookingTypeInfo(BaseModel):
    """Public-facing booking type info."""
    name: str
    slug: str
    description: str | None
    duration_minutes: int
    price: float | None
    min_notice_hours: int
    max_advance_days: int
