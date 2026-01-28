"""Pydantic schemas for recurring invoices."""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, Literal
from pydantic import BaseModel, Field, ConfigDict

from app.schemas.invoice import LineItemCreate, PaymentTerms


# ==================== Recurring Invoice ====================

RecurringFrequency = Literal["weekly", "bi_weekly", "monthly", "quarterly", "annual"]


class RecurringInvoiceBase(BaseModel):
    contact_id: str
    organization_id: Optional[str] = None
    title: Optional[str] = None
    line_items: list[LineItemCreate] = []
    tax_rate: Optional[Decimal] = None
    discount_amount: Decimal = Field(default=Decimal("0"))
    payment_terms: PaymentTerms = "net_30"
    memo: Optional[str] = None
    notes: Optional[str] = None


class RecurringInvoiceCreate(RecurringInvoiceBase):
    frequency: RecurringFrequency
    start_date: date
    end_date: Optional[date] = None
    auto_send: bool = False
    send_days_before: int = 0


class RecurringInvoiceUpdate(BaseModel):
    title: Optional[str] = None
    line_items: Optional[list[LineItemCreate]] = None
    tax_rate: Optional[Decimal] = None
    discount_amount: Optional[Decimal] = None
    payment_terms: Optional[PaymentTerms] = None
    memo: Optional[str] = None
    notes: Optional[str] = None
    frequency: Optional[RecurringFrequency] = None
    end_date: Optional[date] = None
    auto_send: Optional[bool] = None
    send_days_before: Optional[int] = None


class RecurringInvoiceRead(BaseModel):
    id: str
    contact_id: str
    organization_id: Optional[str] = None
    title: Optional[str] = None
    line_items: list[dict]
    subtotal: Decimal
    tax_rate: Optional[Decimal] = None
    tax_amount: Decimal
    discount_amount: Decimal
    total: Decimal
    payment_terms: str
    memo: Optional[str] = None
    notes: Optional[str] = None
    frequency: str
    start_date: date
    end_date: Optional[date] = None
    next_invoice_date: date
    last_generated_date: Optional[date] = None
    is_active: bool
    auto_send: bool
    send_days_before: int
    invoices_generated: int
    created_at: datetime
    updated_at: datetime

    # Computed fields from relationships
    contact_name: Optional[str] = None
    organization_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class RecurringInvoiceList(BaseModel):
    items: list[RecurringInvoiceRead]
    total: int


class RecurringInvoiceDetail(RecurringInvoiceRead):
    """Extended view with generated invoices."""
    generated_invoices: list[dict] = []


# ==================== Stats ====================

class RecurringInvoiceStats(BaseModel):
    active_count: int
    paused_count: int
    ended_count: int
    total_monthly_value: Decimal
    next_generation_count: int  # How many will generate in next 7 days
