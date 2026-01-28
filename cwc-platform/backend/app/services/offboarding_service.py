"""Offboarding workflow service."""

import secrets
from datetime import datetime
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.attributes import flag_modified

from app.models.offboarding import OffboardingWorkflow, OffboardingTemplate, OffboardingActivity
from app.models.contact import Contact
from app.models.project import Project
from app.models.contract import Contract
from app.schemas.offboarding import (
    OffboardingWorkflowCreate,
    OffboardingWorkflowUpdate,
    SurveyResponse,
    TestimonialSubmission,
    OffboardingStats,
)


# Default checklist items by workflow type
DEFAULT_CHECKLISTS = {
    "client": [
        "Verify all invoices paid",
        "Complete final session (if applicable)",
        "Close active projects",
        "Send final recap/summary email",
        "Send satisfaction survey",
        "Request testimonial",
        "Update contact status to past_client",
        "Schedule follow-up reminder (6 months)",
    ],
    "project": [
        "All tasks marked complete",
        "Time entries finalized",
        "Final deliverables sent",
        "Client sign-off received",
        "Final invoice sent (if applicable)",
        "Project files archived",
        "Send completion summary",
    ],
    "contract": [
        "All terms fulfilled",
        "Final payment received (if applicable)",
        "Contract signed by all parties",
        "Send completion confirmation",
        "Archive contract documents",
    ],
}


