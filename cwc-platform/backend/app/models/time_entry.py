"""TimeEntry model for time tracking on tasks."""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, TYPE_CHECKING
import uuid

from sqlalchemy import String, Text, DateTime, Date, Numeric, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.task import Task


class TimeEntry(Base):
    """TimeEntry model for logging time on tasks."""

    __tablename__ = "time_entries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id: Mapped[str] = mapped_column(String(36), ForeignKey("tasks.id"), nullable=False)

    # Entry details
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    hours: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    entry_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Metadata
    created_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # Email or name
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Relationships
    task: Mapped["Task"] = relationship("Task", back_populates="time_entries")

    def __repr__(self) -> str:
        return f"<TimeEntry {self.id}: {self.hours}h on {self.entry_date}>"
