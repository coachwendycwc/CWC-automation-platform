"""
Project management router.
"""
from typing import Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.project import Project
from app.models.task import Task
from app.models.project_template import ProjectTemplate
from app.models.project_activity_log import ProjectActivityLog
from app.models.contact import Contact
from app.models.organization import Organization
from app.models.contract import Contract
from app.models.invoice import Invoice
from app.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectRead,
    ProjectList,
    ProjectDetail,
    ProjectStats,
    ProjectComplete,
    ProjectDuplicate,
    TaskRead,
    TaskStats,
    ProjectActivityLogRead,
)
from app.services.project_service import ProjectService

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get("", response_model=list[ProjectList])
async def list_projects(
    status: Optional[str] = Query(None, description="Filter by status"),
    project_type: Optional[str] = Query(None, description="Filter by type"),
    contact_id: Optional[str] = Query(None, description="Filter by contact"),
    organization_id: Optional[str] = Query(None, description="Filter by organization"),
    search: Optional[str] = Query(None, description="Search project number or title"),
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
) -> list[ProjectList]:
    """List all projects with optional filters."""
    query = select(Project).options(
        selectinload(Project.contact),
        selectinload(Project.organization),
        selectinload(Project.tasks),
    )

    # Apply filters
    conditions = []
    if status:
        conditions.append(Project.status == status)
    if project_type:
        conditions.append(Project.project_type == project_type)
    if contact_id:
        conditions.append(Project.contact_id == contact_id)
    if organization_id:
        conditions.append(Project.organization_id == organization_id)

    if conditions:
        query = query.where(and_(*conditions))

    # Apply search
    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                Project.project_number.ilike(search_term),
                Project.title.ilike(search_term),
            )
        )

    query = query.order_by(Project.created_at.desc()).offset(skip).limit(limit)

    result = await db.execute(query)
    projects = result.scalars().all()

    return [
        ProjectList(
            id=p.id,
            project_number=p.project_number,
            title=p.title,
            project_type=p.project_type,
            status=p.status,
            contact_id=p.contact_id,
            contact_name=p.contact.full_name if p.contact else None,
            organization_name=p.organization.name if p.organization else None,
            start_date=p.start_date,
            target_end_date=p.target_end_date,
            progress_percent=p.progress_percent,
            task_count=len(p.tasks) if p.tasks else 0,
            created_at=p.created_at,
        )
        for p in projects
    ]


@router.get("/stats", response_model=ProjectStats)
async def get_project_stats(
    db: AsyncSession = Depends(get_db),
) -> ProjectStats:
    """Get project statistics for dashboard."""
    service = ProjectService(db)
    stats = await service.get_stats()
    return ProjectStats(**stats)


