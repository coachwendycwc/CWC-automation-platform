"""
Tests for Client Portal Authentication (Magic Link).
"""
import pytest
from unittest.mock import patch, Mock, AsyncMock
from datetime import datetime, timedelta
import uuid
import secrets

from httpx import AsyncClient
from jose import jwt

from app.models.contact import Contact
from app.models.client_session import ClientSession
from app.config import get_settings

settings = get_settings()


class TestRequestMagicLink:
    """Tests for magic link request endpoint."""

    @pytest.mark.asyncio
    async def test_request_magic_link_unknown_email(self, client: AsyncClient):
        """Test magic link request for unknown email returns generic message."""
        with patch("app.services.client_auth_service.email_service") as mock_email:
            response = await client.post(
                "/api/client/auth/request-login",
                json={"email": "nonexistent@example.com"}
            )
            assert response.status_code == 200
            data = response.json()
            # Should return generic message for security
            assert "if an account exists" in data["message"].lower()
            # Should NOT send email
            mock_email._send_email.assert_not_called()

    @pytest.mark.asyncio
    async def test_request_magic_link_portal_disabled(
        self, db_session, client: AsyncClient, test_organization
    ):
        """Test magic link request fails for disabled portal."""
        # Create contact with portal disabled
        contact = Contact(
            id=str(uuid.uuid4()),
            first_name="Disabled",
            last_name="User",
            email="disabled@example.com",
            organization_id=test_organization.id,
            contact_type="client",
            portal_enabled=False,
        )
        db_session.add(contact)
        await db_session.commit()

        with patch("app.services.client_auth_service.email_service") as mock_email:
            response = await client.post(
                "/api/client/auth/request-login",
                json={"email": "disabled@example.com"}
            )
            assert response.status_code == 200
            # Generic message for security
            assert "if an account exists" in response.json()["message"].lower()
            mock_email._send_email.assert_not_called()

    @pytest.mark.asyncio
    async def test_request_magic_link_success(
        self, db_session, client: AsyncClient, test_organization
    ):
        """Test successful magic link request."""
        # Create contact with portal enabled
        contact = Contact(
            id=str(uuid.uuid4()),
            first_name="Portal",
            last_name="User",
            email="portal@example.com",
            organization_id=test_organization.id,
            contact_type="client",
            portal_enabled=True,
        )
        db_session.add(contact)
        await db_session.commit()

        with patch("app.services.client_auth_service.email_service") as mock_email:
            mock_email._send_email = AsyncMock(return_value=True)

            response = await client.post(
                "/api/client/auth/request-login",
                json={"email": "portal@example.com"}
            )
            assert response.status_code == 200
            assert "if an account exists" in response.json()["message"].lower()
            # Should send email
            mock_email._send_email.assert_called_once()

    @pytest.mark.asyncio
    async def test_request_magic_link_rate_limited(
        self, db_session, client: AsyncClient, test_organization
    ):
        """Test magic link rate limiting."""
        contact = Contact(
            id=str(uuid.uuid4()),
            first_name="Rate",
            last_name="Limited",
            email="ratelimited@example.com",
            organization_id=test_organization.id,
            contact_type="client",
            portal_enabled=True,
        )
        db_session.add(contact)
        await db_session.commit()

        # Create 3 recent sessions (max per hour)
        for i in range(3):
            session = ClientSession(
                id=str(uuid.uuid4()),
                contact_id=contact.id,
                token=secrets.token_urlsafe(32),
                expires_at=datetime.utcnow() + timedelta(minutes=15),
                email_sent_at=datetime.utcnow() - timedelta(minutes=i * 10),
            )
            db_session.add(session)
        await db_session.commit()

        with patch("app.services.client_auth_service.email_service"):
            response = await client.post(
                "/api/client/auth/request-login",
                json={"email": "ratelimited@example.com"}
            )
            assert response.status_code == 429
            assert "too many" in response.json()["detail"].lower()


