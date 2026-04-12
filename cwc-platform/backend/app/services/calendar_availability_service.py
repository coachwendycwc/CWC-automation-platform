"""
Calendar availability aggregation service.

Builds a unified busy-time view from connected external calendar accounts.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, date, time, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.calendar_connection import CalendarConnection
from app.services.google_calendar_service import google_calendar_service


@dataclass
class BusyTimeWindow:
    start: datetime
    end: datetime
    provider: str
    connection_id: str


class CalendarAvailabilityService:
    """Aggregates busy-time across active connected calendar accounts."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_busy_windows_for_date(
        self,
        user_id: str,
        target_date: date,
    ) -> list[BusyTimeWindow]:
        day_start = datetime.combine(target_date, time.min)
        day_end = datetime.combine(target_date, time.max)

        result = await self.db.execute(
            select(CalendarConnection).where(
                CalendarConnection.user_id == user_id,
                CalendarConnection.is_active == True,
                CalendarConnection.conflict_check_enabled == True,
            )
        )
        connections = result.scalars().all()

        busy_windows: list[BusyTimeWindow] = []
        for connection in connections:
            if connection.provider == "google" and connection.token_data:
                busy_windows.extend(
                    self._get_google_busy_windows(connection, day_start, day_end)
                )

        return busy_windows

    def _get_google_busy_windows(
        self,
        connection: CalendarConnection,
        day_start: datetime,
        day_end: datetime,
    ) -> list[BusyTimeWindow]:
        events = google_calendar_service.list_events(
            token_data=connection.token_data or {},
            time_min=day_start,
            time_max=day_end,
            calendar_id=connection.calendar_id,
        )

        busy_windows: list[BusyTimeWindow] = []
        for event in events:
            if event.get("status") == "cancelled":
                continue

            start = self._parse_event_time(event.get("start"), is_end=False)
            end = self._parse_event_time(event.get("end"), is_end=True)
            if not start or not end:
                continue
            if end <= day_start or start >= day_end:
                continue

            busy_windows.append(
                BusyTimeWindow(
                    start=max(start, day_start),
                    end=min(end, day_end),
                    provider="google",
                    connection_id=connection.id,
                )
            )

        return busy_windows

    @staticmethod
    def _parse_event_time(
        value: dict | None,
        *,
        is_end: bool,
    ) -> datetime | None:
        if not value:
            return None

        date_time = value.get("dateTime")
        if date_time:
            parsed = datetime.fromisoformat(date_time.replace("Z", "+00:00"))
            if parsed.tzinfo is not None:
                parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
            return parsed

        all_day_date = value.get("date")
        if all_day_date:
            parsed_date = date.fromisoformat(all_day_date)
            if is_end:
                return datetime.combine(parsed_date, time.min)
            return datetime.combine(parsed_date, time.min)

        return None
