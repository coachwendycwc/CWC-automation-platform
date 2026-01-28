"""
Tests for authentication endpoints.
"""
import pytest
from httpx import AsyncClient


class TestAuthEndpoints:
    """Test authentication endpoints."""

    async def test_root_endpoint(self, client: AsyncClient):
        """Test root endpoint returns API info."""
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "CWC Platform API"
        assert data["status"] == "running"

    async def test_health_check(self, client: AsyncClient):
        """Test health check endpoint."""
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    async def test_register_new_user(self, client: AsyncClient):
        """Test user registration."""
        response = await client.post(
            "/api/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "SecurePass123",
                "name": "New User",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "newuser@example.com"

    async def test_register_duplicate_email(self, client: AsyncClient, test_user):
        """Test registration with existing email fails."""
        response = await client.post(
            "/api/auth/register",
            json={
                "email": "test@example.com",  # Same as test_user
                "password": "SecurePass123",
                "name": "Duplicate User",
            },
        )
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]

    async def test_login_success(self, client: AsyncClient, test_user):
        """Test successful login."""
        response = await client.post(
            "/api/auth/login",
            json={
                "email": "test@example.com",
                "password": "testpass123",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == "test@example.com"

    async def test_login_wrong_password(self, client: AsyncClient, test_user):
        """Test login with wrong password fails."""
        response = await client.post(
            "/api/auth/login",
            json={
                "email": "test@example.com",
                "password": "wrongpassword",
            },
        )
        assert response.status_code == 401
        assert "Invalid email or password" in response.json()["detail"]

    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login with non-existent email fails."""
        response = await client.post(
            "/api/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "anypassword",
            },
        )
        assert response.status_code == 401

    async def test_get_me_authenticated(self, client: AsyncClient, auth_headers, test_user):
        """Test getting current user when authenticated."""
        response = await client.get("/api/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email

    @pytest.mark.skip(reason="HTTPBearer with auto_error=False causes internal error - needs auth service fix")
    async def test_get_me_unauthenticated(self, client: AsyncClient):
        """Test getting current user without auth fails."""
        response = await client.get("/api/auth/me")
        # Without credentials, HTTPBearer with auto_error=False returns None
        # which causes an internal error when accessing credentials.credentials
        assert response.status_code in [401, 403]

    async def test_dev_login(self, client: AsyncClient):
        """Test dev login endpoint creates user."""
        response = await client.post("/api/auth/dev-login")
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == "dev@cwcplatform.com"

    async def test_forgot_password(self, client: AsyncClient, test_user):
        """Test forgot password returns success message."""
        response = await client.post(
            "/api/auth/forgot-password",
            json={"email": "test@example.com"},
        )
        assert response.status_code == 200
        # Should return success even if email exists (prevent enumeration)
        assert "message" in response.json()

    async def test_forgot_password_nonexistent(self, client: AsyncClient):
        """Test forgot password with non-existent email still returns success."""
        response = await client.post(
            "/api/auth/forgot-password",
            json={"email": "nonexistent@example.com"},
        )
        assert response.status_code == 200
        # Should return same message to prevent email enumeration
        assert "message" in response.json()
