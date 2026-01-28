from datetime import datetime, date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.services.auth_service import get_current_user
from app.services.email_service import email_service
from app.services.google_calendar_service import google_calendar_service
from app.services.zoom_service import zoom_service
from app.models.user import User
from app.models.booking import Booking
from app.models.booking_type import BookingType
from app.models.contact import Contact
from app.schemas.booking import (
    BookingCreate,
    BookingUpdate,
    BookingResponse,
    BookingDetailResponse,
    BookingList,
)
from app.schemas.booking_type import BookingTypeResponse
from app.schemas.contact import ContactResponse

router = APIRouter(prefix="/bookings", tags=["Bookings"])

import logging
logger = logging.getLogger(__name__)


async def create_zoom_meeting_for_booking(
    user: User, booking: Booking, booking_type: BookingType, contact: Contact, db: AsyncSession
) -> None:
    """Create a Zoom meeting for a confirmed booking if user has Zoom connected."""
    if not user.zoom_token:
        return

    try:
        access_token = user.zoom_token.get("access_token")
        if not access_token:
            return

        meeting = await zoom_service.create_meeting(
            access_token=access_token,
            topic=f"{booking_type.name} - {contact.full_name}",
            start_time=booking.start_time,
            duration_minutes=booking_type.duration_minutes,
            agenda=f"Booking with {contact.full_name}",
        )

        booking.zoom_meeting_id = meeting["id"]
        booking.zoom_meeting_url = meeting["join_url"]
        booking.zoom_meeting_password = meeting.get("password", "")
        await db.commit()

        logger.info(f"Created Zoom meeting {meeting['id']} for booking {booking.id}")
    except Exception as e:
        logger.error(f"Failed to create Zoom meeting for booking {booking.id}: {e}")


async def delete_zoom_meeting_for_booking(user: User, booking: Booking, db: AsyncSession) -> None:
    """Delete Zoom meeting when booking is cancelled."""
    if not user.zoom_token or not booking.zoom_meeting_id:
        return

    try:
        access_token = user.zoom_token.get("access_token")
        if not access_token:
            return

        await zoom_service.delete_meeting(access_token, booking.zoom_meeting_id)
        booking.zoom_meeting_id = None
        booking.zoom_meeting_url = None
        booking.zoom_meeting_password = None
        await db.commit()

        logger.info(f"Deleted Zoom meeting for booking {booking.id}")
    except Exception as e:
        logger.error(f"Failed to delete Zoom meeting for booking {booking.id}: {e}")


