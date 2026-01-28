"""Pydantic schemas for client notes."""
from datetime import datetime
from typing import Optional, List, Literal
from pydantic import BaseModel, Field


# Admin schemas
class NoteCreate(BaseModel):
    """Create a note to a client (admin only)."""
    contact_id: str
    content: str = Field(..., min_length=1)


class NoteReply(BaseModel):
    """Reply to a note."""
    content: str = Field(..., min_length=1)


class NoteResponse(BaseModel):
    """Note response for admin."""
    id: str
    contact_id: str
    contact_name: str
    content: str
    direction: Literal["to_coach", "to_client"]
    parent_id: Optional[str] = None
    is_read: bool
    read_at: Optional[datetime] = None
    created_at: datetime
    replies: List["NoteResponse"] = []

    class Config:
        from_attributes = True


class NoteList(BaseModel):
    """Paginated note list."""
    items: List[NoteResponse]
    total: int
    page: int
    size: int


class UnreadCount(BaseModel):
    """Unread notes count."""
    count: int


# Client portal schemas
class ClientNoteCreate(BaseModel):
    """Create a note to coach (client only)."""
    content: str = Field(..., min_length=1)


class ClientNoteResponse(BaseModel):
    """Note response for client portal."""
    id: str
    content: str
    direction: Literal["to_coach", "to_client"]
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Rebuild for forward references
NoteResponse.model_rebuild()
