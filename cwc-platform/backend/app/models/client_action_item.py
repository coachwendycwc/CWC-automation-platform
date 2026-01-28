"""Client Action Item model for coach-assigned tasks."""
import uuid
from datetime import datetime, date
from typing import Optional, TYPE_CHECKING

from sqlalchemy import String, Text, Date, DateTime, ForeignKey, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.contact import Contact
    from app.models.fathom_webhook import FathomWebhook


class ClientActionItem(Base):
    """Action items/homework assigned to clients by coach."""

    __tablename__ = "client_action_items"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    contact_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("contacts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    session_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("fathom_webhooks.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Content
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    priority: Mapped[str] = mapped_column(String(20), default="medium")  # low, medium, high

    # Status
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, in_progress, completed, skipped
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Reminder tracking
    reminder_sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    overdue_reminder_sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Tracking
    created_by: Mapped[str] = mapped_column(String(50), default="coach")  # coach, session_extraction
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    contact: Mapped["Contact"] = relationship("Contact", back_populates="action_items")
    session: Mapped[Optional["FathomWebhook"]] = relationship("FathomWebhook")
