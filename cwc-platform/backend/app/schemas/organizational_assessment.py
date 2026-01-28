"""Pydantic schemas for organizational needs assessments."""

from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, EmailStr, Field, ConfigDict


# Field option types
AreaOfInterest = Literal[
    "executive_coaching",
    "group_coaching",
    "keynote_speaking",
    "webinars_workshops",
    "virtual_series",
    "other"
]

DesiredOutcome = Literal[
    "executive_presence",
    "communication_collaboration",
    "psychological_safety",
    "navigating_bias",
    "retention_engagement",
    "inclusive_leadership",
    "team_reset",
    "other"
]

PrimaryAudience = Literal[
    "senior_leaders",
    "mid_level_managers",
    "high_potential",
    "specific_team",
    "erg_affinity",
    "organization_wide",
    "other"
]

ParticipantCount = Literal["1-5", "6-15", "16-30", "31-50", "51-100", "100+"]

PreferredFormat = Literal["virtual", "in_person", "hybrid", "not_sure"]

BudgetRange = Literal[
    "under_5k",
    "5k_10k",
    "10k_20k",
    "20k_40k",
    "40k_plus",
    "not_sure"
]

IdealTimeline = Literal[
    "asap",
    "1_2_months",
    "3_4_months",
    "5_plus_months",
    "not_sure"
]

DecisionMaker = Literal[
    "self",
    "hr",
    "ld_talent",
    "dei",
    "executive",
    "procurement",
    "other"
]

DecisionStage = Literal[
    "exploring",
    "comparing",
    "ready_to_select",
    "need_approval",
    "other"
]

AssessmentStatus = Literal["submitted", "reviewed", "contacted", "converted", "archived"]


class OrganizationalAssessmentCreate(BaseModel):
    """Schema for submitting a new assessment (public form)."""

    # Section 1: Contact Information
    full_name: str = Field(..., min_length=2, max_length=200)
    title_role: str = Field(..., min_length=2, max_length=200)
    organization_name: str = Field(..., min_length=2, max_length=200)
    work_email: EmailStr
    phone_number: Optional[str] = Field(None, max_length=50)
    organization_website: Optional[str] = Field(None, max_length=300)

    # Section 2: Areas of Interest
    areas_of_interest: list[AreaOfInterest] = Field(default_factory=list, min_length=1)
    areas_of_interest_other: Optional[str] = None

    # Section 3: Goals and Needs
    desired_outcomes: list[DesiredOutcome] = Field(default_factory=list)
    desired_outcomes_other: Optional[str] = None
    current_challenge: Optional[str] = None

    # Audience
    primary_audience: list[PrimaryAudience] = Field(default_factory=list)
    primary_audience_other: Optional[str] = None
    participant_count: Optional[ParticipantCount] = None

    # Format
    preferred_format: Optional[PreferredFormat] = None
    location: Optional[str] = Field(None, max_length=200)

    # Section 4: Budget and Timeline
    budget_range: Optional[BudgetRange] = None
    specific_budget: Optional[str] = Field(None, max_length=100)
    ideal_timeline: Optional[IdealTimeline] = None
    specific_date: Optional[str] = Field(None, max_length=200)

    # Section 5: Decision Process
    decision_makers: list[DecisionMaker] = Field(default_factory=list)
    decision_makers_other: Optional[str] = None
    decision_stage: Optional[DecisionStage] = None
    decision_stage_other: Optional[str] = None

    # Section 6: Additional Context
    success_definition: Optional[str] = None
    accessibility_needs: Optional[str] = None


class OrganizationalAssessmentUpdate(BaseModel):
    """Schema for updating assessment status (admin)."""
    status: Optional[AssessmentStatus] = None
    booking_id: Optional[str] = None


class OrganizationalAssessmentRead(BaseModel):
    """Schema for reading assessment data."""
    id: str

    # Contact info
    full_name: str
    title_role: str
    organization_name: str
    work_email: str
    phone_number: Optional[str] = None
    organization_website: Optional[str] = None

    # Areas of interest
    areas_of_interest: list[str]
    areas_of_interest_other: Optional[str] = None

    # Goals
    desired_outcomes: list[str]
    desired_outcomes_other: Optional[str] = None
    current_challenge: Optional[str] = None

    # Audience
    primary_audience: list[str]
    primary_audience_other: Optional[str] = None
    participant_count: Optional[str] = None

    # Format
    preferred_format: Optional[str] = None
    location: Optional[str] = None

    # Budget/Timeline
    budget_range: Optional[str] = None
    specific_budget: Optional[str] = None
    ideal_timeline: Optional[str] = None
    specific_date: Optional[str] = None

    # Decision
    decision_makers: list[str]
    decision_makers_other: Optional[str] = None
    decision_stage: Optional[str] = None
    decision_stage_other: Optional[str] = None

    # Additional
    success_definition: Optional[str] = None
    accessibility_needs: Optional[str] = None

    # Tracking
    contact_id: Optional[str] = None
    organization_id: Optional[str] = None
    booking_id: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrganizationalAssessmentList(BaseModel):
    """List response."""
    items: list[OrganizationalAssessmentRead]
    total: int


class OrganizationalAssessmentSubmitResponse(BaseModel):
    """Response after submitting assessment."""
    id: str
    message: str
    booking_url: Optional[str] = None
