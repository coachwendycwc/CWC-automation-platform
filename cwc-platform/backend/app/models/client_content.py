"""
Client Content Model.
Stores digital content (files, links, videos) shared with clients.
"""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, DateTime, Text, Boolean, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.contact import Contact
    from app.models.organization import Organization
    from app.models.project import Project


class ClientContent(Base):
    """Digital content shared with clients through the portal."""

    __tablename__ = "client_contents"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )

    # Content metadata
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Content type: file, link, video, document
    content_type: Mapped[str] = mapped_column(String(50), nullable=False, default="file")

    # For files: stored file path or URL
    file_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)  # bytes
    mime_type: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # For external links/videos
    external_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Access control - content can be assigned to:
    # - Specific contact (individual coaching)
    # - Organization (all members see it)
    # - Project (project-specific content)
    # - None of above = available to all clients of coach
    contact_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("contacts.id", ondelete="CASCADE"), nullable=True
    )
    organization_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True
    )
    project_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=True
    )

    # Drip content - release on a specific date
    release_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Visibility
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Ordering
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    # Category/folder for organization
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    contact: Mapped["Contact | None"] = relationship("Contact", back_populates="contents")
    organization: Mapped["Organization | None"] = relationship("Organization", back_populates="contents")
    project: Mapped["Project | None"] = relationship("Project", back_populates="contents")

    def __repr__(self) -> str:
        return f"<ClientContent {self.title}>"

    @property
    def is_released(self) -> bool:
        """Check if content is available (past release date)."""
        if not self.release_date:
            return True
        return datetime.utcnow() >= self.release_date

    @property
    def content_url(self) -> str | None:
        """Get the URL for this content (file or external)."""
        return self.file_url or self.external_url
