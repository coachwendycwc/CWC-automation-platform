"""
Project template management router.
"""
from typing import Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from app.database import get_db
from app.models.project_template import ProjectTemplate
from app.schemas.project import (
    ProjectTemplateCreate,
    ProjectTemplateUpdate,
    ProjectTemplateRead,
    ProjectTemplateList,
)

router = APIRouter(prefix="/api/project-templates", tags=["project-templates"])


@router.get("", response_model=list[ProjectTemplateList])
async def list_project_templates(
    project_type: Optional[str] = Query(None, description="Filter by type"),
    active_only: bool = Query(True, description="Only show active templates"),
    search: Optional[str] = Query(None, description="Search by name"),
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
) -> list[ProjectTemplateList]:
    """List all project templates."""
    query = select(ProjectTemplate)

    # Apply filters
    if active_only:
        query = query.where(ProjectTemplate.is_active == True)
    if project_type:
        query = query.where(ProjectTemplate.project_type == project_type)
    if search:
        query = query.where(ProjectTemplate.name.ilike(f"%{search}%"))

    query = query.order_by(ProjectTemplate.name).offset(skip).limit(limit)

    result = await db.execute(query)
    templates = result.scalars().all()

    return [
        ProjectTemplateList(
            id=t.id,
            name=t.name,
            project_type=t.project_type,
            default_duration_days=t.default_duration_days,
            task_count=len(t.task_templates) if t.task_templates else 0,
            is_active=t.is_active,
        )
        for t in templates
    ]


@router.get("/{template_id}", response_model=ProjectTemplateRead)
async def get_project_template(
    template_id: str,
    db: AsyncSession = Depends(get_db),
) -> ProjectTemplateRead:
    """Get a specific project template."""
    result = await db.execute(
        select(ProjectTemplate).where(ProjectTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    return ProjectTemplateRead.model_validate(template)


@router.post("", response_model=ProjectTemplateRead, status_code=201)
async def create_project_template(
    data: ProjectTemplateCreate,
    db: AsyncSession = Depends(get_db),
) -> ProjectTemplateRead:
    """Create a new project template."""
    template = ProjectTemplate(
        id=str(uuid.uuid4()),
        name=data.name,
        description=data.description,
        project_type=data.project_type,
        default_duration_days=data.default_duration_days,
        estimated_hours=data.estimated_hours,
        task_templates=[t.model_dump() for t in data.task_templates],
        is_active=True,
    )

    db.add(template)
    await db.commit()
    await db.refresh(template)

    return ProjectTemplateRead.model_validate(template)


@router.put("/{template_id}", response_model=ProjectTemplateRead)
async def update_project_template(
    template_id: str,
    data: ProjectTemplateUpdate,
    db: AsyncSession = Depends(get_db),
) -> ProjectTemplateRead:
    """Update a project template."""
    result = await db.execute(
        select(ProjectTemplate).where(ProjectTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    # Update fields
    update_data = data.model_dump(exclude_unset=True)

    # Handle task_templates specially (convert Pydantic models to dicts)
    if "task_templates" in update_data and update_data["task_templates"] is not None:
        update_data["task_templates"] = [
            t.model_dump() if hasattr(t, "model_dump") else t
            for t in update_data["task_templates"]
        ]

    for field, value in update_data.items():
        setattr(template, field, value)

    await db.commit()
    await db.refresh(template)

    return ProjectTemplateRead.model_validate(template)


@router.delete("/{template_id}", status_code=204)
async def delete_project_template(
    template_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a project template."""
    result = await db.execute(
        select(ProjectTemplate).where(ProjectTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    await db.delete(template)
    await db.commit()


@router.post("/{template_id}/duplicate", response_model=ProjectTemplateRead, status_code=201)
async def duplicate_project_template(
    template_id: str,
    db: AsyncSession = Depends(get_db),
) -> ProjectTemplateRead:
    """Duplicate a project template."""
    result = await db.execute(
        select(ProjectTemplate).where(ProjectTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    new_template = ProjectTemplate(
        id=str(uuid.uuid4()),
        name=f"{template.name} (Copy)",
        description=template.description,
        project_type=template.project_type,
        default_duration_days=template.default_duration_days,
        estimated_hours=template.estimated_hours,
        task_templates=template.task_templates,
        is_active=True,
    )

    db.add(new_template)
    await db.commit()
    await db.refresh(new_template)

    return ProjectTemplateRead.model_validate(new_template)
