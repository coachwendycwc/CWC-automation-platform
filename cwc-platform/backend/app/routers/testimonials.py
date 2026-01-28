"""Testimonials router for admin dashboard."""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.services.auth_service import get_current_user
from app.services.cloudinary_service import cloudinary_service
from app.services.email_service import email_service
from app.models.user import User
from app.models.testimonial import Testimonial
from app.models.contact import Contact
from app.models.organization import Organization
from app.config import get_settings
from app.schemas.testimonial import (
    TestimonialCreate,
    TestimonialUpdate,
    TestimonialResponse,
    TestimonialList,
    TestimonialSendRequest,
)

router = APIRouter(prefix="/api/testimonials", tags=["Testimonials"])


def testimonial_to_response(testimonial: Testimonial) -> TestimonialResponse:
    """Convert testimonial model to response."""
    contact_name = None
    organization_name = None

    if testimonial.contact:
        contact_name = f"{testimonial.contact.first_name} {testimonial.contact.last_name or ''}".strip()
    if testimonial.organization:
        organization_name = testimonial.organization.name

    return TestimonialResponse(
        id=testimonial.id,
        contact_id=testimonial.contact_id,
        organization_id=testimonial.organization_id,
        contact_name=contact_name,
        organization_name=organization_name,
        video_url=testimonial.video_url,
        video_public_id=testimonial.video_public_id,
        video_duration_seconds=testimonial.video_duration_seconds,
        thumbnail_url=testimonial.thumbnail_url,
        quote=testimonial.quote,
        transcript=testimonial.transcript,
        author_name=testimonial.author_name,
        author_title=testimonial.author_title,
        author_company=testimonial.author_company,
        author_photo_url=testimonial.author_photo_url,
        permission_granted=testimonial.permission_granted,
        status=testimonial.status,
        featured=testimonial.featured,
        display_order=testimonial.display_order,
        request_token=testimonial.request_token,
        request_sent_at=testimonial.request_sent_at,
        submitted_at=testimonial.submitted_at,
        reviewed_at=testimonial.reviewed_at,
        has_video=testimonial.has_video,
        created_at=testimonial.created_at,
        updated_at=testimonial.updated_at,
    )


@router.get("", response_model=TestimonialList)
async def list_testimonials(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    contact_id: Optional[str] = None,
    organization_id: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    featured: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all testimonials with filters."""
    query = select(Testimonial).options(
        selectinload(Testimonial.contact),
        selectinload(Testimonial.organization),
    )

    # Apply filters
    if contact_id:
        query = query.where(Testimonial.contact_id == contact_id)
    if organization_id:
        query = query.where(Testimonial.organization_id == organization_id)
    if status_filter:
        query = query.where(Testimonial.status == status_filter)
    if featured is not None:
        query = query.where(Testimonial.featured == featured)

    # Get total count
    count_query = select(func.count(Testimonial.id))
    if contact_id:
        count_query = count_query.where(Testimonial.contact_id == contact_id)
    if organization_id:
        count_query = count_query.where(Testimonial.organization_id == organization_id)
    if status_filter:
        count_query = count_query.where(Testimonial.status == status_filter)
    if featured is not None:
        count_query = count_query.where(Testimonial.featured == featured)

    total = await db.scalar(count_query) or 0

    # Get paginated results
    query = query.offset((page - 1) * size).limit(size).order_by(
        Testimonial.created_at.desc()
    )
    result = await db.execute(query)
    testimonials = result.scalars().unique().all()

    return TestimonialList(
        items=[testimonial_to_response(t) for t in testimonials],
        total=total,
        page=page,
        size=size,
    )


@router.get("/{testimonial_id}", response_model=TestimonialResponse)
async def get_testimonial(
    testimonial_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single testimonial."""
    result = await db.execute(
        select(Testimonial)
        .options(
            selectinload(Testimonial.contact),
            selectinload(Testimonial.organization),
        )
        .where(Testimonial.id == testimonial_id)
    )
    testimonial = result.scalar_one_or_none()

    if not testimonial:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Testimonial not found",
        )

    return testimonial_to_response(testimonial)


