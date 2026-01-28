"""Content management router for admin dashboard."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import Optional

from app.database import get_db
from app.services.auth_service import get_current_user
from app.models.user import User
from app.models.client_content import ClientContent
from app.models.contact import Contact
from app.models.organization import Organization
from app.models.project import Project
from app.schemas.content import (
    ContentCreate,
    ContentUpdate,
    ContentResponse,
    ContentList,
    CategoryResponse,
)

router = APIRouter(prefix="/content", tags=["Content"])


def content_to_response(content: ClientContent) -> ContentResponse:
    """Convert content model to response with related names."""
    return ContentResponse(
        id=content.id,
        title=content.title,
        description=content.description,
        content_type=content.content_type,
        file_url=content.file_url,
        file_name=content.file_name,
        file_size=content.file_size,
        mime_type=content.mime_type,
        external_url=content.external_url,
        contact_id=content.contact_id,
        contact_name=f"{content.contact.first_name} {content.contact.last_name or ''}".strip() if content.contact else None,
        organization_id=content.organization_id,
        organization_name=content.organization.name if content.organization else None,
        project_id=content.project_id,
        project_name=content.project.name if content.project else None,
        release_date=content.release_date,
        is_released=content.is_released,
        is_active=content.is_active,
        sort_order=content.sort_order,
        category=content.category,
        created_at=content.created_at,
        updated_at=content.updated_at,
    )


@router.get("", response_model=ContentList)
async def list_content(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    content_type: Optional[str] = None,
    category: Optional[str] = None,
    contact_id: Optional[str] = None,
    organization_id: Optional[str] = None,
    project_id: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all content with pagination and filters."""
    query = select(ClientContent).options(
        selectinload(ClientContent.contact),
        selectinload(ClientContent.organization),
        selectinload(ClientContent.project),
    )

    # Apply filters
    if search:
        search_filter = (
            ClientContent.title.ilike(f"%{search}%")
            | ClientContent.description.ilike(f"%{search}%")
        )
        query = query.where(search_filter)
    if content_type:
        query = query.where(ClientContent.content_type == content_type)
    if category:
        query = query.where(ClientContent.category == category)
    if contact_id:
        query = query.where(ClientContent.contact_id == contact_id)
    if organization_id:
        query = query.where(ClientContent.organization_id == organization_id)
    if project_id:
        query = query.where(ClientContent.project_id == project_id)
    if is_active is not None:
        query = query.where(ClientContent.is_active == is_active)

    # Get total count
    count_query = select(func.count()).select_from(
        select(ClientContent.id).where(query.whereclause) if query.whereclause is not None else select(ClientContent.id)
    )
    total = await db.scalar(count_query) or 0

    # Get paginated results
    query = query.offset((page - 1) * size).limit(size).order_by(
        ClientContent.sort_order, ClientContent.created_at.desc()
    )
    result = await db.execute(query)
    items = result.scalars().all()

    return ContentList(
        items=[content_to_response(c) for c in items],
        total=total,
        page=page,
        size=size,
    )


@router.get("/categories", response_model=CategoryResponse)
async def list_categories(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all unique content categories."""
    result = await db.execute(
        select(ClientContent.category)
        .where(ClientContent.category.isnot(None))
        .distinct()
        .order_by(ClientContent.category)
    )
    categories = [row[0] for row in result.all() if row[0]]
    return CategoryResponse(categories=categories)


@router.get("/{content_id}", response_model=ContentResponse)
async def get_content(
    content_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single content item."""
    result = await db.execute(
        select(ClientContent)
        .options(
            selectinload(ClientContent.contact),
            selectinload(ClientContent.organization),
            selectinload(ClientContent.project),
        )
        .where(ClientContent.id == content_id)
    )
    content = result.scalar_one_or_none()

    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found",
        )

    return content_to_response(content)


@router.post("", response_model=ContentResponse, status_code=status.HTTP_201_CREATED)
async def create_content(
    data: ContentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new content item."""
    # Validate related entities
    if data.contact_id:
        contact_result = await db.execute(
            select(Contact).where(Contact.id == data.contact_id)
        )
        if not contact_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Contact not found",
            )

    if data.organization_id:
        org_result = await db.execute(
            select(Organization).where(Organization.id == data.organization_id)
        )
        if not org_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Organization not found",
            )

    if data.project_id:
        project_result = await db.execute(
            select(Project).where(Project.id == data.project_id)
        )
        if not project_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project not found",
            )

    # Create content
    content = ClientContent(**data.model_dump())
    db.add(content)
    await db.commit()
    await db.refresh(content)

    # Reload with relationships
    result = await db.execute(
        select(ClientContent)
        .options(
            selectinload(ClientContent.contact),
            selectinload(ClientContent.organization),
            selectinload(ClientContent.project),
        )
        .where(ClientContent.id == content.id)
    )
    content = result.scalar_one()

    return content_to_response(content)


@router.put("/{content_id}", response_model=ContentResponse)
async def update_content(
    content_id: str,
    data: ContentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a content item."""
    result = await db.execute(
        select(ClientContent).where(ClientContent.id == content_id)
    )
    content = result.scalar_one_or_none()

    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found",
        )

    # Validate related entities if being updated
    update_data = data.model_dump(exclude_unset=True)

    if "contact_id" in update_data and update_data["contact_id"]:
        contact_result = await db.execute(
            select(Contact).where(Contact.id == update_data["contact_id"])
        )
        if not contact_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Contact not found",
            )

    if "organization_id" in update_data and update_data["organization_id"]:
        org_result = await db.execute(
            select(Organization).where(Organization.id == update_data["organization_id"])
        )
        if not org_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Organization not found",
            )

    if "project_id" in update_data and update_data["project_id"]:
        project_result = await db.execute(
            select(Project).where(Project.id == update_data["project_id"])
        )
        if not project_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project not found",
            )

    # Update fields
    for key, value in update_data.items():
        setattr(content, key, value)

    await db.commit()
    await db.refresh(content)

    # Reload with relationships
    result = await db.execute(
        select(ClientContent)
        .options(
            selectinload(ClientContent.contact),
            selectinload(ClientContent.organization),
            selectinload(ClientContent.project),
        )
        .where(ClientContent.id == content.id)
    )
    content = result.scalar_one()

    return content_to_response(content)


@router.delete("/{content_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_content(
    content_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a content item."""
    result = await db.execute(
        select(ClientContent).where(ClientContent.id == content_id)
    )
    content = result.scalar_one_or_none()

    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found",
        )

    await db.delete(content)
    await db.commit()
