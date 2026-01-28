"""Stripe Product model - subscription products/services."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, Boolean, DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.stripe_price import StripePrice


class StripeProduct(Base):
    """A Stripe Product representing a subscription service."""

    __tablename__ = "stripe_products"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    stripe_product_id: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False
    )  # prod_xxx
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    prices: Mapped[list["StripePrice"]] = relationship(
        "StripePrice", back_populates="product", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<StripeProduct {self.name}>"