class TestVerifyToken:
    """Tests for magic link token verification."""

    @pytest.mark.asyncio
    async def test_verify_token_invalid(self, client: AsyncClient):
        """Test verification with invalid token."""
        response = await client.post(
            "/api/client/auth/verify-token",
            json={"token": "invalid-token-123"}
        )
        assert response.status_code == 400
        assert "invalid" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_verify_token_expired(
        self, db_session, client: AsyncClient, test_organization
    ):
        """Test verification with expired token."""
        contact = Contact(
            id=str(uuid.uuid4()),
            first_name="Expired",
            last_name="Token",
            email="expired@example.com",
            organization_id=test_organization.id,
            contact_type="client",
            portal_enabled=True,
        )
        db_session.add(contact)
        await db_session.flush()

        # Create expired session
        token = secrets.token_urlsafe(32)
        session = ClientSession(
            id=str(uuid.uuid4()),
            contact_id=contact.id,
            token=token,
            expires_at=datetime.utcnow() - timedelta(hours=1),  # Expired
            is_active=True,
        )
        db_session.add(session)
        await db_session.commit()

        response = await client.post(
            "/api/client/auth/verify-token",
            json={"token": token}
        )
        assert response.status_code == 400
        assert "expired" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_verify_token_already_used(
        self, db_session, client: AsyncClient, test_organization
    ):
        """Test verification with already used token."""
        contact = Contact(
            id=str(uuid.uuid4()),
            first_name="Used",
            last_name="Token",
            email="used@example.com",
            organization_id=test_organization.id,
            contact_type="client",
            portal_enabled=True,
        )
        db_session.add(contact)
        await db_session.flush()

        # Create already-used session
        token = secrets.token_urlsafe(32)
        session = ClientSession(
            id=str(uuid.uuid4()),
            contact_id=contact.id,
            token=token,
            expires_at=datetime.utcnow() + timedelta(minutes=15),
            token_used_at=datetime.utcnow() - timedelta(minutes=5),  # Already used
            is_active=True,
        )
        db_session.add(session)
        await db_session.commit()

        response = await client.post(
            "/api/client/auth/verify-token",
            json={"token": token}
        )
        assert response.status_code == 400
        assert "already been used" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_verify_token_success(
        self, db_session, client: AsyncClient, test_organization
    ):
        """Test successful token verification."""
        contact = Contact(
            id=str(uuid.uuid4()),
            first_name="Valid",
            last_name="User",
            email="valid@example.com",
            organization_id=test_organization.id,
            contact_type="client",
            portal_enabled=True,
        )
        db_session.add(contact)
        await db_session.flush()

        # Create valid session
        token = secrets.token_urlsafe(32)
        session = ClientSession(
            id=str(uuid.uuid4()),
            contact_id=contact.id,
            token=token,
            expires_at=datetime.utcnow() + timedelta(minutes=15),
            is_active=True,
        )
        db_session.add(session)
        await db_session.commit()

        response = await client.post(
            "/api/client/auth/verify-token",
            json={"token": token}
        )
        assert response.status_code == 200
        data = response.json()
        assert "session_token" in data
        assert data["contact"]["email"] == "valid@example.com"
        assert data["contact"]["first_name"] == "Valid"


