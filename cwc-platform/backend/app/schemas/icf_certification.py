"""Schemas for ICF Certification Progress."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ICFCertificationProgressBase(BaseModel):
    """Base schema for certification progress."""

    # ACC Training
    acc_training_hours: float = 0
    acc_training_provider: Optional[str] = None
    acc_training_completed: bool = False
    acc_training_completion_date: Optional[datetime] = None
    acc_training_certificate_url: Optional[str] = None

    # PCC Training
    pcc_training_hours: float = 0
    pcc_training_provider: Optional[str] = None
    pcc_training_completed: bool = False
    pcc_training_completion_date: Optional[datetime] = None
    pcc_training_certificate_url: Optional[str] = None

    # ACC Mentor Coaching
    acc_mentor_hours: float = 0
    acc_mentor_individual_hours: float = 0
    acc_mentor_group_hours: float = 0
    acc_mentor_name: Optional[str] = None
    acc_mentor_credential: Optional[str] = None
    acc_mentor_completed: bool = False

    # PCC Mentor Coaching
    pcc_mentor_hours: float = 0
    pcc_mentor_individual_hours: float = 0
    pcc_mentor_group_hours: float = 0
    pcc_mentor_name: Optional[str] = None
    pcc_mentor_credential: Optional[str] = None
    pcc_mentor_completed: bool = False

    # ACC Exam
    acc_exam_passed: bool = False
    acc_exam_date: Optional[datetime] = None
    acc_exam_score: Optional[int] = None

    # PCC Exam
    pcc_exam_passed: bool = False
    pcc_exam_date: Optional[datetime] = None
    pcc_exam_score: Optional[int] = None

    # ACC Application/Credential
    acc_applied: bool = False
    acc_application_date: Optional[datetime] = None
    acc_credential_received: bool = False
    acc_credential_date: Optional[datetime] = None
    acc_credential_number: Optional[str] = None
    acc_expiration_date: Optional[datetime] = None

    # PCC Application/Credential
    pcc_applied: bool = False
    pcc_application_date: Optional[datetime] = None
    pcc_credential_received: bool = False
    pcc_credential_date: Optional[datetime] = None
    pcc_credential_number: Optional[str] = None
    pcc_expiration_date: Optional[datetime] = None

    # MCC Training
    mcc_training_hours: float = 0
    mcc_training_provider: Optional[str] = None
    mcc_training_completed: bool = False
    mcc_training_completion_date: Optional[datetime] = None
    mcc_training_certificate_url: Optional[str] = None

    # MCC Mentor Coaching (10 hours with MCC mentor)
    mcc_mentor_hours: float = 0
    mcc_mentor_individual_hours: float = 0
    mcc_mentor_group_hours: float = 0
    mcc_mentor_name: Optional[str] = None
    mcc_mentor_completed: bool = False

    # MCC Exam (Performance Evaluation)
    mcc_exam_passed: bool = False
    mcc_exam_date: Optional[datetime] = None
    mcc_exam_score: Optional[int] = None

    # MCC Application/Credential
    mcc_applied: bool = False
    mcc_application_date: Optional[datetime] = None
    mcc_credential_received: bool = False
    mcc_credential_date: Optional[datetime] = None
    mcc_credential_number: Optional[str] = None
    mcc_expiration_date: Optional[datetime] = None

    # Notes
    notes: Optional[str] = None


class ICFCertificationProgressUpdate(ICFCertificationProgressBase):
    """Schema for updating certification progress."""
    pass


class ICFCertificationProgressResponse(ICFCertificationProgressBase):
    """Schema for certification progress response."""
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ICFRequirements(BaseModel):
    """ICF certification requirements reference."""

    # ACC Requirements
    acc_training_required: int = 60
    acc_coaching_hours_required: int = 100
    acc_paid_hours_required: int = 75
    acc_clients_required: int = 8
    acc_mentor_hours_required: int = 10
    acc_mentor_individual_required: int = 3
    acc_mentor_group_max: int = 7

    # PCC Requirements
    pcc_training_required: int = 125
    pcc_coaching_hours_required: int = 500
    pcc_paid_hours_required: int = 450
    pcc_clients_required: int = 25
    pcc_mentor_hours_required: int = 10
    pcc_mentor_individual_required: int = 3
    pcc_mentor_group_max: int = 7

    # MCC Requirements
    mcc_training_required: int = 200  # Total training hours required
    mcc_coaching_hours_required: int = 2500
    mcc_paid_hours_required: int = 2250  # 90% must be paid
    mcc_clients_required: int = 35
    mcc_mentor_hours_required: int = 10  # With MCC mentor
    mcc_mentor_individual_required: int = 3
    mcc_mentor_group_max: int = 7


class ICFCertificationDashboard(BaseModel):
    """Combined dashboard with progress and calculated metrics."""

    # Current coaching stats (from coaching_sessions)
    total_coaching_hours: float
    paid_coaching_hours: float
    pro_bono_hours: float
    total_clients: int

    # Requirements reference
    requirements: ICFRequirements

    # ACC Progress
    acc_training_progress: float  # percentage
    acc_coaching_progress: float
    acc_paid_progress: float
    acc_clients_progress: float
    acc_mentor_progress: float
    acc_ready: bool  # All requirements met

    # PCC Progress
    pcc_training_progress: float
    pcc_coaching_progress: float
    pcc_paid_progress: float
    pcc_clients_progress: float
    pcc_mentor_progress: float
    pcc_ready: bool

    # MCC Progress
    mcc_training_progress: float
    mcc_coaching_progress: float
    mcc_paid_progress: float
    mcc_clients_progress: float
    mcc_mentor_progress: float
    mcc_ready: bool

    # Manual tracking data
    progress: Optional[ICFCertificationProgressResponse] = None
