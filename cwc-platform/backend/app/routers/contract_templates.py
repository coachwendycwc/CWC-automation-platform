"""
Contract template management router.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.contract_template import ContractTemplate
from app.models.contract import Contract
from app.schemas.contract_template import (
    ContractTemplateCreate,
    ContractTemplateUpdate,
    ContractTemplateRead,
    ContractTemplateList,
    ContractTemplatePreview,
    MergeFieldsResponse,
    MergeFieldInfo,
)
from app.services.contract_service import ContractService

router = APIRouter(prefix="/api/contract-templates", tags=["contract-templates"])


@router.get("", response_model=list[ContractTemplateList])
async def list_templates(
    category: Optional[str] = Query(None, description="Filter by category"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search by name"),
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
) -> list[ContractTemplateList]:
    """List all contract templates with optional filters."""
    query = select(ContractTemplate)

    # Apply filters
    conditions = []
    if category:
        conditions.append(ContractTemplate.category == category)
    if is_active is not None:
        conditions.append(ContractTemplate.is_active == is_active)

    if conditions:
        from sqlalchemy import and_
        query = query.where(and_(*conditions))

    if search:
        query = query.where(ContractTemplate.name.ilike(f"%{search}%"))

    query = query.order_by(ContractTemplate.name).offset(skip).limit(limit)

    result = await db.execute(query)
    templates = result.scalars().all()

    # Get contract counts for each template
    template_list = []
    for template in templates:
        count_result = await db.execute(
            select(func.count())
            .where(Contract.template_id == template.id)
        )
        contracts_count = count_result.scalar_one()

        template_list.append(
            ContractTemplateList(
                id=template.id,
                name=template.name,
                description=template.description,
                category=template.category,
                merge_fields=template.merge_fields,
                is_active=template.is_active,
                contracts_count=contracts_count,
                created_at=template.created_at,
            )
        )

    return template_list


@router.get("/merge-fields", response_model=MergeFieldsResponse)
async def get_merge_fields() -> MergeFieldsResponse:
    """Get list of available merge fields with descriptions."""
    field_info = ContractService.get_merge_field_info()
    return MergeFieldsResponse(
        auto_fields=[MergeFieldInfo(**f) for f in field_info["auto_fields"]],
        custom_fields=[MergeFieldInfo(**f) for f in field_info["custom_fields"]],
    )


@router.get("/{template_id}", response_model=ContractTemplateRead)
async def get_template(
    template_id: str,
    db: AsyncSession = Depends(get_db),
) -> ContractTemplateRead:
    """Get a specific contract template."""
    result = await db.execute(
        select(ContractTemplate).where(ContractTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    return ContractTemplateRead.model_validate(template)


@router.get("/{template_id}/preview", response_model=ContractTemplatePreview)
async def preview_template(
    template_id: str,
    db: AsyncSession = Depends(get_db),
) -> ContractTemplatePreview:
    """Preview template with sample merge data."""
    result = await db.execute(
        select(ContractTemplate).where(ContractTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    rendered_content = ContractService.render_preview(template.content)

    return ContractTemplatePreview(
        name=template.name,
        content=rendered_content,
        merge_fields=template.merge_fields,
    )


@router.post("", response_model=ContractTemplateRead, status_code=201)
async def create_template(
    data: ContractTemplateCreate,
    db: AsyncSession = Depends(get_db),
) -> ContractTemplateRead:
    """Create a new contract template."""
    # Extract merge fields from content
    merge_fields = ContractService.extract_merge_fields(data.content)

    template = ContractTemplate(
        name=data.name,
        description=data.description,
        content=data.content,
        category=data.category,
        default_expiry_days=data.default_expiry_days,
        merge_fields=merge_fields,
    )

    db.add(template)
    await db.commit()
    await db.refresh(template)

    return ContractTemplateRead.model_validate(template)


@router.put("/{template_id}", response_model=ContractTemplateRead)
async def update_template(
    template_id: str,
    data: ContractTemplateUpdate,
    db: AsyncSession = Depends(get_db),
) -> ContractTemplateRead:
    """Update a contract template."""
    result = await db.execute(
        select(ContractTemplate).where(ContractTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    # Update fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(template, field, value)

    # Re-extract merge fields if content changed
    if "content" in update_data:
        template.merge_fields = ContractService.extract_merge_fields(template.content)

    await db.commit()
    await db.refresh(template)

    return ContractTemplateRead.model_validate(template)


@router.delete("/{template_id}", status_code=204)
async def delete_template(
    template_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a contract template."""
    result = await db.execute(
        select(ContractTemplate).where(ContractTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    # Check if template is in use
    count_result = await db.execute(
        select(func.count())
        .where(Contract.template_id == template_id)
    )
    contracts_count = count_result.scalar_one()

    if contracts_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete template. It is used by {contracts_count} contracts.",
        )

    await db.delete(template)
    await db.commit()


@router.post("/{template_id}/duplicate", response_model=ContractTemplateRead, status_code=201)
async def duplicate_template(
    template_id: str,
    db: AsyncSession = Depends(get_db),
) -> ContractTemplateRead:
    """Duplicate a contract template."""
    result = await db.execute(
        select(ContractTemplate).where(ContractTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    new_template = ContractTemplate(
        name=f"{template.name} (Copy)",
        description=template.description,
        content=template.content,
        category=template.category,
        default_expiry_days=template.default_expiry_days,
        merge_fields=template.merge_fields,
    )

    db.add(new_template)
    await db.commit()
    await db.refresh(new_template)

    return ContractTemplateRead.model_validate(new_template)
