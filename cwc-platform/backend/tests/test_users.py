"""
Tests for Users endpoints.
"""
import pytest
from httpx import AsyncClient

from app.models.user import User


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

    @pytest.mark.asyncio
    async def test_update_user_unauthenticated(self, client: AsyncClient):
        """Test updating user without authentication."""
        response = await client.put(
            "/api/users/me",
            json={"name": "New Name"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_update_user_name(self, auth_client: AsyncClient):
        """Test updating user name."""
        response = await auth_client.put(
            "/api/users/me",
            json={"name": "Updated Name"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"

    @pytest.mark.asyncio
    async def test_update_user_avatar(self, auth_client: AsyncClient):
        """Test updating user avatar URL."""
        response = await auth_client.put(
            "/api/users/me",
            json={"avatar_url": "https://example.com/avatar.png"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["avatar_url"] == "https://example.com/avatar.png"

    @pytest.mark.asyncio
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

    @pytest.mark.asyncio
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
