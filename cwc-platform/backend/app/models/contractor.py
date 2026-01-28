"""Contractor (1099) tracking for tax reporting."""
import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import Optional

from sqlalchemy import String, Boolean, DateTime, Date, Text, Numeric, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Contractor(Base):
    """Independent contractors for 1099 reporting."""

    __tablename__ = "contractors"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )

    # Basic info
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    business_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Tax info
    tax_id: Mapped[str | None] = mapped_column(String(20), nullable=True)  # EIN or SSN (encrypted)
    tax_id_type: Mapped[str] = mapped_column(String(10), default="ein")  # ein, ssn
    w9_on_file: Mapped[bool] = mapped_column(Boolean, default=False)
    w9_received_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Address (for 1099 mailing)
    address_line1: Mapped[str | None] = mapped_column(String(200), nullable=True)
    address_line2: Mapped[str | None] = mapped_column(String(200), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[str | None] = mapped_column(String(50), nullable=True)
    zip_code: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Service type
    service_type: Mapped[str | None] = mapped_column(String(100), nullable=True)  # e.g., "Virtual Assistant", "Web Designer"

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Notes
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    payments: Mapped[list["ContractorPayment"]] = relationship(
        "ContractorPayment", back_populates="contractor", cascade="all, delete-orphan"
    )


class ContractorPayment(Base):
    """Payments made to contractors."""

    __tablename__ = "contractor_payments"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )

    contractor_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("contractors.id", ondelete="CASCADE"), nullable=False
    )

    # Payment details
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    payment_date: Mapped[date] = mapped_column(Date, nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)

    # Payment method
    payment_method: Mapped[str] = mapped_column(
        String(50), default="bank_transfer"
    )  # bank_transfer, check, paypal, venmo, other
    reference: Mapped[str | None] = mapped_column(String(100), nullable=True)  # Check #, transaction ID

    # Link to expense (optional - if tracked as expense too)
    expense_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("expenses.id", ondelete="SET NULL"), nullable=True
    )

    # Invoice from contractor
    invoice_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    invoice_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Tax year
    tax_year: Mapped[int] = mapped_column(nullable=False)

    # Notes
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )

    # Relationships
    contractor: Mapped["Contractor"] = relationship(
        "Contractor", back_populates="payments"
    )
