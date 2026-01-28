import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, Integer, Boolean, DateTime, Text, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.contract import Contract


class ContractTemplate(Base):
    """Reusable contract template with merge fields."""

    __tablename__ = "contract_templates"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Template content with merge fields like {{client_name}}
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Category for organization
    category: Mapped[str] = mapped_column(
        String(50), nullable=False, default="coaching"
    )  # coaching, workshop, consulting, speaking

    # List of merge fields used in this template
    merge_fields: Mapped[list] = mapped_column(JSON, default=list)

    # Default expiration for contracts created from this template
    default_expiry_days: Mapped[int] = mapped_column(
        Integer, nullable=False, default=7
    )

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    contracts: Mapped[list["Contract"]] = relationship(
        "Contract", back_populates="template"
    )

    def __repr__(self) -> str:
        return f"<ContractTemplate {self.name}>"

    def extract_merge_fields(self) -> list[str]:
        """Extract merge field names from template content."""
        import re
        pattern = r"\{\{(\w+)\}\}"
        fields = re.findall(pattern, self.content)
        return list(set(fields))

    def update_merge_fields(self) -> None:
        """Update the merge_fields list based on content."""
        self.merge_fields = self.extract_merge_fields()
