from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.services.auth_service import require_admin
from app.services.zoom_recording_service import (
    preview_recordings,
    export_recordings,
)

router = APIRouter(prefix="/api/zoom-recordings", tags=["Zoom Recordings"])

MAX_RANGE_DAYS = 31


class ExportRequest(BaseModel):
    date_from: str
    date_to: str


def _validate_range(date_from: str, date_to: str) -> None:
    """Zoom caps a recordings query at one month — fail loudly rather than
    silently returning a partial list."""
    try:
        start = date.fromisoformat(date_from)
        end = date.fromisoformat(date_to)
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Dates must be in YYYY-MM-DD form"
        )
    if end < start:
        raise HTTPException(status_code=400, detail="End date is before start date")
    if (end - start).days > MAX_RANGE_DAYS:
        raise HTTPException(
            status_code=400,
            detail=(
                "Zoom only returns one month of recordings per request. "
                "Export a month at a time."
            ),
        )


@router.get("/preview")
async def preview(
    date_from: str = Query(..., description="YYYY-MM-DD"),
    date_to: str = Query(..., description="YYYY-MM-DD"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> dict:
    """What's in Zoom for this month, how much space it uses, and which
    recordings already exist in CWC. Writes nothing."""
    _validate_range(date_from, date_to)
    try:
        return await preview_recordings(db, current_user, date_from, date_to)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/export")
async def export(
    request: ExportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> dict:
    """Import Zoom recordings as CWC session records, matched to contacts
    where the email is recognisable. Safe to re-run: existing meetings are
    skipped by UUID."""
    _validate_range(request.date_from, request.date_to)
    try:
        return await export_recordings(
            db, current_user, request.date_from, request.date_to
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
