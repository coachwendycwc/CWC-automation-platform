"""Pydantic schemas for testimonials."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


# Admin schemas
class TestimonialBase(BaseModel):
    """Base testimonial schema."""

    author_name: str
    author_title: Optional[str] = None
    author_company: Optional[str] = None
    quote: Optional[str] = None


class TestimonialCreate(TestimonialBase):
    """Schema for creating a testimonial request."""

    contact_id: Optional[str] = None
    organization_id: Optional[str] = None


class TestimonialUpdate(BaseModel):
    """Schema for updating a testimonial."""

    author_name: Optional[str] = None
    author_title: Optional[str] = None
    author_company: Optional[str] = None
    author_photo_url: Optional[str] = None
    quote: Optional[str] = None
    transcript: Optional[str] = None
    status: Optional[str] = None  # pending, approved, rejected
    featured: Optional[bool] = None
    display_order: Optional[int] = None


class TestimonialResponse(TestimonialBase):
    """Schema for testimonial response."""

    id: str
    contact_id: Optional[str] = None
    organization_id: Optional[str] = None
    contact_name: Optional[str] = None
    organization_name: Optional[str] = None

    # Video content
    video_url: Optional[str] = None
    video_public_id: Optional[str] = None
    video_duration_seconds: Optional[int] = None
    thumbnail_url: Optional[str] = None

    # Text content
    transcript: Optional[str] = None
    author_photo_url: Optional[str] = None

    # Permissions & Status
    permission_granted: bool
    status: str
    featured: bool
    display_order: int

    # Request tracking
    request_token: str
    request_sent_at: Optional[datetime] = None
    submitted_at: Optional[datetime] = None
    reviewed_at: Optional[datetime] = None

    # Computed
    has_video: bool = False

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TestimonialList(BaseModel):
    """Schema for paginated testimonial list."""

    items: List[TestimonialResponse]
    total: int
    page: int
    size: int


# Public submission schemas
class TestimonialRequestInfo(BaseModel):
    """Schema for public testimonial request info."""

    id: str
    author_name: str
    author_title: Optional[str] = None
    author_company: Optional[str] = None
    status: str
    already_submitted: bool = False


class TestimonialSubmit(BaseModel):
    """Schema for submitting a testimonial."""

    author_name: str
    author_title: Optional[str] = None
    author_company: Optional[str] = None
    author_photo_url: Optional[str] = None
    quote: Optional[str] = None
    video_url: Optional[str] = None
    video_public_id: Optional[str] = None
    video_duration_seconds: Optional[int] = None
    thumbnail_url: Optional[str] = None
    permission_granted: bool = True


class TestimonialSubmitResponse(BaseModel):
    """Schema for testimonial submission response."""

    id: str
    message: str


# Public gallery schemas
class TestimonialPublic(BaseModel):
    """Schema for public gallery testimonial."""

    id: str
    author_name: str
    author_title: Optional[str] = None
    author_company: Optional[str] = None
    author_photo_url: Optional[str] = None
    quote: Optional[str] = None
    video_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    video_duration_seconds: Optional[int] = None
    featured: bool = False

    class Config:
        from_attributes = True


class TestimonialGallery(BaseModel):
    """Schema for public gallery response."""

    featured: List[TestimonialPublic]
    items: List[TestimonialPublic]
    total: int


# Upload schemas
class VideoUploadSignature(BaseModel):
    """Schema for Cloudinary upload signature."""

    signature: str
    timestamp: int
    cloud_name: str
    api_key: str
    folder: str


class VideoUploadResponse(BaseModel):
    """Schema for video upload response."""

    url: str
    public_id: str
    duration: int
    thumbnail_url: Optional[str] = None


# Email request schema
class TestimonialSendRequest(BaseModel):
    """Schema for sending testimonial request email."""

    custom_message: Optional[str] = None
