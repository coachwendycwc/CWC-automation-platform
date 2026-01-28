"""Subscription model - active Stripe subscriptions."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, Boolean, DateTime, Text, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.contact import Contact
    from app.models.organization import Organization
    from app.models.stripe_customer import StripeCustomer
    from app.models.stripe_price import StripePrice
    from app.models.invoice import Invoice


class Subscription(Base):
    """An active subscription for a contact."""

    __tablename__ = "subscriptions"

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
    stripe_customer_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("stripe_customers.id", ondelete="CASCADE"), nullable=False
    )
    stripe_price_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("stripe_prices.id", ondelete="RESTRICT"), nullable=False
    )
    stripe_subscription_id: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False
    )  # sub_xxx

    # Status: active, past_due, canceled, incomplete, trialing, paused
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="active")

    # Schedule details
    current_period_start: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    current_period_end: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    cancel_at_period_end: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    canceled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Trial support
    trial_start: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    trial_end: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Metadata
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    contact: Mapped["Contact"] = relationship("Contact", back_populates="subscriptions")
    organization: Mapped["Organization | None"] = relationship("Organization")
    stripe_customer: Mapped["StripeCustomer"] = relationship(
        "StripeCustomer", back_populates="subscriptions"
    )
    stripe_price: Mapped["StripePrice"] = relationship(
        "StripePrice", back_populates="subscriptions"
    )
    invoices: Mapped[list["Invoice"]] = relationship(
        "Invoice", back_populates="subscription"
    )

    def __repr__(self) -> str:
        return f"<Subscription {self.stripe_subscription_id} ({self.status})>"

    @property
    def is_active(self) -> bool:
        """Check if subscription is currently active."""
        return self.status in ("active", "trialing")

    @property
    def is_canceled(self) -> bool:
        """Check if subscription is canceled."""
        return self.status == "canceled" or self.cancel_at_period_end
