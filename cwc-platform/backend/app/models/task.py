"""Task model for project task management."""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, TYPE_CHECKING
import uuid

from sqlalchemy import String, Text, DateTime, Date, Numeric, Integer, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.time_entry import TimeEntry
    from app.models.project_activity_log import ProjectActivityLog


class Task(Base):
    """Task model for project tasks."""

    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"), nullable=False)

    # Task info
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="todo")  # todo, in_progress, review, completed, blocked
    priority: Mapped[str] = mapped_column(String(20), default="medium")  # low, medium, high, urgent

    # Assignment
    assigned_to: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # Email or name

    # Timeline
    due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Time tracking
    estimated_hours: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2), nullable=True)
    actual_hours: Mapped[Decimal] = mapped_column(Numeric(8, 2), default=Decimal("0"))

    # Ordering & dependencies
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    depends_on_task_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("tasks.id"), nullable=True)

    # Subtasks (self-referential)
    parent_task_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("tasks.id"), nullable=True)

    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="tasks")
    time_entries: Mapped[list["TimeEntry"]] = relationship("TimeEntry", back_populates="task", cascade="all, delete-orphan")
    activity_logs: Mapped[list["ProjectActivityLog"]] = relationship("ProjectActivityLog", back_populates="task", cascade="all, delete-orphan")

    # Self-referential relationships
    depends_on: Mapped[Optional["Task"]] = relationship(
        "Task",
        remote_side=[id],
        foreign_keys=[depends_on_task_id],
        backref="dependents"
    )
    parent_task: Mapped[Optional["Task"]] = relationship(
        "Task",
        remote_side=[id],
        foreign_keys=[parent_task_id],
        backref="subtasks"
    )

    def __repr__(self) -> str:
        return f"<Task {self.task_number}: {self.title}>"
