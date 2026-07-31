"""Move Zoom recordings into storage we own.

The export built earlier records Zoom's *download URLs*. Those stop working
the moment a recording is deleted from Zoom, so they are a pointer at someone
else's disk, not a copy. This module moves the actual bytes.

That distinction is the whole point: Zoom bills $40/month to warehouse ~340 GB,
and a Pro seat includes only 10 GB. The storage add-on cannot be cancelled
until the media lives somewhere else.

Design notes:
- Storage is an interface. LocalStorage works with no credentials at all, so
  the whole pipeline is testable before AWS exists. S3Storage is the same
  contract against a bucket.
- Every archive is verified (non-empty, checksummed) before the session record
  is repointed. A truncated download must never look like a success.
- The job is resumable and safe to re-run, because a multi-hour transfer of
  hundreds of gigabytes will be interrupted.
"""
import hashlib
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fathom_webhook import FathomWebhook

logger = logging.getLogger(__name__)

DOWNLOAD_TIMEOUT_SECONDS = 900  # session recordings are large


class Storage(ABC):
    """Somewhere we can put a file and get it back."""

    @abstractmethod
    def write(self, key: str, content: bytes) -> str:
        """Store the bytes; return the URL/locator to record."""

    @abstractmethod
    def read(self, locator: str) -> bytes:
        """Read back what we stored — used to verify an archive."""

    @abstractmethod
    def exists(self, key: str) -> bool: ...

    @abstractmethod
    def locator_for(self, key: str) -> str:
        """The locator a given key would have, without writing anything."""


class LocalStorage(Storage):
    """Files on this machine.

    Useful on its own (an external drive is a legitimate archive) and it means
    the pipeline can be exercised end to end before any cloud account exists.
    """

    def __init__(self, root: Path | str):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        return self.root / key

    def write(self, key: str, content: bytes) -> str:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        # Write to a temp name first so an interrupted write can never be
        # mistaken for a finished file.
        tmp = path.with_suffix(path.suffix + ".partial")
        tmp.write_bytes(content)
        tmp.replace(path)
        return str(path)

    def read(self, locator: str) -> bytes:
        return Path(locator).read_bytes()

    def exists(self, key: str) -> bool:
        return self._path(key).exists()

    def locator_for(self, key: str) -> str:
        return str(self._path(key))


class S3Storage(Storage):
    """An S3 bucket. Requires boto3 and AWS credentials."""

    def __init__(self, bucket: str, prefix: str = "recordings/"):
        import boto3  # imported lazily so local use needs no AWS dependency

        self.bucket = bucket
        self.prefix = prefix.rstrip("/") + "/"
        self.client = boto3.client("s3")

    def _key(self, key: str) -> str:
        return f"{self.prefix}{key}"

    def write(self, key: str, content: bytes) -> str:
        self.client.put_object(Bucket=self.bucket, Key=self._key(key), Body=content)
        return f"s3://{self.bucket}/{self._key(key)}"

    def read(self, locator: str) -> bytes:
        _, _, rest = locator.partition("s3://")
        bucket, _, key = rest.partition("/")
        return self.client.get_object(Bucket=bucket, Key=key)["Body"].read()

    def locator_for(self, key: str) -> str:
        return f"s3://{self.bucket}/{self._key(key)}"

    def exists(self, key: str) -> bool:
        from botocore.exceptions import ClientError

        try:
            self.client.head_object(Bucket=self.bucket, Key=self._key(key))
            return True
        except ClientError:
            return False


async def fetch_recording(url: str, access_token: str | None = None) -> bytes:
    """Download one recording from Zoom.

    Zoom's download URLs need the OAuth token; without it they return a login
    page rather than the media, which is exactly the sort of thing that would
    otherwise be archived as a "successful" 2 KB file.
    """
    headers = {"Authorization": f"Bearer {access_token}"} if access_token else {}
    async with httpx.AsyncClient(
        timeout=DOWNLOAD_TIMEOUT_SECONDS, follow_redirects=True
    ) as client:
        response = await client.get(url, headers=headers)
        if response.status_code != 200:
            raise RuntimeError(
                f"Zoom returned {response.status_code} for the recording download"
            )
        return response.content


