"""Export Zoom cloud recordings into CWC session records.

Zoom bills separately to warehouse recordings and a Pro seat includes only
10 GB, so recordings have to come out of Zoom before that add-on can be
dropped. Exported sessions land in the same table the client portal already
reads, matched to a contact where possible.

Imported rows are NOT client-visible until a human confirms the match — an
automatic email match is a good guess, not proof, and session recordings are
private to the individual coachee.
"""
import logging
import re
from datetime import datetime
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contact import Contact
from app.models.fathom_webhook import FathomWebhook
from app.models.user import User
from app.services.zoom_service import zoom_service

logger = logging.getLogger(__name__)

EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
ZOOM_API_URL = "https://api.zoom.us/v2"
VIDEO_TYPES = {"MP4", "M4A"}
TRANSCRIPT_TYPES = {"TRANSCRIPT", "CC", "VTT"}


async def list_cloud_recordings(
    access_token: str,
    date_from: str,
    date_to: str,
    next_page_token: str = "",
) -> dict[str, Any]:
    """One page of the authenticated user's cloud recordings.

    Zoom caps each query at a one-month range, so callers walk month by month.
    """
    params: dict[str, Any] = {
        "from": date_from,
        "to": date_to,
        "page_size": 300,
    }
    if next_page_token:
        params["next_page_token"] = next_page_token

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.get(
            f"{ZOOM_API_URL}/users/me/recordings",
            headers={"Authorization": f"Bearer {access_token}"},
            params=params,
        )
        if response.status_code != 200:
            logger.error("Zoom recordings list failed: %s", response.text)
            raise ValueError(
                "Could not read recordings from Zoom. Reconnect Zoom in "
                "Settings and try again."
            )
        return response.json()


def _access_token(user: User) -> str:
    if not user.zoom_token or not user.zoom_token.get("access_token"):
        raise ValueError("Zoom is not connected for this user")
    return user.zoom_token["access_token"]


def _emails_in(meeting: dict[str, Any]) -> list[str]:
    """Every email this meeting mentions, best candidates first."""
    emails: list[str] = []
    for participant in meeting.get("participants") or []:
        if participant.get("email"):
            emails.append(participant["email"])
    for key in ("topic", "agenda"):
        emails.extend(EMAIL_PATTERN.findall(meeting.get(key) or ""))
    return emails


async def _match_contact(
    db: AsyncSession, meeting: dict[str, Any]
) -> Contact | None:
    """Best-effort contact match. A miss is fine — the row still imports."""
    for email in _emails_in(meeting):
        contact = (
            await db.execute(
                select(Contact).where(Contact.email == email.lower())
            )
        ).scalars().first()
        if contact is not None:
            return contact
    return None


def _pick_files(meeting: dict[str, Any]) -> tuple[dict | None, dict | None]:
    """The video file to keep, and its transcript if Zoom made one."""
    video = None
    transcript = None
    for entry in meeting.get("recording_files") or []:
        if entry.get("status") not in (None, "completed"):
            continue
        file_type = (entry.get("file_type") or "").upper()
        if file_type in VIDEO_TYPES and video is None:
            video = entry
        elif file_type in TRANSCRIPT_TYPES and transcript is None:
            transcript = entry
    return video, transcript


def _recorded_at(meeting: dict[str, Any]) -> datetime | None:
    raw = meeting.get("start_time")
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).replace(
            tzinfo=None
        )
    except ValueError:
        return None


async def preview_recordings(
    db: AsyncSession,
    user: User,
    date_from: str,
    date_to: str,
) -> dict[str, Any]:
    """What would be exported, and how much storage it frees. Writes nothing."""
    payload = await list_cloud_recordings(_access_token(user), date_from, date_to)

    recordings = []
    total_bytes = 0
    for meeting in payload.get("meetings", []):
        video, transcript = _pick_files(meeting)
        contact = await _match_contact(db, meeting)
        existing = (
            await db.execute(
                select(FathomWebhook).where(
                    FathomWebhook.recording_id == str(meeting.get("uuid"))
                )
            )
        ).scalars().first()
        size = meeting.get("total_size") or 0
        total_bytes += size
        recordings.append(
            {
                "uuid": meeting.get("uuid"),
                "topic": meeting.get("topic"),
                "start_time": meeting.get("start_time"),
                "duration_minutes": meeting.get("duration"),
                "size_bytes": size,
                "has_video": video is not None,
                "has_transcript": transcript is not None,
                "matched_contact_id": contact.id if contact else None,
                "matched_contact_name": (
                    f"{contact.first_name} {contact.last_name or ''}".strip()
                    if contact
                    else None
                ),
                "already_imported": existing is not None,
            }
        )

    return {
        "count": len(recordings),
        "total_bytes": total_bytes,
        "recordings": recordings,
    }


async def export_recordings(
    db: AsyncSession,
    user: User,
    date_from: str,
    date_to: str,
) -> dict[str, Any]:
    """Import Zoom recordings as session records, keyed by meeting UUID.

    Stores Zoom's download URL rather than copying the media: it keeps the
    export fast and reversible. Downloading the files to owned storage is the
    follow-up that makes deleting them from Zoom safe.
    """
    access_token = _access_token(user)
    payload = await list_cloud_recordings(access_token, date_from, date_to)

    imported = 0
    skipped = 0
    matched = 0
    errors: list[str] = []

    for meeting in payload.get("meetings", []):
        uuid = str(meeting.get("uuid") or "")
        if not uuid:
            errors.append(f"Meeting {meeting.get('id')} has no uuid; skipped")
            continue

        existing = (
            await db.execute(
                select(FathomWebhook).where(FathomWebhook.recording_id == uuid)
            )
        ).scalars().first()
        if existing is not None:
            skipped += 1
            continue

        video, transcript = _pick_files(meeting)
        if video is None:
            skipped += 1
            continue

        contact = await _match_contact(db, meeting)
        if contact is not None:
            matched += 1

        duration_minutes = meeting.get("duration") or 0
        record = FathomWebhook(
            recording_id=uuid,
            source="zoom",
            meeting_title=meeting.get("topic"),
            recording_url=video.get("download_url"),
            # transcript column holds text, not a URL; keep the Zoom fetch URL
            # in summary so a later pass can download the actual VTT.
            summary=(
                {"zoom_transcript_url": transcript.get("download_url")}
                if transcript
                else None
            ),
            duration_seconds=int(duration_minutes) * 60,
            recorded_at=_recorded_at(meeting),
            contact_id=contact.id if contact else None,
            # A guessed match is not proof; a human confirms before the client
            # can see it.
            client_visible=False,
            processing_status="imported",
            processed_at=datetime.utcnow(),
        )
        db.add(record)
        imported += 1

    await db.commit()
    return {
        "imported": imported,
        "skipped": skipped,
        "matched_to_contact": matched,
        "errors": errors,
    }
