"""
Public booking endpoints - no authentication required.
"""
from datetime import datetime, date, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.booking import Booking
from app.models.booking_type import BookingType
from app.models.contact import Contact
from app.models.user import User
from app.services.scheduling_service import SchedulingService
from app.schemas.booking import (
    PublicBookingCreate,
    PublicBookingResponse,
    RescheduleRequest,
    CancelRequest,
    TimeSlot,
    AvailableSlotsResponse,
    PublicBookingTypeInfo,
)

router = APIRouter(prefix="/book", tags=["Public Booking"])


async def get_first_user(db: AsyncSession) -> User:
    """Get the first user (coach) for availability. In single-user mode, this is the main user."""
    result = await db.execute(select(User).limit(1))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No users configured in the system",
        )
    return user


@router.get("/{slug}", response_model=PublicBookingTypeInfo)
async def get_public_booking_type(
    slug: str,
    db: AsyncSession = Depends(get_db),
):
    """Get public booking type info by slug."""
    result = await db.execute(
        select(BookingType).where(
            BookingType.slug == slug,
            BookingType.is_active == True,
        )
    )
    booking_type = result.scalar_one_or_none()

    if not booking_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking type not found",
        )

    return PublicBookingTypeInfo(
        name=booking_type.name,
        slug=booking_type.slug,
        description=booking_type.description,
        duration_minutes=booking_type.duration_minutes,
        price=float(booking_type.price) if booking_type.price else None,
        min_notice_hours=booking_type.min_notice_hours,
        max_advance_days=booking_type.max_advance_days,
    )


@router.get("/{slug}/slots", response_model=AvailableSlotsResponse)
async def get_available_slots(
    slug: str,
    target_date: date = Query(..., alias="date"),
    db: AsyncSession = Depends(get_db),
):
    """Get available time slots for a specific date."""
    # Get booking type
    result = await db.execute(
        select(BookingType).where(
            BookingType.slug == slug,
            BookingType.is_active == True,
        )
    )
    booking_type = result.scalar_one_or_none()

    if not booking_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking type not found",
        )

    # Get the coach user
    user = await get_first_user(db)

    # Calculate available slots
    scheduling = SchedulingService(db)
    available_times = await scheduling.get_available_slots(
        booking_type=booking_type,
        target_date=target_date,
        user_id=user.id,
    )

    # Convert to response format
    slots = []
    for start_time in available_times:
        end_time = start_time + timedelta(minutes=booking_type.duration_minutes)
        slots.append(TimeSlot(
            start_time=start_time,
            end_time=end_time,
            available=True,
        ))

    return AvailableSlotsResponse(
        date=target_date.isoformat(),
        slots=slots,
    )


