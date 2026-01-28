import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, JSON, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Contact(Base):
    __tablename__ = "contacts"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str | None] = mapped_column(String(100))
    email: Mapped[str | None] = mapped_column(String(255), index=True)
    phone: Mapped[str | None] = mapped_column(String(50))

    organization_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("organizations.id"), index=True
    )

    role: Mapped[str | None] = mapped_column(String(100))
    title: Mapped[str | None] = mapped_column(String(100))

    contact_type: Mapped[str] = mapped_column(
        String(20), default="lead", index=True
    )

    coaching_type: Mapped[str | None] = mapped_column(String(20))

    # Client portal access
    portal_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    is_org_admin: Mapped[bool] = mapped_column(Boolean, default=False)

    tags: Mapped[list] = mapped_column(JSON, default=list)
    source: Mapped[str | None] = mapped_column(String(100))

    # Engagement tracking for email workflows
    last_activity_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_session_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    welcome_series_completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    weekly_summary_sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    monthly_summary_sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    organization: Mapped["Organization | None"] = relationship(
        "Organization",
        back_populates="contacts",
        foreign_keys=[organization_id],
    )
    interactions: Mapped[list["Interaction"]] = relationship(
        "Interaction",
        back_populates="contact",
        cascade="all, delete-orphan",
    )
    bookings: Mapped[list["Booking"]] = relationship(
        "Booking",
        back_populates="contact",
        cascade="all, delete-orphan",
    )
    invoices: Mapped[list["Invoice"]] = relationship(
        "Invoice",
        back_populates="contact",
        cascade="all, delete-orphan",
    )
    contracts: Mapped[list["Contract"]] = relationship(
        "Contract",
        back_populates="contact",
        cascade="all, delete-orphan",
    )
    projects: Mapped[list["Project"]] = relationship(
        "Project",
        back_populates="contact",
        cascade="all, delete-orphan",
    )
    client_sessions: Mapped[list["ClientSession"]] = relationship(
        "ClientSession",
        back_populates="contact",
        cascade="all, delete-orphan",
    )
    session_recordings: Mapped[list["FathomWebhook"]] = relationship(
        "FathomWebhook",
        back_populates="contact",
    )
    portal_audit_logs: Mapped[list["PortalAuditLog"]] = relationship(
        "PortalAuditLog",
        back_populates="contact",
        cascade="all, delete-orphan",
    )
    contents: Mapped[list["ClientContent"]] = relationship(
        "ClientContent",
        back_populates="contact",
        cascade="all, delete-orphan",
    )
    notes: Mapped[list["ClientNote"]] = relationship(
        "ClientNote",
        back_populates="contact",
        cascade="all, delete-orphan",
    )
    action_items: Mapped[list["ClientActionItem"]] = relationship(
        "ClientActionItem",
        back_populates="contact",
        cascade="all, delete-orphan",
    )
    goals: Mapped[list["ClientGoal"]] = relationship(
        "ClientGoal",
        back_populates="contact",
        cascade="all, delete-orphan",
    )
    testimonials: Mapped[list["Testimonial"]] = relationship(
        "Testimonial",
        back_populates="contact",
    )
    stripe_customer: Mapped["StripeCustomer | None"] = relationship(
        "StripeCustomer",
        back_populates="contact",
        uselist=False,
    )
    subscriptions: Mapped[list["Subscription"]] = relationship(
        "Subscription",
        back_populates="contact",
        cascade="all, delete-orphan",
    )
    recurring_invoices: Mapped[list["RecurringInvoice"]] = relationship(
        "RecurringInvoice",
        back_populates="contact",
        cascade="all, delete-orphan",
    )
    onboarding_assessment: Mapped["OnboardingAssessment | None"] = relationship(
        "OnboardingAssessment",
        back_populates="contact",
        uselist=False,
        cascade="all, delete-orphan",
    )
    coaching_sessions: Mapped[list["CoachingSession"]] = relationship(
        "CoachingSession",
        back_populates="contact",
        cascade="all, delete-orphan",
    )

    @property
    def full_name(self) -> str:
        if self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name


from app.models.organization import Organization
from app.models.interaction import Interaction
from app.models.booking import Booking
from app.models.invoice import Invoice
from app.models.contract import Contract
from app.models.project import Project
from app.models.client_session import ClientSession
from app.models.fathom_webhook import FathomWebhook
from app.models.portal_audit_log import PortalAuditLog
from app.models.client_content import ClientContent
from app.models.client_note import ClientNote
from app.models.client_action_item import ClientActionItem
from app.models.client_goal import ClientGoal
from app.models.testimonial import Testimonial
from app.models.stripe_customer import StripeCustomer
from app.models.subscription import Subscription
from app.models.recurring_invoice import RecurringInvoice
from app.models.onboarding_assessment import OnboardingAssessment
from app.models.coaching_session import CoachingSession
