"""Export Zoom cloud recordings into CWC so they live with the client.

Zoom charges $40/mo to warehouse ~340GB of recordings, and a Pro seat only
includes 10GB — so recordings must come out before the storage add-on can be
dropped. Imported recordings land in the same model the client portal already
reads (FathomWebhook), matched to a contact by participant email.
"""
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contact import Contact
from app.models.fathom_webhook import FathomWebhook
from app.models.user import User
from app.services.zoom_recording_service import (
    export_recordings,
    preview_recordings,
    _match_contact,
)

ZOOM_PAGE = {
    "from": "2026-06-01",
    "to": "2026-06-30",
    "next_page_token": "",
    "meetings": [
        {
            "uuid": "abc==",
            "id": 8123456789,
            "topic": "Coaching session — Amara",
            "start_time": "2026-06-10T15:00:00Z",
            "duration": 60,
            "total_size": 524288000,
            "recording_files": [
                {
                    "id": "rec-1",
                    "file_type": "MP4",
                    "recording_type": "shared_screen_with_speaker_view",
                    "file_size": 524288000,
                    "download_url": "https://zoom.us/rec/download/rec-1",
                    "status": "completed",
                },
                {
                    "id": "rec-1-vtt",
                    "file_type": "TRANSCRIPT",
                    "recording_type": "audio_transcript",
                    "file_size": 2048,
                    "download_url": "https://zoom.us/rec/download/rec-1-vtt",
                    "status": "completed",
                },
            ],
        },
        {
            "uuid": "def==",
            "id": 8123456790,
            "topic": "Discovery call",
            "start_time": "2026-06-20T18:30:00Z",
            "duration": 30,
            "total_size": 104857600,
            "recording_files": [
                {
                    "id": "rec-2",
                    "file_type": "MP4",
                    "recording_type": "shared_screen_with_speaker_view",
                    "file_size": 104857600,
                    "download_url": "https://zoom.us/rec/download/rec-2",
                    "status": "completed",
                }
            ],
        },
    ],
}


@pytest.fixture
async def zoom_user(db_session: AsyncSession, test_user: User) -> User:
    test_user.zoom_token = {
        "access_token": "zoom-access",
        "refresh_token": "zoom-refresh",
    }
    await db_session.commit()
    return test_user


def mock_zoom(page: dict = ZOOM_PAGE):
    return patch(
        "app.services.zoom_recording_service.list_cloud_recordings",
        new_callable=AsyncMock,
        return_value=page,
    )


class TestPreview:
    async def test_preview_lists_recordings_without_writing(
        self, db_session: AsyncSession, zoom_user: User
    ):
        with mock_zoom():
            result = await preview_recordings(
                db_session, zoom_user, "2026-06-01", "2026-06-30"
            )
        assert result["count"] == 2
        assert result["total_bytes"] == 524288000 + 104857600
        titles = [item["topic"] for item in result["recordings"]]
        assert "Coaching session — Amara" in titles

        stored = (await db_session.execute(select(FathomWebhook))).scalars().all()
        assert stored == []

    async def test_preview_reports_matched_contact(
        self, db_session: AsyncSession, zoom_user: User, test_contact: Contact
    ):
        page = {
            **ZOOM_PAGE,
            "meetings": [
                {
                    **ZOOM_PAGE["meetings"][0],
                    "participant_audio_files": [],
                    "host_email": "coach@example.com",
                    "topic": f"Session with {test_contact.email}",
                }
            ],
        }
        with mock_zoom(page):
            result = await preview_recordings(
                db_session, zoom_user, "2026-06-01", "2026-06-30"
            )
        assert result["recordings"][0]["matched_contact_id"] == test_contact.id


class TestExport:
    async def test_export_creates_session_records(
        self, db_session: AsyncSession, zoom_user: User
    ):
        with mock_zoom():
            result = await export_recordings(
                db_session, zoom_user, "2026-06-01", "2026-06-30"
            )
        assert result["imported"] == 2

        records = (
            await db_session.execute(
                select(FathomWebhook).order_by(FathomWebhook.recorded_at)
            )
        ).scalars().all()
        assert len(records) == 2
        first = records[0]
        assert first.meeting_title == "Coaching session — Amara"
        assert first.recording_url == "https://zoom.us/rec/download/rec-1"
        assert first.duration_seconds == 3600
        assert first.source == "zoom"
        # Not shown to clients until a human reviews the match
        assert first.client_visible is False

    async def test_export_is_idempotent(
        self, db_session: AsyncSession, zoom_user: User
    ):
        with mock_zoom():
            await export_recordings(db_session, zoom_user, "2026-06-01", "2026-06-30")
            second = await export_recordings(
                db_session, zoom_user, "2026-06-01", "2026-06-30"
            )
        assert second["imported"] == 0
        assert second["skipped"] == 2
        records = (await db_session.execute(select(FathomWebhook))).scalars().all()
        assert len(records) == 2

    async def test_export_links_matched_contact(
        self, db_session: AsyncSession, zoom_user: User, test_contact: Contact
    ):
        page = {
            **ZOOM_PAGE,
            "meetings": [
                {
                    **ZOOM_PAGE["meetings"][0],
                    "topic": f"Session with {test_contact.email}",
                }
            ],
        }
        with mock_zoom(page):
            await export_recordings(db_session, zoom_user, "2026-06-01", "2026-06-30")
        record = (await db_session.execute(select(FathomWebhook))).scalar_one()
        assert record.contact_id == test_contact.id

    async def test_meeting_without_files_is_skipped(
        self, db_session: AsyncSession, zoom_user: User
    ):
        page = {**ZOOM_PAGE, "meetings": [{**ZOOM_PAGE["meetings"][0], "recording_files": []}]}
        with mock_zoom(page):
            result = await export_recordings(
                db_session, zoom_user, "2026-06-01", "2026-06-30"
            )
        assert result["imported"] == 0
        records = (await db_session.execute(select(FathomWebhook))).scalars().all()
        assert records == []

    async def test_user_without_zoom_connection_errors(
        self, db_session: AsyncSession, test_user: User
    ):
        test_user.zoom_token = None
        await db_session.commit()
        with pytest.raises(ValueError):
            await export_recordings(
                db_session, test_user, "2026-06-01", "2026-06-30"
            )


class TestContactMatching:
    async def test_matches_on_participant_email(
        self, db_session: AsyncSession, test_contact: Contact
    ):
        matched = await _match_contact(
            db_session,
            {"topic": "Coaching", "participants": [{"email": test_contact.email}]},
        )
        assert matched is not None
        assert matched.id == test_contact.id

    async def test_matches_email_inside_topic(
        self, db_session: AsyncSession, test_contact: Contact
    ):
        matched = await _match_contact(
            db_session, {"topic": f"Call with {test_contact.email}"}
        )
        assert matched is not None

    async def test_no_match_returns_none(self, db_session: AsyncSession):
        matched = await _match_contact(db_session, {"topic": "Team standup"})
        assert matched is None
