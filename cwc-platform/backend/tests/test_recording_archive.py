"""Archiving Zoom recordings into storage we own.

Zoom's download URLs die when the recording is deleted, so the export built
earlier records *links*, not media. This moves the actual bytes somewhere we
control, which is what makes cancelling Zoom's storage add-on safe.

The properties that matter for a ~340 GB one-way job:
- dry run must move nothing
- a partial or corrupted download must never be mistaken for a complete one
- re-running must skip what's already archived (it will be interrupted)
- a session record must only be repointed AFTER its bytes are safely stored
"""
import hashlib
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fathom_webhook import FathomWebhook
from app.services.recording_archive import (
    LocalStorage,
    archive_recordings,
    plan_archive,
)

VIDEO = b"fake mp4 bytes for testing" * 100


@pytest.fixture
def storage(tmp_path: Path) -> LocalStorage:
    return LocalStorage(tmp_path)


async def make_recording(
    db: AsyncSession, uuid: str = "abc==", url: str = "https://zoom.us/rec/dl/abc"
) -> FathomWebhook:
    rec = FathomWebhook(
        recording_id=uuid,
        source="zoom",
        meeting_title="Coaching session",
        recording_url=url,
        duration_seconds=3600,
    )
    db.add(rec)
    await db.commit()
    await db.refresh(rec)
    return rec


def mock_download(content: bytes = VIDEO):
    return patch(
        "app.services.recording_archive.fetch_recording",
        new_callable=AsyncMock,
        return_value=content,
    )


class TestPlan:
    async def test_plan_lists_what_would_be_archived(
        self, db_session: AsyncSession, storage: LocalStorage
    ):
        await make_recording(db_session)
        plan = await plan_archive(db_session, storage)
        assert plan["pending"] == 1
        assert plan["already_archived"] == 0

    async def test_plan_writes_nothing(
        self, db_session: AsyncSession, storage: LocalStorage, tmp_path: Path
    ):
        await make_recording(db_session)
        await plan_archive(db_session, storage)
        assert list(tmp_path.iterdir()) == []

    async def test_plan_ignores_non_zoom_sessions(
        self, db_session: AsyncSession, storage: LocalStorage
    ):
        db_session.add(
            FathomWebhook(
                recording_id="fathom-1",
                source="fathom",
                recording_url="https://fathom.video/x",
            )
        )
        await db_session.commit()
        plan = await plan_archive(db_session, storage)
        assert plan["pending"] == 0


class TestArchive:
    async def test_archives_bytes_and_repoints_the_record(
        self, db_session: AsyncSession, storage: LocalStorage
    ):
        rec = await make_recording(db_session)
        with mock_download():
            result = await archive_recordings(db_session, storage)
        assert result["archived"] == 1

        await db_session.refresh(rec)
        assert rec.archived_url is not None
        assert rec.archived_at is not None
        # The Zoom URL is kept: until Zoom is actually purged it is a fallback,
        # and afterwards it is a record of where the file came from.
        assert rec.recording_url == "https://zoom.us/rec/dl/abc"

        stored = storage.read(rec.archived_url)
        assert stored == VIDEO

    async def test_dry_run_moves_nothing(
        self, db_session: AsyncSession, storage: LocalStorage, tmp_path: Path
    ):
        rec = await make_recording(db_session)
        with mock_download():
            result = await archive_recordings(db_session, storage, dry_run=True)
        assert result["would_archive"] == 1
        assert list(tmp_path.iterdir()) == []
        await db_session.refresh(rec)
        assert rec.archived_url is None

    async def test_rerun_archives_nothing_twice(
        self, db_session: AsyncSession, storage: LocalStorage
    ):
        """Re-running after an interruption must not re-download or duplicate."""
        rec = await make_recording(db_session)
        with mock_download():
            first = await archive_recordings(db_session, storage)
            second = await archive_recordings(db_session, storage)
        assert first["archived"] == 1
        assert second["archived"] == 0  # nothing left pending

    async def test_resumes_when_bytes_exist_but_record_was_not_updated(
        self, db_session: AsyncSession, storage: LocalStorage
    ):
        """Interrupted between writing the file and committing the record:
        the next run must adopt the existing file, not re-download it."""
        rec = await make_recording(db_session)
        from app.services.recording_archive import _storage_key

        storage.write(_storage_key(rec), VIDEO)  # simulate the orphaned write

        with patch(
            "app.services.recording_archive.fetch_recording",
            new_callable=AsyncMock,
            side_effect=AssertionError("should not re-download an existing file"),
        ):
            result = await archive_recordings(db_session, storage)

        assert result["skipped"] == 1
        await db_session.refresh(rec)
        assert rec.archived_url is not None

    async def test_records_checksum_so_corruption_is_detectable(
        self, db_session: AsyncSession, storage: LocalStorage
    ):
        rec = await make_recording(db_session)
        with mock_download():
            await archive_recordings(db_session, storage)
        await db_session.refresh(rec)
        assert rec.archived_sha256 == hashlib.sha256(VIDEO).hexdigest()
        assert rec.archived_bytes == len(VIDEO)


class TestFailuresAreSafe:
    async def test_empty_download_is_not_treated_as_success(
        self, db_session: AsyncSession, storage: LocalStorage
    ):
        """A zero-byte response must never look like a completed archive."""
        rec = await make_recording(db_session)
        with mock_download(content=b""):
            result = await archive_recordings(db_session, storage)
        assert result["archived"] == 0
        assert result["failed"] == 1
        await db_session.refresh(rec)
        assert rec.archived_url is None

    async def test_download_error_leaves_record_untouched(
        self, db_session: AsyncSession, storage: LocalStorage
    ):
        rec = await make_recording(db_session)
        with patch(
            "app.services.recording_archive.fetch_recording",
            new_callable=AsyncMock,
            side_effect=Exception("connection reset"),
        ):
            result = await archive_recordings(db_session, storage)
        assert result["failed"] == 1
        await db_session.refresh(rec)
        assert rec.archived_url is None
        assert rec.archived_at is None

    async def test_one_failure_does_not_stop_the_rest(
        self, db_session: AsyncSession, storage: LocalStorage
    ):
        await make_recording(db_session, uuid="good==", url="https://zoom.us/rec/good")
        await make_recording(db_session, uuid="bad==", url="https://zoom.us/rec/bad")

        async def flaky(url: str, *a, **k):
            if "bad" in url:
                raise Exception("that one is broken")
            return VIDEO

        with patch(
            "app.services.recording_archive.fetch_recording",
            new_callable=AsyncMock,
            side_effect=flaky,
        ):
            result = await archive_recordings(db_session, storage)
        assert result["archived"] == 1
        assert result["failed"] == 1

    async def test_limit_allows_a_small_first_run(
        self, db_session: AsyncSession, storage: LocalStorage
    ):
        """Archive one recording first and check it, before committing to 340GB."""
        await make_recording(db_session, uuid="a==")
        await make_recording(db_session, uuid="b==")
        with mock_download():
            result = await archive_recordings(db_session, storage, limit=1)
        assert result["archived"] == 1
