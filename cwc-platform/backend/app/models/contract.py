import uuid
import secrets
import hashlib
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, Boolean, DateTime, Text, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.contract_template import ContractTemplate
    from app.models.contact import Contact
    from app.models.organization import Organization
    from app.models.invoice import Invoice
    from app.models.signature_audit_log import SignatureAuditLog
    from app.models.project import Project


class Contract(Base):
    """Contract document with e-signature support."""

    __tablename__ = "contracts"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    contract_number: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False
    )

    # Source template (optional - contracts can be created without template)
    template_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("contract_templates.id", ondelete="SET NULL"), nullable=True
    )

    # Client info
    contact_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False
    )
    organization_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True
    )

    # Content
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)  # Rendered HTML

    # Status tracking
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="draft"
    )  # draft, sent, viewed, signed, expired, declined, void

    sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    viewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    signed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    declined_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    decline_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Signature data
    signer_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    signer_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    signer_ip: Mapped[str | None] = mapped_column(String(45), nullable=True)
    signature_data: Mapped[str | None] = mapped_column(Text, nullable=True)  # Base64
    signature_type: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )  # drawn, typed

    # Audit hashes for legal validity
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    signature_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Links to other entities
    linked_invoice_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("invoices.id", ondelete="SET NULL"), nullable=True
    )
    linked_project_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="SET NULL"), nullable=True
    )

    # Public access token
    view_token: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True, default=lambda: secrets.token_urlsafe(32)
    )

    # Notes
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    template: Mapped["ContractTemplate | None"] = relationship(
        "ContractTemplate", back_populates="contracts"
    )
    contact: Mapped["Contact"] = relationship("Contact", back_populates="contracts")
    organization: Mapped["Organization | None"] = relationship("Organization")
    linked_invoice: Mapped["Invoice | None"] = relationship("Invoice")
    linked_project: Mapped["Project | None"] = relationship(
        "Project", foreign_keys=[linked_project_id]
    )
    audit_logs: Mapped[list["SignatureAuditLog"]] = relationship(
        "SignatureAuditLog", back_populates="contract", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Contract {self.contract_number}>"

    def generate_content_hash(self) -> str:
        """Generate SHA-256 hash of contract content."""
        return hashlib.sha256(self.content.encode()).hexdigest()

    def generate_signature_hash(self, timestamp: datetime) -> str:
        """Generate tamper-proof hash of signature event."""
        data = f"{self.id}:{self.content_hash}:{self.signature_data}:{self.signer_ip}:{timestamp.isoformat()}"
        return hashlib.sha256(data.encode()).hexdigest()

    def can_be_signed(self) -> bool:
        """Check if contract is in a state that allows signing."""
        if self.status not in ["sent", "viewed"]:
            return False
        if self.expires_at and datetime.now() > self.expires_at:
            return False
        return True

    def mark_as_signed(
        self,
        signer_name: str,
        signer_email: str,
        signer_ip: str,
        signature_data: str,
        signature_type: str,
    ) -> None:
        """Mark contract as signed with signature data."""
        now = datetime.now()
        self.signer_name = signer_name
        self.signer_email = signer_email
        self.signer_ip = signer_ip
        self.signature_data = signature_data
        self.signature_type = signature_type
        self.content_hash = self.generate_content_hash()
        self.signature_hash = self.generate_signature_hash(now)
        self.signed_at = now
        self.status = "signed"
