"""
Tests for Google Calendar and Zoom OAuth integrations.
"""
import pytest
from unittest.mock import patch, Mock, AsyncMock
from datetime import datetime, timedelta
import uuid

from httpx import AsyncClient

from app.models.user import User


class TestIntegrationStatus:
    """Tests for integration status endpoint."""

    @pytest.mark.asyncio
    async def test_get_status_unauthenticated(self, client: AsyncClient):
        """Test status endpoint requires authentication."""
        response = await client.get("/api/integrations/status")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_status_no_integrations(
        self, auth_client: AsyncClient, test_user: User
    ):
        """Test status when no integrations connected."""
        response = await auth_client.get("/api/integrations/status")
        assert response.status_code == 200
        data = response.json()
        assert data["google_calendar"] is False
        assert data["zoom"] is False

    @pytest.mark.asyncio
    async def test_get_status_with_google_calendar(
        self, db_session, auth_client: AsyncClient, test_user: User
    ):
        """Test status when Google Calendar is connected."""
        # Add Google Calendar token to user
        test_user.google_calendar_token = {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
            "expires_at": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
        }
        await db_session.commit()

        response = await auth_client.get("/api/integrations/status")
        assert response.status_code == 200
        data = response.json()
        assert data["google_calendar"] is True
        assert data["zoom"] is False

    @pytest.mark.asyncio
    async def test_get_status_with_zoom(
        self, db_session, auth_client: AsyncClient, test_user: User
    ):
        """Test status when Zoom is connected."""
        test_user.zoom_token = {
            "access_token": "zoom_test_token",
            "refresh_token": "zoom_refresh_token",
        }
        await db_session.commit()

        response = await auth_client.get("/api/integrations/status")
        assert response.status_code == 200
        data = response.json()
        assert data["google_calendar"] is False
        assert data["zoom"] is True


