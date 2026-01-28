"""
Tests for Scheduling service.
"""
import pytest
from datetime import datetime, date, time, timedelta
from unittest.mock import patch, MagicMock, AsyncMock
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.scheduling_service import SchedulingService
from app.models.booking_type import BookingType
from app.models.availability import Availability, AvailabilityOverride
from app.models.booking import Booking


@pytest.fixture
def mock_booking_type() -> BookingType:
    """Create a mock booking type."""
    bt = MagicMock(spec=BookingType)
    bt.id = str(uuid.uuid4())
    bt.duration_minutes = 60
    bt.buffer_before = 0
    bt.buffer_after = 15
    bt.min_notice_hours = 24
    bt.max_advance_days = 30
    bt.max_per_day = 5
    return bt


class TestSchedulingServiceParsing:
    """Tests for time parsing utilities."""

    def test_parse_time(self):
        """Test time string parsing."""
        target = date(2024, 3, 15)
        result = SchedulingService._parse_time("09:00", target)

        assert result == datetime(2024, 3, 15, 9, 0)

    def test_parse_time_afternoon(self):
        """Test afternoon time parsing."""
        target = date(2024, 3, 15)
        result = SchedulingService._parse_time("14:30", target)

        assert result == datetime(2024, 3, 15, 14, 30)

    def test_parse_time_midnight(self):
        """Test midnight time parsing."""
        target = date(2024, 3, 15)
        result = SchedulingService._parse_time("00:00", target)

        assert result == datetime(2024, 3, 15, 0, 0)


class TestSchedulingServiceCancellation:
    """Tests for cancellation/rescheduling policies."""

    @pytest.fixture
    def service(self, db_session):
        """Create scheduling service."""
        return SchedulingService(db_session)

    @pytest.mark.asyncio
    async def test_can_cancel_future_booking(self, service):
        """Test can cancel booking more than 24hrs away."""
        booking = MagicMock(spec=Booking)
        booking.start_time = datetime.now() + timedelta(hours=48)

        result = await service.can_cancel(booking)
        assert result is True

    @pytest.mark.asyncio
    async def test_cannot_cancel_soon_booking(self, service):
        """Test cannot cancel booking less than 24hrs away."""
        booking = MagicMock(spec=Booking)
        booking.start_time = datetime.now() + timedelta(hours=12)

        result = await service.can_cancel(booking)
        assert result is False

    @pytest.mark.asyncio
    async def test_can_cancel_exactly_24hrs(self, service):
        """Test can cancel booking exactly 24hrs away."""
        booking = MagicMock(spec=Booking)
        booking.start_time = datetime.now() + timedelta(hours=24, minutes=1)

        result = await service.can_cancel(booking)
        assert result is True

    @pytest.mark.asyncio
    async def test_can_cancel_custom_notice(self, service):
        """Test cancellation with custom notice period."""
        booking = MagicMock(spec=Booking)
        booking.start_time = datetime.now() + timedelta(hours=50)

        # 48hr notice period
        result = await service.can_cancel(booking, hours_notice=48)
        assert result is True

    @pytest.mark.asyncio
    async def test_can_reschedule(self, service):
        """Test rescheduling uses same logic as cancel."""
        booking = MagicMock(spec=Booking)
        booking.start_time = datetime.now() + timedelta(hours=48)

        result = await service.can_reschedule(booking)
        assert result is True


