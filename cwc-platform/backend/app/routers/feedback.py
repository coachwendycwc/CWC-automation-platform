"""Public feedback and testimonial endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.offboarding_service import OffboardingService
from app.schemas.offboarding import (
    SurveyResponse,
    SurveyPublicData,
    TestimonialSubmission,
    TestimonialPublicData,
)

router = APIRouter(prefix="/api", tags=["feedback"])


# ============== Survey Endpoints ==============

@router.get("/feedback/{token}", response_model=SurveyPublicData)
async def get_survey(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    """Get survey data for public survey page."""
    service = OffboardingService(db)
    workflow = await service.get_workflow_by_survey_token(token)

    if not workflow:
        raise HTTPException(status_code=404, detail="Survey not found or link has expired")

    contact_name = ""
    if workflow.contact:
        contact_name = f"{workflow.contact.first_name} {workflow.contact.last_name}"

    project_title = None
    if workflow.related_project:
        project_title = workflow.related_project.title

    return SurveyPublicData(
        contact_name=contact_name,
        workflow_type=workflow.workflow_type,
        project_title=project_title,
        already_completed=workflow.survey_completed_at is not None,
    )


@router.post("/feedback/{token}")
async def submit_survey(
    token: str,
    response: SurveyResponse,
    db: AsyncSession = Depends(get_db),
):
    """Submit survey response."""
    service = OffboardingService(db)
    workflow = await service.get_workflow_by_survey_token(token)

    if not workflow:
        raise HTTPException(status_code=404, detail="Survey not found or link has expired")

    if workflow.survey_completed_at:
        raise HTTPException(status_code=400, detail="Survey already completed")

    await service.submit_survey(workflow.id, response)

    return {"success": True, "message": "Thank you for your feedback!"}


# ============== Testimonial Endpoints ==============

@router.get("/testimonial/{token}", response_model=TestimonialPublicData)
async def get_testimonial_request(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    """Get testimonial request data for public page."""
    service = OffboardingService(db)
    workflow = await service.get_workflow_by_testimonial_token(token)

    if not workflow:
        raise HTTPException(status_code=404, detail="Testimonial request not found or link has expired")

    contact_name = ""
    if workflow.contact:
        contact_name = f"{workflow.contact.first_name} {workflow.contact.last_name}"

    return TestimonialPublicData(
        contact_name=contact_name,
        workflow_type=workflow.workflow_type,
        already_submitted=workflow.testimonial_received,
    )


@router.post("/testimonial/{token}")
async def submit_testimonial(
    token: str,
    submission: TestimonialSubmission,
    db: AsyncSession = Depends(get_db),
):
    """Submit testimonial."""
    service = OffboardingService(db)
    workflow = await service.get_workflow_by_testimonial_token(token)

    if not workflow:
        raise HTTPException(status_code=404, detail="Testimonial request not found or link has expired")

    if workflow.testimonial_received:
        raise HTTPException(status_code=400, detail="Testimonial already submitted")

    await service.submit_testimonial(workflow.id, submission)

    return {"success": True, "message": "Thank you for sharing your story!"}
