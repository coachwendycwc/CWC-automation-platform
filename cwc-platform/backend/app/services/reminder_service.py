"""
Background reminder service for booking notifications.
Sends 24h and 1h reminders before scheduled bookings.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import async_session_maker
from app.models.booking import Booking
from app.models.contact import Contact
from app.models.booking_type import BookingType
from app.services.email_service import email_service
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class ReminderService:
    """Service for sending booking reminders."""

    def __init__(self):
        self.is_running = False
        self._task: Optional[asyncio.Task] = None

    async def start(self):
        """Start the reminder scheduler."""
        if self.is_running:
            logger.warning("Reminder service already running")
            return

        self.is_running = True
        self._task = asyncio.create_task(self._run_scheduler())
        logger.info("Reminder service started")

    async def stop(self):
        """Stop the reminder scheduler."""
        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Reminder service stopped")

    async def _run_scheduler(self):
        """Main scheduler loop - runs every 5 minutes."""
        while self.is_running:
            try:
                await self.check_and_send_reminders()
            except Exception as e:
                logger.error(f"Error in reminder scheduler: {e}")

            # Wait 5 minutes before next check
            await asyncio.sleep(300)

    async def check_and_send_reminders(self):
        """Check for upcoming bookings and send reminders."""
        async with async_session_maker() as db:
            now = datetime.utcnow()

            # 24-hour reminder window: bookings between 23-25 hours from now
            window_24h_start = now + timedelta(hours=23)
            window_24h_end = now + timedelta(hours=25)

            # 1-hour reminder window: bookings between 50-70 minutes from now
            window_1h_start = now + timedelta(minutes=50)
            window_1h_end = now + timedelta(minutes=70)

            # Find bookings needing 24h reminder
            await self._send_24h_reminders(db, window_24h_start, window_24h_end)

            # Find bookings needing 1h reminder
            await self._send_1h_reminders(db, window_1h_start, window_1h_end)

    async def _send_24h_reminders(
        self, db: AsyncSession, window_start: datetime, window_end: datetime
    ):
        """Send 24-hour reminders for upcoming bookings."""
        result = await db.execute(
            select(Booking)
            .options(
                selectinload(Booking.contact),
                selectinload(Booking.booking_type),
            )
            .where(
                and_(
                    Booking.status == "confirmed",
                    Booking.start_time >= window_start,
                    Booking.start_time <= window_end,
                    Booking.reminder_24h_sent_at.is_(None),
                )
            )
        )
        bookings = result.scalars().all()

        for booking in bookings:
            try:
                await self._send_reminder(db, booking, hours_until=24)
                booking.reminder_24h_sent_at = datetime.utcnow()
                await db.commit()
                logger.info(f"Sent 24h reminder for booking {booking.id}")
            except Exception as e:
                logger.error(f"Failed to send 24h reminder for booking {booking.id}: {e}")
                await db.rollback()

    async def _send_1h_reminders(
        self, db: AsyncSession, window_start: datetime, window_end: datetime
    ):
        """Send 1-hour reminders for upcoming bookings."""
        result = await db.execute(
            select(Booking)
            .options(
                selectinload(Booking.contact),
                selectinload(Booking.booking_type),
            )
            .where(
                and_(
                    Booking.status == "confirmed",
                    Booking.start_time >= window_start,
                    Booking.start_time <= window_end,
                    Booking.reminder_1h_sent_at.is_(None),
                )
            )
        )
        bookings = result.scalars().all()

        for booking in bookings:
            try:
                await self._send_reminder(db, booking, hours_until=1)
                booking.reminder_1h_sent_at = datetime.utcnow()
                await db.commit()
                logger.info(f"Sent 1h reminder for booking {booking.id}")
            except Exception as e:
                logger.error(f"Failed to send 1h reminder for booking {booking.id}: {e}")
                await db.rollback()

    async def _send_reminder(self, db: AsyncSession, booking: Booking, hours_until: int):
        """Send a reminder email for a booking."""
        contact = booking.contact
        booking_type = booking.booking_type

        if not contact or not contact.email:
            logger.warning(f"No email for booking {booking.id}")
            return

        # Get meeting link from Google Calendar event if available
        meeting_link = None
        if booking.google_event_id:
            # Could fetch from Google Calendar, but for now we'll skip
            pass

        await email_service.send_booking_reminder(
            to_email=contact.email,
            contact_name=f"{contact.first_name} {contact.last_name}".strip(),
            booking_type=booking_type.name if booking_type else "Session",
            booking_date=booking.start_time,
            meeting_link=meeting_link,
            hours_until=hours_until,
        )

    async def send_immediate_reminder(self, booking_id: str, hours_until: int = 24) -> bool:
        """Send an immediate reminder for a specific booking (manual trigger)."""
        async with async_session_maker() as db:
            result = await db.execute(
                select(Booking)
                .options(
                    selectinload(Booking.contact),
                    selectinload(Booking.booking_type),
                )
                .where(Booking.id == booking_id)
            )
            booking = result.scalar_one_or_none()

            if not booking:
                logger.error(f"Booking {booking_id} not found")
                return False

            try:
                await self._send_reminder(db, booking, hours_until)

                # Update the appropriate reminder field
                if hours_until >= 12:
                    booking.reminder_24h_sent_at = datetime.utcnow()
                else:
                    booking.reminder_1h_sent_at = datetime.utcnow()

                await db.commit()
                return True
            except Exception as e:
                logger.error(f"Failed to send reminder for booking {booking_id}: {e}")
                await db.rollback()
                return False


# Singleton instance
reminder_service = ReminderService()
