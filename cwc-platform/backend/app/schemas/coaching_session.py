from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional


class CoachingSessionCreate(BaseModel):
    contact_id: Optional[str] = None
    client_name: str
    client_email: Optional[str] = None
    session_date: date
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_hours: float = 1.0
    session_type: str = "individual"  # individual, group
    group_size: Optional[int] = None
    payment_type: str = "paid"  # paid, pro_bono
    source: str = "manual"  # manual, google_calendar, zoom, honeybook
    external_id: Optional[str] = None
    meeting_title: Optional[str] = None
    notes: Optional[str] = None
    is_verified: bool = False


class CoachingSessionUpdate(BaseModel):
    contact_id: Optional[str] = None
    client_name: Optional[str] = None
    client_email: Optional[str] = None
    session_date: Optional[date] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_hours: Optional[float] = None
    session_type: Optional[str] = None
    group_size: Optional[int] = None
    payment_type: Optional[str] = None
    meeting_title: Optional[str] = None
    notes: Optional[str] = None
    is_verified: Optional[bool] = None


class CoachingSessionResponse(BaseModel):
    id: str
    contact_id: Optional[str]
    client_name: str
    client_email: Optional[str]
    session_date: date
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    duration_hours: float
    session_type: str
    group_size: Optional[int]
    payment_type: str
    source: str
    external_id: Optional[str]
    meeting_title: Optional[str]
    notes: Optional[str]
    is_verified: bool
    created_at: datetime
    updated_at: datetime

    # Joined fields
    contact_name: Optional[str] = None

    model_config = {"from_attributes": True}


class CoachingSessionListResponse(BaseModel):
    items: list[CoachingSessionResponse]
    total: int
    page: int
    size: int


class ICFSummary(BaseModel):
    total_hours: float
    paid_hours: float
    pro_bono_hours: float
    individual_hours: float
    group_hours: float
    total_sessions: int
    total_clients: int
    verified_hours: float
    unverified_hours: float


class ClientHoursSummary(BaseModel):
    client_name: str
    contact_id: Optional[str]
    total_sessions: int
    total_hours: float
    paid_hours: float
    pro_bono_hours: float
    individual_hours: float
    group_hours: float
    first_session: Optional[date]
    last_session: Optional[date]


class ICFExportRow(BaseModel):
    client_number: int
    client_name: str
    contact_information: str
    individual_group: str
    number_in_group: Optional[int]
    session_date: date
    duration_hours: float
    paid_hours: float
    pro_bono_hours: float


class CalendarSyncRequest(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class CalendarSyncResponse(BaseModel):
    synced: int
    skipped: int
    errors: int
    message: str


class BulkImportRequest(BaseModel):
    sessions: list[CoachingSessionCreate]


class BulkImportResponse(BaseModel):
    imported: int
    skipped: int
    errors: list[str]
