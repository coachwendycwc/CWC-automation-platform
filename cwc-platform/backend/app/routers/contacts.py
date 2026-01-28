from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.services.auth_service import get_current_user
from app.models.user import User
from app.models.contact import Contact
from app.models.organization import Organization
from app.schemas.contact import (
    ContactCreate,
    ContactUpdate,
    ContactResponse,
    ContactList,
    ContactWithOrganization,
)

router = APIRouter(prefix="/contacts", tags=["Contacts"])


@router.get("", response_model=ContactList)
async def list_contacts(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    search: str | None = None,
    contact_type: str | None = None,
    coaching_type: str | None = None,
    organization_id: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all contacts with pagination and filters."""
    query = select(Contact)

    if search:
        search_filter = (
            Contact.first_name.ilike(f"%{search}%")
            | Contact.last_name.ilike(f"%{search}%")
            | Contact.email.ilike(f"%{search}%")
        )
        query = query.where(search_filter)
    if contact_type:
        query = query.where(Contact.contact_type == contact_type)
    if coaching_type:
        query = query.where(Contact.coaching_type == coaching_type)
    if organization_id:
        query = query.where(Contact.organization_id == organization_id)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)

    # Get paginated results
    query = query.offset((page - 1) * size).limit(size).order_by(Contact.first_name)
    result = await db.execute(query)
    contacts = result.scalars().all()

    return ContactList(
        items=[ContactResponse.model_validate(c) for c in contacts],
        total=total or 0,
        page=page,
        size=size,
    )


@router.post("", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
async def create_contact(
    contact_data: ContactCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new contact."""
    # Validate organization exists if provided
    if contact_data.organization_id:
        org_result = await db.execute(
            select(Organization).where(Organization.id == contact_data.organization_id)
        )
        if not org_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Organization not found",
            )

    contact = Contact(**contact_data.model_dump())
    db.add(contact)
    await db.commit()
    await db.refresh(contact)
    return ContactResponse.model_validate(contact)


@router.get("/{contact_id}", response_model=ContactWithOrganization)
async def get_contact(
    contact_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single contact by ID with organization info."""
    result = await db.execute(
        select(Contact)
        .options(selectinload(Contact.organization))
        .where(Contact.id == contact_id)
    )
    contact = result.scalar_one_or_none()

    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found",
        )

    return ContactWithOrganization.model_validate(contact)


@router.put("/{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: str,
    update_data: ContactUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a contact."""
    result = await db.execute(select(Contact).where(Contact.id == contact_id))
    contact = result.scalar_one_or_none()

    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found",
        )

    # Validate organization if being updated
    update_dict = update_data.model_dump(exclude_unset=True)
    if "organization_id" in update_dict and update_dict["organization_id"]:
        org_result = await db.execute(
            select(Organization).where(Organization.id == update_dict["organization_id"])
        )
        if not org_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Organization not found",
            )

    for field, value in update_dict.items():
        setattr(contact, field, value)

    await db.commit()
    await db.refresh(contact)
    return ContactResponse.model_validate(contact)


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(
    contact_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a contact."""
    result = await db.execute(select(Contact).where(Contact.id == contact_id))
    contact = result.scalar_one_or_none()

    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found",
        )

    await db.delete(contact)
    await db.commit()
