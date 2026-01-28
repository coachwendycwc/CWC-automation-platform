"""Mileage tracking for business travel deductions."""
import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, TYPE_CHECKING

from sqlalchemy import String, DateTime, Date, Text, Numeric, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.contact import Contact


class MileageLog(Base):
    """Log of business miles driven."""

    __tablename__ = "mileage_logs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )

    # Trip details
    trip_date: Mapped[date] = mapped_column(Date, nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    purpose: Mapped[str] = mapped_column(
        String(50), default="client_meeting"
    )  # client_meeting, training, conference, errand, other

    # Mileage
    miles: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    rate_per_mile: Mapped[Decimal] = mapped_column(
        Numeric(6, 4), default=Decimal("0.67")  # 2024 IRS rate
    )
    total_deduction: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    # Locations
    start_location: Mapped[str | None] = mapped_column(String(200), nullable=True)
    end_location: Mapped[str | None] = mapped_column(String(200), nullable=True)
    round_trip: Mapped[bool] = mapped_column(default=False)

    # Link to client (optional)
    contact_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True
    )

    # Tax year
    tax_year: Mapped[int] = mapped_column(nullable=False)

    # Notes
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    contact: Mapped[Optional["Contact"]] = relationship("Contact")


class MileageRate(Base):
    """IRS mileage rates by year."""

    __tablename__ = "mileage_rates"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    year: Mapped[int] = mapped_column(unique=True, nullable=False)
    rate_per_mile: Mapped[Decimal] = mapped_column(Numeric(6, 4), nullable=False)
    effective_date: Mapped[date] = mapped_column(Date, nullable=False)
    notes: Mapped[str | None] = mapped_column(String(200), nullable=True)
