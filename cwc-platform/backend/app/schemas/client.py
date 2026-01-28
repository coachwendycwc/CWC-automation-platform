"""Pydantic schemas for client portal."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field


# Auth schemas
class MagicLinkRequest(BaseModel):
    """Request for magic link login."""
    email: EmailStr


class MagicLinkResponse(BaseModel):
    """Response for magic link request."""
    message: str


class VerifyTokenRequest(BaseModel):
    """Request to verify magic link token."""
    token: str


class ClientSession(BaseModel):
    """Client session response."""
    session_token: str
    contact: "ClientContact"


class ClientContact(BaseModel):
    """Client contact info."""
    id: str
    first_name: str
    last_name: Optional[str] = None
    email: Optional[str] = None
    organization_id: Optional[str] = None
    organization_name: Optional[str] = None
    organization_logo_url: Optional[str] = None
    is_org_admin: bool = False


# Dashboard schemas
class DashboardStats(BaseModel):
    """Dashboard statistics."""
    unpaid_invoices: int
    total_due: float
    upcoming_bookings: int
    active_projects: int
    pending_contracts: int


class DashboardResponse(BaseModel):
    """Dashboard response with stats and recent items."""
    stats: DashboardStats
    recent_invoices: List["ClientInvoiceSummary"]
    upcoming_bookings: List["ClientBookingSummary"]


# Invoice schemas
class ClientInvoiceSummary(BaseModel):
    """Invoice summary for list view."""
    id: str
    invoice_number: str
    created_at: datetime
    due_date: datetime
    total: float
    balance_due: float
    status: str
    contact_name: Optional[str] = None  # For org view


class ClientInvoiceDetail(ClientInvoiceSummary):
    """Invoice detail with line items."""
    line_items: List["ClientLineItem"]
    payments: List["ClientPaymentSummary"]
    view_token: str


class ClientLineItem(BaseModel):
    """Invoice line item."""
    description: str
    quantity: float
    unit_price: float
    amount: float


class ClientPaymentSummary(BaseModel):
    """Payment summary."""
    id: str
    amount: float
    payment_date: datetime
    payment_method: Optional[str] = None


# Contract schemas
class ClientContractSummary(BaseModel):
    """Contract summary for list view."""
    id: str
    contract_number: str
    title: str
    status: str
    created_at: datetime
    signed_at: Optional[datetime] = None
    contact_name: Optional[str] = None  # For org view


class ClientContractDetail(ClientContractSummary):
    """Contract detail."""
    content: str
    expires_at: Optional[datetime] = None
    view_token: str


# Booking schemas
class ClientBookingSummary(BaseModel):
    """Booking summary for list view."""
    id: str
    booking_type_name: str
    start_time: datetime
    end_time: datetime
    status: str
    meeting_link: Optional[str] = None


class ClientBookingDetail(ClientBookingSummary):
    """Booking detail."""
    notes: Optional[str] = None
    can_cancel: bool


# Project schemas
class ClientProjectSummary(BaseModel):
    """Project summary for list view."""
    id: str
    name: str
    status: str
    progress: float
    created_at: datetime
    contact_name: Optional[str] = None  # For org view


class ClientProjectDetail(ClientProjectSummary):
    """Project detail with tasks."""
    description: Optional[str] = None
    tasks: List["ClientTaskSummary"]


class ClientTaskSummary(BaseModel):
    """Task summary."""
    id: str
    title: str
    status: str
    due_date: Optional[datetime] = None


# Session Recording schemas
class ClientSessionRecordingSummary(BaseModel):
    """Session recording summary for list view."""
    id: str
    meeting_title: Optional[str] = None
    recorded_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    has_recording: bool
    has_transcript: bool
    has_summary: bool
    has_homework: bool
    contact_name: Optional[str] = None  # For org view


class ClientHomeworkItem(BaseModel):
    """Homework item from a session."""
    description: str
    completed: bool = False


class ClientSessionRecordingDetail(BaseModel):
    """Session recording detail with video, transcript, summary, homework."""
    id: str
    meeting_title: Optional[str] = None
    recorded_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    recording_url: Optional[str] = None
    transcript: Optional[str] = None
    summary: Optional[dict] = None
    action_items: Optional[List[str]] = None
    homework: Optional[List[ClientHomeworkItem]] = None


# Profile schemas
class ClientProfile(BaseModel):
    """Client profile."""
    id: str
    first_name: str
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    organization_name: Optional[str] = None
    is_org_admin: bool = False


class ClientProfileUpdate(BaseModel):
    """Client profile update request."""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=50)


# Organization schemas (for org admins)
class OrgBillingSummary(BaseModel):
    """Organization billing summary."""
    total_invoiced: float
    total_paid: float
    total_outstanding: float
    invoice_count: int


class OrgUsageStats(BaseModel):
    """Organization usage statistics (no session content, just counts)."""
    total_employees: int
    employees_with_sessions: int
    total_sessions_completed: int
    total_sessions_upcoming: int
    total_coaching_hours: float


class OrgEmployeeSummary(BaseModel):
    """Employee summary for org admin view (no session content)."""
    id: str
    first_name: str
    last_name: Optional[str] = None
    email: Optional[str] = None
    sessions_completed: int
    sessions_upcoming: int
    last_session_date: Optional[datetime] = None


class OrgDashboardResponse(BaseModel):
    """Organization dashboard for org admins."""
    organization_name: str
    organization_id: str
    billing: OrgBillingSummary
    usage: OrgUsageStats
    recent_invoices: List[ClientInvoiceSummary]
    pending_contracts: int


# Content delivery schemas
class ClientContentSummary(BaseModel):
    """Content item summary for list view."""
    id: str
    title: str
    description: Optional[str] = None
    content_type: str  # file, link, video, document
    category: Optional[str] = None
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    external_url: Optional[str] = None
    release_date: Optional[datetime] = None
    is_released: bool
    created_at: datetime


class ClientContentDetail(ClientContentSummary):
    """Content item detail with download URL."""
    file_url: Optional[str] = None
    mime_type: Optional[str] = None


class ClientContentCategory(BaseModel):
    """Content category with items."""
    name: str
    items: List[ClientContentSummary]


# Update forward references
ClientSession.model_rebuild()
DashboardResponse.model_rebuild()
ClientInvoiceDetail.model_rebuild()
ClientProjectDetail.model_rebuild()
OrgDashboardResponse.model_rebuild()
