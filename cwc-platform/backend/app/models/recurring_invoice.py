"""Recurring Invoice model - template for auto-generated invoices."""

import uuid
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import String, Integer, Boolean, DateTime, Date, Text, Numeric, JSON, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.contact import Contact
    from app.models.organization import Organization
    from app.models.invoice import Invoice


class RecurringInvoice(Base):
    """Template for auto-generating invoices on a schedule."""

    __tablename__ = "recurring_invoices"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )

    # References
    contact_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False
    )
    organization_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True
    )

    # Template details (same structure as Invoice)
    title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    line_items: Mapped[list] = mapped_column(JSON, default=list)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    tax_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)

    payment_terms: Mapped[str] = mapped_column(String(20), nullable=False, default="net_30")
    memo: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Schedule: weekly, bi_weekly, monthly, quarterly, annual
    frequency: Mapped[str] = mapped_column(String(20), nullable=False, default="monthly")
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)  # null = no end
    next_invoice_date: Mapped[date] = mapped_column(Date, nullable=False)
    last_generated_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Settings
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    auto_send: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    send_days_before: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Tracking
    invoices_generated: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    contact: Mapped["Contact"] = relationship("Contact", back_populates="recurring_invoices")
    organization: Mapped["Organization | None"] = relationship("Organization")
    generated_invoices: Mapped[list["Invoice"]] = relationship(
        "Invoice", back_populates="recurring_invoice"
    )

    def __repr__(self) -> str:
        return f"<RecurringInvoice {self.id} ({self.frequency})>"

    def calculate_next_date(self, from_date: date | None = None) -> date:
        """Calculate the next invoice date based on frequency."""
        current = from_date or self.next_invoice_date

        if self.frequency == "weekly":
            return current + relativedelta(weeks=1)
        elif self.frequency == "bi_weekly":
            return current + relativedelta(weeks=2)
        elif self.frequency == "monthly":
            return current + relativedelta(months=1)
        elif self.frequency == "quarterly":
            return current + relativedelta(months=3)
        elif self.frequency == "annual":
            return current + relativedelta(years=1)
        else:
            # Default to monthly
            return current + relativedelta(months=1)

    def recalculate_totals(self) -> None:
        """Recalculate all totals from line items."""
        self.subtotal = sum(
            Decimal(str(item.get("amount", 0))) for item in (self.line_items or [])
        )
        self.tax_amount = (
            self.subtotal * (self.tax_rate / 100) if self.tax_rate else Decimal(0)
        )
        self.total = self.subtotal + self.tax_amount - self.discount_amount

    @property
    def is_ended(self) -> bool:
        """Check if recurring invoice has ended."""
        if self.end_date and date.today() > self.end_date:
            return True
        return False

    @property
    def display_frequency(self) -> str:
        """Human-readable frequency."""
        freq_map = {
            "weekly": "Weekly",
            "bi_weekly": "Bi-Weekly",
            "monthly": "Monthly",
            "quarterly": "Quarterly",
            "annual": "Annual",
        }
        return freq_map.get(self.frequency, self.frequency.title())
