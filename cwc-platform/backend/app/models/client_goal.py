"""Client goal model for goal tracking."""
import uuid
from datetime import datetime, date
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import String, Text, Date, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.contact import Contact
    from app.models.goal_milestone import GoalMilestone


class ClientGoal(Base):
    """Goal set for a client with progress tracking."""

    __tablename__ = "client_goals"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    contact_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # career, health, relationships, etc.

    status: Mapped[str] = mapped_column(
        String(20), default="active"
    )  # active, completed, abandoned
    target_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Reminder tracking
    target_reminder_sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    progress_checkin_sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    contact: Mapped["Contact"] = relationship(back_populates="goals")
    milestones: Mapped[List["GoalMilestone"]] = relationship(
        back_populates="goal",
        cascade="all, delete-orphan",
        order_by="GoalMilestone.sort_order",
    )

    @property
    def progress_percent(self) -> int:
        """Calculate progress based on completed milestones."""
        if not self.milestones:
            return 0
        completed = sum(1 for m in self.milestones if m.is_completed)
        return int((completed / len(self.milestones)) * 100)
