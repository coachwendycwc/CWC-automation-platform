"""
Zoom integration service for OAuth and meeting creation.
"""

import base64
import logging
from datetime import datetime
from typing import Optional
import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class ZoomService:
    """Service for Zoom OAuth and meeting management."""

    OAUTH_URL = "https://zoom.us/oauth/authorize"
    TOKEN_URL = "https://zoom.us/oauth/token"
    API_URL = "https://api.zoom.us/v2"

    def __init__(self):
        self.client_id = settings.zoom_client_id
        self.client_secret = settings.zoom_client_secret
        self.redirect_uri = settings.zoom_redirect_uri

    @property
    def is_configured(self) -> bool:
        """Check if Zoom credentials are configured."""
        return bool(self.client_id and self.client_secret)

    def get_authorization_url(self, state: str) -> str:
        """Generate Zoom OAuth authorization URL."""
        if not self.is_configured:
            raise ValueError("Zoom credentials not configured")

        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "state": state,
        }

        query = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.OAUTH_URL}?{query}"

    async def exchange_code_for_tokens(self, code: str) -> dict:
        """Exchange authorization code for access and refresh tokens."""
        if not self.is_configured:
            raise ValueError("Zoom credentials not configured")

        # Create Basic auth header
        credentials = f"{self.client_id}:{self.client_secret}"
        auth_header = base64.b64encode(credentials.encode()).decode()

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.TOKEN_URL,
                headers={
                    "Authorization": f"Basic {auth_header}",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": self.redirect_uri,
                },
            )

            if response.status_code != 200:
                logger.error(f"Zoom token exchange failed: {response.text}")
                raise Exception(f"Failed to exchange code: {response.text}")

            return response.json()

    async def refresh_access_token(self, refresh_token: str) -> dict:
        """Refresh an expired access token."""
        if not self.is_configured:
            raise ValueError("Zoom credentials not configured")

        credentials = f"{self.client_id}:{self.client_secret}"
        auth_header = base64.b64encode(credentials.encode()).decode()

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.TOKEN_URL,
                headers={
                    "Authorization": f"Basic {auth_header}",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                },
            )

            if response.status_code != 200:
                logger.error(f"Zoom token refresh failed: {response.text}")
                raise Exception(f"Failed to refresh token: {response.text}")

            return response.json()

    async def get_user_info(self, access_token: str) -> dict:
        """Get the authenticated user's Zoom profile."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.API_URL}/users/me",
                headers={"Authorization": f"Bearer {access_token}"},
            )

            if response.status_code != 200:
                logger.error(f"Zoom get user failed: {response.text}")
                raise Exception(f"Failed to get user: {response.text}")

            return response.json()

    async def create_meeting(
        self,
        access_token: str,
        topic: str,
        start_time: datetime,
        duration_minutes: int,
        timezone: str = "America/New_York",
        agenda: Optional[str] = None,
    ) -> dict:
        """
        Create a Zoom meeting.

        Returns dict with:
            - id: Meeting ID
            - join_url: URL for participants to join
            - start_url: URL for host to start
            - password: Meeting password
        """
        meeting_data = {
            "topic": topic,
            "type": 2,  # Scheduled meeting
            "start_time": start_time.strftime("%Y-%m-%dT%H:%M:%S"),
            "duration": duration_minutes,
            "timezone": timezone,
            "settings": {
                "host_video": True,
                "participant_video": True,
                "join_before_host": False,
                "mute_upon_entry": True,
                "waiting_room": True,
                "auto_recording": "none",
            },
        }

        if agenda:
            meeting_data["agenda"] = agenda

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.API_URL}/users/me/meetings",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                },
                json=meeting_data,
            )

            if response.status_code not in [200, 201]:
                logger.error(f"Zoom create meeting failed: {response.text}")
                raise Exception(f"Failed to create meeting: {response.text}")

            data = response.json()
            return {
                "id": str(data["id"]),
                "join_url": data["join_url"],
                "start_url": data["start_url"],
                "password": data.get("password", ""),
            }

    async def delete_meeting(self, access_token: str, meeting_id: str) -> bool:
        """Delete a Zoom meeting."""
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self.API_URL}/meetings/{meeting_id}",
                headers={"Authorization": f"Bearer {access_token}"},
            )

            if response.status_code == 204:
                return True
            elif response.status_code == 404:
                logger.warning(f"Meeting {meeting_id} not found")
                return True  # Already deleted
            else:
                logger.error(f"Zoom delete meeting failed: {response.text}")
                return False

    async def update_meeting(
        self,
        access_token: str,
        meeting_id: str,
        topic: Optional[str] = None,
        start_time: Optional[datetime] = None,
        duration_minutes: Optional[int] = None,
    ) -> bool:
        """Update an existing Zoom meeting."""
        update_data = {}

        if topic:
            update_data["topic"] = topic
        if start_time:
            update_data["start_time"] = start_time.strftime("%Y-%m-%dT%H:%M:%S")
        if duration_minutes:
            update_data["duration"] = duration_minutes

        if not update_data:
            return True  # Nothing to update

        async with httpx.AsyncClient() as client:
            response = await client.patch(
                f"{self.API_URL}/meetings/{meeting_id}",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                },
                json=update_data,
            )

            if response.status_code == 204:
                return True
            else:
                logger.error(f"Zoom update meeting failed: {response.text}")
                return False


# Singleton instance
zoom_service = ZoomService()
