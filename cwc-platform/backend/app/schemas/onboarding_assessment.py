"""
Pydantic schemas for Onboarding Assessment.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# Coaching motivation options
COACHING_MOTIVATIONS = [
    "career_transition",
    "new_role",
    "workplace_challenges",
    "work_life_balance",
    "leadership_step",
]

# Feedback preference options
FEEDBACK_PREFERENCES = ["direct", "gentle", "both", "explore"]


class OnboardingAssessmentCreate(BaseModel):
    """Schema for submitting an onboarding assessment."""

    # Section 1: Client Context
    name_pronouns: Optional[str] = None
    phone: Optional[str] = None
    role_title: Optional[str] = None
    organization_industry: Optional[str] = None
    time_in_role: Optional[str] = None
    role_description: Optional[str] = None
    coaching_motivations: Optional[list[str]] = None

    # Section 2: Self Assessment (1-10 ratings)
    confidence_leadership: Optional[int] = Field(None, ge=1, le=10)
    feeling_respected: Optional[int] = Field(None, ge=1, le=10)
    clear_goals_short_term: Optional[int] = Field(None, ge=1, le=10)
    clear_goals_long_term: Optional[int] = Field(None, ge=1, le=10)
    work_life_balance: Optional[int] = Field(None, ge=1, le=10)
    stress_management: Optional[int] = Field(None, ge=1, le=10)
    access_mentors: Optional[int] = Field(None, ge=1, le=10)
    navigate_bias: Optional[int] = Field(None, ge=1, le=10)
    communication_effectiveness: Optional[int] = Field(None, ge=1, le=10)
    taking_up_space: Optional[int] = Field(None, ge=1, le=10)
    team_advocacy: Optional[int] = Field(None, ge=1, le=10)
    career_satisfaction: Optional[int] = Field(None, ge=1, le=10)
    priority_focus_areas: Optional[str] = None

    # Section 3: Identity & Workplace Experience
    workplace_experience: Optional[str] = None
    self_doubt_patterns: Optional[str] = None
    habits_to_shift: Optional[str] = None

    # Section 4: Goals for Coaching
    coaching_goal: Optional[str] = None
    success_evidence: Optional[str] = None
    thriving_vision: Optional[str] = None

    # Section 5: Wellbeing & Support
    commitment_time: Optional[int] = Field(None, ge=1, le=10)
    commitment_energy: Optional[int] = Field(None, ge=1, le=10)
    commitment_focus: Optional[int] = Field(None, ge=1, le=10)
    potential_barriers: Optional[str] = None
    support_needed: Optional[str] = None
    feedback_preference: Optional[str] = None
    sensitive_topics: Optional[str] = None

    # Section 6: Logistics & Preferences
    scheduling_preferences: Optional[str] = None


class OnboardingAssessmentResponse(BaseModel):
    """Full assessment response for admin/client viewing."""

    id: str
    contact_id: str
    token: str

    # Section 1: Client Context
    name_pronouns: Optional[str] = None
    phone: Optional[str] = None
    role_title: Optional[str] = None
    organization_industry: Optional[str] = None
    time_in_role: Optional[str] = None
    role_description: Optional[str] = None
    coaching_motivations: Optional[list[str]] = None

    # Section 2: Self Assessment
    confidence_leadership: Optional[int] = None
    feeling_respected: Optional[int] = None
    clear_goals_short_term: Optional[int] = None
    clear_goals_long_term: Optional[int] = None
    work_life_balance: Optional[int] = None
    stress_management: Optional[int] = None
    access_mentors: Optional[int] = None
    navigate_bias: Optional[int] = None
    communication_effectiveness: Optional[int] = None
    taking_up_space: Optional[int] = None
    team_advocacy: Optional[int] = None
    career_satisfaction: Optional[int] = None
    priority_focus_areas: Optional[str] = None

    # Section 3: Identity & Workplace Experience
    workplace_experience: Optional[str] = None
    self_doubt_patterns: Optional[str] = None
    habits_to_shift: Optional[str] = None

    # Section 4: Goals for Coaching
    coaching_goal: Optional[str] = None
    success_evidence: Optional[str] = None
    thriving_vision: Optional[str] = None

    # Section 5: Wellbeing & Support
    commitment_time: Optional[int] = None
    commitment_energy: Optional[int] = None
    commitment_focus: Optional[int] = None
    potential_barriers: Optional[str] = None
    support_needed: Optional[str] = None
    feedback_preference: Optional[str] = None
    sensitive_topics: Optional[str] = None

    # Section 6: Logistics & Preferences
    scheduling_preferences: Optional[str] = None

    # Tracking
    email_sent_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    # Contact info (for admin list view)
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None

    class Config:
        from_attributes = True


class OnboardingAssessmentPublicData(BaseModel):
    """Minimal data for public page load (before submission)."""

    contact_name: str
    contact_email: Optional[str] = None
    already_completed: bool


class OnboardingAssessmentListItem(BaseModel):
    """Summary item for listing assessments."""

    id: str
    contact_id: str
    contact_name: str
    contact_email: Optional[str] = None
    completed_at: Optional[datetime] = None
    email_sent_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True
