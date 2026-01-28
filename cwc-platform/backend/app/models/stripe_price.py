"""Stripe Price model - pricing options for products."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import String, Integer, Boolean, DateTime, Numeric, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.stripe_product import StripeProduct
    from app.models.subscription import Subscription


class StripePrice(Base):
    """A Stripe Price representing a recurring pricing option."""

    __tablename__ = "stripe_prices"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    product_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("stripe_products.id", ondelete="CASCADE"), nullable=False
    )
    stripe_price_id: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False
    )  # price_xxx

    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="usd")

    # Recurring interval: weekly, monthly, quarterly, yearly
    interval: Mapped[str] = mapped_column(String(20), nullable=False)
    interval_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    # Relationships
    product: Mapped["StripeProduct"] = relationship(
        "StripeProduct", back_populates="prices"
    )
    subscriptions: Mapped[list["Subscription"]] = relationship(
        "Subscription", back_populates="stripe_price"
    )

    def __repr__(self) -> str:
        return f"<StripePrice {self.amount} {self.currency}/{self.interval}>"

    @property
    def display_interval(self) -> str:
        """Human-readable interval display."""
        if self.interval_count == 1:
            return self.interval
        return f"every {self.interval_count} {self.interval}s"
