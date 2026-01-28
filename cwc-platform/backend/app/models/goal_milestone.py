"""Goal milestone model for tracking progress checkpoints."""
import uuid
from datetime import datetime, date
from typing import Optional, TYPE_CHECKING

from sqlalchemy import String, Text, Date, DateTime, Boolean, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.client_goal import ClientGoal


class GoalMilestone(Base):
    """Milestone checkpoint for a client goal."""

    __tablename__ = "goal_milestones"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    goal_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("client_goals.id", ondelete="CASCADE"), nullable=False
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    target_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    goal: Mapped["ClientGoal"] = relationship(back_populates="milestones")
