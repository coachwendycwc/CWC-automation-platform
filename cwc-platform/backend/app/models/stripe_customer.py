"""Stripe Customer model - links contacts to Stripe customers."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.contact import Contact
    from app.models.subscription import Subscription


class StripeCustomer(Base):
    """Links a Contact to a Stripe Customer object."""

    __tablename__ = "stripe_customers"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    contact_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("contacts.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    stripe_customer_id: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False
    )  # cus_xxx
    default_payment_method_id: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )  # pm_xxx

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    contact: Mapped["Contact"] = relationship(
        "Contact", back_populates="stripe_customer"
    )
    subscriptions: Mapped[list["Subscription"]] = relationship(
        "Subscription", back_populates="stripe_customer"
    )

    def __repr__(self) -> str:
        return f"<StripeCustomer {self.stripe_customer_id}>"
