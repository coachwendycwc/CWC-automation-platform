import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import String, Integer, Boolean, DateTime, Text, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.booking import Booking


class BookingType(Base):
    """Defines types of bookings available (e.g., Coaching Session, Strategy Session)."""

    __tablename__ = "booking_types"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    color: Mapped[str] = mapped_column(String(7), nullable=False, default="#3B82F6")
    price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    buffer_before: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    buffer_after: Mapped[int] = mapped_column(Integer, nullable=False, default=15)
    min_notice_hours: Mapped[int] = mapped_column(Integer, nullable=False, default=24)
    max_advance_days: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    max_per_day: Mapped[int | None] = mapped_column(Integer, nullable=True)
    requires_confirmation: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    bookings: Mapped[list["Booking"]] = relationship(
        "Booking", back_populates="booking_type"
    )

    def __repr__(self) -> str:
        return f"<BookingType {self.name}>"
