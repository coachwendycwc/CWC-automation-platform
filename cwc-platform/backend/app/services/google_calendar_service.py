"""
Google Calendar integration service.
Handles OAuth flow and calendar event sync.
"""
import os
import logging
from datetime import datetime, timedelta
from typing import Optional
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

# Google Calendar API scopes
SCOPES = [
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/calendar.readonly",
]


class GoogleCalendarService:
    """Service for Google Calendar integration."""

    def __init__(self):
        self.client_id = os.getenv("GOOGLE_CLIENT_ID")
        self.client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        self.redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8001/api/integrations/google/callback")

        if not self.client_id or not self.client_secret:
            logger.warning("Google Calendar credentials not configured")

    def is_configured(self) -> bool:
        """Check if Google Calendar is configured."""
        return bool(self.client_id and self.client_secret)

    def get_auth_url(self, state: Optional[str] = None) -> str:
        """
        Get the Google OAuth authorization URL.

        Args:
            state: Optional state parameter for CSRF protection

        Returns:
            Authorization URL
        """
        if not self.is_configured():
            raise ValueError("Google Calendar not configured")

        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            },
            scopes=SCOPES,
            redirect_uri=self.redirect_uri,
        )

        auth_url, _ = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            state=state,
            prompt="consent",
        )

        return auth_url

    def exchange_code(self, code: str) -> dict:
        """
        Exchange authorization code for tokens.

        Args:
            code: Authorization code from callback

        Returns:
            Token data including access_token, refresh_token
        """
        if not self.is_configured():
            raise ValueError("Google Calendar not configured")

        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            },
            scopes=SCOPES,
            redirect_uri=self.redirect_uri,
        )

        flow.fetch_token(code=code)
        credentials = flow.credentials

        return {
            "access_token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "token_uri": credentials.token_uri,
            "client_id": credentials.client_id,
            "client_secret": credentials.client_secret,
            "scopes": list(credentials.scopes) if credentials.scopes else SCOPES,
            "expiry": credentials.expiry.isoformat() if credentials.expiry else None,
        }

    def get_credentials(self, token_data: dict) -> Credentials:
        """
        Create Credentials object from stored token data.

        Args:
            token_data: Stored token data

        Returns:
            Credentials object
        """
        credentials = Credentials(
            token=token_data.get("access_token"),
            refresh_token=token_data.get("refresh_token"),
            token_uri=token_data.get("token_uri", "https://oauth2.googleapis.com/token"),
            client_id=token_data.get("client_id") or self.client_id,
            client_secret=token_data.get("client_secret") or self.client_secret,
            scopes=token_data.get("scopes", SCOPES),
        )

        # Refresh if expired
        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())

        return credentials

    def create_event(
        self,
        token_data: dict,
        summary: str,
        start_time: datetime,
        end_time: datetime,
        description: Optional[str] = None,
        location: Optional[str] = None,
        attendees: Optional[list[str]] = None,
        calendar_id: str = "primary",
    ) -> dict:
        """
        Create a calendar event.

        Args:
            token_data: OAuth token data
            summary: Event title
            start_time: Event start time
            end_time: Event end time
            description: Optional event description
            location: Optional event location
            attendees: Optional list of attendee emails
            calendar_id: Calendar ID (default: primary)

        Returns:
            Created event data
        """
        credentials = self.get_credentials(token_data)
        service = build("calendar", "v3", credentials=credentials)

        event = {
            "summary": summary,
            "start": {
                "dateTime": start_time.isoformat(),
                "timeZone": "America/New_York",  # TODO: Make configurable
            },
            "end": {
                "dateTime": end_time.isoformat(),
                "timeZone": "America/New_York",
            },
        }

        if description:
            event["description"] = description

        if location:
            event["location"] = location

        if attendees:
            event["attendees"] = [{"email": email} for email in attendees]

        try:
            result = service.events().insert(
                calendarId=calendar_id,
                body=event,
                sendUpdates="all" if attendees else "none",
            ).execute()

            logger.info(f"Created Google Calendar event: {result.get('id')}")
            return result
        except HttpError as e:
            logger.error(f"Failed to create Google Calendar event: {e}")
            raise

    def update_event(
        self,
        token_data: dict,
        event_id: str,
        summary: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        description: Optional[str] = None,
        location: Optional[str] = None,
        calendar_id: str = "primary",
    ) -> dict:
        """Update an existing calendar event."""
        credentials = self.get_credentials(token_data)
        service = build("calendar", "v3", credentials=credentials)

        # Get existing event
        event = service.events().get(calendarId=calendar_id, eventId=event_id).execute()

        # Update fields
        if summary:
            event["summary"] = summary
        if start_time:
            event["start"] = {
                "dateTime": start_time.isoformat(),
                "timeZone": "America/New_York",
            }
        if end_time:
            event["end"] = {
                "dateTime": end_time.isoformat(),
                "timeZone": "America/New_York",
            }
        if description is not None:
            event["description"] = description
        if location is not None:
            event["location"] = location

        try:
            result = service.events().update(
                calendarId=calendar_id,
                eventId=event_id,
                body=event,
            ).execute()

            logger.info(f"Updated Google Calendar event: {event_id}")
            return result
        except HttpError as e:
            logger.error(f"Failed to update Google Calendar event: {e}")
            raise

    def delete_event(
        self,
        token_data: dict,
        event_id: str,
        calendar_id: str = "primary",
    ) -> bool:
        """Delete a calendar event."""
        credentials = self.get_credentials(token_data)
        service = build("calendar", "v3", credentials=credentials)

        try:
            service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
            logger.info(f"Deleted Google Calendar event: {event_id}")
            return True
        except HttpError as e:
            logger.error(f"Failed to delete Google Calendar event: {e}")
            return False

    def list_events(
        self,
        token_data: dict,
        time_min: Optional[datetime] = None,
        time_max: Optional[datetime] = None,
        max_results: int = 100,
        calendar_id: str = "primary",
    ) -> list[dict]:
        """List calendar events."""
        credentials = self.get_credentials(token_data)
        service = build("calendar", "v3", credentials=credentials)

        if not time_min:
            time_min = datetime.utcnow()
        if not time_max:
            time_max = time_min + timedelta(days=30)

        try:
            result = service.events().list(
                calendarId=calendar_id,
                timeMin=time_min.isoformat() + "Z",
                timeMax=time_max.isoformat() + "Z",
                maxResults=max_results,
                singleEvents=True,
                orderBy="startTime",
            ).execute()

            return result.get("items", [])
        except HttpError as e:
            logger.error(f"Failed to list Google Calendar events: {e}")
            raise


# Singleton instance
google_calendar_service = GoogleCalendarService()