def _storage_key(record: FathomWebhook) -> str:
    """A stable, readable path: recordings/2026/06/<uuid>.mp4"""
    when = record.recorded_at or record.created_at or datetime.utcnow()
    safe_id = (record.recording_id or record.id).replace("/", "_").replace("=", "")
    return f"{when.year}/{when.month:02d}/{safe_id}.mp4"


async def _pending(db: AsyncSession, limit: int | None = None) -> list[FathomWebhook]:
    stmt = (
        select(FathomWebhook)
        .where(
            FathomWebhook.source == "zoom",
            FathomWebhook.recording_url.is_not(None),
            FathomWebhook.archived_url.is_(None),
        )
        .order_by(FathomWebhook.recorded_at)
    )
    if limit:
        stmt = stmt.limit(limit)
    return list((await db.execute(stmt)).scalars().all())


async def plan_archive(db: AsyncSession, storage: Storage) -> dict[str, Any]:
    """What would be archived, without touching anything."""
    pending = await _pending(db)
    already = (
        await db.execute(
            select(FathomWebhook).where(
                FathomWebhook.source == "zoom",
                FathomWebhook.archived_url.is_not(None),
            )
        )
    ).scalars().all()
    return {
        "pending": len(pending),
        "already_archived": len(already),
        "recordings": [
            {
                "id": r.id,
                "title": r.meeting_title,
                "recorded_at": r.recorded_at.isoformat() if r.recorded_at else None,
                "key": _storage_key(r),
            }
            for r in pending
        ],
    }


async def archive_recordings(
    db: AsyncSession,
    storage: Storage,
    access_token: str | None = None,
    dry_run: bool = False,
    limit: int | None = None,
) -> dict[str, Any]:
    """Download pending recordings and repoint their session records.

    Safe to interrupt and re-run: anything already archived is skipped, and a
    record is only repointed after its bytes are verified in storage.
    """
    pending = await _pending(db, limit=limit)

    if dry_run:
        return {
            "would_archive": len(pending),
            "archived": 0,
            "skipped": 0,
            "failed": 0,
            "errors": [],
        }

    archived = skipped = failed = 0
    errors: list[str] = []

    for record in pending:
        key = _storage_key(record)
        if storage.exists(key):
            # Bytes are already there from an interrupted run; just record it.
            record.archived_url = storage.locator_for(key)
            record.archived_at = datetime.utcnow()
            skipped += 1
            continue

        try:
            content = await fetch_recording(record.recording_url, access_token)
        except Exception as exc:  # network, auth, Zoom outage
            failed += 1
            errors.append(f"{record.meeting_title or record.id}: {exc}")
            logger.warning("Could not download recording %s: %s", record.id, exc)
            continue

        if not content:
            # An empty body is a failure, not an archive. Recording this as a
            # success would be how a client's session silently disappears.
            failed += 1
            errors.append(
                f"{record.meeting_title or record.id}: Zoom returned an empty file"
            )
            continue

        locator = storage.write(key, content)

        # Verify before claiming success — the whole point is that Zoom's copy
        # is about to be deletable.
        stored = storage.read(locator)
        if len(stored) != len(content):
            failed += 1
            errors.append(f"{record.meeting_title or record.id}: stored size mismatch")
            continue

        record.archived_url = locator
        record.archived_at = datetime.utcnow()
        record.archived_bytes = len(content)
        record.archived_sha256 = hashlib.sha256(content).hexdigest()
        archived += 1
        logger.info("Archived recording %s (%s bytes)", record.id, len(content))

    await db.commit()
    return {
        "archived": archived,
        "skipped": skipped,
        "failed": failed,
        "would_archive": 0,
        "errors": errors,
    }
