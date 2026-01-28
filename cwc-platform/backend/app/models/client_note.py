"""
Client Note Model.
Two-way notes/messages between coach and clients.
"""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import String, DateTime, Text, Boolean, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.contact import Contact


class ClientNote(Base):
    """Notes exchanged between coach and clients."""

    __tablename__ = "client_notes"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )

    # Link to contact
    contact_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Note content
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Direction: who sent this note
    # "to_coach" = client sent to coach
    # "to_client" = coach sent to client
    direction: Mapped[str] = mapped_column(String(20), nullable=False)

    # For replies - links to parent note (self-referential)
    parent_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("client_notes.id", ondelete="CASCADE"), nullable=True
    )

    # Read status
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    read_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    # Relationships
    contact: Mapped["Contact"] = relationship("Contact", back_populates="notes")
    parent: Mapped[Optional["ClientNote"]] = relationship(
        "ClientNote",
        remote_side=[id],
        back_populates="replies",
        foreign_keys=[parent_id],
    )
    replies: Mapped[List["ClientNote"]] = relationship(
        "ClientNote",
        back_populates="parent",
        foreign_keys=[parent_id],
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<ClientNote {self.id} ({self.direction})>"