@router.get("", response_model=BookingList)
async def list_bookings(
    status_filter: Optional[str] = Query(None, alias="status"),
    booking_type_id: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all bookings with optional filters.

    - status: Filter by booking status (pending, confirmed, completed, cancelled, no_show)
    - booking_type_id: Filter by booking type
    - start_date: Filter by start date (inclusive)
    - end_date: Filter by end date (inclusive)
    """
    query = (
        select(Booking)
        .options(selectinload(Booking.booking_type), selectinload(Booking.contact))
    )
    count_query = select(func.count()).select_from(Booking)

    # Apply filters
    filters = []
    if status_filter:
        filters.append(Booking.status == status_filter)
    if booking_type_id:
        filters.append(Booking.booking_type_id == booking_type_id)
    if start_date:
        filters.append(Booking.start_time >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        filters.append(Booking.start_time <= datetime.combine(end_date, datetime.max.time()))

    if filters:
        query = query.where(and_(*filters))
        count_query = count_query.where(and_(*filters))

    query = query.order_by(Booking.start_time.desc()).offset(offset).limit(limit)

    result = await db.execute(query)
    bookings = result.scalars().all()

    total = await db.scalar(count_query)

    items = []
    for booking in bookings:
        items.append(
            BookingDetailResponse(
                id=booking.id,
                booking_type_id=booking.booking_type_id,
                contact_id=booking.contact_id,
                start_time=booking.start_time,
                end_time=booking.end_time,
                status=booking.status,
                google_event_id=booking.google_event_id,
                notes=booking.notes,
                cancellation_reason=booking.cancellation_reason,
                cancelled_at=booking.cancelled_at,
                cancelled_by=booking.cancelled_by,
                confirmation_token=booking.confirmation_token,
                reminder_24h_sent_at=booking.reminder_24h_sent_at,
                reminder_1h_sent_at=booking.reminder_1h_sent_at,
                created_at=booking.created_at,
                updated_at=booking.updated_at,
                booking_type=BookingTypeResponse.model_validate(booking.booking_type),
                contact=ContactResponse.model_validate(booking.contact),
            )
        )

    return BookingList(items=items, total=total or 0)


@router.post("", response_model=BookingDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(
    data: BookingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new booking (admin)."""
    # Verify booking type exists
    bt_result = await db.execute(
        select(BookingType).where(BookingType.id == data.booking_type_id)
    )
    booking_type = bt_result.scalar_one_or_none()
    if not booking_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Booking type not found",
        )

    # Verify contact exists
    contact_result = await db.execute(
        select(Contact).where(Contact.id == data.contact_id)
    )
    contact = contact_result.scalar_one_or_none()
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contact not found",
        )

    # Calculate end time
    end_time = data.start_time + timedelta(minutes=booking_type.duration_minutes)

    # Create booking
    booking = Booking(
        booking_type_id=data.booking_type_id,
        contact_id=data.contact_id,
        start_time=data.start_time,
        end_time=end_time,
        notes=data.notes,
        status="confirmed" if not booking_type.requires_confirmation else "pending",
    )
    db.add(booking)
    await db.commit()
    await db.refresh(booking)

    # Send confirmation email if auto-confirmed
    if booking.status == "confirmed" and contact.email:
        await email_service.send_booking_confirmation(
            to_email=contact.email,
            contact_name=contact.full_name,
            booking_type=booking_type.name,
            booking_date=booking.start_time,
            booking_duration=booking_type.duration_minutes,
            meeting_link=None,  # No location_details on BookingType
        )

    # Sync to Google Calendar if connected
    if current_user.google_calendar_token and booking.status == "confirmed":
        try:
            event = google_calendar_service.create_event(
                token_data=current_user.google_calendar_token,
                summary=f"{booking_type.name} - {contact.full_name}",
                start_time=booking.start_time,
                end_time=end_time,
                description=f"Booking with {contact.full_name}\n\n{data.notes or ''}",
                location=booking_type.location_details,
                attendees=[contact.email] if contact.email else None,
            )
            booking.google_event_id = event.get("id")
            await db.commit()
        except Exception as e:
            logger.error(f"Failed to create Google Calendar event: {e}")

    # Create Zoom meeting if connected and auto-confirmed
    if booking.status == "confirmed":
        await create_zoom_meeting_for_booking(current_user, booking, booking_type, contact, db)

    return BookingDetailResponse(
        id=booking.id,
        booking_type_id=booking.booking_type_id,
        contact_id=booking.contact_id,
        start_time=booking.start_time,
        end_time=booking.end_time,
        status=booking.status,
        google_event_id=booking.google_event_id,
        notes=booking.notes,
        cancellation_reason=booking.cancellation_reason,
        cancelled_at=booking.cancelled_at,
        cancelled_by=booking.cancelled_by,
        confirmation_token=booking.confirmation_token,
        reminder_24h_sent_at=booking.reminder_24h_sent_at,
        reminder_1h_sent_at=booking.reminder_1h_sent_at,
        created_at=booking.created_at,
        updated_at=booking.updated_at,
        booking_type=BookingTypeResponse.model_validate(booking_type),
        contact=ContactResponse.model_validate(contact),
    )


@router.get("/{booking_id}", response_model=BookingDetailResponse)
async def get_booking(
    booking_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single booking by ID."""
    result = await db.execute(
        select(Booking)
        .options(selectinload(Booking.booking_type), selectinload(Booking.contact))
        .where(Booking.id == booking_id)
    )
    booking = result.scalar_one_or_none()

    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )

    return BookingDetailResponse(
        id=booking.id,
        booking_type_id=booking.booking_type_id,
        contact_id=booking.contact_id,
        start_time=booking.start_time,
        end_time=booking.end_time,
        status=booking.status,
        google_event_id=booking.google_event_id,
        notes=booking.notes,
        cancellation_reason=booking.cancellation_reason,
        cancelled_at=booking.cancelled_at,
        cancelled_by=booking.cancelled_by,
        confirmation_token=booking.confirmation_token,
        reminder_24h_sent_at=booking.reminder_24h_sent_at,
        reminder_1h_sent_at=booking.reminder_1h_sent_at,
        created_at=booking.created_at,
        updated_at=booking.updated_at,
        booking_type=BookingTypeResponse.model_validate(booking.booking_type),
        contact=ContactResponse.model_validate(booking.contact),
    )


@router.put("/{booking_id}", response_model=BookingDetailResponse)
async def update_booking(
    booking_id: str,
    data: BookingUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a booking (notes, status)."""
    result = await db.execute(
        select(Booking)
        .options(selectinload(Booking.booking_type), selectinload(Booking.contact))
        .where(Booking.id == booking_id)
    )
    booking = result.scalar_one_or_none()

    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )

    # Update fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(booking, field, value)

    await db.commit()
    await db.refresh(booking)

    return BookingDetailResponse(
        id=booking.id,
        booking_type_id=booking.booking_type_id,
        contact_id=booking.contact_id,
        start_time=booking.start_time,
        end_time=booking.end_time,
        status=booking.status,
        google_event_id=booking.google_event_id,
        notes=booking.notes,
        cancellation_reason=booking.cancellation_reason,
        cancelled_at=booking.cancelled_at,
        cancelled_by=booking.cancelled_by,
        confirmation_token=booking.confirmation_token,
        reminder_24h_sent_at=booking.reminder_24h_sent_at,
        reminder_1h_sent_at=booking.reminder_1h_sent_at,
        created_at=booking.created_at,
        updated_at=booking.updated_at,
        booking_type=BookingTypeResponse.model_validate(booking.booking_type),
        contact=ContactResponse.model_validate(booking.contact),
    )


