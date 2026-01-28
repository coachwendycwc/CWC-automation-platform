"""
Tests for Public Booking Page endpoints.
"""
import pytest
from unittest.mock import patch, AsyncMock
from datetime import datetime, date, timedelta, time
from decimal import Decimal
import uuid

from httpx import AsyncClient

from app.models.booking_type import BookingType
from app.models.booking import Booking
from app.models.availability import Availability, AvailabilityOverride
from app.models.contact import Contact
from app.models.user import User


@pytest.fixture
async def test_booking_type(db_session) -> BookingType:
    """Create a test booking type."""
    booking_type = BookingType(
        id=str(uuid.uuid4()),
        name="Discovery Call",
        slug="discovery-call",
        duration_minutes=30,
        price=Decimal("0.00"),
        is_active=True,
        description="Free 30-minute discovery call",
        color="#7c3aed",
    )
    db_session.add(booking_type)
    await db_session.commit()
    await db_session.refresh(booking_type)
    return booking_type


@pytest.fixture
async def test_availability(db_session) -> Availability:
    """Create test availability."""
    availability = Availability(
        id=str(uuid.uuid4()),
        day_of_week=1,  # Monday
        start_time=time(9, 0),
        end_time=time(17, 0),
        is_active=True,
    )
    db_session.add(availability)
    await db_session.commit()
    await db_session.refresh(availability)
    return availability


@pytest.fixture
async def test_user_for_booking(db_session) -> User:
    """Create a test user for booking availability."""
    from app.models.user import User
    user = User(
        id=str(uuid.uuid4()),
        email="coach@example.com",
        hashed_password="hashedpassword",
        name="Test Coach",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


class TestGetBookingType:
    """Tests for getting public booking type by slug."""

    @pytest.mark.asyncio
    async def test_get_type_not_found(self, client: AsyncClient):
        """Test getting non-existent booking type."""
        response = await client.get("/api/book/nonexistent")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_type_success(
        self, client: AsyncClient, test_booking_type: BookingType
    ):
        """Test getting booking type by slug."""
        response = await client.get(
            f"/api/book/{test_booking_type.slug}"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Discovery Call"
        assert data["duration_minutes"] == 30

    @pytest.mark.asyncio
    async def test_get_type_inactive(
        self, db_session, client: AsyncClient
    ):
        """Test inactive booking type is not returned."""
        inactive_type = BookingType(
            id=str(uuid.uuid4()),
            name="Inactive Type",
            slug="inactive-type",
            duration_minutes=30,
            is_active=False,
        )
        db_session.add(inactive_type)
        await db_session.commit()

        response = await client.get("/api/book/inactive-type")
        assert response.status_code == 404


class TestGetAvailableSlots:
    """Tests for getting available time slots."""

    @pytest.mark.asyncio
    async def test_get_slots_booking_type_not_found(
        self, client: AsyncClient
    ):
        """Test getting slots for non-existent booking type."""
        target_date = date.today() + timedelta(days=7)
        response = await client.get(
            "/api/book/nonexistent/slots",
            params={"date": target_date.isoformat()}
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_slots_with_availability(
        self, db_session, client: AsyncClient, test_booking_type: BookingType, test_user_for_booking: User
    ):
        """Test getting available slots."""
        # Find next Monday
        today = date.today()
        days_until_monday = (7 - today.weekday()) % 7
        if days_until_monday == 0:
            days_until_monday = 7
        next_monday = today + timedelta(days=days_until_monday)

        # Create Monday availability
        availability = Availability(
            id=str(uuid.uuid4()),
            day_of_week=0,  # Monday (0-indexed)
            start_time=time(9, 0),
            end_time=time(12, 0),
            is_active=True,
        )
        db_session.add(availability)
        await db_session.commit()

        response = await client.get(
            f"/api/book/{test_booking_type.slug}/slots",
            params={"date": next_monday.isoformat()}
        )
        assert response.status_code == 200
        data = response.json()
        assert "slots" in data
        assert "date" in data


class TestCreatePublicBooking:
    """Tests for creating bookings via public page."""

    @pytest.mark.asyncio
    async def test_create_booking_invalid_type(self, client: AsyncClient):
        """Test booking with invalid booking type."""
        response = await client.post(
            "/api/book/nonexistent",
            json={
                "start_time": "2024-03-01T10:00:00",
                "first_name": "John",
                "last_name": "Doe",
                "email": "john@example.com",
            }
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_booking_slot_unavailable(
        self, db_session, client: AsyncClient, test_booking_type: BookingType, test_user_for_booking: User
    ):
        """Test booking when slot is unavailable."""
        response = await client.post(
            f"/api/book/{test_booking_type.slug}",
            json={
                "start_time": "2024-03-01T03:00:00",  # 3 AM - unlikely to be available
                "first_name": "John",
                "last_name": "Doe",
                "email": "john@example.com",
            }
        )
        assert response.status_code == 400


class TestManageBooking:
    """Tests for managing bookings via token."""

    @pytest.mark.asyncio
    async def test_get_booking_invalid_token(self, client: AsyncClient):
        """Test getting booking with invalid token."""
        response = await client.get("/api/book/manage/invalid-token")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_booking_success(
        self, db_session, client: AsyncClient, test_booking_type: BookingType, test_contact: Contact
    ):
        """Test getting booking by confirmation token."""
        confirmation_token = f"confirm_{uuid.uuid4().hex}"
        booking = Booking(
            id=str(uuid.uuid4()),
            booking_type_id=test_booking_type.id,
            contact_id=test_contact.id,
            start_time=datetime.now() + timedelta(days=7),
            end_time=datetime.now() + timedelta(days=7, minutes=30),
            status="confirmed",
            confirmation_token=confirmation_token,
        )
        db_session.add(booking)
        await db_session.commit()

        response = await client.get(f"/api/book/manage/{confirmation_token}")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "confirmed"

    @pytest.mark.asyncio
    async def test_cancel_booking(
        self, db_session, client: AsyncClient, test_booking_type: BookingType, test_contact: Contact
    ):
        """Test cancelling a booking."""
        confirmation_token = f"cancel_{uuid.uuid4().hex}"
        booking = Booking(
            id=str(uuid.uuid4()),
            booking_type_id=test_booking_type.id,
            contact_id=test_contact.id,
            start_time=datetime.now() + timedelta(days=7),
            end_time=datetime.now() + timedelta(days=7, minutes=30),
            status="confirmed",
            confirmation_token=confirmation_token,
        )
        db_session.add(booking)
        await db_session.commit()

        response = await client.post(
            f"/api/book/manage/{confirmation_token}/cancel",
            json={"reason": "Cannot make it"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "cancelled"

    @pytest.mark.asyncio
    async def test_cancel_already_cancelled_booking(
        self, db_session, client: AsyncClient, test_booking_type: BookingType, test_contact: Contact
    ):
        """Test cannot cancel already cancelled booking."""
        confirmation_token = f"already_cancelled_{uuid.uuid4().hex}"
        booking = Booking(
            id=str(uuid.uuid4()),
            booking_type_id=test_booking_type.id,
            contact_id=test_contact.id,
            start_time=datetime.now() + timedelta(days=7),
            end_time=datetime.now() + timedelta(days=7, minutes=30),
            status="cancelled",
            confirmation_token=confirmation_token,
        )
        db_session.add(booking)
        await db_session.commit()

        response = await client.post(
            f"/api/book/manage/{confirmation_token}/cancel",
            json={"reason": "Changed my mind"}
        )
        assert response.status_code == 400