class TestGoogleCalendarIntegration:
    """Tests for Google Calendar OAuth flow."""

    @pytest.mark.asyncio
    async def test_get_auth_url_not_configured(
        self, auth_client: AsyncClient
    ):
        """Test auth URL fails when not configured."""
        with patch("app.routers.integrations.google_calendar_service") as mock_service:
            mock_service.is_configured.return_value = False

            response = await auth_client.get("/api/integrations/google/auth-url")
            assert response.status_code == 503
            assert "not configured" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_auth_url_success(
        self, auth_client: AsyncClient
    ):
        """Test getting Google OAuth URL."""
        with patch("app.routers.integrations.google_calendar_service") as mock_service:
            mock_service.is_configured.return_value = True
            mock_service.get_auth_url.return_value = "https://accounts.google.com/oauth/authorize?..."

            response = await auth_client.get("/api/integrations/google/auth-url")
            assert response.status_code == 200
            data = response.json()
            assert "auth_url" in data
            assert "google.com" in data["auth_url"]

    @pytest.mark.asyncio
    async def test_google_callback_invalid_state(
        self, client: AsyncClient
    ):
        """Test callback with invalid state parameter."""
        response = await client.get(
            "/api/integrations/google/callback",
            params={"code": "test_code", "state": "invalid_state"}
        )
        assert response.status_code == 400
        assert "state" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_google_callback_user_not_found(
        self, db_session, client: AsyncClient
    ):
        """Test callback when user not found."""
        from app.routers.integrations import oauth_states

        # Set up state for non-existent user
        state = "test_state_123"
        oauth_states[state] = str(uuid.uuid4())  # Non-existent user ID

        response = await client.get(
            "/api/integrations/google/callback",
            params={"code": "test_code", "state": state}
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_google_callback_success(
        self, db_session, client: AsyncClient, test_user: User
    ):
        """Test successful Google OAuth callback."""
        from app.routers.integrations import oauth_states

        state = "valid_state_456"
        oauth_states[state] = str(test_user.id)

        with patch("app.routers.integrations.google_calendar_service") as mock_service:
            mock_service.exchange_code.return_value = {
                "access_token": "new_access_token",
                "refresh_token": "new_refresh_token",
                "expires_at": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
            }

            response = await client.get(
                "/api/integrations/google/callback",
                params={"code": "valid_code", "state": state},
                follow_redirects=False
            )
            # Should redirect to settings
            assert response.status_code == 307
            assert "google_connected=true" in response.headers["location"]

    @pytest.mark.asyncio
    async def test_disconnect_google(
        self, db_session, auth_client: AsyncClient, test_user: User
    ):
        """Test disconnecting Google Calendar."""
        # First connect
        test_user.google_calendar_token = {"access_token": "test"}
        await db_session.commit()

        response = await auth_client.delete("/api/integrations/google/disconnect")
        assert response.status_code == 200
        assert "disconnected" in response.json()["message"].lower()

        # Verify token is removed
        await db_session.refresh(test_user)
        assert test_user.google_calendar_token is None

    @pytest.mark.asyncio
    async def test_list_events_not_connected(
        self, auth_client: AsyncClient
    ):
        """Test listing events when not connected."""
        response = await auth_client.get("/api/integrations/google/events")
        assert response.status_code == 400
        assert "not connected" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_list_events_success(
        self, db_session, auth_client: AsyncClient, test_user: User
    ):
        """Test listing Google Calendar events."""
        test_user.google_calendar_token = {"access_token": "test_token"}
        await db_session.commit()

        with patch("app.routers.integrations.google_calendar_service") as mock_service:
            mock_service.list_events.return_value = [
                {
                    "id": "event1",
                    "summary": "Meeting 1",
                    "start": {"dateTime": "2024-01-20T10:00:00Z"},
                    "end": {"dateTime": "2024-01-20T11:00:00Z"},
                },
                {
                    "id": "event2",
                    "summary": "Meeting 2",
                    "start": {"dateTime": "2024-01-21T14:00:00Z"},
                    "end": {"dateTime": "2024-01-21T15:00:00Z"},
                },
            ]

            response = await auth_client.get("/api/integrations/google/events")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data[0]["summary"] == "Meeting 1"

    @pytest.mark.asyncio
    async def test_create_event_not_connected(
        self, auth_client: AsyncClient
    ):
        """Test creating event when not connected."""
        response = await auth_client.post(
            "/api/integrations/google/events",
            json={
                "summary": "Test Event",
                "start_time": "2024-01-25T10:00:00Z",
                "end_time": "2024-01-25T11:00:00Z",
            }
        )
        assert response.status_code == 400
        assert "not connected" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_create_event_success(
        self, db_session, auth_client: AsyncClient, test_user: User
    ):
        """Test creating a Google Calendar event."""
        test_user.google_calendar_token = {"access_token": "test_token"}
        await db_session.commit()

        with patch("app.routers.integrations.google_calendar_service") as mock_service:
            mock_service.create_event.return_value = {
                "id": "new_event_123",
                "htmlLink": "https://calendar.google.com/event?id=new_event_123",
            }

            response = await auth_client.post(
                "/api/integrations/google/events",
                json={
                    "summary": "Coaching Session",
                    "start_time": "2024-01-25T10:00:00Z",
                    "end_time": "2024-01-25T11:00:00Z",
                    "description": "Weekly coaching session",
                    "attendees": ["client@example.com"],
                }
            )
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == "new_event_123"

    @pytest.mark.asyncio
    async def test_delete_event_success(
        self, db_session, auth_client: AsyncClient, test_user: User
    ):
        """Test deleting a Google Calendar event."""
        test_user.google_calendar_token = {"access_token": "test_token"}
        await db_session.commit()

        with patch("app.routers.integrations.google_calendar_service") as mock_service:
            mock_service.delete_event.return_value = True

            response = await auth_client.delete(
                "/api/integrations/google/events/event_to_delete"
            )
            assert response.status_code == 200
            assert "deleted" in response.json()["message"].lower()


class TestZoomIntegration:
    """Tests for Zoom OAuth flow."""

    @pytest.mark.asyncio
    async def test_get_zoom_auth_url_not_configured(
        self, auth_client: AsyncClient
    ):
        """Test Zoom auth URL fails when not configured."""
        with patch("app.routers.integrations.zoom_service") as mock_service:
            mock_service.is_configured = False

            response = await auth_client.get("/api/integrations/zoom/auth-url")
            assert response.status_code == 503
            assert "not configured" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_zoom_auth_url_success(
        self, auth_client: AsyncClient
    ):
        """Test getting Zoom OAuth URL."""
        with patch("app.routers.integrations.zoom_service") as mock_service:
            mock_service.is_configured = True
            mock_service.get_authorization_url.return_value = "https://zoom.us/oauth/authorize?..."

            response = await auth_client.get("/api/integrations/zoom/auth-url")
            assert response.status_code == 200
            data = response.json()
            assert "auth_url" in data
            assert "zoom.us" in data["auth_url"]

    @pytest.mark.asyncio
    async def test_zoom_callback_invalid_state(
        self, client: AsyncClient
    ):
        """Test Zoom callback with invalid state."""
        response = await client.get(
            "/api/integrations/zoom/callback",
            params={"code": "test_code", "state": "invalid_state"}
        )
        assert response.status_code == 400
        assert "state" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_zoom_callback_wrong_prefix(
        self, client: AsyncClient
    ):
        """Test Zoom callback with non-zoom state prefix."""
        from app.routers.integrations import oauth_states

        state = "wrong_prefix_state"
        oauth_states[state] = "google:user123"  # Wrong prefix

        response = await client.get(
            "/api/integrations/zoom/callback",
            params={"code": "test_code", "state": state}
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_zoom_callback_success(
        self, db_session, client: AsyncClient, test_user: User
    ):
        """Test successful Zoom OAuth callback."""
        from app.routers.integrations import oauth_states

        state = "zoom_valid_state"
        oauth_states[state] = f"zoom:{test_user.id}"

        with patch("app.routers.integrations.zoom_service") as mock_service:
            mock_service.exchange_code_for_tokens = AsyncMock(return_value={
                "access_token": "zoom_access_token",
                "refresh_token": "zoom_refresh_token",
            })

            response = await client.get(
                "/api/integrations/zoom/callback",
                params={"code": "valid_code", "state": state},
                follow_redirects=False
            )
            assert response.status_code == 307
            assert "zoom_connected=true" in response.headers["location"]

    @pytest.mark.asyncio
    async def test_disconnect_zoom(
        self, db_session, auth_client: AsyncClient, test_user: User
    ):
        """Test disconnecting Zoom."""
        test_user.zoom_token = {"access_token": "zoom_test"}
        await db_session.commit()

        response = await auth_client.delete("/api/integrations/zoom/disconnect")
        assert response.status_code == 200
        assert "disconnected" in response.json()["message"].lower()

        await db_session.refresh(test_user)
        assert test_user.zoom_token is None

    @pytest.mark.asyncio
    async def test_get_zoom_user_not_connected(
        self, auth_client: AsyncClient
    ):
        """Test getting Zoom user when not connected."""
        response = await auth_client.get("/api/integrations/zoom/user")
        assert response.status_code == 400
        assert "not connected" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_zoom_user_success(
        self, db_session, auth_client: AsyncClient, test_user: User
    ):
        """Test getting Zoom user info."""
        test_user.zoom_token = {"access_token": "zoom_token"}
        await db_session.commit()

        with patch("app.routers.integrations.zoom_service") as mock_service:
            mock_service.get_user_info = AsyncMock(return_value={
                "id": "zoom_user_123",
                "email": "user@example.com",
                "first_name": "Test",
                "last_name": "User",
            })

            response = await auth_client.get("/api/integrations/zoom/user")
            assert response.status_code == 200
            data = response.json()
            assert data["email"] == "user@example.com"

    @pytest.mark.asyncio
    async def test_get_zoom_user_invalid_token(
        self, db_session, auth_client: AsyncClient, test_user: User
    ):
        """Test getting Zoom user with invalid token."""
        test_user.zoom_token = {}  # Missing access_token
        await db_session.commit()

        response = await auth_client.get("/api/integrations/zoom/user")
        assert response.status_code == 400
        assert "token" in response.json()["detail"].lower()


class TestOAuthStateManagement:
    """Tests for OAuth state storage and verification."""

    def test_state_is_removed_after_use(self):
        """Test OAuth state is removed after being used."""
        from app.routers.integrations import oauth_states

        state = "test_state_to_remove"
        oauth_states[state] = "user_123"

        # Simulate state being consumed
        consumed = oauth_states.pop(state, None)
        assert consumed == "user_123"
        assert state not in oauth_states

    def test_state_not_found_returns_none(self):
        """Test missing state returns None."""
        from app.routers.integrations import oauth_states

        result = oauth_states.pop("nonexistent_state", None)
        assert result is None
