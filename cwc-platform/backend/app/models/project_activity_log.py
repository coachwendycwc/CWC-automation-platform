"""ProjectActivityLog model for tracking project and task activity."""

from datetime import datetime
from typing import Optional, TYPE_CHECKING
import uuid

from sqlalchemy import String, DateTime, JSON, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.task import Task


class ProjectActivityLog(Base):
    """ProjectActivityLog model for audit trail on projects and tasks."""

    __tablename__ = "project_activity_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Links
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"), nullable=False)
    task_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("tasks.id"), nullable=True)

    # Activity info
    action: Mapped[str] = mapped_column(String(50), nullable=False)  # created, updated, status_changed, task_added, etc.
    actor: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # Email or name
    details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # Additional context

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="activity_logs")
    task: Mapped[Optional["Task"]] = relationship("Task", back_populates="activity_logs")

    def __repr__(self) -> str:
        return f"<ProjectActivityLog {self.action} on {self.project_id}>"
