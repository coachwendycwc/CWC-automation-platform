import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, DateTime, JSON, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.fathom_webhook import FathomWebhook
    from app.models.contact import Contact
    from app.models.invoice import Invoice


class FathomExtraction(Base):
    """AI extraction from Fathom transcript for invoice generation."""

    __tablename__ = "fathom_extractions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )

    # Link to the Fathom webhook record
    fathom_webhook_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("fathom_webhooks.id", ondelete="CASCADE"), nullable=False
    )

    # Matched contact (if found)
    contact_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True
    )

    # Extracted data from AI (stubbed for now)
    # Structure: {
    #   client_name: str,
    #   client_email: str,
    #   service_type: str,
    #   service_description: str,
    #   price_discussed: float,
    #   duration: str,
    #   package_name: str,
    #   start_date: str,
    #   special_requests: list[str],
    #   trigger_phrases: list[str]
    # }
    extracted_data: Mapped[dict] = mapped_column(JSON, default=dict)

    # Confidence scores for each extracted field
    # Structure: {field_name: confidence_score (0-100)}
    confidence_scores: Mapped[dict] = mapped_column(JSON, default=dict)

    # Draft invoice link
    draft_invoice_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("invoices.id", ondelete="SET NULL"), nullable=True
    )

    # Review workflow
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending"
    )  # pending, reviewed, approved, rejected

    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    reviewed_by: Mapped[str | None] = mapped_column(String(36), nullable=True)

    # Corrections made during review (for AI learning)
    # Structure: [{field: str, original: any, corrected: any}]
    corrections: Mapped[list] = mapped_column(JSON, default=list)

    # Notes from reviewer
    review_notes: Mapped[str | None] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    # Relationships
    fathom_webhook: Mapped["FathomWebhook"] = relationship("FathomWebhook")
    contact: Mapped["Contact | None"] = relationship("Contact")
    draft_invoice: Mapped["Invoice | None"] = relationship("Invoice")

    def __repr__(self) -> str:
        return f"<FathomExtraction {self.id} - {self.status}>"

    def calculate_overall_confidence(self) -> float:
        """Calculate overall confidence score from all fields."""
        if not self.confidence_scores:
            return 0.0
        scores = list(self.confidence_scores.values())
        return sum(scores) / len(scores) if scores else 0.0

    def get_confidence_level(self) -> str:
        """Get confidence level string based on overall score."""
        score = self.calculate_overall_confidence()
        if score >= 85:
            return "high"
        elif score >= 60:
            return "medium"
        else:
            return "low"

    def add_correction(self, field: str, original: any, corrected: any) -> None:
        """Record a correction made during review."""
        if self.corrections is None:
            self.corrections = []
        self.corrections.append({
            "field": field,
            "original": original,
            "corrected": corrected,
            "timestamp": datetime.now().isoformat(),
        })