class TestGetCurrentClient:
    """Tests for getting current client info."""

    @pytest.mark.asyncio
    async def test_get_me_no_auth(self, client: AsyncClient):
        """Test /me without authorization header."""
        response = await client.get("/api/client/auth/me")
        assert response.status_code == 422  # Missing required header

    @pytest.mark.asyncio
    async def test_get_me_invalid_token(self, client: AsyncClient):
        """Test /me with invalid JWT."""
        response = await client.get(
            "/api/client/auth/me",
            headers={"Authorization": "Bearer invalid-jwt-token"}
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_me_wrong_token_type(
        self, db_session, client: AsyncClient, test_organization
    ):
        """Test /me with non-client token type."""
        # Create a token with wrong type
        token = jwt.encode(
            {
                "sub": "some-user-id",
                "type": "admin",  # Wrong type
                "exp": datetime.utcnow() + timedelta(days=1),
            },
            settings.secret_key,
            algorithm="HS256",
        )

        response = await client.get(
            "/api/client/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 401
        assert "session type" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_me_expired_session(
        self, db_session, client: AsyncClient, test_organization
    ):
        """Test /me with expired session."""
        contact = Contact(
            id=str(uuid.uuid4()),
            first_name="Session",
            last_name="Expired",
            email="session_expired@example.com",
            organization_id=test_organization.id,
            contact_type="client",
            portal_enabled=True,
        )
        db_session.add(contact)
        await db_session.flush()

        session_id = str(uuid.uuid4())
        session = ClientSession(
            id=session_id,
            contact_id=contact.id,
            token="original-token",
            expires_at=datetime.utcnow() - timedelta(days=1),
            is_active=False,  # Inactive session
        )
        db_session.add(session)
        await db_session.commit()

        # Create valid JWT but for inactive session
        token = jwt.encode(
            {
                "sub": contact.id,
                "session_id": session_id,
                "type": "client",
                "exp": datetime.utcnow() + timedelta(days=1),
            },
            settings.secret_key,
            algorithm="HS256",
        )

        response = await client.get(
            "/api/client/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 401
        assert "expired" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_me_success(
        self, db_session, client: AsyncClient, test_organization
    ):
        """Test successful /me request."""
        contact = Contact(
            id=str(uuid.uuid4()),
            first_name="Current",
            last_name="Client",
            email="current@example.com",
            organization_id=test_organization.id,
            contact_type="client",
            portal_enabled=True,
            is_org_admin=True,
        )
        db_session.add(contact)
        await db_session.flush()

        session_id = str(uuid.uuid4())
        session = ClientSession(
            id=session_id,
            contact_id=contact.id,
            token="valid-token",
            expires_at=datetime.utcnow() + timedelta(days=7),
            is_active=True,
        )
        db_session.add(session)
        await db_session.commit()

        # Create valid JWT
        token = jwt.encode(
            {
                "sub": contact.id,
                "session_id": session_id,
                "type": "client",
                "exp": datetime.utcnow() + timedelta(days=7),
            },
            settings.secret_key,
            algorithm="HS256",
        )

        response = await client.get(
            "/api/client/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "current@example.com"
        assert data["first_name"] == "Current"
        assert data["is_org_admin"] is True


class TestLogout:
    """Tests for client logout."""

    @pytest.mark.asyncio
    async def test_logout_success(
        self, db_session, client: AsyncClient, test_organization
    ):
        """Test successful logout."""
        contact = Contact(
            id=str(uuid.uuid4()),
            first_name="Logout",
            last_name="User",
            email="logout@example.com",
            organization_id=test_organization.id,
            contact_type="client",
            portal_enabled=True,
        )
        db_session.add(contact)
        await db_session.flush()

        session_id = str(uuid.uuid4())
        session = ClientSession(
            id=session_id,
            contact_id=contact.id,
            token="logout-token",
            expires_at=datetime.utcnow() + timedelta(days=7),
            is_active=True,
        )
        db_session.add(session)
        await db_session.commit()

        token = jwt.encode(
            {
                "sub": contact.id,
                "session_id": session_id,
                "type": "client",
                "exp": datetime.utcnow() + timedelta(days=7),
            },
            settings.secret_key,
            algorithm="HS256",
        )

        response = await client.post(
            "/api/client/auth/logout",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert "logged out" in response.json()["message"].lower()

        # Verify session is now inactive
        await db_session.refresh(session)
        assert session.is_active is False

    @pytest.mark.asyncio
    async def test_logout_invalid_token(self, client: AsyncClient):
        """Test logout with invalid token still succeeds."""
        response = await client.post(
            "/api/client/auth/logout",
            headers={"Authorization": "Bearer invalid-token"}
        )
        # Should still return success (graceful handling)
        assert response.status_code == 200


class TestClientAuthService:
    """Unit tests for ClientAuthService."""

    @pytest.mark.asyncio
    async def test_rate_limit_check_under_limit(
        self, db_session, test_contact: Contact
    ):
        """Test rate limit check when under limit."""
        from app.services.client_auth_service import ClientAuthService

        # Enable portal for test contact
        test_contact.portal_enabled = True
        await db_session.commit()

        service = ClientAuthService(db_session)
        result = await service._check_rate_limit(test_contact.id)
        assert result is True

    @pytest.mark.asyncio
    async def test_rate_limit_check_at_limit(
        self, db_session, test_contact: Contact
    ):
        """Test rate limit check when at limit."""
        from app.services.client_auth_service import ClientAuthService, MAX_MAGIC_LINKS_PER_HOUR

        # Create sessions up to the limit
        for i in range(MAX_MAGIC_LINKS_PER_HOUR):
            session = ClientSession(
                id=str(uuid.uuid4()),
                contact_id=test_contact.id,
                token=secrets.token_urlsafe(32),
                expires_at=datetime.utcnow() + timedelta(minutes=15),
                email_sent_at=datetime.utcnow() - timedelta(minutes=i * 5),
            )
            db_session.add(session)
        await db_session.commit()

        service = ClientAuthService(db_session)
        result = await service._check_rate_limit(test_contact.id)
        assert result is False

    @pytest.mark.asyncio
    async def test_send_magic_link_email_no_email(
        self, db_session, test_contact: Contact
    ):
        """Test email not sent when contact has no email."""
        from app.services.client_auth_service import ClientAuthService

        test_contact.email = None
        await db_session.commit()

        service = ClientAuthService(db_session)
        result = await service._send_magic_link_email(test_contact, "http://test.com/link")
        assert result is False
