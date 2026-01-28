"""Schemas for client action items."""
from datetime import datetime, date
from typing import Optional, Literal
from pydantic import BaseModel


# ============ Admin Schemas ============

class ActionItemCreate(BaseModel):
    """Create action item (admin)."""
    contact_id: str
    session_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    due_date: Optional[date] = None
    priority: Literal["low", "medium", "high"] = "medium"


class ActionItemUpdate(BaseModel):
    """Update action item (admin)."""
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[date] = None
    priority: Optional[Literal["low", "medium", "high"]] = None
    status: Optional[Literal["pending", "in_progress", "completed", "skipped"]] = None


class ActionItemResponse(BaseModel):
    """Action item response (admin)."""
    id: str
    contact_id: str
    contact_name: str
    session_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    due_date: Optional[date] = None
    priority: str
    status: str
    completed_at: Optional[datetime] = None
    created_by: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ActionItemList(BaseModel):
    """Paginated action item list."""
    items: list[ActionItemResponse]
    total: int
    page: int
    size: int


# ============ Client Portal Schemas ============

class ClientActionItemResponse(BaseModel):
    """Action item response for client portal."""
    id: str
    title: str
    description: Optional[str] = None
    due_date: Optional[date] = None
    priority: str
    status: str
    completed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ClientActionItemStatusUpdate(BaseModel):
    """Update action item status (client)."""
    status: Literal["completed", "skipped", "in_progress"]
