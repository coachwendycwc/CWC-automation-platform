import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, DateTime, Boolean, JSON, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class CalendarConnection(Base):
    """Connected external calendar account used for unified availability."""

    __tablename__ = "calendar_connections"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    provider: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    account_email: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    account_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    external_account_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    calendar_id: Mapped[str] = mapped_column(String(255), nullable=False, default="primary")
    calendar_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    token_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    sync_direction: Mapped[str] = mapped_column(String(20), nullable=False, default="read_write")
    conflict_check_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    provider_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship("User", back_populates="calendar_connections")

    def __repr__(self) -> str:
        return f"<CalendarConnection {self.provider}:{self.account_email or self.calendar_id}>"
