"""Offboarding workflow router."""

import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.offboarding_service import OffboardingService
from app.services.email_service import email_service
from app.schemas.offboarding import (
    OffboardingWorkflowCreate,
    OffboardingWorkflowUpdate,
    OffboardingWorkflowRead,
    OffboardingWorkflowDetail,
    OffboardingWorkflowList,
    OffboardingActivityRead,
    OffboardingTemplateCreate,
    OffboardingTemplateUpdate,
    OffboardingTemplateRead,
    OffboardingStats,
)

router = APIRouter(prefix="/api/offboarding", tags=["offboarding"])


# ============== Workflows ==============

@router.get("", response_model=OffboardingWorkflowList)
async def list_workflows(
    status: Optional[str] = Query(None),
    workflow_type: Optional[str] = Query(None),
    contact_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List offboarding workflows with filters."""
    service = OffboardingService(db)
    skip = (page - 1) * size
    items, total = await service.list_workflows(
        status=status,
        workflow_type=workflow_type,
        contact_id=contact_id,
        skip=skip,
        limit=size,
    )
    return OffboardingWorkflowList(
        items=[OffboardingWorkflowRead.model_validate(w) for w in items],
        total=total,
    )


@router.get("/stats", response_model=OffboardingStats)
async def get_stats(db: AsyncSession = Depends(get_db)):
    """Get offboarding statistics."""
    service = OffboardingService(db)
    return await service.get_stats()


@router.post("/initiate", response_model=OffboardingWorkflowRead)
async def initiate_workflow(
    data: OffboardingWorkflowCreate,
    db: AsyncSession = Depends(get_db),
):
    """Initiate a new offboarding workflow."""
    service = OffboardingService(db)
    workflow = await service.initiate_workflow(data)
    return OffboardingWorkflowRead.model_validate(workflow)


@router.get("/{workflow_id}", response_model=OffboardingWorkflowDetail)
async def get_workflow(
    workflow_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a workflow by ID with details."""
    service = OffboardingService(db)
    workflow = await service.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    # Build response with related data
    response = OffboardingWorkflowDetail.model_validate(workflow)
    if workflow.contact:
        response.contact_name = f"{workflow.contact.first_name} {workflow.contact.last_name}"
        response.contact_email = workflow.contact.email
    if workflow.related_project:
        response.project_title = workflow.related_project.title
    if workflow.related_contract:
        response.contract_title = workflow.related_contract.title
    response.activities = [
        OffboardingActivityRead.model_validate(a) for a in workflow.activities
    ]
    return response


@router.put("/{workflow_id}", response_model=OffboardingWorkflowRead)
async def update_workflow(
    workflow_id: str,
    data: OffboardingWorkflowUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a workflow."""
    service = OffboardingService(db)
    workflow = await service.update_workflow(workflow_id, data)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return OffboardingWorkflowRead.model_validate(workflow)


@router.post("/{workflow_id}/checklist/{item_index}", response_model=OffboardingWorkflowRead)
async def toggle_checklist_item(
    workflow_id: str,
    item_index: int,
    db: AsyncSession = Depends(get_db),
):
    """Toggle a checklist item's completion status."""
    service = OffboardingService(db)
    workflow = await service.toggle_checklist_item(workflow_id, item_index)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow or item not found")
    return OffboardingWorkflowRead.model_validate(workflow)


@router.post("/{workflow_id}/complete", response_model=OffboardingWorkflowRead)
async def complete_workflow(
    workflow_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Mark a workflow as complete."""
    service = OffboardingService(db)
    workflow = await service.complete_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return OffboardingWorkflowRead.model_validate(workflow)


@router.post("/{workflow_id}/cancel", response_model=OffboardingWorkflowRead)
async def cancel_workflow(
    workflow_id: str,
    reason: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Cancel a workflow."""
    service = OffboardingService(db)
    workflow = await service.cancel_workflow(workflow_id, reason)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return OffboardingWorkflowRead.model_validate(workflow)


@router.get("/{workflow_id}/activity", response_model=list[OffboardingActivityRead])
async def get_workflow_activity(
    workflow_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get activity log for a workflow."""
    service = OffboardingService(db)
    activities = await service.get_activities(workflow_id)
    return [OffboardingActivityRead.model_validate(a) for a in activities]


# ============== Email Actions ==============

@router.post("/{workflow_id}/send-completion-email")
async def send_completion_email(
    workflow_id: str,
    custom_message: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Send completion/thank you email."""
    service = OffboardingService(db)
    workflow = await service.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    if not workflow.contact or not workflow.contact.email:
        raise HTTPException(status_code=400, detail="Contact has no email address")

    contact_name = f"{workflow.contact.first_name} {workflow.contact.last_name}"
    project_title = workflow.related_project.title if workflow.related_project else None

    success = await email_service.send_offboarding_completion(
        to_email=workflow.contact.email,
        contact_name=contact_name,
        workflow_type=workflow.workflow_type,
        project_title=project_title,
        custom_message=custom_message,
    )

    if success:
        await service.log_activity(workflow_id, "completion_email_sent", {})

    return {"success": success}


@router.post("/{workflow_id}/send-survey")
async def send_survey(
    workflow_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Send survey request email."""
    service = OffboardingService(db)
    workflow = await service.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    if not workflow.contact or not workflow.contact.email:
        raise HTTPException(status_code=400, detail="Contact has no email address")

    if workflow.survey_completed_at:
        raise HTTPException(status_code=400, detail="Survey already completed")

    base_url = os.getenv("FRONTEND_URL", "http://localhost:3001")
    survey_url = f"{base_url}/feedback/{workflow.survey_token}"
    contact_name = f"{workflow.contact.first_name} {workflow.contact.last_name}"

    success = await email_service.send_survey_request(
        to_email=workflow.contact.email,
        contact_name=contact_name,
        survey_url=survey_url,
        workflow_type=workflow.workflow_type,
    )

    if success:
        await service.mark_survey_sent(workflow_id)

    return {"success": success}


@router.post("/{workflow_id}/request-testimonial")
async def request_testimonial(
    workflow_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Send testimonial request email."""
    service = OffboardingService(db)
    workflow = await service.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    if not workflow.contact or not workflow.contact.email:
        raise HTTPException(status_code=400, detail="Contact has no email address")

    if workflow.testimonial_received:
        raise HTTPException(status_code=400, detail="Testimonial already received")

    base_url = os.getenv("FRONTEND_URL", "http://localhost:3001")
    testimonial_url = f"{base_url}/testimonial/{workflow.testimonial_token}"
    contact_name = f"{workflow.contact.first_name} {workflow.contact.last_name}"

    success = await email_service.send_testimonial_request(
        to_email=workflow.contact.email,
        contact_name=contact_name,
        testimonial_url=testimonial_url,
        workflow_type=workflow.workflow_type,
    )

    if success:
        await service.mark_testimonial_requested(workflow_id)

    return {"success": success}


@router.post("/{workflow_id}/approve-testimonial", response_model=OffboardingWorkflowRead)
async def approve_testimonial(
    workflow_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Approve a testimonial for public use."""
    service = OffboardingService(db)
    workflow = await service.approve_testimonial(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return OffboardingWorkflowRead.model_validate(workflow)


# ============== Templates ==============

templates_router = APIRouter(prefix="/api/offboarding-templates", tags=["offboarding"])


@templates_router.get("", response_model=list[OffboardingTemplateRead])
async def list_templates(
    workflow_type: Optional[str] = Query(None),
    active_only: bool = Query(True),
    db: AsyncSession = Depends(get_db),
):
    """List offboarding templates."""
    service = OffboardingService(db)
    templates = await service.list_templates(workflow_type, active_only)
    return [OffboardingTemplateRead.model_validate(t) for t in templates]


@templates_router.post("", response_model=OffboardingTemplateRead)
async def create_template(
    data: OffboardingTemplateCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create an offboarding template."""
    service = OffboardingService(db)
    template = await service.create_template(data.model_dump())
    return OffboardingTemplateRead.model_validate(template)


@templates_router.get("/{template_id}", response_model=OffboardingTemplateRead)
async def get_template(
    template_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a template by ID."""
    service = OffboardingService(db)
    template = await service.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return OffboardingTemplateRead.model_validate(template)


@templates_router.put("/{template_id}", response_model=OffboardingTemplateRead)
async def update_template(
    template_id: str,
    data: OffboardingTemplateUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a template."""
    service = OffboardingService(db)
    template = await service.update_template(template_id, data.model_dump(exclude_unset=True))
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return OffboardingTemplateRead.model_validate(template)


@templates_router.delete("/{template_id}")
async def delete_template(
    template_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete a template."""
    service = OffboardingService(db)
    success = await service.delete_template(template_id)
    if not success:
        raise HTTPException(status_code=404, detail="Template not found")
    return {"success": True}
