import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, DateTime, Text, JSON, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.contact import Contact


class PortalAuditLog(Base):
    """Audit log for client portal access events."""

    __tablename__ = "portal_audit_logs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    contact_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False
    )

    # Action performed
    action: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # login, logout, view_invoice, view_contract, download_pdf, cancel_booking, etc.

    # Resource accessed (optional)
    resource_type: Mapped[str | None] = mapped_column(String(50), nullable=True)  # invoice, contract, booking, project
    resource_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    # Actor information
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Additional context
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    # Relationships
    contact: Mapped["Contact"] = relationship("Contact", back_populates="portal_audit_logs")

    def __repr__(self) -> str:
        return f"<PortalAuditLog {self.action} by contact {self.contact_id}>"

    @classmethod
    def log_action(
        cls,
        contact_id: str,
        action: str,
        resource_type: str | None = None,
        resource_id: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        details: dict | None = None,
    ) -> "PortalAuditLog":
        """Factory method to create an audit log entry."""
        return cls(
            contact_id=contact_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details,
        )
