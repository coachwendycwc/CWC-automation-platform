"""Pydantic schemas for offboarding workflows."""

from datetime import datetime, date
from typing import Optional, Literal
from pydantic import BaseModel, Field


# ============== Checklist Item ==============

class ChecklistItem(BaseModel):
    """A single checklist item."""
    item: str
    completed: bool = False
    completed_at: Optional[datetime] = None


# ============== Offboarding Workflow ==============

WorkflowType = Literal["client", "project", "contract"]
WorkflowStatus = Literal["pending", "in_progress", "completed", "cancelled"]


class OffboardingWorkflowCreate(BaseModel):
    """Schema for creating an offboarding workflow."""
    contact_id: str
    workflow_type: WorkflowType
    related_project_id: Optional[str] = None
    related_contract_id: Optional[str] = None
    template_id: Optional[str] = None  # Optional template to use
    send_survey: bool = True
    request_testimonial: bool = True
    send_certificate: bool = False
    notes: Optional[str] = None


class OffboardingWorkflowUpdate(BaseModel):
    """Schema for updating an offboarding workflow."""
    send_survey: Optional[bool] = None
    request_testimonial: Optional[bool] = None
    send_certificate: Optional[bool] = None
    notes: Optional[str] = None


class OffboardingWorkflowRead(BaseModel):
    """Schema for reading an offboarding workflow."""
    id: str
    contact_id: str
    workflow_type: str
    related_project_id: Optional[str]
    related_contract_id: Optional[str]
    status: str
    initiated_at: datetime
    completed_at: Optional[datetime]
    checklist: list[dict]
    send_survey: bool
    request_testimonial: bool
    send_certificate: bool
    survey_sent_at: Optional[datetime]
    survey_completed_at: Optional[datetime]
    survey_response: Optional[dict]
    testimonial_requested_at: Optional[datetime]
    testimonial_received: bool
    testimonial_text: Optional[str]
    testimonial_photo_url: Optional[str] = None
    testimonial_approved: bool
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OffboardingWorkflowDetail(OffboardingWorkflowRead):
    """Extended schema with related data."""
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    project_title: Optional[str] = None
    contract_title: Optional[str] = None
    survey_token: Optional[str] = None
    testimonial_token: Optional[str] = None
    activities: list["OffboardingActivityRead"] = []

    class Config:
        from_attributes = True


class OffboardingWorkflowList(BaseModel):
    """Schema for list response."""
    items: list[OffboardingWorkflowRead]
    total: int


# ============== Offboarding Template ==============

class OffboardingTemplateCreate(BaseModel):
    """Schema for creating an offboarding template."""
    name: str
    description: Optional[str] = None
    workflow_type: WorkflowType
    checklist_items: list[str] = []
    completion_email_subject: Optional[str] = None
    completion_email_body: Optional[str] = None
    survey_email_subject: Optional[str] = None
    survey_email_body: Optional[str] = None
    testimonial_email_subject: Optional[str] = None
    testimonial_email_body: Optional[str] = None
    survey_delay_days: int = 3
    testimonial_delay_days: int = 7


class OffboardingTemplateUpdate(BaseModel):
    """Schema for updating an offboarding template."""
    name: Optional[str] = None
    description: Optional[str] = None
    checklist_items: Optional[list[str]] = None
    completion_email_subject: Optional[str] = None
    completion_email_body: Optional[str] = None
    survey_email_subject: Optional[str] = None
    survey_email_body: Optional[str] = None
    testimonial_email_subject: Optional[str] = None
    testimonial_email_body: Optional[str] = None
    survey_delay_days: Optional[int] = None
    testimonial_delay_days: Optional[int] = None
    is_active: Optional[bool] = None


class OffboardingTemplateRead(BaseModel):
    """Schema for reading an offboarding template."""
    id: str
    name: str
    description: Optional[str]
    workflow_type: str
    checklist_items: list[str]
    completion_email_subject: Optional[str]
    completion_email_body: Optional[str]
    survey_email_subject: Optional[str]
    survey_email_body: Optional[str]
    testimonial_email_subject: Optional[str]
    testimonial_email_body: Optional[str]
    survey_delay_days: int
    testimonial_delay_days: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============== Offboarding Activity ==============

