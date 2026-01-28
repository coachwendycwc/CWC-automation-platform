"""
Organizational Assessments router.
Handles public form submission and admin management.
"""
import os
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.organizational_assessment import OrganizationalAssessment
from app.models.contact import Contact
from app.models.organization import Organization
from app.services.email_service import email_service
from app.schemas.organizational_assessment import (
    OrganizationalAssessmentCreate,
    OrganizationalAssessmentUpdate,
    OrganizationalAssessmentRead,
    OrganizationalAssessmentList,
    OrganizationalAssessmentSubmitResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/assessments", tags=["assessments"])


# ==================== Public Endpoints ====================


@router.post("/organizations/submit", response_model=OrganizationalAssessmentSubmitResponse, status_code=201)
async def submit_assessment(
    data: OrganizationalAssessmentCreate,
    db: AsyncSession = Depends(get_db),
):
    """Submit an organizational needs assessment (public)."""

    # Check if contact already exists by email
    result = await db.execute(
        select(Contact).where(Contact.email == data.work_email)
    )
    contact = result.scalar_one_or_none()

    # Check if organization exists by name
    result = await db.execute(
        select(Organization).where(Organization.name == data.organization_name)
    )
    organization = result.scalar_one_or_none()

    # Create organization if doesn't exist
    if not organization:
        organization = Organization(
            name=data.organization_name,
            website=data.organization_website,
        )
        db.add(organization)
        await db.flush()

    # Create contact if doesn't exist
    if not contact:
        # Split full name
        name_parts = data.full_name.strip().split(" ", 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ""

        contact = Contact(
            first_name=first_name,
            last_name=last_name,
            email=data.work_email,
            phone=data.phone_number,
            title=data.title_role,
            contact_type="lead",
            organization_id=organization.id,
        )
        db.add(contact)
        await db.flush()
    else:
        # Update contact with organization if not linked
        if not contact.organization_id:
            contact.organization_id = organization.id

    # Create assessment
    assessment = OrganizationalAssessment(
        contact_id=contact.id,
        organization_id=organization.id,
        full_name=data.full_name,
        title_role=data.title_role,
        organization_name=data.organization_name,
        work_email=data.work_email,
        phone_number=data.phone_number,
        organization_website=data.organization_website,
        areas_of_interest=data.areas_of_interest,
        areas_of_interest_other=data.areas_of_interest_other,
        desired_outcomes=data.desired_outcomes,
        desired_outcomes_other=data.desired_outcomes_other,
        current_challenge=data.current_challenge,
        primary_audience=data.primary_audience,
        primary_audience_other=data.primary_audience_other,
        participant_count=data.participant_count,
        preferred_format=data.preferred_format,
        location=data.location,
        budget_range=data.budget_range,
        specific_budget=data.specific_budget,
        ideal_timeline=data.ideal_timeline,
        specific_date=data.specific_date,
        decision_makers=data.decision_makers,
        decision_makers_other=data.decision_makers_other,
        decision_stage=data.decision_stage,
        decision_stage_other=data.decision_stage_other,
        success_definition=data.success_definition,
        accessibility_needs=data.accessibility_needs,
        status="submitted",
    )
    db.add(assessment)
    await db.commit()
    await db.refresh(assessment)

    logger.info(f"New organizational assessment from {data.organization_name}")

    # Send notification email to admin
    try:
        admin_email = os.getenv("COACH_EMAIL")
        if admin_email:
            await email_service.send_assessment_notification(
                assessment=assessment,
                admin_email=admin_email,
            )
    except Exception as e:
        logger.error(f"Failed to send assessment notification: {e}")

    # Build booking URL (discovery call)
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3001")
    booking_url = f"{frontend_url}/book/discovery-call?assessment_id={assessment.id}"

    return OrganizationalAssessmentSubmitResponse(
        id=assessment.id,
        message="Thank you! Your needs assessment has been submitted. Please book a discovery call to discuss your goals.",
        booking_url=booking_url,
    )


# ==================== Admin Endpoints ====================


@router.get("", response_model=OrganizationalAssessmentList)
async def list_assessments(
    db: AsyncSession = Depends(get_db),
    status: Optional[str] = Query(None, description="Filter by status"),
    search: Optional[str] = Query(None, description="Search by org name or email"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    """List all organizational assessments (admin)."""
    query = select(OrganizationalAssessment)

    if status:
        query = query.where(OrganizationalAssessment.status == status)

    if search:
        search_term = f"%{search}%"
        query = query.where(
            (OrganizationalAssessment.organization_name.ilike(search_term)) |
            (OrganizationalAssessment.work_email.ilike(search_term)) |
            (OrganizationalAssessment.full_name.ilike(search_term))
        )

    # Count
    count_query = select(func.count(OrganizationalAssessment.id))
    if status:
        count_query = count_query.where(OrganizationalAssessment.status == status)
    if search:
        count_query = count_query.where(
            (OrganizationalAssessment.organization_name.ilike(search_term)) |
            (OrganizationalAssessment.work_email.ilike(search_term)) |
            (OrganizationalAssessment.full_name.ilike(search_term))
        )

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Get results
    query = query.order_by(OrganizationalAssessment.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    assessments = result.scalars().all()

    return OrganizationalAssessmentList(
        items=[OrganizationalAssessmentRead.model_validate(a) for a in assessments],
        total=total,
    )


@router.get("/stats")
async def get_assessment_stats(
    db: AsyncSession = Depends(get_db),
):
    """Get assessment statistics."""
    stats = {}

    for status in ["submitted", "reviewed", "contacted", "converted", "archived"]:
        result = await db.execute(
            select(func.count(OrganizationalAssessment.id))
            .where(OrganizationalAssessment.status == status)
        )
        stats[status] = result.scalar() or 0

    # Total
    result = await db.execute(select(func.count(OrganizationalAssessment.id)))
    stats["total"] = result.scalar() or 0

    return stats


@router.get("/{assessment_id}", response_model=OrganizationalAssessmentRead)
async def get_assessment(
    assessment_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a single assessment (admin)."""
    result = await db.execute(
        select(OrganizationalAssessment)
        .options(
            selectinload(OrganizationalAssessment.contact),
            selectinload(OrganizationalAssessment.organization),
            selectinload(OrganizationalAssessment.booking),
        )
        .where(OrganizationalAssessment.id == assessment_id)
    )
    assessment = result.scalar_one_or_none()

    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    return OrganizationalAssessmentRead.model_validate(assessment)


@router.put("/{assessment_id}", response_model=OrganizationalAssessmentRead)
async def update_assessment(
    assessment_id: str,
    data: OrganizationalAssessmentUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update assessment status (admin)."""
    result = await db.execute(
        select(OrganizationalAssessment)
        .where(OrganizationalAssessment.id == assessment_id)
    )
    assessment = result.scalar_one_or_none()

    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    if data.status is not None:
        assessment.status = data.status
    if data.booking_id is not None:
        assessment.booking_id = data.booking_id

    await db.commit()
    await db.refresh(assessment)

    return OrganizationalAssessmentRead.model_validate(assessment)


@router.delete("/{assessment_id}")
async def delete_assessment(
    assessment_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete an assessment (admin)."""
    result = await db.execute(
        select(OrganizationalAssessment)
        .where(OrganizationalAssessment.id == assessment_id)
    )
    assessment = result.scalar_one_or_none()

    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    await db.delete(assessment)
    await db.commit()

    return {"status": "ok", "message": "Assessment deleted"}
