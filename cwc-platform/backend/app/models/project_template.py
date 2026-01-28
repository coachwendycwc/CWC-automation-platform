"""ProjectTemplate model for reusable project templates."""

from datetime import datetime
from decimal import Decimal
from typing import Optional, TYPE_CHECKING
import uuid

from sqlalchemy import String, Text, DateTime, Numeric, Integer, Boolean, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.project import Project


class ProjectTemplate(Base):
    """ProjectTemplate model for creating projects from templates."""

    __tablename__ = "project_templates"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Template info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    project_type: Mapped[str] = mapped_column(String(50), default="coaching")  # coaching, workshop, consulting, speaking

    # Default settings
    default_duration_days: Mapped[int] = mapped_column(Integer, default=30)
    estimated_hours: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2), nullable=True)

    # Template tasks (JSON array)
    # Structure: [{"title": str, "description": str|None, "estimated_hours": float|None, "order_index": int}]
    task_templates: Mapped[Optional[list]] = mapped_column(JSON, nullable=True, default=list)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    projects: Mapped[list["Project"]] = relationship("Project", back_populates="template")

    def __repr__(self) -> str:
        return f"<ProjectTemplate {self.name}>"
