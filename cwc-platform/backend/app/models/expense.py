"""Expense tracking models for bookkeeping."""
import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import Optional

from sqlalchemy import String, Boolean, DateTime, Date, Text, Numeric, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ExpenseCategory(Base):
    """Categories for organizing expenses."""

    __tablename__ = "expense_categories"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    color: Mapped[str] = mapped_column(String(7), default="#6b7280")  # Hex color
    icon: Mapped[str | None] = mapped_column(String(50), nullable=True)  # Lucide icon name
    is_tax_deductible: Mapped[bool] = mapped_column(Boolean, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )

    # Relationships
    expenses: Mapped[list["Expense"]] = relationship(
        "Expense", back_populates="category"
    )


class Expense(Base):
    """Individual expense entries."""

    __tablename__ = "expenses"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )

    # Basic info
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    expense_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Category
    category_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("expense_categories.id", ondelete="SET NULL"), nullable=True
    )

    # Vendor/payee
    vendor: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Payment details
    payment_method: Mapped[str] = mapped_column(
        String(50), default="card"
    )  # card, cash, check, bank_transfer, other
    reference: Mapped[str | None] = mapped_column(String(100), nullable=True)  # Check #, transaction ID

    # Receipt
    receipt_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Recurring expense tracking
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False)
    recurring_expense_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("recurring_expenses.id", ondelete="SET NULL"), nullable=True
    )

    # Tax
    is_tax_deductible: Mapped[bool] = mapped_column(Boolean, default=True)
    tax_year: Mapped[int] = mapped_column(nullable=False)

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
    category: Mapped[Optional["ExpenseCategory"]] = relationship(
        "ExpenseCategory", back_populates="expenses"
    )
    recurring_expense: Mapped[Optional["RecurringExpense"]] = relationship(
        "RecurringExpense", back_populates="expenses"
    )


class RecurringExpense(Base):
    """Template for recurring expenses (subscriptions, rent, etc.)."""

    __tablename__ = "recurring_expenses"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )

    # Template info
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    vendor: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Category
    category_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("expense_categories.id", ondelete="SET NULL"), nullable=True
    )

    # Frequency
    frequency: Mapped[str] = mapped_column(
        String(20), default="monthly"
    )  # weekly, monthly, quarterly, yearly

    # Schedule
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    next_due_date: Mapped[date] = mapped_column(Date, nullable=False)
    last_generated_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Settings
    auto_create: Mapped[bool] = mapped_column(Boolean, default=False)  # Auto-create expense on due date
    reminder_days: Mapped[int] = mapped_column(default=3)  # Days before to remind

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
    category: Mapped[Optional["ExpenseCategory"]] = relationship("ExpenseCategory")
    expenses: Mapped[list["Expense"]] = relationship(
        "Expense", back_populates="recurring_expense"
    )
