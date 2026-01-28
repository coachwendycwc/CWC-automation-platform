import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, DateTime, Boolean, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.availability import Availability, AvailabilityOverride


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    name: Mapped[str | None] = mapped_column(String(255))
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    google_id: Mapped[str | None] = mapped_column(String(255), unique=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500))
    role: Mapped[str] = mapped_column(String(20), default="user")  # admin, user
    is_active: Mapped[bool] = mapped_column(default=True)
    password_reset_token: Mapped[str | None] = mapped_column(String(255), nullable=True)
    password_reset_expires: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Integration tokens (stored as JSON)
    google_calendar_token: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    zoom_token: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    availabilities: Mapped[list["Availability"]] = relationship(
        "Availability", back_populates="user", cascade="all, delete-orphan"
    )
    availability_overrides: Mapped[list["AvailabilityOverride"]] = relationship(
        "AvailabilityOverride", back_populates="user", cascade="all, delete-orphan"
    )
