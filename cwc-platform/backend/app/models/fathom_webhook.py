import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, Text, Integer, DateTime, JSON, ForeignKey, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

if TYPE_CHECKING:
    from app.models.contact import Contact
    from app.models.booking import Booking


class FathomWebhook(Base):
    __tablename__ = "fathom_webhooks"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    recording_id: Mapped[str | None] = mapped_column(String(100), unique=True)
    meeting_title: Mapped[str | None] = mapped_column(String(255))

    # Recording URL from Fathom
    recording_url: Mapped[str | None] = mapped_column(String(500))

    transcript: Mapped[str | None] = mapped_column(Text)
    summary: Mapped[dict | None] = mapped_column(JSON)
    action_items: Mapped[list | None] = mapped_column(JSON)
    attendees: Mapped[list | None] = mapped_column(JSON)

    # Client homework/todos extracted from session
    homework: Mapped[list | None] = mapped_column(JSON)

    duration_seconds: Mapped[int | None] = mapped_column(Integer)
    recorded_at: Mapped[datetime | None] = mapped_column(DateTime)

    # Link to contact for client portal access
    contact_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("contacts.id", ondelete="SET NULL"), index=True
    )

    # Client visibility settings
    client_visible: Mapped[bool] = mapped_column(Boolean, default=True)

    processed_at: Mapped[datetime | None] = mapped_column(DateTime)
    processing_status: Mapped[str] = mapped_column(
        String(20), default="pending", index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    # Relationships
    contact: Mapped["Contact | None"] = relationship("Contact", back_populates="session_recordings")
    bookings: Mapped[list["Booking"]] = relationship("Booking", back_populates="fathom_webhook")
