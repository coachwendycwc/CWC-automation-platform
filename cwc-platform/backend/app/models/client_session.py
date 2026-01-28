import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Boolean, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class ClientSession(Base):
    """Stores magic link tokens and client portal sessions."""

    __tablename__ = "client_sessions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    contact_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("contacts.id"), index=True
    )

    # Magic link token (used once to create session)
    token: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    token_used_at: Mapped[datetime | None] = mapped_column(DateTime)

    # Session JWT (used for authenticated requests)
    session_token: Mapped[str | None] = mapped_column(String(500), unique=True)

    # Metadata
    email_sent_at: Mapped[datetime | None] = mapped_column(DateTime)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(Text)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    # Relationships
    contact: Mapped["Contact"] = relationship(
        "Contact",
        back_populates="client_sessions",
    )


from app.models.contact import Contact