@router.post("", response_model=TestimonialResponse, status_code=status.HTTP_201_CREATED)
async def create_testimonial(
    data: TestimonialCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new testimonial request."""
    contact = None
    organization = None

    # Validate contact if provided
    if data.contact_id:
        contact_result = await db.execute(
            select(Contact).where(Contact.id == data.contact_id)
        )
        contact = contact_result.scalar_one_or_none()
        if not contact:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Contact not found",
            )

    # Validate organization if provided
    if data.organization_id:
        org_result = await db.execute(
            select(Organization).where(Organization.id == data.organization_id)
        )
        organization = org_result.scalar_one_or_none()
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Organization not found",
            )

    # Create testimonial
    testimonial = Testimonial(
        contact_id=data.contact_id,
        organization_id=data.organization_id,
        author_name=data.author_name,
        author_title=data.author_title,
        author_company=data.author_company or (organization.name if organization else None),
        quote=data.quote,
        status="pending",
    )
    db.add(testimonial)
    await db.commit()

    # Reload with relationships
    result = await db.execute(
        select(Testimonial)
        .options(
            selectinload(Testimonial.contact),
            selectinload(Testimonial.organization),
        )
        .where(Testimonial.id == testimonial.id)
    )
    testimonial = result.scalar_one()

    return testimonial_to_response(testimonial)


@router.put("/{testimonial_id}", response_model=TestimonialResponse)
async def update_testimonial(
    testimonial_id: str,
    data: TestimonialUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a testimonial."""
    result = await db.execute(
        select(Testimonial)
        .options(
            selectinload(Testimonial.contact),
            selectinload(Testimonial.organization),
        )
        .where(Testimonial.id == testimonial_id)
    )
    testimonial = result.scalar_one_or_none()

    if not testimonial:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Testimonial not found",
        )

    # Update fields
    if data.author_name is not None:
        testimonial.author_name = data.author_name
    if data.author_title is not None:
        testimonial.author_title = data.author_title
    if data.author_company is not None:
        testimonial.author_company = data.author_company
    if data.author_photo_url is not None:
        testimonial.author_photo_url = data.author_photo_url
    if data.quote is not None:
        testimonial.quote = data.quote
    if data.transcript is not None:
        testimonial.transcript = data.transcript
    if data.status is not None:
        testimonial.status = data.status
        if data.status in ["approved", "rejected"]:
            testimonial.reviewed_at = datetime.utcnow()
    if data.featured is not None:
        testimonial.featured = data.featured
    if data.display_order is not None:
        testimonial.display_order = data.display_order

    await db.commit()
    await db.refresh(testimonial)

    return testimonial_to_response(testimonial)


@router.delete("/{testimonial_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_testimonial(
    testimonial_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a testimonial and its video from Cloudinary."""
    result = await db.execute(
        select(Testimonial).where(Testimonial.id == testimonial_id)
    )
    testimonial = result.scalar_one_or_none()

    if not testimonial:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Testimonial not found",
        )

    # Delete video from Cloudinary if exists
    if testimonial.video_public_id:
        cloudinary_service.delete_video(testimonial.video_public_id)

    await db.delete(testimonial)
    await db.commit()


@router.post("/{testimonial_id}/send", response_model=TestimonialResponse)
async def send_testimonial_request(
    testimonial_id: str,
    data: TestimonialSendRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Send testimonial request email to the contact."""
    result = await db.execute(
        select(Testimonial)
        .options(
            selectinload(Testimonial.contact),
            selectinload(Testimonial.organization),
        )
        .where(Testimonial.id == testimonial_id)
    )
    testimonial = result.scalar_one_or_none()

    if not testimonial:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Testimonial not found",
        )

    if not testimonial.contact or not testimonial.contact.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contact has no email address",
        )

    # Build testimonial URL
    settings = get_settings()
    testimonial_url = f"{settings.frontend_url}/record/{testimonial.request_token}"

    # Send email
    await email_service.send_testimonial_request(
        to_email=testimonial.contact.email,
        contact_name=testimonial.author_name,
        testimonial_url=testimonial_url,
    )

    # Update request sent timestamp
    testimonial.request_sent_at = datetime.utcnow()
    await db.commit()
    await db.refresh(testimonial)

    return testimonial_to_response(testimonial)
