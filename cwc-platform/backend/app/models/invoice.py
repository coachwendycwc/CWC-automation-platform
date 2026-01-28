import uuid
import secrets
from datetime import datetime, date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import String, Integer, Boolean, DateTime, Date, Text, Numeric, JSON, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.contact import Contact
    from app.models.organization import Organization
    from app.models.payment import Payment
    from app.models.payment_plan import PaymentPlan
    from app.models.project import Project
    from app.models.subscription import Subscription
    from app.models.recurring_invoice import RecurringInvoice


class Invoice(Base):
    """Invoice for services rendered."""

    __tablename__ = "invoices"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    invoice_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)

    # Client info
    contact_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False
    )
    organization_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True
    )

    # Subscription/Recurring references
    subscription_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("subscriptions.id", ondelete="SET NULL"), nullable=True
    )
    recurring_invoice_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("recurring_invoices.id", ondelete="SET NULL"), nullable=True
    )
    stripe_invoice_id: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )  # inv_xxx from Stripe

    # Line items stored as JSON
    line_items: Mapped[list] = mapped_column(
        JSON, default=list
    )  # [{description, quantity, unit_price, amount, service_type, booking_id}]

    # Totals
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    tax_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    amount_paid: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    balance_due: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)

    # Payment terms
    payment_terms: Mapped[str] = mapped_column(
        String(20), nullable=False, default="net_30"
    )  # due_on_receipt, net_15, net_30, custom
    due_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Status tracking
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="draft"
    )  # draft, sent, viewed, partial, paid, overdue, cancelled
    sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    viewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Payment plan support
    is_payment_plan: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Tokens for public access
    view_token: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True, default=lambda: secrets.token_urlsafe(32)
    )

    # Notes
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)  # Internal notes
    memo: Mapped[str | None] = mapped_column(Text, nullable=True)  # Appears on invoice

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    contact: Mapped["Contact"] = relationship("Contact", back_populates="invoices")
    organization: Mapped["Organization | None"] = relationship("Organization")
    payments: Mapped[list["Payment"]] = relationship(
        "Payment", back_populates="invoice", cascade="all, delete-orphan"
    )
    payment_plan: Mapped["PaymentPlan | None"] = relationship(
        "PaymentPlan", back_populates="invoice", uselist=False
    )
    linked_project: Mapped["Project | None"] = relationship(
        "Project", back_populates="linked_invoice", foreign_keys="Project.linked_invoice_id"
    )
    subscription: Mapped["Subscription | None"] = relationship(
        "Subscription", back_populates="invoices"
    )
    recurring_invoice: Mapped["RecurringInvoice | None"] = relationship(
        "RecurringInvoice", back_populates="generated_invoices"
    )

    def __repr__(self) -> str:
        return f"<Invoice {self.invoice_number}>"

    def recalculate_totals(self) -> None:
        """Recalculate all totals from line items."""
        self.subtotal = sum(
            Decimal(str(item.get("amount", 0))) for item in (self.line_items or [])
        )
        self.tax_amount = (
            self.subtotal * (self.tax_rate / 100) if self.tax_rate else Decimal(0)
        )
        self.total = self.subtotal + self.tax_amount - self.discount_amount
        self.balance_due = self.total - self.amount_paid

    def update_payment_status(self) -> None:
        """Update status based on payments."""
        if self.balance_due <= 0:
            self.status = "paid"
            self.paid_at = datetime.now()
        elif self.amount_paid > 0:
            self.status = "partial"
