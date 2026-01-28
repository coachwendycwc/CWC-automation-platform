"""Pydantic schemas for subscriptions and Stripe integration."""

from datetime import datetime
from decimal import Decimal
from typing import Optional, Literal
from pydantic import BaseModel, Field, ConfigDict


# ==================== Stripe Customer ====================

class StripeCustomerCreate(BaseModel):
    contact_id: str


class StripeCustomerRead(BaseModel):
    id: str
    contact_id: str
    stripe_customer_id: str
    default_payment_method_id: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==================== Stripe Product ====================

class StripeProductCreate(BaseModel):
    name: str
    description: Optional[str] = None


class StripeProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class StripeProductRead(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    stripe_product_id: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==================== Stripe Price ====================

BillingInterval = Literal["weekly", "monthly", "quarterly", "yearly"]


class StripePriceCreate(BaseModel):
    product_id: str
    amount: Decimal = Field(..., description="Amount in dollars")
    currency: str = "usd"
    interval: BillingInterval
    interval_count: int = 1


class StripePriceRead(BaseModel):
    id: str
    product_id: str
    stripe_price_id: str
    amount: Decimal
    currency: str
    interval: str
    interval_count: int
    is_active: bool
    created_at: datetime

    # Computed fields from relationships
    product_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ==================== Subscription ====================

SubscriptionStatus = Literal[
    "active", "past_due", "canceled", "incomplete", "trialing", "paused"
]


class SubscriptionCreate(BaseModel):
    contact_id: str
    organization_id: Optional[str] = None
    price_id: str  # Our internal price ID
    trial_days: Optional[int] = None
    notes: Optional[str] = None


class SubscriptionUpdate(BaseModel):
    price_id: Optional[str] = None  # Change plan
    notes: Optional[str] = None


class SubscriptionRead(BaseModel):
    id: str
    contact_id: str
    organization_id: Optional[str] = None
    stripe_customer_id: str
    stripe_price_id: str
    stripe_subscription_id: str
    status: str
    current_period_start: datetime
    current_period_end: datetime
    cancel_at_period_end: bool
    canceled_at: Optional[datetime] = None
    trial_start: Optional[datetime] = None
    trial_end: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    # Computed fields from relationships
    contact_name: Optional[str] = None
    organization_name: Optional[str] = None
    product_name: Optional[str] = None
    price_amount: Optional[Decimal] = None
    price_interval: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class SubscriptionList(BaseModel):
    items: list[SubscriptionRead]
    total: int


class SubscriptionDetail(SubscriptionRead):
    """Extended subscription view with billing history."""
    billing_history: list[dict] = []
    payment_methods: list[dict] = []


# ==================== Setup Intent ====================

class SetupIntentResponse(BaseModel):
    setup_intent_id: str
    client_secret: str
    status: str


# ==================== Payment Method ====================

class PaymentMethodCard(BaseModel):
    brand: str
    last4: str
    exp_month: int
    exp_year: int


class PaymentMethodRead(BaseModel):
    payment_method_id: str
    type: str
    card: Optional[PaymentMethodCard] = None


# ==================== Stats ====================

class SubscriptionStats(BaseModel):
    active_count: int
    trialing_count: int
    past_due_count: int
    canceled_count: int
    monthly_recurring_revenue: Decimal
    annual_recurring_revenue: Decimal
