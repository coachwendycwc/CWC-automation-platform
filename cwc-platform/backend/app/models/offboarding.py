"""Offboarding workflow models."""

from datetime import datetime
from typing import Optional
import uuid

from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, Integer, JSON
from sqlalchemy.orm import relationship

from app.database import Base


class OffboardingWorkflow(Base):
    """Offboarding workflow for clients, projects, or contracts."""

    __tablename__ = "offboarding_workflows"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    contact_id = Column(String(36), ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False)

    # Workflow type
    workflow_type = Column(String(20), nullable=False)  # "client", "project", "contract"
    related_project_id = Column(String(36), ForeignKey("projects.id", ondelete="SET NULL"), nullable=True)
    related_contract_id = Column(String(36), ForeignKey("contracts.id", ondelete="SET NULL"), nullable=True)

    # Status tracking
    status = Column(String(20), nullable=False, default="pending")  # pending, in_progress, completed, cancelled
    initiated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Checklist items (JSON array)
    checklist = Column(JSON, nullable=False, default=list)  # [{item: str, completed: bool, completed_at: str}]

    # Options
    send_survey = Column(Boolean, nullable=False, default=True)
    request_testimonial = Column(Boolean, nullable=False, default=True)
    send_certificate = Column(Boolean, nullable=False, default=False)

    # Survey tracking
    survey_sent_at = Column(DateTime, nullable=True)
    survey_token = Column(String(64), unique=True, nullable=True)
    survey_completed_at = Column(DateTime, nullable=True)
    survey_response = Column(JSON, nullable=True)

    # Testimonial tracking
    testimonial_requested_at = Column(DateTime, nullable=True)
    testimonial_token = Column(String(64), unique=True, nullable=True)
    testimonial_received = Column(Boolean, nullable=False, default=False)
    testimonial_text = Column(Text, nullable=True)
    testimonial_author_name = Column(String(200), nullable=True)
    testimonial_author_title = Column(String(200), nullable=True)
    testimonial_photo_url = Column(Text, nullable=True)  # Base64 encoded photo or URL
    testimonial_permission_granted = Column(Boolean, nullable=False, default=False)
    testimonial_approved = Column(Boolean, nullable=False, default=False)

    # Notes
    notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    contact = relationship("Contact", backref="offboarding_workflows")
    related_project = relationship("Project", backref="offboarding_workflows")
    related_contract = relationship("Contract", backref="offboarding_workflows")
    activities = relationship("OffboardingActivity", back_populates="workflow", cascade="all, delete-orphan")


class OffboardingTemplate(Base):
    """Template for offboarding workflows."""

    __tablename__ = "offboarding_templates"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    workflow_type = Column(String(20), nullable=False)  # "client", "project", "contract"

    # Default checklist items (JSON array of strings)
    checklist_items = Column(JSON, nullable=False, default=list)

    # Email templates
    completion_email_subject = Column(String(200), nullable=True)
    completion_email_body = Column(Text, nullable=True)
    survey_email_subject = Column(String(200), nullable=True)
    survey_email_body = Column(Text, nullable=True)
    testimonial_email_subject = Column(String(200), nullable=True)
    testimonial_email_body = Column(Text, nullable=True)

    # Timing (days after initiation)
    survey_delay_days = Column(Integer, nullable=False, default=3)
    testimonial_delay_days = Column(Integer, nullable=False, default=7)

    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class OffboardingActivity(Base):
    """Activity log for offboarding workflows."""

    __tablename__ = "offboarding_activities"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workflow_id = Column(String(36), ForeignKey("offboarding_workflows.id", ondelete="CASCADE"), nullable=False)

    action = Column(String(50), nullable=False)  # initiated, checklist_updated, survey_sent, completed, etc.
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationship
    workflow = relationship("OffboardingWorkflow", back_populates="activities")