class OffboardingActivityRead(BaseModel):
    """Schema for reading an offboarding activity."""
    id: str
    workflow_id: str
    action: str
    details: Optional[dict]
    created_at: datetime

    class Config:
        from_attributes = True


# ============== Survey & Testimonial ==============

# Outcome options for checkboxes
OUTCOME_OPTIONS = [
    "increased_confidence",
    "stronger_communication",
    "clearer_decision_making",
    "better_boundaries",
    "navigated_bias",
    "career_move_promotion",
    "pay_increase",
    "improved_work_relationships",
    "reduced_imposter_syndrome",
    "clarity_on_identity",
]

# Helpful parts options for checkboxes
HELPFUL_PARTS_OPTIONS = [
    "powerful_questions",
    "practical_tools",
    "accountability",
    "role_play",
    "mindset_work",
    "values_identity_work",
    "navigating_bias_support",
    "resources_homework",
]


class SurveyResponse(BaseModel):
    """Schema for comprehensive end-of-engagement survey response."""

    # Section 1: Overall Experience
    satisfaction_rating: int = Field(..., ge=1, le=10)  # 1-10 scale
    nps_score: int = Field(..., ge=0, le=10)  # 0-10 NPS
    initial_goals: Optional[str] = None  # What were you hoping to get

    # Section 2: Growth + Measurement (Outcomes)
    outcomes: Optional[list[str]] = None  # List of outcome checkboxes
    outcomes_other: Optional[str] = None  # "Other" text field
    specific_wins: Optional[str] = None  # 1-3 specific wins
    progress_rating: Optional[int] = Field(None, ge=1, le=10)  # Progress toward goals
    most_transformative: Optional[str] = None  # What felt most transformative

    # Section 3: Coaching Process (What Worked)
    helpful_parts: Optional[list[str]] = None  # List of helpful checkboxes
    helpful_parts_other: Optional[str] = None  # "Other" text field
    least_helpful: Optional[str] = None  # What was least helpful
    wish_done_earlier: Optional[str] = None  # What to do earlier

    # Section 4: Equity, Safety, and Support
    psychological_safety: Optional[str] = None  # strongly_agree, agree, neutral, disagree, strongly_disagree
    woc_support_rating: Optional[int] = Field(None, ge=1, le=10)  # WOC support rating
    support_feedback: Optional[str] = None  # What helped feel supported

    # Section 5: Testimonial Permission (kept with survey for convenience)
    may_share_testimonial: Optional[str] = None  # "yes_with_name", "not_now"
    display_name_title: Optional[str] = None  # How to display name/title
    written_testimonial: Optional[str] = None  # Written testimonial text
    willing_to_record_video: Optional[bool] = None  # Open to video testimonial
    video_upload_preference: Optional[str] = None  # portal, email, link, text

    # Video testimonial data (if recorded in form)
    video_url: Optional[str] = None  # Cloudinary video URL
    video_public_id: Optional[str] = None  # Cloudinary public ID
    video_duration_seconds: Optional[int] = None  # Video duration
    video_thumbnail_url: Optional[str] = None  # Thumbnail URL

    # Legacy fields for backward compatibility
    most_valued: Optional[str] = None
    improvement_suggestions: Optional[str] = None
    additional_comments: Optional[str] = None


class SurveyPublicData(BaseModel):
    """Public data shown on survey page."""
    contact_name: str
    workflow_type: str
    project_title: Optional[str] = None
    already_completed: bool = False


class TestimonialSubmission(BaseModel):
    """Schema for testimonial submission."""
    testimonial_text: str = Field(..., min_length=10, max_length=2000)
    author_name: str
    author_title: Optional[str] = None
    photo: Optional[str] = None  # Base64 encoded photo
    permission_granted: bool = False  # Permission to use publicly


class TestimonialPublicData(BaseModel):
    """Public data shown on testimonial page."""
    contact_name: str
    workflow_type: str
    already_submitted: bool = False


# ============== Stats ==============

class OffboardingStats(BaseModel):
    """Statistics for offboarding dashboard."""
    total_workflows: int
    pending: int
    in_progress: int
    completed: int
    cancelled: int
    surveys_sent: int
    surveys_completed: int
    testimonials_received: int
    testimonials_approved: int
    avg_satisfaction: Optional[float] = None
    avg_nps: Optional[float] = None


# Update forward references
OffboardingWorkflowDetail.model_rebuild()