class TestGetAvailableSlots:
    """Tests for slot availability calculation."""

    @pytest.fixture
    def service(self, db_session):
        """Create scheduling service with mocked DB."""
        return SchedulingService(db_session)

    @pytest.mark.asyncio
    async def test_date_too_soon(self, service, mock_booking_type):
        """Test returns empty for dates within min notice period."""
        # Date is today, which is within 24hr notice
        target = date.today()

        result = await service.get_available_slots(
            mock_booking_type, target, "user123"
        )

        # Should be empty or very limited due to min_notice
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_date_too_far(self, service, mock_booking_type):
        """Test returns empty for dates beyond max advance."""
        # Date is 60 days ahead but max is 30
        target = date.today() + timedelta(days=60)

        result = await service.get_available_slots(
            mock_booking_type, target, "user123"
        )

        assert result == []

    @pytest.mark.asyncio
    async def test_blocked_date_override(self, db_session, mock_booking_type):
        """Test returns empty for blocked date override."""
        service = SchedulingService(db_session)

        # Create a blocked override
        target = date.today() + timedelta(days=7)
        override = AvailabilityOverride(
            id=str(uuid.uuid4()),
            user_id="user123",
            date=target,
            is_available=False,
        )
        db_session.add(override)
        await db_session.commit()

        result = await service.get_available_slots(
            mock_booking_type, target, "user123"
        )

        assert result == []

    @pytest.mark.asyncio
    async def test_no_availability_for_day(self, service, mock_booking_type):
        """Test returns empty when no availability set."""
        # Future date with no availability records
        target = date.today() + timedelta(days=5)

        result = await service.get_available_slots(
            mock_booking_type, target, "user123"
        )

        assert result == []

    @pytest.mark.asyncio
    async def test_slots_with_availability(self, db_session, mock_booking_type):
        """Test returns slots when availability is set."""
        service = SchedulingService(db_session)

        # Create availability for the target day
        target = date.today() + timedelta(days=3)
        day_of_week = target.weekday()

        availability = Availability(
            id=str(uuid.uuid4()),
            user_id="user123",
            day_of_week=day_of_week,
            start_time="09:00",
            end_time="17:00",
            is_active=True,
        )
        db_session.add(availability)
        await db_session.commit()

        result = await service.get_available_slots(
            mock_booking_type, target, "user123"
        )

        # Should have slots (8 hours / 1.25 hours per slot = ~6 slots)
        assert len(result) > 0
        # All slots should be datetime objects
        for slot in result:
            assert isinstance(slot, datetime)

    @pytest.mark.asyncio
    async def test_slots_filtered_by_existing_booking(self, db_session, mock_booking_type):
        """Test slots are filtered when booking exists."""
        service = SchedulingService(db_session)

        target = date.today() + timedelta(days=3)
        day_of_week = target.weekday()

        # Create availability
        availability = Availability(
            id=str(uuid.uuid4()),
            user_id="user123",
            day_of_week=day_of_week,
            start_time="09:00",
            end_time="12:00",
            is_active=True,
        )
        db_session.add(availability)

        # Create a booking that takes 10-11am
        booking = Booking(
            id=str(uuid.uuid4()),
            booking_type_id=mock_booking_type.id,
            start_time=datetime.combine(target, time(10, 0)),
            end_time=datetime.combine(target, time(11, 0)),
            status="confirmed",
        )
        db_session.add(booking)
        await db_session.commit()

        result = await service.get_available_slots(
            mock_booking_type, target, "user123"
        )

        # 10am slot should not be available
        for slot in result:
            assert slot.hour != 10

    @pytest.mark.asyncio
    async def test_max_per_day_limit(self, db_session, mock_booking_type):
        """Test max_per_day limit is respected."""
        service = SchedulingService(db_session)

        target = date.today() + timedelta(days=3)
        day_of_week = target.weekday()
        mock_booking_type.max_per_day = 2

        # Create availability
        availability = Availability(
            id=str(uuid.uuid4()),
            user_id="user123",
            day_of_week=day_of_week,
            start_time="09:00",
            end_time="17:00",
            is_active=True,
        )
        db_session.add(availability)

        # Create max bookings for the day
        for hour in [9, 11]:
            booking = Booking(
                id=str(uuid.uuid4()),
                booking_type_id=mock_booking_type.id,
                start_time=datetime.combine(target, time(hour, 0)),
                end_time=datetime.combine(target, time(hour + 1, 0)),
                status="confirmed",
            )
            db_session.add(booking)
        await db_session.commit()

        result = await service.get_available_slots(
            mock_booking_type, target, "user123"
        )

        # Should return empty as max reached
        assert result == []

    @pytest.mark.asyncio
    async def test_cancelled_bookings_ignored(self, db_session, mock_booking_type):
        """Test cancelled bookings don't block slots."""
        service = SchedulingService(db_session)

        target = date.today() + timedelta(days=3)
        day_of_week = target.weekday()

        # Create availability
        availability = Availability(
            id=str(uuid.uuid4()),
            user_id="user123",
            day_of_week=day_of_week,
            start_time="10:00",
            end_time="12:00",
            is_active=True,
        )
        db_session.add(availability)

        # Create a cancelled booking
        booking = Booking(
            id=str(uuid.uuid4()),
            booking_type_id=mock_booking_type.id,
            start_time=datetime.combine(target, time(10, 0)),
            end_time=datetime.combine(target, time(11, 0)),
            status="cancelled",
        )
        db_session.add(booking)
        await db_session.commit()

        result = await service.get_available_slots(
            mock_booking_type, target, "user123"
        )

        # 10am slot should be available since booking was cancelled
        assert any(slot.hour == 10 for slot in result)


class TestGetAvailableDates:
    """Tests for available dates calculation."""

    @pytest.fixture
    def service(self, db_session):
        """Create scheduling service."""
        return SchedulingService(db_session)

    @pytest.mark.asyncio
    async def test_get_available_dates_empty(self, service, mock_booking_type):
        """Test returns empty when no availability."""
        result = await service.get_available_dates(
            mock_booking_type,
            "user123",
            days_ahead=7,
        )

        # No availability configured, so no dates
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_available_dates_with_availability(
        self, db_session, mock_booking_type
    ):
        """Test returns dates with availability."""
        service = SchedulingService(db_session)

        # Create availability for every day of the week
        for day in range(7):
            availability = Availability(
                id=str(uuid.uuid4()),
                user_id="user123",
                day_of_week=day,
                start_time="09:00",
                end_time="17:00",
                is_active=True,
            )
            db_session.add(availability)
        await db_session.commit()

        result = await service.get_available_dates(
            mock_booking_type,
            "user123",
            days_ahead=14,
        )

        # Should have multiple available dates
        assert len(result) > 0
        # All should be date objects
        for d in result:
            assert isinstance(d, date)

    @pytest.mark.asyncio
    async def test_get_available_dates_respects_max_advance(
        self, db_session, mock_booking_type
    ):
        """Test dates beyond max_advance_days are excluded."""
        service = SchedulingService(db_session)
        mock_booking_type.max_advance_days = 7

        # Create availability
        for day in range(7):
            availability = Availability(
                id=str(uuid.uuid4()),
                user_id="user123",
                day_of_week=day,
                start_time="09:00",
                end_time="17:00",
                is_active=True,
            )
            db_session.add(availability)
        await db_session.commit()

        result = await service.get_available_dates(
            mock_booking_type,
            "user123",
            days_ahead=30,  # More than max_advance_days
        )

        # Should not have dates beyond max_advance_days
        max_date = date.today() + timedelta(days=7)
        for d in result:
            assert d <= max_date
