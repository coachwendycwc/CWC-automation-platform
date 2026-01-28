import uuid
from datetime import datetime, date
from typing import TYPE_CHECKING

from sqlalchemy import String, Integer, Boolean, DateTime, Date, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class Availability(Base):
    """Weekly recurring availability slots."""

    __tablename__ = "availabilities"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    day_of_week: Mapped[int] = mapped_column(
        Integer, nullable=False
    )  # 0=Monday, 6=Sunday
    start_time: Mapped[str] = mapped_column(String(5), nullable=False)  # "09:00"
    end_time: Mapped[str] = mapped_column(String(5), nullable=False)  # "17:00"
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="availabilities")

    def __repr__(self) -> str:
        return f"<Availability day={self.day_of_week} {self.start_time}-{self.end_time}>"


class AvailabilityOverride(Base):
    """Date-specific availability overrides (block days or add extra hours)."""

    __tablename__ = "availability_overrides"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[str | None] = mapped_column(
        String(5), nullable=True
    )  # null = blocked all day
    end_time: Mapped[str | None] = mapped_column(String(5), nullable=True)
    is_available: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )  # false = blocked
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="availability_overrides")

    def __repr__(self) -> str:
        return f"<AvailabilityOverride {self.date} available={self.is_available}>"