class OffboardingService:
    """Service for managing offboarding workflows."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def initiate_workflow(
        self,
        data: OffboardingWorkflowCreate,
    ) -> OffboardingWorkflow:
        """Initiate a new offboarding workflow."""
        # Get checklist items from template or use defaults
        checklist_items = DEFAULT_CHECKLISTS.get(data.workflow_type, [])

        if data.template_id:
            template = await self.db.get(OffboardingTemplate, data.template_id)
            if template and template.checklist_items:
                checklist_items = template.checklist_items

        # Create checklist with completion tracking
        checklist = [
            {"item": item, "completed": False, "completed_at": None}
            for item in checklist_items
        ]

        # Generate tokens for survey and testimonial
        survey_token = secrets.token_urlsafe(32)
        testimonial_token = secrets.token_urlsafe(32)

        workflow = OffboardingWorkflow(
            contact_id=data.contact_id,
            workflow_type=data.workflow_type,
            related_project_id=data.related_project_id,
            related_contract_id=data.related_contract_id,
            status="pending",
            checklist=checklist,
            send_survey=data.send_survey,
            request_testimonial=data.request_testimonial,
            send_certificate=data.send_certificate,
            survey_token=survey_token,
            testimonial_token=testimonial_token,
            notes=data.notes,
        )

        self.db.add(workflow)
        await self.db.commit()
        await self.db.refresh(workflow)

        # Log activity
        await self.log_activity(
            workflow.id,
            "initiated",
            {"workflow_type": data.workflow_type},
        )

        return workflow

    async def get_workflow(self, workflow_id: str) -> Optional[OffboardingWorkflow]:
        """Get a workflow by ID with related data."""
        query = (
            select(OffboardingWorkflow)
            .where(OffboardingWorkflow.id == workflow_id)
            .options(
                selectinload(OffboardingWorkflow.contact),
                selectinload(OffboardingWorkflow.related_project),
                selectinload(OffboardingWorkflow.related_contract),
                selectinload(OffboardingWorkflow.activities),
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_workflow_by_survey_token(self, token: str) -> Optional[OffboardingWorkflow]:
        """Get workflow by survey token."""
        query = (
            select(OffboardingWorkflow)
            .where(OffboardingWorkflow.survey_token == token)
            .options(selectinload(OffboardingWorkflow.contact))
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_workflow_by_testimonial_token(self, token: str) -> Optional[OffboardingWorkflow]:
        """Get workflow by testimonial token."""
        query = (
            select(OffboardingWorkflow)
            .where(OffboardingWorkflow.testimonial_token == token)
            .options(selectinload(OffboardingWorkflow.contact))
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_workflows(
        self,
        status: Optional[str] = None,
        workflow_type: Optional[str] = None,
        contact_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[OffboardingWorkflow], int]:
        """List workflows with filters."""
        query = select(OffboardingWorkflow)

        if status:
            query = query.where(OffboardingWorkflow.status == status)
        if workflow_type:
            query = query.where(OffboardingWorkflow.workflow_type == workflow_type)
        if contact_id:
            query = query.where(OffboardingWorkflow.contact_id == contact_id)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Get items with pagination
        query = (
            query
            .options(selectinload(OffboardingWorkflow.contact))
            .order_by(OffboardingWorkflow.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def update_workflow(
        self,
        workflow_id: str,
        data: OffboardingWorkflowUpdate,
    ) -> Optional[OffboardingWorkflow]:
        """Update a workflow."""
        workflow = await self.db.get(OffboardingWorkflow, workflow_id)
        if not workflow:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(workflow, key, value)

        workflow.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(workflow)

        return workflow

    async def toggle_checklist_item(
        self,
        workflow_id: str,
        item_index: int,
    ) -> Optional[OffboardingWorkflow]:
        """Toggle a checklist item's completion status."""
        workflow = await self.db.get(OffboardingWorkflow, workflow_id)
        if not workflow:
            return None

        checklist = list(workflow.checklist)
        if item_index < 0 or item_index >= len(checklist):
            return None

        item = checklist[item_index]
        item["completed"] = not item["completed"]
        item["completed_at"] = datetime.utcnow().isoformat() if item["completed"] else None

        workflow.checklist = checklist
        flag_modified(workflow, "checklist")

        # Update status to in_progress if first item completed
        if workflow.status == "pending" and any(i["completed"] for i in checklist):
            workflow.status = "in_progress"

        workflow.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(workflow)

        # Log activity
        await self.log_activity(
            workflow_id,
            "checklist_updated",
            {"item": item["item"], "completed": item["completed"]},
        )

        return workflow

    async def complete_workflow(self, workflow_id: str) -> Optional[OffboardingWorkflow]:
        """Mark a workflow as complete."""
        workflow = await self.db.get(OffboardingWorkflow, workflow_id)
        if not workflow:
            return None

        workflow.status = "completed"
        workflow.completed_at = datetime.utcnow()
        workflow.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(workflow)

        # Log activity
        await self.log_activity(workflow_id, "completed", {})

        return workflow

    async def cancel_workflow(self, workflow_id: str, reason: Optional[str] = None) -> Optional[OffboardingWorkflow]:
        """Cancel a workflow."""
        workflow = await self.db.get(OffboardingWorkflow, workflow_id)
        if not workflow:
            return None

        workflow.status = "cancelled"
        workflow.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(workflow)

        # Log activity
        await self.log_activity(workflow_id, "cancelled", {"reason": reason})

        return workflow

    async def mark_survey_sent(self, workflow_id: str) -> Optional[OffboardingWorkflow]:
        """Mark survey as sent."""
        workflow = await self.db.get(OffboardingWorkflow, workflow_id)
        if not workflow:
            return None

        workflow.survey_sent_at = datetime.utcnow()
        workflow.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(workflow)

        # Log activity
        await self.log_activity(workflow_id, "survey_sent", {})

        return workflow

    async def submit_survey(
        self,
        workflow_id: str,
        response: SurveyResponse,
    ) -> Optional[OffboardingWorkflow]:
        """Submit survey response."""
        workflow = await self.db.get(OffboardingWorkflow, workflow_id)
        if not workflow:
            return None

        workflow.survey_completed_at = datetime.utcnow()
        workflow.survey_response = response.model_dump()
        workflow.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(workflow)

        # Log activity
        await self.log_activity(
            workflow_id,
            "survey_completed",
            {"satisfaction": response.satisfaction_rating, "nps": response.nps_score},
        )

        return workflow

    async def mark_testimonial_requested(self, workflow_id: str) -> Optional[OffboardingWorkflow]:
        """Mark testimonial as requested."""
        workflow = await self.db.get(OffboardingWorkflow, workflow_id)
        if not workflow:
            return None

        workflow.testimonial_requested_at = datetime.utcnow()
        workflow.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(workflow)

        # Log activity
        await self.log_activity(workflow_id, "testimonial_requested", {})

        return workflow

    async def submit_testimonial(
        self,
        workflow_id: str,
        submission: TestimonialSubmission,
    ) -> Optional[OffboardingWorkflow]:
        """Submit testimonial."""
        workflow = await self.db.get(OffboardingWorkflow, workflow_id)
        if not workflow:
            return None

        workflow.testimonial_received = True
        workflow.testimonial_text = submission.testimonial_text
        workflow.testimonial_author_name = submission.author_name
        workflow.testimonial_author_title = submission.author_title
        workflow.testimonial_photo_url = submission.photo
        workflow.testimonial_permission_granted = submission.permission_granted
        workflow.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(workflow)

        # Log activity
        await self.log_activity(
            workflow_id,
            "testimonial_received",
            {"allow_public": submission.allow_public_use},
        )

        return workflow

    async def approve_testimonial(self, workflow_id: str) -> Optional[OffboardingWorkflow]:
        """Approve a testimonial for public use."""
        workflow = await self.db.get(OffboardingWorkflow, workflow_id)
        if not workflow:
            return None

        workflow.testimonial_approved = True
        workflow.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(workflow)

        # Log activity
        await self.log_activity(workflow_id, "testimonial_approved", {})

        return workflow

    async def log_activity(
        self,
        workflow_id: str,
        action: str,
        details: Optional[dict] = None,
    ) -> OffboardingActivity:
        """Log an activity for a workflow."""
        activity = OffboardingActivity(
            workflow_id=workflow_id,
            action=action,
            details=details,
        )
        self.db.add(activity)
        await self.db.commit()
        return activity

    async def get_activities(self, workflow_id: str) -> list[OffboardingActivity]:
        """Get activities for a workflow."""
        query = (
            select(OffboardingActivity)
            .where(OffboardingActivity.workflow_id == workflow_id)
            .order_by(OffboardingActivity.created_at.desc())
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_stats(self) -> OffboardingStats:
        """Get offboarding statistics."""
        # Count by status
        status_counts = {}
        for status in ["pending", "in_progress", "completed", "cancelled"]:
            query = select(func.count()).where(OffboardingWorkflow.status == status)
            result = await self.db.execute(query)
            status_counts[status] = result.scalar() or 0

        total = sum(status_counts.values())

        # Survey stats
        surveys_sent_query = select(func.count()).where(OffboardingWorkflow.survey_sent_at.isnot(None))
        surveys_sent_result = await self.db.execute(surveys_sent_query)
        surveys_sent = surveys_sent_result.scalar() or 0

        surveys_completed_query = select(func.count()).where(OffboardingWorkflow.survey_completed_at.isnot(None))
        surveys_completed_result = await self.db.execute(surveys_completed_query)
        surveys_completed = surveys_completed_result.scalar() or 0

        # Testimonial stats
        testimonials_received_query = select(func.count()).where(OffboardingWorkflow.testimonial_received == True)
        testimonials_received_result = await self.db.execute(testimonials_received_query)
        testimonials_received = testimonials_received_result.scalar() or 0

        testimonials_approved_query = select(func.count()).where(OffboardingWorkflow.testimonial_approved == True)
        testimonials_approved_result = await self.db.execute(testimonials_approved_query)
        testimonials_approved = testimonials_approved_result.scalar() or 0

        # Average satisfaction and NPS (would need to query survey_response JSON)
        # For now, return None - can implement with JSON extraction if needed
        avg_satisfaction = None
        avg_nps = None

        return OffboardingStats(
            total_workflows=total,
            pending=status_counts["pending"],
            in_progress=status_counts["in_progress"],
            completed=status_counts["completed"],
            cancelled=status_counts["cancelled"],
            surveys_sent=surveys_sent,
            surveys_completed=surveys_completed,
            testimonials_received=testimonials_received,
            testimonials_approved=testimonials_approved,
            avg_satisfaction=avg_satisfaction,
            avg_nps=avg_nps,
        )

    # ============== Templates ==============

    async def create_template(self, data: dict) -> OffboardingTemplate:
        """Create an offboarding template."""
        template = OffboardingTemplate(**data)
        self.db.add(template)
        await self.db.commit()
        await self.db.refresh(template)
        return template

    async def get_template(self, template_id: str) -> Optional[OffboardingTemplate]:
        """Get a template by ID."""
        return await self.db.get(OffboardingTemplate, template_id)

    async def list_templates(
        self,
        workflow_type: Optional[str] = None,
        active_only: bool = True,
    ) -> list[OffboardingTemplate]:
        """List templates."""
        query = select(OffboardingTemplate)

        if workflow_type:
            query = query.where(OffboardingTemplate.workflow_type == workflow_type)
        if active_only:
            query = query.where(OffboardingTemplate.is_active == True)

        query = query.order_by(OffboardingTemplate.name)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_template(
        self,
        template_id: str,
        data: dict,
    ) -> Optional[OffboardingTemplate]:
        """Update a template."""
        template = await self.db.get(OffboardingTemplate, template_id)
        if not template:
            return None

        for key, value in data.items():
            if value is not None:
                setattr(template, key, value)

        template.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(template)
        return template

    async def delete_template(self, template_id: str) -> bool:
        """Delete a template."""
        template = await self.db.get(OffboardingTemplate, template_id)
        if not template:
            return False

        await self.db.delete(template)
        await self.db.commit()
        return True
