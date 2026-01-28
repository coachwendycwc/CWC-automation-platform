import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, DateTime, ForeignKey, DECIMAL, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    logo_url: Mapped[str | None] = mapped_column(String(500))
    industry: Mapped[str | None] = mapped_column(String(100))
    size: Mapped[str | None] = mapped_column(String(50))
    website: Mapped[str | None] = mapped_column(String(255))

    primary_contact_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("contacts.id", use_alter=True)
    )
    billing_contact_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("contacts.id", use_alter=True)
    )

    tags: Mapped[list] = mapped_column(JSON, default=list)
    segment: Mapped[str | None] = mapped_column(String(50))
    source: Mapped[str | None] = mapped_column(String(100))

    lifetime_value: Mapped[Decimal] = mapped_column(DECIMAL(12, 2), default=0)
    status: Mapped[str] = mapped_column(String(20), default="active")

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    contacts: Mapped[list["Contact"]] = relationship(
        "Contact",
        back_populates="organization",
        foreign_keys="Contact.organization_id",
    )
    primary_contact: Mapped["Contact | None"] = relationship(
        "Contact",
        foreign_keys=[primary_contact_id],
        post_update=True,
    )
    billing_contact: Mapped["Contact | None"] = relationship(
        "Contact",
        foreign_keys=[billing_contact_id],
        post_update=True,
    )
    projects: Mapped[list["Project"]] = relationship(
        "Project",
        back_populates="organization",
    )
    contents: Mapped[list["ClientContent"]] = relationship(
        "ClientContent",
        back_populates="organization",
        cascade="all, delete-orphan",
    )
    testimonials: Mapped[list["Testimonial"]] = relationship(
        "Testimonial",
        back_populates="organization",
    )


from app.models.contact import Contact
from app.models.project import Project
from app.models.client_content import ClientContent
from app.models.testimonial import Testimonial
