import uuid
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from app.models.booking import Booking
from app.models.booking_type import BookingType
from app.models.calendar_connection import CalendarConnection
from app.models.contact import Contact
from app.models.user import User
from app.services.booking_calendar_service import BookingCalendarService

pytestmark = pytest.mark.anyio


async def test_create_booking_event_uses_primary_calendar_connection(db_session):
    user = User(
        id=str(uuid.uuid4()),
        email="coach@example.com",
        name="Coach",
        password_hash="hashed",
        role="admin",
        is_active=True,
    )
    contact = Contact(
        id=str(uuid.uuid4()),
        first_name="Jane",
        last_name="Client",
        email="jane@example.com",
        contact_type="lead",
    )
    booking_type = BookingType(
        id=str(uuid.uuid4()),
        name="Strategy Session",
        slug="strategy-session-service",
        duration_minutes=60,
        is_active=True,
    )
    connection = CalendarConnection(
        id=str(uuid.uuid4()),
        user_id=user.id,
        provider="google",
        calendar_id="team-calendar",
        token_data={"access_token": "conn-token"},
        is_primary=True,
        is_active=True,
    )
    booking = Booking(
        id=str(uuid.uuid4()),
        booking_type_id=booking_type.id,
        contact_id=contact.id,
        start_time=datetime.utcnow() + timedelta(days=7),
        end_time=datetime.utcnow() + timedelta(days=7, hours=1),
        status="confirmed",
    )
    db_session.add_all([user, contact, booking_type, connection, booking])
    await db_session.commit()

    service = BookingCalendarService(db_session)

    with patch(
        "app.services.booking_calendar_service.google_calendar_service.create_event",
        return_value={"id": "evt_123"},
    ) as mock_create:
        await service.create_booking_event(
            user=user,
            booking=booking,
            booking_type=booking_type,
            contact=contact,
        )

    await db_session.refresh(booking)
    assert booking.google_event_id == "evt_123"
    assert booking.calendar_connection_id == connection.id
    assert mock_create.call_args.kwargs["calendar_id"] == "team-calendar"
    assert mock_create.call_args.kwargs["token_data"] == {"access_token": "conn-token"}


async def test_delete_booking_event_falls_back_to_legacy_token(db_session):
    user = User(
        id=str(uuid.uuid4()),
        email="coach@example.com",
        name="Coach",
        password_hash="hashed",
        role="admin",
        is_active=True,
        google_calendar_token={"access_token": "legacy-token"},
    )
    contact = Contact(
        id=str(uuid.uuid4()),
        first_name="Legacy",
        last_name="Client",
        email="legacy@example.com",
        contact_type="lead",
    )
    booking_type = BookingType(
        id=str(uuid.uuid4()),
        name="Legacy Session",
        slug="legacy-session",
        duration_minutes=60,
        is_active=True,
    )
    booking = Booking(
        id=str(uuid.uuid4()),
        booking_type_id=booking_type.id,
        contact_id=contact.id,
        start_time=datetime.utcnow() + timedelta(days=7),
        end_time=datetime.utcnow() + timedelta(days=7, hours=1),
        status="confirmed",
        google_event_id="evt_legacy",
    )
    db_session.add_all([user, contact, booking_type, booking])
    await db_session.commit()

    service = BookingCalendarService(db_session)

    with patch(
        "app.services.booking_calendar_service.google_calendar_service.delete_event",
        return_value=True,
    ) as mock_delete:
        await service.delete_booking_event(user=user, booking=booking)

    await db_session.refresh(booking)
    assert booking.google_event_id is None
    assert booking.calendar_connection_id is None
    assert mock_delete.call_args.kwargs["token_data"] == {"access_token": "legacy-token"}
    assert mock_delete.call_args.kwargs["calendar_id"] == "primary"


async def test_update_booking_event_uses_existing_connection_id(db_session):
    user = User(
        id=str(uuid.uuid4()),
        email="coach@example.com",
        name="Coach",
        password_hash="hashed",
        role="admin",
        is_active=True,
    )
    contact = Contact(
        id=str(uuid.uuid4()),
        first_name="Jane",
        last_name="Client",
        email="jane@example.com",
        contact_type="lead",
    )
    booking_type = BookingType(
        id=str(uuid.uuid4()),
        name="Strategy Session",
        slug="strategy-session-update",
        duration_minutes=60,
        is_active=True,
    )
    connection = CalendarConnection(
        id=str(uuid.uuid4()),
        user_id=user.id,
        provider="google",
        calendar_id="brand-calendar",
        token_data={"access_token": "conn-token"},
        is_primary=False,
        is_active=True,
    )
    booking = Booking(
        id=str(uuid.uuid4()),
        booking_type_id=booking_type.id,
        contact_id=contact.id,
        start_time=datetime.utcnow() + timedelta(days=7),
        end_time=datetime.utcnow() + timedelta(days=7, hours=1),
        status="confirmed",
        google_event_id="evt_123",
        calendar_connection_id=connection.id,
        notes="Bring prep questions.",
    )
    db_session.add_all([user, contact, booking_type, connection, booking])
    await db_session.commit()

    booking.start_time = booking.start_time + timedelta(days=1)
    booking.end_time = booking.end_time + timedelta(days=1)

    service = BookingCalendarService(db_session)

    with patch(
        "app.services.booking_calendar_service.google_calendar_service.update_event",
        return_value={"id": "evt_123"},
    ) as mock_update:
        await service.update_booking_event(
            user=user,
            booking=booking,
            booking_type=booking_type,
            contact=contact,
        )

    assert mock_update.call_args.kwargs["calendar_id"] == "brand-calendar"
    assert mock_update.call_args.kwargs["event_id"] == "evt_123"
    assert mock_update.call_args.kwargs["token_data"] == {"access_token": "conn-token"}
