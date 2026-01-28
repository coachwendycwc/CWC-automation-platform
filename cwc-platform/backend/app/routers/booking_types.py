from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.services.auth_service import get_current_user
from app.models.user import User
from app.models.booking_type import BookingType
from app.schemas.booking_type import (
    BookingTypeCreate,
    BookingTypeUpdate,
    BookingTypeResponse,
    BookingTypeList,
)

router = APIRouter(prefix="/booking-types", tags=["Booking Types"])


@router.get("", response_model=BookingTypeList)
async def list_booking_types(
    active_only: bool = Query(False, description="Only return active booking types"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all booking types."""
    query = select(BookingType)
    count_query = select(func.count()).select_from(BookingType)

    if active_only:
        query = query.where(BookingType.is_active == True)
        count_query = count_query.where(BookingType.is_active == True)

    query = query.order_by(BookingType.name).offset(offset).limit(limit)

    result = await db.execute(query)
    booking_types = result.scalars().all()

    total = await db.scalar(count_query)

    return BookingTypeList(
        items=[BookingTypeResponse.model_validate(bt) for bt in booking_types],
        total=total or 0,
    )


@router.post("", response_model=BookingTypeResponse, status_code=status.HTTP_201_CREATED)
async def create_booking_type(
    data: BookingTypeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new booking type."""
    # Check if slug already exists
    existing = await db.execute(
        select(BookingType).where(BookingType.slug == data.slug)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A booking type with this slug already exists",
        )

    booking_type = BookingType(**data.model_dump())
    db.add(booking_type)
    await db.commit()
    await db.refresh(booking_type)

    return BookingTypeResponse.model_validate(booking_type)


@router.get("/{booking_type_id}", response_model=BookingTypeResponse)
async def get_booking_type(
    booking_type_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a booking type by ID."""
    result = await db.execute(
        select(BookingType).where(BookingType.id == booking_type_id)
    )
    booking_type = result.scalar_one_or_none()

    if not booking_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking type not found",
        )

    return BookingTypeResponse.model_validate(booking_type)


@router.put("/{booking_type_id}", response_model=BookingTypeResponse)
async def update_booking_type(
    booking_type_id: str,
    data: BookingTypeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a booking type."""
    result = await db.execute(
        select(BookingType).where(BookingType.id == booking_type_id)
    )
    booking_type = result.scalar_one_or_none()

    if not booking_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking type not found",
        )

    # Check if new slug conflicts with existing
    if data.slug and data.slug != booking_type.slug:
        existing = await db.execute(
            select(BookingType).where(BookingType.slug == data.slug)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A booking type with this slug already exists",
            )

    # Update fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(booking_type, field, value)

    await db.commit()
    await db.refresh(booking_type)

    return BookingTypeResponse.model_validate(booking_type)


@router.delete("/{booking_type_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_booking_type(
    booking_type_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a booking type."""
    from app.models.booking import Booking

    result = await db.execute(
        select(BookingType).where(BookingType.id == booking_type_id)
    )
    booking_type = result.scalar_one_or_none()

    if not booking_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking type not found",
        )

    # Check if there are existing bookings for this type
    booking_count = await db.scalar(
        select(func.count()).select_from(Booking).where(
            Booking.booking_type_id == booking_type_id
        )
    )
    if booking_count and booking_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete booking type with existing bookings. Deactivate it instead.",
        )

    await db.delete(booking_type)
    await db.commit()
