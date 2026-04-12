from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking
from app.models.booking_type import BookingType
from app.models.calendar_connection import CalendarConnection
from app.models.contact import Contact
from app.models.user import User
from app.services.google_calendar_service import google_calendar_service

logger = logging.getLogger(__name__)


class BookingCalendarService:
    """Sync bookings to the selected primary calendar connection."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_primary_google_connection(self, user_id: str) -> CalendarConnection | None:
        result = await self.db.execute(
            select(CalendarConnection).where(
                CalendarConnection.user_id == user_id,
                CalendarConnection.provider == "google",
                CalendarConnection.is_active == True,
                CalendarConnection.is_primary == True,
            )
        )
        return result.scalar_one_or_none()

    async def _get_google_write_target(
        self, user: User, preferred_connection_id: str | None = None
    ) -> tuple[dict | None, str, str | None]:
        connection: CalendarConnection | None = None

        if preferred_connection_id:
            result = await self.db.execute(
                select(CalendarConnection).where(
                    CalendarConnection.id == preferred_connection_id,
                    CalendarConnection.user_id == user.id,
                    CalendarConnection.provider == "google",
                    CalendarConnection.is_active == True,
                )
            )
            connection = result.scalar_one_or_none()

        if connection is None:
            connection = await self._get_primary_google_connection(user.id)

        if connection and connection.token_data and connection.sync_direction != "read":
            return connection.token_data, connection.calendar_id or "primary", connection.id

        if user.google_calendar_token:
            return user.google_calendar_token, "primary", None

        return None, "primary", None

    async def create_booking_event(
        self,
        *,
        user: User,
        booking: Booking,
        booking_type: BookingType,
        contact: Contact,
    ) -> None:
        token_data, calendar_id, connection_id = await self._get_google_write_target(user)
        create_google_meet = booking_type.location_type == "google_meet"

        if booking_type.location_type == "custom" and booking_type.location_details:
            booking.meeting_provider = "custom"
            booking.meeting_url = booking_type.location_details
            await self.db.commit()

        if not token_data:
            return

        try:
            description_lines = [f"Booking with {contact.full_name}"]
            if booking_type.location_type:
                description_lines.append(f"Location: {booking_type.location_type.replace('_', ' ').title()}")
            if booking_type.location_details:
                description_lines.append(f"Location details: {booking_type.location_details}")
            if booking.notes:
                description_lines.append("")
                description_lines.append(booking.notes)

            event = google_calendar_service.create_event(
                token_data=token_data,
                calendar_id=calendar_id,
                summary=f"{booking_type.name} - {contact.full_name}",
                start_time=booking.start_time,
                end_time=booking.end_time,
                description="\n".join(description_lines),
                location=booking_type.location_details if booking_type.location_type in {"phone", "in_person", "custom"} else None,
                attendees=[contact.email] if contact.email else None,
                create_google_meet=create_google_meet,
            )
            booking.google_event_id = event.get("id")
            booking.calendar_connection_id = connection_id
            if create_google_meet:
                booking.meeting_provider = "google_meet"
                booking.meeting_url = (
                    event.get("hangoutLink")
                    or event.get("conferenceData", {})
                    .get("entryPoints", [{}])[0]
                    .get("uri")
                )
            elif booking_type.location_type in {"phone", "in_person"}:
                booking.meeting_provider = booking_type.location_type
                booking.meeting_url = booking_type.location_details
            await self.db.commit()
        except Exception as exc:
            logger.error(f"Failed to create Google Calendar event for booking {booking.id}: {exc}")

    async def update_booking_event(
        self,
        *,
        user: User,
        booking: Booking,
        booking_type: BookingType,
        contact: Contact,
    ) -> None:
        if not booking.google_event_id:
            return

        create_google_meet = booking_type.location_type == "google_meet"
        token_data, calendar_id, connection_id = await self._get_google_write_target(
            user, booking.calendar_connection_id
        )
        if not token_data:
            return

        try:
            description_lines = [f"Booking with {contact.full_name}"]
            if booking_type.location_type and booking_type.location_type != "zoom":
                description_lines.append(f"Location: {booking_type.location_type.replace('_', ' ').title()}")
            if booking_type.location_details:
                description_lines.append(f"Location details: {booking_type.location_details}")
            if booking.notes:
                description_lines.append("")
                description_lines.append(booking.notes)

            google_calendar_service.update_event(
                token_data=token_data,
                calendar_id=calendar_id,
                event_id=booking.google_event_id,
                summary=f"{booking_type.name} - {contact.full_name}",
                start_time=booking.start_time,
                end_time=booking.end_time,
                description="\n".join(description_lines),
                location=booking_type.location_details if booking_type.location_type in {"phone", "in_person", "custom"} else None,
                create_google_meet=create_google_meet,
            )
            booking.calendar_connection_id = connection_id
            if booking_type.location_type in {"phone", "in_person", "custom"}:
                booking.meeting_provider = booking_type.location_type
                booking.meeting_url = booking_type.location_details
            await self.db.commit()
        except Exception as exc:
            logger.error(f"Failed to update Google Calendar event for booking {booking.id}: {exc}")

    async def delete_booking_event(self, *, user: User, booking: Booking) -> None:
        if not booking.google_event_id:
            return

        token_data, calendar_id, connection_id = await self._get_google_write_target(
            user, booking.calendar_connection_id
        )
        if not token_data:
            return

        try:
            success = google_calendar_service.delete_event(
                token_data=token_data,
                calendar_id=calendar_id,
                event_id=booking.google_event_id,
            )
            if success:
                booking.google_event_id = None
                booking.calendar_connection_id = connection_id
                await self.db.commit()
        except Exception as exc:
            logger.error(f"Failed to delete Google Calendar event for booking {booking.id}: {exc}")
