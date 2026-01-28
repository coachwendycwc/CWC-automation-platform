from datetime import datetime
from fastapi import APIRouter, HTTPException, status, Request, Header, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
import hmac
import hashlib

from app.database import get_db
from app.config import get_settings
from app.models.fathom_webhook import FathomWebhook

settings = get_settings()
router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


class FathomWebhookPayload(BaseModel):
    recording_id: str | None = None
    title: str | None = None
    transcript: list[dict] | str | None = None
    default_summary: dict | None = None
    action_items: list[dict] | None = None
    calendar_invitees: list[dict] | None = None
    duration_seconds: int | None = None
    recorded_at: str | None = None


def verify_fathom_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verify the Fathom webhook signature."""
    if secret == "stubbed-for-now":
        return True  # Skip verification in dev mode

    expected = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


@router.post("/fathom", status_code=status.HTTP_200_OK)
async def receive_fathom_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_fathom_signature: str | None = Header(None, alias="X-Fathom-Signature"),
):
    """
    Receive webhooks from Fathom after call recordings.

    This endpoint stores the raw webhook payload for later processing.
    Actual invoice extraction happens in Phase 3.
    """
    body = await request.body()

    # Verify signature (skip in dev mode)
    if not verify_fathom_signature(
        body,
        x_fathom_signature or "",
        settings.fathom_webhook_secret,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature",
        )

    # Parse payload
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload",
        )

    recording_id = payload.get("recording_id")

    # Check for duplicate
    if recording_id:
        existing = await db.execute(
            select(FathomWebhook).where(FathomWebhook.recording_id == recording_id)
        )
        if existing.scalar_one_or_none():
            return {"status": "duplicate", "recording_id": recording_id}

    # Convert transcript list to text if needed
    transcript_text = None
    if payload.get("transcript"):
        if isinstance(payload["transcript"], list):
            transcript_text = "\n".join(
                f"{item.get('speaker', 'Unknown')}: {item.get('text', '')}"
                for item in payload["transcript"]
            )
        else:
            transcript_text = str(payload["transcript"])

    # Parse recorded_at
    recorded_at = None
    if payload.get("recorded_at"):
        try:
            recorded_at = datetime.fromisoformat(
                payload["recorded_at"].replace("Z", "+00:00")
            )
        except Exception:
            pass

    # Store webhook
    webhook = FathomWebhook(
        recording_id=recording_id,
        meeting_title=payload.get("title"),
        transcript=transcript_text,
        summary=payload.get("default_summary"),
        action_items=payload.get("action_items"),
        attendees=payload.get("calendar_invitees"),
        duration_seconds=payload.get("duration_seconds"),
        recorded_at=recorded_at,
        processing_status="pending",
    )
    db.add(webhook)
    await db.commit()

    return {"status": "received", "recording_id": recording_id}


@router.get("/fathom/test")
async def test_fathom_endpoint():
    """Test endpoint to verify webhook URL is reachable."""
    return {"status": "ok", "message": "Fathom webhook endpoint is active"}
