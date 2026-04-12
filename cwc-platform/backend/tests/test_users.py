"""
Tests for Users endpoints.
"""
import pytest
from httpx import AsyncClient
from io import BytesIO
from unittest.mock import patch

from app.models.user import User

pytestmark = pytest.mark.anyio


class TestGetCurrentUser:
    """Tests for getting current user profile."""

    @pytest.mark.asyncio
    async def test_get_current_user_unauthenticated(self, client: AsyncClient):
        """Test getting current user without authentication."""
        response = await client.get("/api/users/me")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_authenticated(self, auth_client: AsyncClient, test_user: User):
        """Test getting current user when authenticated."""
        response = await auth_client.get("/api/users/me")
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert "id" in data


class TestUpdateCurrentUser:
    """Tests for updating current user profile."""

    async def test_update_user_unauthenticated(self, client: AsyncClient):
        """Test updating user without authentication."""
        response = await client.put(
            "/api/users/me",
            json={"name": "New Name"},
        )
        assert response.status_code == 401

    async def test_update_user_name(self, auth_client: AsyncClient):
        """Test updating user name."""
        response = await auth_client.put(
            "/api/users/me",
            json={"name": "Updated Name"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"

    async def test_update_user_avatar(self, auth_client: AsyncClient):
        """Test updating user avatar URL."""
        response = await auth_client.put(
            "/api/users/me",
            json={"avatar_url": "https://example.com/avatar.png"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["avatar_url"] == "https://example.com/avatar.png"

    async def test_update_user_both_fields(self, auth_client: AsyncClient):
        """Test updating both name and avatar."""
        response = await auth_client.put(
            "/api/users/me",
            json={
                "name": "New Name",
                "avatar_url": "https://example.com/new-avatar.png",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Name"
        assert data["avatar_url"] == "https://example.com/new-avatar.png"

    async def test_update_user_empty_values(self, auth_client: AsyncClient, test_user: User):
        """Test updating with null values doesn't change existing."""
        # First set a name
        await auth_client.put("/api/users/me", json={"name": "Initial Name"})

        # Then update with only avatar
        response = await auth_client.put(
            "/api/users/me",
            json={"avatar_url": "https://example.com/avatar.png"},
        )
        assert response.status_code == 200
        data = response.json()
        # Name should still be set
        assert data["name"] == "Initial Name"
        assert data["avatar_url"] == "https://example.com/avatar.png"

    async def test_upload_user_booking_logo(self, auth_client: AsyncClient):
        """Test uploading a booking logo updates the current user profile."""
        with patch(
            "app.routers.users.cloudinary_service.upload_image",
            return_value={"url": "https://example.com/logo.png"},
        ), patch(
            "app.routers.users.brand_color_service.extract_palette",
            return_value=["#B43A5B", "#F4B400", "#1F3C88"],
        ):
            response = await auth_client.post(
                "/api/users/me/upload-image?target=booking_logo",
                files={"file": ("logo.png", BytesIO(b"fake-image"), "image/png")},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["user"]["booking_page_logo_url"] == "https://example.com/logo.png"
        assert data["suggested_colors"] == ["#B43A5B", "#F4B400", "#1F3C88"]

    async def test_upload_user_avatar_rejects_non_image(self, auth_client: AsyncClient):
        """Test uploading a non-image file fails validation."""
        response = await auth_client.post(
            "/api/users/me/upload-image?target=avatar",
            files={"file": ("notes.txt", BytesIO(b"not-an-image"), "text/plain")},
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "File must be an image"

    async def test_upload_user_booking_banner(self, auth_client: AsyncClient):
        """Test uploading a booking banner updates the current user profile."""
        with patch(
            "app.routers.users.cloudinary_service.upload_image",
            return_value={"url": "https://example.com/banner.png"},
        ):
            response = await auth_client.post(
                "/api/users/me/upload-image?target=booking_banner",
                files={"file": ("banner.png", BytesIO(b"fake-banner"), "image/png")},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["user"]["booking_page_banner_url"] == "https://example.com/banner.png"
        assert data["suggested_colors"] == []