@router.post("/{slug}", response_model=PublicBookingResponse, status_code=status.HTTP_201_CREATED)
async def create_public_booking(
    slug: str,
    data: PublicBookingCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a booking from the public booking page.
    Creates or finds a contact based on email.
    """
    # Get booking type
    result = await db.execute(
        select(BookingType).where(
            BookingType.slug == slug,
            BookingType.is_active == True,
        )
    )
    booking_type = result.scalar_one_or_none()

    if not booking_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking type not found",
        )

    # Get the coach user
    user = await get_first_user(db)

    # Verify slot is still available
    scheduling = SchedulingService(db)
    target_date = data.start_time.date()
    available_slots = await scheduling.get_available_slots(
        booking_type=booking_type,
        target_date=target_date,
        user_id=user.id,
    )

    # Check if requested time is in available slots
    slot_available = any(
        abs((slot - data.start_time).total_seconds()) < 60
        for slot in available_slots
    )

    if not slot_available:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Selected time slot is no longer available",
        )

    # Find or create contact
    contact_result = await db.execute(
        select(Contact).where(Contact.email == data.email)
    )
    contact = contact_result.scalar_one_or_none()

    if not contact:
        contact = Contact(
            first_name=data.first_name,
            last_name=data.last_name,
            email=data.email,
            phone=data.phone,
            source="booking_page",
            contact_type="lead",
        )
        db.add(contact)
        await db.flush()

    # Calculate end time
    end_time = data.start_time + timedelta(minutes=booking_type.duration_minutes)

    # Create booking
    booking = Booking(
        booking_type_id=booking_type.id,
        contact_id=contact.id,
        start_time=data.start_time,
        end_time=end_time,
        notes=data.notes,
        status="confirmed" if not booking_type.requires_confirmation else "pending",
    )
    db.add(booking)
    await db.commit()
    await db.refresh(booking)

    # TODO: Send confirmation email

    can_modify = await scheduling.can_cancel(booking)

    return PublicBookingResponse(
        id=booking.id,
        start_time=booking.start_time,
        end_time=booking.end_time,
        status=booking.status,
        booking_type_name=booking_type.name,
        booking_type_duration=booking_type.duration_minutes,
        can_cancel=can_modify,
        can_reschedule=can_modify,
    )


# --- Self-service management (token-based) ---


@router.get("/manage/{token}", response_model=PublicBookingResponse)
async def get_booking_by_token(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    """Get booking details by confirmation token."""
    result = await db.execute(
        select(Booking)
        .options(selectinload(Booking.booking_type))
        .where(Booking.confirmation_token == token)
    )
    booking = result.scalar_one_or_none()

    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )

    scheduling = SchedulingService(db)
    can_modify = await scheduling.can_cancel(booking)

    return PublicBookingResponse(
        id=booking.id,
        start_time=booking.start_time,
        end_time=booking.end_time,
        status=booking.status,
        booking_type_name=booking.booking_type.name,
        booking_type_duration=booking.booking_type.duration_minutes,
        can_cancel=can_modify and booking.status not in ["cancelled", "completed"],
        can_reschedule=can_modify and booking.status not in ["cancelled", "completed"],
    )


@router.post("/manage/{token}/reschedule", response_model=PublicBookingResponse)
async def reschedule_booking(
    token: str,
    data: RescheduleRequest,
    db: AsyncSession = Depends(get_db),
):
    """Reschedule a booking (self-service)."""
    result = await db.execute(
        select(Booking)
        .options(selectinload(Booking.booking_type))
        .where(Booking.confirmation_token == token)
    )
    booking = result.scalar_one_or_none()

    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )

    if booking.status in ["cancelled", "completed"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot reschedule a {booking.status} booking",
        )

    scheduling = SchedulingService(db)

    # Check 24hr policy
    if not await scheduling.can_reschedule(booking):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bookings cannot be rescheduled less than 24 hours before the start time",
        )

    # Get the coach user
    user = await get_first_user(db)

    # Verify new slot is available
    target_date = data.new_start_time.date()
    available_slots = await scheduling.get_available_slots(
        booking_type=booking.booking_type,
        target_date=target_date,
        user_id=user.id,
    )

    slot_available = any(
        abs((slot - data.new_start_time).total_seconds()) < 60
        for slot in available_slots
    )

    if not slot_available:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Selected time slot is not available",
        )

    # Update booking
    new_end_time = data.new_start_time + timedelta(
        minutes=booking.booking_type.duration_minutes
    )
    booking.start_time = data.new_start_time
    booking.end_time = new_end_time

    await db.commit()
    await db.refresh(booking)

    # TODO: Send reschedule confirmation email

    can_modify = await scheduling.can_cancel(booking)

    return PublicBookingResponse(
        id=booking.id,
        start_time=booking.start_time,
        end_time=booking.end_time,
        status=booking.status,
        booking_type_name=booking.booking_type.name,
        booking_type_duration=booking.booking_type.duration_minutes,
        can_cancel=can_modify,
        can_reschedule=can_modify,
    )


@router.post("/manage/{token}/cancel", response_model=PublicBookingResponse)
async def cancel_booking_self_service(
    token: str,
    data: CancelRequest,
    db: AsyncSession = Depends(get_db),
):
    """Cancel a booking (self-service)."""
    result = await db.execute(
        select(Booking)
        .options(selectinload(Booking.booking_type))
        .where(Booking.confirmation_token == token)
    )
    booking = result.scalar_one_or_none()

    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )

    if booking.status == "cancelled":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Booking is already cancelled",
        )

    if booking.status == "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot cancel a completed booking",
        )

    scheduling = SchedulingService(db)

    # Check 24hr policy
    if not await scheduling.can_cancel(booking):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bookings cannot be cancelled less than 24 hours before the start time",
        )

    # Cancel booking
    booking.status = "cancelled"
    booking.cancellation_reason = data.reason
    booking.cancelled_at = datetime.now()
    booking.cancelled_by = "client"

    await db.commit()
    await db.refresh(booking)

    # TODO: Send cancellation confirmation email

    return PublicBookingResponse(
        id=booking.id,
        start_time=booking.start_time,
        end_time=booking.end_time,
        status=booking.status,
        booking_type_name=booking.booking_type.name,
        booking_type_duration=booking.booking_type.duration_minutes,
        can_cancel=False,
        can_reschedule=False,
    )
