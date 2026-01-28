from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.services.auth_service import get_current_user
from app.models.user import User
from app.models.organization import Organization
from app.models.contact import Contact
from app.schemas.organization import (
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationResponse,
    OrganizationList,
    OrganizationWithContacts,
)

router = APIRouter(prefix="/organizations", tags=["Organizations"])


@router.get("", response_model=OrganizationList)
async def list_organizations(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    search: str | None = None,
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all organizations with pagination and filters."""
    query = select(Organization)

    if search:
        query = query.where(Organization.name.ilike(f"%{search}%"))
    if status:
        query = query.where(Organization.status == status)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)

    # Get paginated results
    query = query.offset((page - 1) * size).limit(size).order_by(Organization.name)
    result = await db.execute(query)
    organizations = result.scalars().all()

    return OrganizationList(
        items=[OrganizationResponse.model_validate(org) for org in organizations],
        total=total or 0,
        page=page,
        size=size,
    )


@router.post("", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(
    org_data: OrganizationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new organization."""
    organization = Organization(**org_data.model_dump())
    db.add(organization)
    await db.commit()
    await db.refresh(organization)
    return OrganizationResponse.model_validate(organization)


@router.get("/{org_id}", response_model=OrganizationWithContacts)
async def get_organization(
    org_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single organization by ID with contact info."""
    result = await db.execute(select(Organization).where(Organization.id == org_id))
    organization = result.scalar_one_or_none()

    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    # Get contact count
    count_result = await db.execute(
        select(func.count()).where(Contact.organization_id == org_id)
    )
    contact_count = count_result.scalar() or 0

    response = OrganizationWithContacts.model_validate(organization)
    response.contact_count = contact_count

    return response


@router.put("/{org_id}", response_model=OrganizationResponse)
async def update_organization(
    org_id: str,
    update_data: OrganizationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update an organization."""
    result = await db.execute(select(Organization).where(Organization.id == org_id))
    organization = result.scalar_one_or_none()

    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(organization, field, value)

    await db.commit()
    await db.refresh(organization)
    return OrganizationResponse.model_validate(organization)


@router.delete("/{org_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_organization(
    org_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete an organization."""
    result = await db.execute(select(Organization).where(Organization.id == org_id))
    organization = result.scalar_one_or_none()

    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    await db.delete(organization)
    await db.commit()
