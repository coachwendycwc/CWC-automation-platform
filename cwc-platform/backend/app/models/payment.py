import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import String, DateTime, Date, Text, Numeric, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.invoice import Invoice


class Payment(Base):
    """Payment record for an invoice."""

    __tablename__ = "payments"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    invoice_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False
    )

    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    payment_method: Mapped[str] = mapped_column(
        String(20), nullable=False, default="other"
    )  # card, bank_transfer, cash, check, other
    payment_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Stripe fields (for future integration)
    stripe_payment_intent_id: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )
    stripe_charge_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Reference info
    reference: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )  # Check number, transfer reference, etc.
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    created_by: Mapped[str | None] = mapped_column(
        String(36), nullable=True
    )  # User who recorded payment

    # Relationships
    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="payments")

    def __repr__(self) -> str:
        return f"<Payment {self.id} - ${self.amount}>"
