"""
Onboarding Assessment API endpoints.
Public endpoints for coachee submission, admin endpoints for management.
"""
import secrets
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.contact import Contact
from app.models.onboarding_assessment import OnboardingAssessment
from app.models.user import User
from app.schemas.onboarding_assessment import (
    OnboardingAssessmentCreate,
    OnboardingAssessmentResponse,
    OnboardingAssessmentPublicData,
    OnboardingAssessmentListItem,
)
from app.services.auth_service import get_current_user
from app.services.email_service import email_service
from app.config import get_settings

settings = get_settings()

router = APIRouter(prefix="/api", tags=["onboarding-assessment"])


# =============================================================================
# PUBLIC ENDPOINTS (Token-based, no authentication required)
# =============================================================================


@router.get("/onboarding/{token}", response_model=OnboardingAssessmentPublicData)
async def get_assessment_by_token(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get assessment info by token (public).
    Used to load the assessment form page.
    """
    result = await db.execute(
        select(OnboardingAssessment)
        .options(selectinload(OnboardingAssessment.contact))
        .where(OnboardingAssessment.token == token)
    )
    assessment = result.scalar_one_or_none()

    if not assessment:
        raise HTTPException(
            status_code=404,
            detail="Assessment not found or link has expired",
        )

    return OnboardingAssessmentPublicData(
        contact_name=assessment.contact.full_name if assessment.contact else "Unknown",
        contact_email=assessment.contact.email if assessment.contact else None,
        already_completed=assessment.completed_at is not None,
    )


@router.post("/onboarding/{token}")
async def submit_assessment(
    token: str,
    data: OnboardingAssessmentCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Submit an onboarding assessment (public).
    """
    result = await db.execute(
        select(OnboardingAssessment)
        .options(selectinload(OnboardingAssessment.contact))
        .where(OnboardingAssessment.token == token)
    )
    assessment = result.scalar_one_or_none()

    if not assessment:
        raise HTTPException(
            status_code=404,
            detail="Assessment not found or link has expired",
        )

    if assessment.completed_at:
        raise HTTPException(
            status_code=400,
            detail="This assessment has already been submitted",
        )

    # Update all fields from submission
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(assessment, field, value)

    assessment.completed_at = datetime.utcnow()

    await db.commit()

    return {"success": True, "message": "Assessment submitted successfully"}


# =============================================================================
# ADMIN ENDPOINTS (Authentication required)
# =============================================================================


@router.get(
    "/onboarding-assessments", response_model=list[OnboardingAssessmentListItem]
)
async def list_assessments(
    status: Optional[str] = None,  # "completed" or "pending"
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all onboarding assessments (admin).
    """
    query = select(OnboardingAssessment).options(
        selectinload(OnboardingAssessment.contact)
    )

    if status == "completed":
        query = query.where(OnboardingAssessment.completed_at.isnot(None))
    elif status == "pending":
        query = query.where(OnboardingAssessment.completed_at.is_(None))

    query = query.order_by(OnboardingAssessment.created_at.desc())

    result = await db.execute(query)
    assessments = result.scalars().all()

    return [
        OnboardingAssessmentListItem(
            id=a.id,
            contact_id=a.contact_id,
            contact_name=a.contact.full_name if a.contact else "Unknown",
            contact_email=a.contact.email if a.contact else None,
            completed_at=a.completed_at,
            email_sent_at=a.email_sent_at,
            created_at=a.created_at,
        )
        for a in assessments
    ]


@router.get(
    "/onboarding-assessments/{assessment_id}",
    response_model=OnboardingAssessmentResponse,
)
async def get_assessment(
    assessment_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get assessment details by ID (admin).
    """
    result = await db.execute(
        select(OnboardingAssessment)
        .options(selectinload(OnboardingAssessment.contact))
        .where(OnboardingAssessment.id == assessment_id)
    )
    assessment = result.scalar_one_or_none()

    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    response = OnboardingAssessmentResponse.model_validate(assessment)
    response.contact_name = assessment.contact.full_name if assessment.contact else None
    response.contact_email = assessment.contact.email if assessment.contact else None

    return response


@router.get(
    "/contacts/{contact_id}/onboarding",
    response_model=Optional[OnboardingAssessmentResponse],
)
async def get_assessment_for_contact(
    contact_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get assessment for a specific contact (admin).
    """
    result = await db.execute(
        select(OnboardingAssessment)
        .options(selectinload(OnboardingAssessment.contact))
        .where(OnboardingAssessment.contact_id == contact_id)
    )
    assessment = result.scalar_one_or_none()

    if not assessment:
        return None

    response = OnboardingAssessmentResponse.model_validate(assessment)
    response.contact_name = assessment.contact.full_name if assessment.contact else None
    response.contact_email = assessment.contact.email if assessment.contact else None

    return response


@router.post("/contacts/{contact_id}/onboarding/create")
async def create_assessment_for_contact(
    contact_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create an onboarding assessment for a contact (admin).
    Used to manually trigger assessment for a contact.
    """
    # Check if contact exists
    contact_result = await db.execute(
        select(Contact).where(Contact.id == contact_id)
    )
    contact = contact_result.scalar_one_or_none()

    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    # Check if assessment already exists
    existing = await db.execute(
        select(OnboardingAssessment).where(
            OnboardingAssessment.contact_id == contact_id
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="Assessment already exists for this contact",
        )

    # Create assessment
    assessment = OnboardingAssessment(
        contact_id=contact_id,
        token=secrets.token_urlsafe(32),
    )
    db.add(assessment)
    await db.commit()
    await db.refresh(assessment)

    return {
        "id": assessment.id,
        "token": assessment.token,
        "assessment_url": f"{settings.frontend_url}/onboarding/{assessment.token}",
    }


@router.post("/contacts/{contact_id}/onboarding/resend")
async def resend_assessment_email(
    contact_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Resend the onboarding assessment email (admin).
    """
    result = await db.execute(
        select(OnboardingAssessment)
        .options(selectinload(OnboardingAssessment.contact))
        .where(OnboardingAssessment.contact_id == contact_id)
    )
    assessment = result.scalar_one_or_none()

    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    if assessment.completed_at:
        raise HTTPException(
            status_code=400,
            detail="Assessment has already been completed",
        )

    if not assessment.contact or not assessment.contact.email:
        raise HTTPException(
            status_code=400,
            detail="Contact has no email address",
        )

    # Send email
    assessment_url = f"{settings.frontend_url}/onboarding/{assessment.token}"
    await email_service.send_onboarding_assessment(
        contact=assessment.contact,
        assessment_url=assessment_url,
    )

    # Update sent timestamp
    assessment.email_sent_at = datetime.utcnow()
    await db.commit()

    return {"success": True, "message": "Assessment email sent"}
