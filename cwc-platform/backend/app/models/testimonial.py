"""Testimonial model for video testimonials."""
import uuid
import secrets
from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import String, Text, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.contact import Contact
    from app.models.organization import Organization


def generate_request_token() -> str:
    """Generate a unique request token for testimonial submissions."""
    return secrets.token_urlsafe(32)


class Testimonial(Base):
    """Video testimonial from a client or organization."""

    __tablename__ = "testimonials"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )

    # Source - can be linked to contact and/or organization
    contact_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True
    )
    organization_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True
    )

    # Video content
    video_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    video_public_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )  # Cloudinary public ID
    video_duration_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Text content
    quote: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # Pull quote / key message
    transcript: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Author info (may differ from contact data)
    author_name: Mapped[str] = mapped_column(String(255), nullable=False)
    author_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    author_company: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    author_photo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Permissions & Status
    permission_granted: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(
        String(20), default="pending"
    )  # pending, approved, rejected
    featured: Mapped[bool] = mapped_column(Boolean, default=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0)

    # Request tracking
    request_token: Mapped[str] = mapped_column(
        String(64), unique=True, default=generate_request_token
    )
    request_sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    contact: Mapped[Optional["Contact"]] = relationship(back_populates="testimonials")
    organization: Mapped[Optional["Organization"]] = relationship(
        back_populates="testimonials"
    )

    @property
    def has_video(self) -> bool:
        """Check if testimonial has a video uploaded."""
        return bool(self.video_url)

    @property
    def is_approved(self) -> bool:
        """Check if testimonial is approved for display."""
        return self.status == "approved" and self.permission_granted

    @property
    def display_name(self) -> str:
        """Get the display name for the testimonial author."""
        parts = [self.author_name]
        if self.author_title:
            parts.append(self.author_title)
        if self.author_company:
            parts.append(self.author_company)
        return ", ".join(parts)
