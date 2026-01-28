import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, DateTime, Text, JSON, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.contract import Contract


class SignatureAuditLog(Base):
    """Audit log for contract signature events - provides legal trail."""

    __tablename__ = "signature_audit_logs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    contract_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False
    )

    # Action performed
    action: Mapped[str] = mapped_column(
        String(30), nullable=False
    )  # created, sent, viewed, signed, declined, expired, voided

    # Actor information
    actor_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Additional context
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    # Relationships
    contract: Mapped["Contract"] = relationship("Contract", back_populates="audit_logs")

    def __repr__(self) -> str:
        return f"<SignatureAuditLog {self.action} on {self.contract_id}>"

    @classmethod
    def log_action(
        cls,
        contract_id: str,
        action: str,
        actor_email: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        details: dict | None = None,
    ) -> "SignatureAuditLog":
        """Factory method to create an audit log entry."""
        return cls(
            contract_id=contract_id,
            action=action,
            actor_email=actor_email,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details,
        )
