import uuid
from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Interaction(Base):
    __tablename__ = "interactions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    contact_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("contacts.id"), nullable=False, index=True
    )

    interaction_type: Mapped[str] = mapped_column(String(20), nullable=False)

    subject: Mapped[str | None] = mapped_column(String(255))
    content: Mapped[str | None] = mapped_column(Text)
    direction: Mapped[str | None] = mapped_column(String(10))

    gmail_message_id: Mapped[str | None] = mapped_column(String(255))

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    created_by: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id")
    )

    # Relationships
    contact: Mapped["Contact"] = relationship("Contact", back_populates="interactions")
    creator: Mapped["User | None"] = relationship("User")


from app.models.contact import Contact
from app.models.user import User