@router.post("/{booking_id}/confirm", response_model=BookingDetailResponse)
async def confirm_booking(
    booking_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Confirm a pending booking."""
    result = await db.execute(
        select(Booking)
        .options(selectinload(Booking.booking_type), selectinload(Booking.contact))
        .where(Booking.id == booking_id)
    )
    booking = result.scalar_one_or_none()

    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )

    if booking.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot confirm booking with status '{booking.status}'",
        )

    booking.status = "confirmed"
    await db.commit()
    await db.refresh(booking)

    # Send confirmation email
    meeting_link = booking.zoom_meeting_url or booking.booking_type.location_details
    if booking.contact and booking.contact.email:
        await email_service.send_booking_confirmation(
            to_email=booking.contact.email,
            contact_name=booking.contact.full_name,
            booking_type=booking.booking_type.name,
            booking_date=booking.start_time,
            booking_duration=booking.booking_type.duration_minutes,
            meeting_link=meeting_link,
        )

    # Create Zoom meeting if connected
    await create_zoom_meeting_for_booking(
        current_user, booking, booking.booking_type, booking.contact, db
    )

    # Refresh to get updated Zoom fields
    await db.refresh(booking)

    return BookingDetailResponse(
        id=booking.id,
        booking_type_id=booking.booking_type_id,
        contact_id=booking.contact_id,
        start_time=booking.start_time,
        end_time=booking.end_time,
        status=booking.status,
        google_event_id=booking.google_event_id,
        zoom_meeting_id=booking.zoom_meeting_id,
        zoom_meeting_url=booking.zoom_meeting_url,
        zoom_meeting_password=booking.zoom_meeting_password,
        notes=booking.notes,
        cancellation_reason=booking.cancellation_reason,
        cancelled_at=booking.cancelled_at,
        cancelled_by=booking.cancelled_by,
        confirmation_token=booking.confirmation_token,
        reminder_24h_sent_at=booking.reminder_24h_sent_at,
        reminder_1h_sent_at=booking.reminder_1h_sent_at,
        created_at=booking.created_at,
        updated_at=booking.updated_at,
        booking_type=BookingTypeResponse.model_validate(booking.booking_type),
        contact=ContactResponse.model_validate(booking.contact),
    )


@router.post("/{booking_id}/cancel", response_model=BookingDetailResponse)
async def cancel_booking(
    booking_id: str,
    reason: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cancel a booking (by host)."""
    result = await db.execute(
        select(Booking)
        .options(selectinload(Booking.booking_type), selectinload(Booking.contact))
        .where(Booking.id == booking_id)
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

    booking.status = "cancelled"
    booking.cancellation_reason = reason
    booking.cancelled_at = datetime.now()
    booking.cancelled_by = "host"

    await db.commit()
    await db.refresh(booking)

    # Send cancellation email
    if booking.contact and booking.contact.email:
        await email_service.send_booking_cancelled(
            to_email=booking.contact.email,
            contact_name=booking.contact.full_name,
            booking_type=booking.booking_type.name,
            booking_date=booking.start_time,
        )

    # Delete from Google Calendar if synced
    if current_user.google_calendar_token and booking.google_event_id:
        try:
            google_calendar_service.delete_event(
                token_data=current_user.google_calendar_token,
                event_id=booking.google_event_id,
            )
            booking.google_event_id = None
            await db.commit()
        except Exception as e:
            logger.error(f"Failed to delete Google Calendar event: {e}")

    # Delete Zoom meeting if exists
    await delete_zoom_meeting_for_booking(current_user, booking, db)

    return BookingDetailResponse(
        id=booking.id,
        booking_type_id=booking.booking_type_id,
        contact_id=booking.contact_id,
        start_time=booking.start_time,
        end_time=booking.end_time,
        status=booking.status,
        google_event_id=booking.google_event_id,
        notes=booking.notes,
        cancellation_reason=booking.cancellation_reason,
        cancelled_at=booking.cancelled_at,
        cancelled_by=booking.cancelled_by,
        confirmation_token=booking.confirmation_token,
        reminder_24h_sent_at=booking.reminder_24h_sent_at,
        reminder_1h_sent_at=booking.reminder_1h_sent_at,
        created_at=booking.created_at,
        updated_at=booking.updated_at,
        booking_type=BookingTypeResponse.model_validate(booking.booking_type),
        contact=ContactResponse.model_validate(booking.contact),
    )
