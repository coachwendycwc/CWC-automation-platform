"""
Integrations router for OAuth flows and external service connections.
"""
import os
import secrets
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.database import get_db
from app.services.auth_service import get_current_user
from app.services.google_calendar_service import google_calendar_service
from app.services.zoom_service import zoom_service
from app.models.user import User

router = APIRouter(prefix="/api/integrations", tags=["integrations"])


class IntegrationStatus(BaseModel):
    """Integration status response."""
    google_calendar: bool = False
    zoom: bool = False


class GoogleCalendarEvent(BaseModel):
    """Google Calendar event data."""
    summary: str
    start_time: datetime
    end_time: datetime
    description: Optional[str] = None
    location: Optional[str] = None
    attendees: Optional[list[str]] = None


# In-memory state storage (use Redis in production)
oauth_states: dict[str, str] = {}


@router.get("/status", response_model=IntegrationStatus)
async def get_integration_status(
    current_user: User = Depends(get_current_user),
) -> IntegrationStatus:
    """Get status of all integrations for current user."""
    return IntegrationStatus(
        google_calendar=current_user.google_calendar_token is not None,
        zoom=current_user.zoom_token is not None,
    )


# ============ Google Calendar ============

@router.get("/google/auth-url")
async def get_google_auth_url(
    current_user: User = Depends(get_current_user),
) -> dict:
    """Get Google OAuth authorization URL."""
    if not google_calendar_service.is_configured():
        raise HTTPException(
            status_code=503,
            detail="Google Calendar integration not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET.",
        )

    # Generate state for CSRF protection
    state = secrets.token_urlsafe(32)
    oauth_states[state] = str(current_user.id)

    auth_url = google_calendar_service.get_auth_url(state=state)

    return {"auth_url": auth_url}


@router.get("/google/callback")
async def google_oauth_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    """Handle Google OAuth callback."""
    # Verify state
    user_id = oauth_states.pop(state, None)
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid state parameter")

    # Get user
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        # Exchange code for tokens
        token_data = google_calendar_service.exchange_code(code)

        # Store tokens in user record
        user.google_calendar_token = token_data

        await db.commit()

        # Redirect to settings page with success message
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3001")
        return RedirectResponse(f"{frontend_url}/settings?google_connected=true")

    except Exception as e:
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3001")
        return RedirectResponse(f"{frontend_url}/settings?google_error={str(e)}")


@router.delete("/google/disconnect")
async def disconnect_google(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Disconnect Google Calendar integration."""
    # Get fresh user from DB
    result = await db.execute(select(User).where(User.id == current_user.id))
    user = result.scalar_one_or_none()

    if user:
        user.google_calendar_token = None
        await db.commit()

    return {"message": "Google Calendar disconnected"}


@router.get("/google/events")
async def list_google_events(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    """List upcoming Google Calendar events."""
    if not current_user.google_calendar_token:
        raise HTTPException(
            status_code=400,
            detail="Google Calendar not connected",
        )

    try:
        from datetime import timedelta

        time_min = datetime.utcnow()
        time_max = time_min + timedelta(days=days)

        events = google_calendar_service.list_events(
            token_data=current_user.google_calendar_token,
            time_min=time_min,
            time_max=time_max,
        )

        return events
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/google/events")
async def create_google_event(
    event: GoogleCalendarEvent,
    current_user: User = Depends(get_current_user),
) -> dict:
    """Create a Google Calendar event."""
    if not current_user.google_calendar_token:
        raise HTTPException(
            status_code=400,
            detail="Google Calendar not connected",
        )

    try:
        result = google_calendar_service.create_event(
            token_data=current_user.google_calendar_token,
            summary=event.summary,
            start_time=event.start_time,
            end_time=event.end_time,
            description=event.description,
            location=event.location,
            attendees=event.attendees,
        )

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/google/events/{event_id}")
async def delete_google_event(
    event_id: str,
    current_user: User = Depends(get_current_user),
) -> dict:
    """Delete a Google Calendar event."""
    if not current_user.google_calendar_token:
        raise HTTPException(
            status_code=400,
            detail="Google Calendar not connected",
        )

    try:
        success = google_calendar_service.delete_event(
            token_data=current_user.google_calendar_token,
            event_id=event_id,
        )

        if success:
            return {"message": "Event deleted"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete event")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ Zoom ============

@router.get("/zoom/auth-url")
async def get_zoom_auth_url(
    current_user: User = Depends(get_current_user),
) -> dict:
    """Get Zoom OAuth authorization URL."""
    if not zoom_service.is_configured:
        raise HTTPException(
            status_code=503,
            detail="Zoom integration not configured. Set ZOOM_CLIENT_ID and ZOOM_CLIENT_SECRET.",
        )

    # Generate state for CSRF protection
    state = secrets.token_urlsafe(32)
    oauth_states[state] = f"zoom:{current_user.id}"

    auth_url = zoom_service.get_authorization_url(state=state)

    return {"auth_url": auth_url}


@router.get("/zoom/callback")
async def zoom_oauth_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    """Handle Zoom OAuth callback."""
    # Verify state
    state_data = oauth_states.pop(state, None)
    if not state_data or not state_data.startswith("zoom:"):
        raise HTTPException(status_code=400, detail="Invalid state parameter")

    user_id = state_data.replace("zoom:", "")

    # Get user
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        # Exchange code for tokens
        token_data = await zoom_service.exchange_code_for_tokens(code)

        # Store tokens in user record
        user.zoom_token = token_data

        await db.commit()

        # Redirect to settings page with success message
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3001")
        return RedirectResponse(f"{frontend_url}/settings?zoom_connected=true")

    except Exception as e:
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3001")
        return RedirectResponse(f"{frontend_url}/settings?zoom_error={str(e)}")


@router.delete("/zoom/disconnect")
async def disconnect_zoom(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Disconnect Zoom integration."""
    # Get fresh user from DB
    result = await db.execute(select(User).where(User.id == current_user.id))
    user = result.scalar_one_or_none()

    if user:
        user.zoom_token = None
        await db.commit()

    return {"message": "Zoom disconnected"}


@router.get("/zoom/user")
async def get_zoom_user(
    current_user: User = Depends(get_current_user),
) -> dict:
    """Get connected Zoom user info."""
    if not current_user.zoom_token:
        raise HTTPException(
            status_code=400,
            detail="Zoom not connected",
        )

    try:
        access_token = current_user.zoom_token.get("access_token")
        if not access_token:
            raise HTTPException(status_code=400, detail="Invalid Zoom token")

        user_info = await zoom_service.get_user_info(access_token)
        return user_info
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
