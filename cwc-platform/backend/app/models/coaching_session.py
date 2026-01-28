import uuid
from datetime import datetime, date
from sqlalchemy import String, DateTime, Date, ForeignKey, Float, Boolean, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class CoachingSession(Base):
    """ICF Coaching Session tracking for certification hours."""

    __tablename__ = "coaching_sessions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )

    # Link to contact (optional - for unmatched calendar events)
    contact_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("contacts.id"), index=True
    )

    # Client info (for sessions without linked contact)
    client_name: Mapped[str] = mapped_column(String(255), nullable=False)
    client_email: Mapped[str | None] = mapped_column(String(255))

    # Session details
    session_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    start_time: Mapped[datetime | None] = mapped_column(DateTime)
    end_time: Mapped[datetime | None] = mapped_column(DateTime)
    duration_hours: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)

    # ICF classification
    session_type: Mapped[str] = mapped_column(
        String(20), default="individual", index=True
    )  # individual, group
    group_size: Mapped[int | None] = mapped_column()  # Number of participants if group

    # Payment classification
    payment_type: Mapped[str] = mapped_column(
        String(20), default="paid", index=True
    )  # paid, pro_bono

    # Source tracking
    source: Mapped[str] = mapped_column(
        String(50), default="manual", index=True
    )  # manual, google_calendar, zoom, honeybook
    external_id: Mapped[str | None] = mapped_column(String(255))  # Calendar event ID, etc.

    # Meeting details
    meeting_title: Mapped[str | None] = mapped_column(String(500))
    notes: Mapped[str | None] = mapped_column(Text)

    # Status
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    contact: Mapped["Contact | None"] = relationship(
        "Contact",
        back_populates="coaching_sessions",
    )


from app.models.contact import Contact