@router.get("/{project_id}", response_model=ProjectDetail)
async def get_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
) -> ProjectDetail:
    """Get a specific project with full details."""
    result = await db.execute(
        select(Project)
        .options(
            selectinload(Project.contact),
            selectinload(Project.organization),
            selectinload(Project.template),
            selectinload(Project.linked_contract),
            selectinload(Project.linked_invoice),
            selectinload(Project.tasks).selectinload(Task.time_entries),
            selectinload(Project.activity_logs),
        )
        .where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get task stats
    service = ProjectService(db)
    task_stats = await service.get_task_stats(project_id)

    return ProjectDetail(
        id=project.id,
        project_number=project.project_number,
        contact_id=project.contact_id,
        organization_id=project.organization_id,
        title=project.title,
        description=project.description,
        project_type=project.project_type,
        status=project.status,
        start_date=project.start_date,
        target_end_date=project.target_end_date,
        actual_end_date=project.actual_end_date,
        budget_amount=project.budget_amount,
        estimated_hours=project.estimated_hours,
        linked_contract_id=project.linked_contract_id,
        linked_invoice_id=project.linked_invoice_id,
        template_id=project.template_id,
        progress_percent=project.progress_percent,
        view_token=project.view_token,
        client_visible=project.client_visible,
        created_at=project.created_at,
        updated_at=project.updated_at,
        contact_name=project.contact.full_name if project.contact else None,
        contact_email=project.contact.email if project.contact else None,
        organization_name=project.organization.name if project.organization else None,
        template_name=project.template.name if project.template else None,
        linked_contract_number=project.linked_contract.contract_number if project.linked_contract else None,
        linked_invoice_number=project.linked_invoice.invoice_number if project.linked_invoice else None,
        tasks=[TaskRead.model_validate(task) for task in project.tasks],
        activity_logs=[ProjectActivityLogRead.model_validate(log) for log in project.activity_logs],
        task_stats=TaskStats(**task_stats),
    )


@router.post("", response_model=ProjectRead, status_code=201)
async def create_project(
    data: ProjectCreate,
    db: AsyncSession = Depends(get_db),
) -> ProjectRead:
    """Create a new project (optionally from template)."""
    service = ProjectService(db)

    # If using a template, use the service method
    if data.template_id:
        project = await service.create_from_template(
            template_id=data.template_id,
            contact_id=data.contact_id,
            title=data.title,
            organization_id=data.organization_id,
            start_date=data.start_date,
            description=data.description,
            budget_amount=data.budget_amount,
        )
        await db.commit()
        await db.refresh(project)
        return ProjectRead.model_validate(project)

    # Create project without template
    project_number = await service.generate_project_number()

    project = Project(
        id=str(uuid.uuid4()),
        project_number=project_number,
        contact_id=data.contact_id,
        organization_id=data.organization_id,
        title=data.title,
        description=data.description,
        project_type=data.project_type,
        status="planning",
        start_date=data.start_date,
        target_end_date=data.target_end_date,
        budget_amount=data.budget_amount,
        estimated_hours=data.estimated_hours,
        linked_contract_id=data.linked_contract_id,
        linked_invoice_id=data.linked_invoice_id,
    )

    db.add(project)
    await db.flush()

    # Log creation
    await service.log_activity(
        project_id=project.id,
        action="created",
        details={"project_type": data.project_type},
    )

    await db.commit()
    await db.refresh(project)

    return ProjectRead.model_validate(project)


@router.put("/{project_id}", response_model=ProjectRead)
async def update_project(
    project_id: str,
    data: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
) -> ProjectRead:
    """Update a project."""
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Track status change for logging
    old_status = project.status

    # Update fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)

    # Log status change if applicable
    if "status" in update_data and update_data["status"] != old_status:
        service = ProjectService(db)
        await service.log_activity(
            project_id=project_id,
            action="status_changed",
            details={"old_status": old_status, "new_status": update_data["status"]},
        )

    await db.commit()
    await db.refresh(project)

    return ProjectRead.model_validate(project)


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a project and its tasks."""
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    await db.delete(project)
    await db.commit()


@router.post("/{project_id}/complete", response_model=ProjectRead)
async def complete_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
) -> ProjectRead:
    """Mark a project as completed."""
    service = ProjectService(db)

    try:
        project = await service.complete_project(project_id)
        await db.commit()
        await db.refresh(project)
        return ProjectRead.model_validate(project)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{project_id}/duplicate", response_model=ProjectRead, status_code=201)
async def duplicate_project(
    project_id: str,
    data: ProjectDuplicate,
    db: AsyncSession = Depends(get_db),
) -> ProjectRead:
    """Duplicate a project with tasks."""
    service = ProjectService(db)

    try:
        new_project = await service.duplicate_project(
            project_id=project_id,
            new_title=data.new_title,
            include_tasks=data.include_tasks,
        )
        await db.commit()
        await db.refresh(new_project)
        return ProjectRead.model_validate(new_project)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{project_id}/activity", response_model=list[ProjectActivityLogRead])
async def get_project_activity(
    project_id: str,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
) -> list[ProjectActivityLogRead]:
    """Get activity log for a project."""
    # Verify project exists
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    result = await db.execute(
        select(ProjectActivityLog)
        .where(ProjectActivityLog.project_id == project_id)
        .order_by(ProjectActivityLog.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    logs = result.scalars().all()

    return [ProjectActivityLogRead.model_validate(log) for log in logs]
