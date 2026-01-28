"""ICF Certification Progress tracking model."""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text
from app.database import Base


class ICFCertificationProgress(Base):
    """Track progress toward ICF ACC and PCC certifications."""

    __tablename__ = "icf_certification_progress"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # ACC Training (60 hours required)
    acc_training_hours = Column(Float, default=0)
    acc_training_provider = Column(String(255), nullable=True)
    acc_training_completed = Column(Boolean, default=False)
    acc_training_completion_date = Column(DateTime, nullable=True)
    acc_training_certificate_url = Column(String(500), nullable=True)

    # PCC Training (125 hours required - additional 65 after ACC)
    pcc_training_hours = Column(Float, default=0)
    pcc_training_provider = Column(String(255), nullable=True)
    pcc_training_completed = Column(Boolean, default=False)
    pcc_training_completion_date = Column(DateTime, nullable=True)
    pcc_training_certificate_url = Column(String(500), nullable=True)

    # ACC Mentor Coaching (10 hours required)
    acc_mentor_hours = Column(Float, default=0)
    acc_mentor_individual_hours = Column(Float, default=0)  # Min 3 hours
    acc_mentor_group_hours = Column(Float, default=0)  # Max 7 hours
    acc_mentor_name = Column(String(255), nullable=True)
    acc_mentor_credential = Column(String(20), nullable=True)  # ACC, PCC, MCC
    acc_mentor_completed = Column(Boolean, default=False)

    # PCC Mentor Coaching (10 hours required with PCC/MCC)
    pcc_mentor_hours = Column(Float, default=0)
    pcc_mentor_individual_hours = Column(Float, default=0)
    pcc_mentor_group_hours = Column(Float, default=0)
    pcc_mentor_name = Column(String(255), nullable=True)
    pcc_mentor_credential = Column(String(20), nullable=True)  # PCC or MCC only
    pcc_mentor_completed = Column(Boolean, default=False)

    # ACC Exam
    acc_exam_passed = Column(Boolean, default=False)
    acc_exam_date = Column(DateTime, nullable=True)
    acc_exam_score = Column(Integer, nullable=True)

    # PCC Exam
    pcc_exam_passed = Column(Boolean, default=False)
    pcc_exam_date = Column(DateTime, nullable=True)
    pcc_exam_score = Column(Integer, nullable=True)

    # ACC Application
    acc_applied = Column(Boolean, default=False)
    acc_application_date = Column(DateTime, nullable=True)
    acc_credential_received = Column(Boolean, default=False)
    acc_credential_date = Column(DateTime, nullable=True)
    acc_credential_number = Column(String(50), nullable=True)
    acc_expiration_date = Column(DateTime, nullable=True)

    # PCC Application
    pcc_applied = Column(Boolean, default=False)
    pcc_application_date = Column(DateTime, nullable=True)
    pcc_credential_received = Column(Boolean, default=False)
    pcc_credential_date = Column(DateTime, nullable=True)
    pcc_credential_number = Column(String(50), nullable=True)
    pcc_expiration_date = Column(DateTime, nullable=True)

    # MCC Training (200 hours total required)
    mcc_training_hours = Column(Float, default=0)
    mcc_training_provider = Column(String(255), nullable=True)
    mcc_training_completed = Column(Boolean, default=False)
    mcc_training_completion_date = Column(DateTime, nullable=True)
    mcc_training_certificate_url = Column(String(500), nullable=True)

    # MCC Mentor Coaching (10 hours with MCC mentor)
    mcc_mentor_hours = Column(Float, default=0)
    mcc_mentor_individual_hours = Column(Float, default=0)
    mcc_mentor_group_hours = Column(Float, default=0)
    mcc_mentor_name = Column(String(255), nullable=True)
    mcc_mentor_completed = Column(Boolean, default=False)

    # MCC Exam (Performance Evaluation)
    mcc_exam_passed = Column(Boolean, default=False)
    mcc_exam_date = Column(DateTime, nullable=True)
    mcc_exam_score = Column(Integer, nullable=True)

    # MCC Application
    mcc_applied = Column(Boolean, default=False)
    mcc_application_date = Column(DateTime, nullable=True)
    mcc_credential_received = Column(Boolean, default=False)
    mcc_credential_date = Column(DateTime, nullable=True)
    mcc_credential_number = Column(String(50), nullable=True)
    mcc_expiration_date = Column(DateTime, nullable=True)

    # Notes
    notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
