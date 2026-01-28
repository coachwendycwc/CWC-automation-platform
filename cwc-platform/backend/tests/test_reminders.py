"""
Tests for Reminder Scheduler endpoints.
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime, date, timedelta
from decimal import Decimal
import uuid

from httpx import AsyncClient

from app.models.booking import Booking
from app.models.booking_type import BookingType
from app.models.invoice import Invoice
from app.models.contact import Contact


@pytest.fixture
async def test_booking_for_reminder(
    db_session, test_contact: Contact
) -> Booking:
    """Create a booking that needs reminders."""
    booking_type = BookingType(
        id=str(uuid.uuid4()),
        name="Coaching Session",
        slug="coaching-session",
        duration_minutes=60,
        is_active=True,
    )
    db_session.add(booking_type)
    await db_session.flush()

    booking = Booking(
        id=str(uuid.uuid4()),
        booking_type_id=booking_type.id,
        contact_id=test_contact.id,
        start_time=datetime.utcnow() + timedelta(hours=24),
        end_time=datetime.utcnow() + timedelta(hours=25),
        status="confirmed",
    )
    db_session.add(booking)
    await db_session.commit()
    await db_session.refresh(booking)
    return booking


class TestReminderCheck:
    """Tests for the reminder check endpoint."""

    @pytest.mark.asyncio
    async def test_trigger_reminder_check(
        self, auth_client: AsyncClient
    ):
        """Test triggering a reminder check."""
        with patch("app.services.reminder_service.reminder_service") as mock_service:
            mock_service.check_and_send_reminders = AsyncMock()

            response = await auth_client.post("/api/reminders/check")
            assert response.status_code == 200
            data = response.json()
            assert "message" in data

    @pytest.mark.asyncio
    async def test_trigger_reminder_check_unauthenticated(
        self, client: AsyncClient
    ):
        """Test reminder check requires authentication."""
        response = await client.post("/api/reminders/check")
        assert response.status_code == 401


class TestSendBookingReminder:
    """Tests for sending individual booking reminders."""

    @pytest.mark.asyncio
    async def test_send_reminder_success(
        self, auth_client: AsyncClient, test_booking_for_reminder: Booking
    ):
        """Test sending a reminder for a specific booking."""
        with patch("app.services.reminder_service.reminder_service") as mock_service:
            mock_service.send_immediate_reminder = AsyncMock(return_value=True)

            response = await auth_client.post(
                f"/api/reminders/send/{test_booking_for_reminder.id}"
            )
            assert response.status_code == 200
            data = response.json()
            assert "message" in data

    @pytest.mark.asyncio
    async def test_send_reminder_not_found(
        self, auth_client: AsyncClient
    ):
        """Test sending reminder for non-existent booking."""
        with patch("app.services.reminder_service.reminder_service") as mock_service:
            mock_service.send_immediate_reminder = AsyncMock(return_value=False)

            response = await auth_client.post(
                f"/api/reminders/send/{uuid.uuid4()}"
            )
            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_send_reminder_with_hours_param(
        self, auth_client: AsyncClient, test_booking_for_reminder: Booking
    ):
        """Test sending reminder with custom hours_until parameter."""
        with patch("app.services.reminder_service.reminder_service") as mock_service:
            mock_service.send_immediate_reminder = AsyncMock(return_value=True)

            response = await auth_client.post(
                f"/api/reminders/send/{test_booking_for_reminder.id}",
                params={"hours_until": 1}
            )
            assert response.status_code == 200


class TestReminderStatus:
    """Tests for reminder service status endpoint."""

    @pytest.mark.asyncio
    async def test_get_status(self, auth_client: AsyncClient):
        """Test getting reminder service status."""
        response = await auth_client.get("/api/reminders/status")
        assert response.status_code == 200
        data = response.json()
        assert "is_running" in data
        assert "message" in data

    @pytest.mark.asyncio
    async def test_get_status_unauthenticated(self, client: AsyncClient):
        """Test status endpoint requires authentication."""
        response = await client.get("/api/reminders/status")
        assert response.status_code == 401
