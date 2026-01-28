from datetime import datetime, date
from decimal import Decimal
from typing import Optional, Literal
from pydantic import BaseModel, Field, ConfigDict


# Line Item schemas
class LineItemBase(BaseModel):
    description: str
    quantity: Decimal = Field(default=Decimal("1"))
    unit_price: Decimal
    service_type: Optional[str] = None  # coaching, workshop, consulting, etc.
    booking_id: Optional[str] = None


class LineItemCreate(LineItemBase):
    pass


class LineItem(LineItemBase):
    amount: Decimal

    model_config = ConfigDict(from_attributes=True)


# Invoice schemas
PaymentTerms = Literal["due_on_receipt", "net_15", "net_30", "50_50_split", "custom"]
InvoiceStatus = Literal["draft", "sent", "viewed", "partial", "paid", "overdue", "cancelled"]


class InvoiceBase(BaseModel):
    contact_id: str
    organization_id: Optional[str] = None
    payment_terms: PaymentTerms = "net_30"
    tax_rate: Optional[Decimal] = None
    discount_amount: Decimal = Field(default=Decimal("0"))
    notes: Optional[str] = None
    memo: Optional[str] = None


class InvoiceCreate(InvoiceBase):
    line_items: list[LineItemCreate] = []
    due_date: Optional[date] = None  # If not provided, calculated from payment_terms


class InvoiceUpdate(BaseModel):
    contact_id: Optional[str] = None
    organization_id: Optional[str] = None
    line_items: Optional[list[LineItemCreate]] = None
    payment_terms: Optional[PaymentTerms] = None
    due_date: Optional[date] = None
    tax_rate: Optional[Decimal] = None
    discount_amount: Optional[Decimal] = None
    notes: Optional[str] = None
    memo: Optional[str] = None
    status: Optional[InvoiceStatus] = None


class InvoiceRead(BaseModel):
    id: str
    invoice_number: str
    contact_id: str
    organization_id: Optional[str] = None
    line_items: list[dict]
    subtotal: Decimal
    tax_rate: Optional[Decimal] = None
    tax_amount: Decimal
    discount_amount: Decimal
    total: Decimal
    amount_paid: Decimal
    balance_due: Decimal
    payment_terms: str
    due_date: date
    status: str
    sent_at: Optional[datetime] = None
    viewed_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    is_payment_plan: bool
    view_token: str
    notes: Optional[str] = None
    memo: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InvoiceList(BaseModel):
    id: str
    invoice_number: str
    contact_id: str
    contact_name: Optional[str] = None
    organization_name: Optional[str] = None
    total: Decimal
    balance_due: Decimal
    status: str
    due_date: date
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InvoiceSend(BaseModel):
    send_email: bool = True
    email_message: Optional[str] = None


class InvoiceStats(BaseModel):
    total_revenue: Decimal
    total_outstanding: Decimal
    total_overdue: Decimal
    invoices_count: int
    paid_count: int
    pending_count: int
    overdue_count: int


# Public invoice view (limited data)
class InvoicePublic(BaseModel):
    invoice_number: str
    line_items: list[dict]
    subtotal: Decimal
    tax_rate: Optional[Decimal] = None
    tax_amount: Decimal
    discount_amount: Decimal
    total: Decimal
    amount_paid: Decimal
    balance_due: Decimal
    payment_terms: str
    due_date: date
    status: str
    memo: Optional[str] = None
    contact_name: str
    organization_name: Optional[str] = None
    is_overdue: bool

    model_config = ConfigDict(from_attributes=True)
