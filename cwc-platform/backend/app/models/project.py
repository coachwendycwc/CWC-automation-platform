"""Project model for project management."""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, TYPE_CHECKING
import uuid
import secrets

from sqlalchemy import String, Text, DateTime, Date, Numeric, Integer, Boolean, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.contact import Contact
    from app.models.organization import Organization
    from app.models.contract import Contract
    from app.models.invoice import Invoice
    from app.models.task import Task
    from app.models.project_template import ProjectTemplate
    from app.models.project_activity_log import ProjectActivityLog
    from app.models.client_content import ClientContent


class Project(Base):
    """Project model for tracking client engagements."""

    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)

    # Client linkage
    contact_id: Mapped[str] = mapped_column(String(36), ForeignKey("contacts.id"), nullable=False)
    organization_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=True)

    # Basic info
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    project_type: Mapped[str] = mapped_column(String(50), default="coaching")  # coaching, workshop, consulting, speaking
    status: Mapped[str] = mapped_column(String(20), default="planning")  # planning, active, paused, completed, cancelled

    # Timeline
    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    target_end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    actual_end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Budget & Hours
    budget_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    estimated_hours: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2), nullable=True)

    # Links to other entities
    linked_contract_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("contracts.id"), nullable=True)
    linked_invoice_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("invoices.id"), nullable=True)
    template_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("project_templates.id"), nullable=True)

    # Progress (computed from tasks, stored for performance)
    progress_percent: Mapped[int] = mapped_column(Integer, default=0)

    # Public access (optional client visibility)
    view_token: Mapped[str] = mapped_column(String(64), unique=True, default=lambda: secrets.token_urlsafe(32))
    client_visible: Mapped[bool] = mapped_column(Boolean, default=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    contact: Mapped["Contact"] = relationship("Contact", back_populates="projects")
    organization: Mapped[Optional["Organization"]] = relationship("Organization", back_populates="projects")
    linked_contract: Mapped[Optional["Contract"]] = relationship("Contract", foreign_keys=[linked_contract_id])
    linked_invoice: Mapped[Optional["Invoice"]] = relationship("Invoice", back_populates="linked_project", foreign_keys=[linked_invoice_id])
    template: Mapped[Optional["ProjectTemplate"]] = relationship("ProjectTemplate", back_populates="projects")
    tasks: Mapped[list["Task"]] = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    activity_logs: Mapped[list["ProjectActivityLog"]] = relationship("ProjectActivityLog", back_populates="project", cascade="all, delete-orphan")
    contents: Mapped[list["ClientContent"]] = relationship("ClientContent", back_populates="project", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Project {self.project_number}: {self.title}>"
