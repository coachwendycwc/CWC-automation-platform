import uuid
import secrets
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, DateTime, Text, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.booking_type import BookingType
    from app.models.contact import Contact
    from app.models.fathom_webhook import FathomWebhook


class Booking(Base):
    """A scheduled booking/appointment."""

    __tablename__ = "bookings"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    booking_type_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("booking_types.id", ondelete="CASCADE"), nullable=False
    )
    contact_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False
    )
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending"
    )  # pending, confirmed, completed, cancelled, no_show
    google_event_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    zoom_meeting_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    zoom_meeting_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    zoom_meeting_password: Mapped[str | None] = mapped_column(String(50), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    cancellation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    cancelled_by: Mapped[str | None] = mapped_column(
        String(10), nullable=True
    )  # "client" or "host"
    confirmation_token: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True, default=lambda: secrets.token_urlsafe(32)
    )
    reminder_24h_sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    reminder_1h_sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    post_session_sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Link to session recording
    fathom_webhook_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("fathom_webhooks.id", ondelete="SET NULL"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    booking_type: Mapped["BookingType"] = relationship(
        "BookingType", back_populates="bookings"
    )
    contact: Mapped["Contact"] = relationship("Contact", back_populates="bookings")
    fathom_webhook: Mapped["FathomWebhook | None"] = relationship(
        "FathomWebhook", back_populates="bookings"
    )

    def __repr__(self) -> str:
        return f"<Booking {self.id} {self.status}>"
