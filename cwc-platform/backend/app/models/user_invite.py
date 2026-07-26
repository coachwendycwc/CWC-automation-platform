import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class UserInvite(Base):
    """Single-use, expiring invitation that gates staff registration.

    Registration is invite-only: /auth/register consumes one of these, and the
    new user's role comes from the invite, never from the request body.
    """

    __tablename__ = "user_invites"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="user")
    token: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )
    invited_by: Mapped[str] = mapped_column(String(36), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
