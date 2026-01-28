"""
Onboarding Assessment model for coachee intake forms.
"""
import uuid
import secrets
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.contact import Contact


class OnboardingAssessment(Base):
    """
    Onboarding assessment form completed by coachees after payment.
    One-time assessment required before first coaching session.
    """

    __tablename__ = "onboarding_assessments"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    contact_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("contacts.id", ondelete="CASCADE"),
        unique=True,
        index=True,
    )
    token: Mapped[str] = mapped_column(
        String(64), unique=True, default=lambda: secrets.token_urlsafe(32)
    )

    # Section 1: Client Context
    name_pronouns: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    role_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    organization_industry: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    time_in_role: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    role_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    coaching_motivations: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    # Section 2: Self Assessment (1-10 ratings)
    confidence_leadership: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    feeling_respected: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    clear_goals_short_term: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    clear_goals_long_term: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    work_life_balance: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    stress_management: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    access_mentors: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    navigate_bias: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    communication_effectiveness: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )
    taking_up_space: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    team_advocacy: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    career_satisfaction: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    priority_focus_areas: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Section 3: Identity & Workplace Experience
    workplace_experience: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    self_doubt_patterns: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    habits_to_shift: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Section 4: Goals for Coaching
    coaching_goal: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    success_evidence: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    thriving_vision: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Section 5: Wellbeing & Support
    commitment_time: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    commitment_energy: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    commitment_focus: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    potential_barriers: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    support_needed: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    feedback_preference: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # direct, gentle, both, explore
    sensitive_topics: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Section 6: Logistics & Preferences
    scheduling_preferences: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Tracking
    email_sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Reminder tracking (assessment not completed)
    reminder_day1_sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    reminder_day3_sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    reminder_day7_sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Welcome series tracking (after assessment completed)
    welcome_day0_sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    welcome_day3_sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    welcome_day7_sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    contact: Mapped["Contact"] = relationship(
        "Contact", back_populates="onboarding_assessment"
    )
