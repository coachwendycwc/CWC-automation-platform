from datetime import datetime, date
from pydantic import BaseModel, Field, field_validator
import re


class AvailabilityBase(BaseModel):
    day_of_week: int = Field(..., ge=0, le=6)  # 0=Monday, 6=Sunday
    start_time: str = Field(..., pattern=r"^\d{2}:\d{2}$")  # "09:00"
    end_time: str = Field(..., pattern=r"^\d{2}:\d{2}$")  # "17:00"
    is_active: bool = True

    @field_validator("start_time", "end_time")
    @classmethod
    def validate_time_format(cls, v: str) -> str:
        hours, minutes = v.split(":")
        if not (0 <= int(hours) <= 23 and 0 <= int(minutes) <= 59):
            raise ValueError("Invalid time format")
        return v


class AvailabilityCreate(AvailabilityBase):
    pass


class AvailabilityResponse(AvailabilityBase):
    id: str
    user_id: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AvailabilityBulkUpdate(BaseModel):
    """For updating the entire weekly schedule at once."""
    availabilities: list[AvailabilityCreate]


class WeeklyAvailabilityResponse(BaseModel):
    """Weekly schedule grouped by day."""
    monday: list[AvailabilityResponse] = []
    tuesday: list[AvailabilityResponse] = []
    wednesday: list[AvailabilityResponse] = []
    thursday: list[AvailabilityResponse] = []
    friday: list[AvailabilityResponse] = []
    saturday: list[AvailabilityResponse] = []
    sunday: list[AvailabilityResponse] = []


# Availability Overrides

class AvailabilityOverrideBase(BaseModel):
    date: date
    start_time: str | None = Field(default=None, pattern=r"^\d{2}:\d{2}$")
    end_time: str | None = Field(default=None, pattern=r"^\d{2}:\d{2}$")
    is_available: bool = False
    reason: str | None = None

    @field_validator("start_time", "end_time")
    @classmethod
    def validate_time_format(cls, v: str | None) -> str | None:
        if v is None:
            return v
        hours, minutes = v.split(":")
        if not (0 <= int(hours) <= 23 and 0 <= int(minutes) <= 59):
            raise ValueError("Invalid time format")
        return v


class AvailabilityOverrideCreate(AvailabilityOverrideBase):
    pass


class AvailabilityOverrideResponse(AvailabilityOverrideBase):
    id: str
    user_id: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AvailabilityOverrideList(BaseModel):
    items: list[AvailabilityOverrideResponse]
    total: int
