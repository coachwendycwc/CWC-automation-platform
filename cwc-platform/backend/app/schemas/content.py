"""Pydantic schemas for content management (admin)."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class ContentCreate(BaseModel):
    """Create content request."""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    content_type: str = Field(default="file", pattern="^(file|document|video|link)$")
    file_url: Optional[str] = Field(None, max_length=500)
    file_name: Optional[str] = Field(None, max_length=255)
    file_size: Optional[int] = None
    mime_type: Optional[str] = Field(None, max_length=100)
    external_url: Optional[str] = Field(None, max_length=500)
    contact_id: Optional[str] = None
    organization_id: Optional[str] = None
    project_id: Optional[str] = None
    release_date: Optional[datetime] = None
    is_active: bool = True
    sort_order: int = 0
    category: Optional[str] = Field(None, max_length=100)


class ContentUpdate(BaseModel):
    """Update content request."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    content_type: Optional[str] = Field(None, pattern="^(file|document|video|link)$")
    file_url: Optional[str] = Field(None, max_length=500)
    file_name: Optional[str] = Field(None, max_length=255)
    file_size: Optional[int] = None
    mime_type: Optional[str] = Field(None, max_length=100)
    external_url: Optional[str] = Field(None, max_length=500)
    contact_id: Optional[str] = None
    organization_id: Optional[str] = None
    project_id: Optional[str] = None
    release_date: Optional[datetime] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None
    category: Optional[str] = Field(None, max_length=100)


class ContentResponse(BaseModel):
    """Content response."""
    id: str
    title: str
    description: Optional[str] = None
    content_type: str
    file_url: Optional[str] = None
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    external_url: Optional[str] = None
    contact_id: Optional[str] = None
    contact_name: Optional[str] = None
    organization_id: Optional[str] = None
    organization_name: Optional[str] = None
    project_id: Optional[str] = None
    project_name: Optional[str] = None
    release_date: Optional[datetime] = None
    is_released: bool
    is_active: bool
    sort_order: int
    category: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ContentList(BaseModel):
    """Paginated content list."""
    items: List[ContentResponse]
    total: int
    page: int
    size: int


class CategoryResponse(BaseModel):
    """Content category response."""
    categories: List[str]
