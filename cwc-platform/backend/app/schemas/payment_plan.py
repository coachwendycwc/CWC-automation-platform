from datetime import datetime, date
from decimal import Decimal
from typing import Optional, Literal
from pydantic import BaseModel, ConfigDict


PaymentFrequency = Literal["weekly", "bi_weekly", "monthly", "custom"]
PaymentPlanStatus = Literal["active", "completed", "cancelled"]


class ScheduleItem(BaseModel):
    installment: int
    due_date: str
    amount: float
    status: str  # pending, paid, overdue
    payment_id: Optional[str] = None


class PaymentPlanBase(BaseModel):
    number_of_payments: int
    payment_frequency: PaymentFrequency = "monthly"
    start_date: date


class PaymentPlanCreate(PaymentPlanBase):
    pass


class PaymentPlanUpdate(BaseModel):
    payment_frequency: Optional[PaymentFrequency] = None
    start_date: Optional[date] = None
    status: Optional[PaymentPlanStatus] = None


class PaymentPlanRead(BaseModel):
    id: str
    invoice_id: str
    total_amount: Decimal
    number_of_payments: int
    payment_frequency: str
    start_date: date
    schedule: list[dict]
    status: str
    created_at: datetime
    # Computed fields
    next_due: Optional[dict] = None
    paid_installments: int = 0
    remaining_installments: int = 0

    model_config = ConfigDict(from_attributes=True)
