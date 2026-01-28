"""Organizational Needs Assessment model."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, Text, DateTime, JSON, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.contact import Contact
    from app.models.organization import Organization
    from app.models.booking import Booking


class OrganizationalAssessment(Base):
    """Stores organizational needs assessment submissions."""

    __tablename__ = "organizational_assessments"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )

    # Contact info (creates or links to contact/organization)
    contact_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True
    )
    organization_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True
    )

    # Section 1: Contact Information
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    title_role: Mapped[str] = mapped_column(String(200), nullable=False)
    organization_name: Mapped[str] = mapped_column(String(200), nullable=False)
    work_email: Mapped[str] = mapped_column(String(200), nullable=False)
    phone_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    organization_website: Mapped[str | None] = mapped_column(String(300), nullable=True)

    # Section 2: Areas of Interest (multi-select stored as JSON array)
    areas_of_interest: Mapped[list] = mapped_column(JSON, default=list)
    # Options: executive_coaching, group_coaching, keynote_speaking,
    #          webinars_workshops, virtual_series, other
    areas_of_interest_other: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Section 3: Goals and Needs
    desired_outcomes: Mapped[list] = mapped_column(JSON, default=list)
    # Options: executive_presence, communication_collaboration, psychological_safety,
    #          navigating_bias, retention_engagement, inclusive_leadership, team_reset, other
    desired_outcomes_other: Mapped[str | None] = mapped_column(Text, nullable=True)
    current_challenge: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Audience
    primary_audience: Mapped[list] = mapped_column(JSON, default=list)
    # Options: senior_leaders, mid_level_managers, high_potential, specific_team,
    #          erg_affinity, organization_wide, other
    primary_audience_other: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Participants
    participant_count: Mapped[str | None] = mapped_column(String(20), nullable=True)
    # Options: 1-5, 6-15, 16-30, 31-50, 51-100, 100+

    # Format
    preferred_format: Mapped[str | None] = mapped_column(String(20), nullable=True)
    # Options: virtual, in_person, hybrid, not_sure
    location: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Section 4: Budget and Timeline
    budget_range: Mapped[str | None] = mapped_column(String(30), nullable=True)
    # Options: under_5k, 5k_10k, 10k_20k, 20k_40k, 40k_plus, not_sure
    specific_budget: Mapped[str | None] = mapped_column(String(100), nullable=True)

    ideal_timeline: Mapped[str | None] = mapped_column(String(30), nullable=True)
    # Options: asap, 1_2_months, 3_4_months, 5_plus_months, not_sure
    specific_date: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Section 5: Decision Process
    decision_makers: Mapped[list] = mapped_column(JSON, default=list)
    # Options: self, hr, ld_talent, dei, executive, procurement, other
    decision_makers_other: Mapped[str | None] = mapped_column(Text, nullable=True)

    decision_stage: Mapped[str | None] = mapped_column(String(30), nullable=True)
    # Options: exploring, comparing, ready_to_select, need_approval, other
    decision_stage_other: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Section 6: Additional Context
    success_definition: Mapped[str | None] = mapped_column(Text, nullable=True)
    accessibility_needs: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Tracking
    booking_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("bookings.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="submitted")
    # Options: submitted, reviewed, contacted, converted, archived

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    contact: Mapped["Contact | None"] = relationship("Contact")
    organization: Mapped["Organization | None"] = relationship("Organization")
    booking: Mapped["Booking | None"] = relationship("Booking")

    def __repr__(self) -> str:
        return f"<OrganizationalAssessment {self.id} - {self.organization_name}>"
