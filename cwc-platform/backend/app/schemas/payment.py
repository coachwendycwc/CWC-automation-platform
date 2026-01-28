from datetime import datetime, date
from decimal import Decimal
from typing import Optional, Literal
from pydantic import BaseModel, ConfigDict


PaymentMethod = Literal["card", "bank_transfer", "cash", "check", "other"]


class PaymentBase(BaseModel):
    amount: Decimal
    payment_method: PaymentMethod = "other"
    payment_date: date
    reference: Optional[str] = None
    notes: Optional[str] = None


class PaymentCreate(PaymentBase):
    pass


class PaymentRead(BaseModel):
    id: str
    invoice_id: str
    amount: Decimal
    payment_method: str
    payment_date: date
    stripe_payment_intent_id: Optional[str] = None
    stripe_charge_id: Optional[str] = None
    reference: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    created_by: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PaymentList(BaseModel):
    id: str
    invoice_id: str
    invoice_number: Optional[str] = None
    amount: Decimal
    payment_method: str
    payment_date: date
    reference: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
