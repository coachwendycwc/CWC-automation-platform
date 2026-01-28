"""
Scheduling service for calculating available time slots.
"""
from datetime import datetime, date, time, timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.booking_type import BookingType
from app.models.availability import Availability, AvailabilityOverride
from app.models.booking import Booking


class SchedulingService:
    """Service for managing scheduling and slot calculation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_available_slots(
        self,
        booking_type: BookingType,
        target_date: date,
        user_id: str,
    ) -> list[datetime]:
        """
        Calculate available time slots for a given date and booking type.

        Args:
            booking_type: The booking type with duration and constraints
            target_date: The date to check availability for
            user_id: The user (coach) whose availability to check

        Returns:
            List of available start times as datetime objects
        """
        now = datetime.now()
        today = now.date()

        # Check if date is within allowed range
        # For min_notice check, we need the datetime to check properly
        min_datetime = now + timedelta(hours=booking_type.min_notice_hours)
        min_date = min_datetime.date()
        max_date = today + timedelta(days=booking_type.max_advance_days)

        if target_date < min_date:
            return []
        if target_date > max_date:
            return []

        # Check for date override first
        override = await self._get_date_override(user_id, target_date)

        if override is not None:
            if not override.is_available:
                # Day is blocked
                return []
            # Use override times
            if override.start_time and override.end_time:
                time_windows = [(override.start_time, override.end_time)]
            else:
                # Override without times means blocked
                return []
        else:
            # Get regular availability for this day of week
            day_of_week = target_date.weekday()  # 0=Monday
            availabilities = await self._get_day_availability(user_id, day_of_week)

            if not availabilities:
                return []

            time_windows = [
                (a.start_time, a.end_time)
                for a in availabilities
                if a.is_active
            ]

        if not time_windows:
            return []

        # Generate time slots
        duration = timedelta(minutes=booking_type.duration_minutes)
        buffer_after = timedelta(minutes=booking_type.buffer_after)
        buffer_before = timedelta(minutes=booking_type.buffer_before)

        slots = []
        for start_str, end_str in time_windows:
            window_start = self._parse_time(start_str, target_date)
            window_end = self._parse_time(end_str, target_date)

            current = window_start
            while current + duration <= window_end:
                slots.append(current)
                current = current + duration + buffer_after

        # Get existing bookings for the day
        existing_bookings = await self._get_day_bookings(target_date)

        # Filter out slots that conflict with existing bookings
        available_slots = []
        for slot_start in slots:
            slot_end = slot_start + duration

            # Check if slot is in the past (with buffer for same-day booking)
            if target_date == today:
                min_time = now + timedelta(hours=booking_type.min_notice_hours)
                if slot_start < min_time:
                    continue

            # Check for conflicts with existing bookings
            has_conflict = False
            for booking in existing_bookings:
                if booking.status in ["cancelled", "no_show"]:
                    continue

                # Include buffer times in conflict check
                booking_start = booking.start_time - buffer_before
                booking_end = booking.end_time + buffer_after

                # Check for overlap
                if slot_start < booking_end and slot_end > booking_start:
                    has_conflict = True
                    break

            if not has_conflict:
                available_slots.append(slot_start)

        # Check max_per_day limit
        if booking_type.max_per_day:
            active_bookings = [
                b for b in existing_bookings
                if b.status not in ["cancelled", "no_show"]
            ]
            if len(active_bookings) >= booking_type.max_per_day:
                return []

        return available_slots

    async def get_available_dates(
        self,
        booking_type: BookingType,
        user_id: str,
        start_date: Optional[date] = None,
        days_ahead: int = 30,
    ) -> list[date]:
        """
        Get dates that have at least one available slot.

        Args:
            booking_type: The booking type
            user_id: The user whose availability to check
            start_date: Starting date (defaults to today + min_notice)
            days_ahead: Number of days to check ahead

        Returns:
            List of dates with available slots
        """
        if start_date is None:
            start_date = date.today() + timedelta(
                hours=booking_type.min_notice_hours
            )
            if isinstance(start_date, datetime):
                start_date = start_date.date()

        available_dates = []
        current = start_date

        for _ in range(days_ahead):
            if current > date.today() + timedelta(days=booking_type.max_advance_days):
                break

            slots = await self.get_available_slots(booking_type, current, user_id)
            if slots:
                available_dates.append(current)

            current += timedelta(days=1)

        return available_dates

    async def _get_day_availability(
        self, user_id: str, day_of_week: int
    ) -> list[Availability]:
        """Get availability records for a specific day of week."""
        result = await self.db.execute(
            select(Availability).where(
                and_(
                    Availability.user_id == user_id,
                    Availability.day_of_week == day_of_week,
                    Availability.is_active == True,
                )
            )
        )
        return list(result.scalars().all())

    async def _get_date_override(
        self, user_id: str, target_date: date
    ) -> Optional[AvailabilityOverride]:
        """Get override for a specific date, if any."""
        result = await self.db.execute(
            select(AvailabilityOverride).where(
                and_(
                    AvailabilityOverride.user_id == user_id,
                    AvailabilityOverride.date == target_date,
                )
            )
        )
        return result.scalar_one_or_none()

    async def _get_day_bookings(self, target_date: date) -> list[Booking]:
        """Get all bookings for a specific date."""
        day_start = datetime.combine(target_date, time.min)
        day_end = datetime.combine(target_date, time.max)

        result = await self.db.execute(
            select(Booking).where(
                and_(
                    Booking.start_time >= day_start,
                    Booking.start_time <= day_end,
                )
            )
        )
        return list(result.scalars().all())

    @staticmethod
    def _parse_time(time_str: str, target_date: date) -> datetime:
        """Parse a time string (HH:MM) and combine with date."""
        hours, minutes = map(int, time_str.split(":"))
        return datetime.combine(target_date, time(hours, minutes))

    async def can_cancel(self, booking: Booking, hours_notice: int = 24) -> bool:
        """Check if a booking can be cancelled (24hr policy by default)."""
        now = datetime.now()
        time_until_booking = booking.start_time - now
        return time_until_booking >= timedelta(hours=hours_notice)

    async def can_reschedule(self, booking: Booking, hours_notice: int = 24) -> bool:
        """Check if a booking can be rescheduled (same as cancel policy)."""
        return await self.can_cancel(booking, hours_notice)
