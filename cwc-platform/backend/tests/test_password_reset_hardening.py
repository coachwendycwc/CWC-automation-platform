"""Password-reset hardening.

Two flaws, same shape as the client-portal ones already fixed:
1. The reset token was stored in plaintext, so read access to the database
   (a backup, a dump, a log) meant you could reset any account's password.
2. The expiry check read `if user.password_reset_expires and ... < utcnow()`,
   so a NULL expiry FAILED OPEN — a token with no expiry never expired.

Plus: no minimum password length anywhere, so a reset could set "a".
"""
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services.auth_service import hash_token, hash_password


async def request_reset(client: AsyncClient, email: str) -> str:
    """Trigger a reset email and return the raw token from the link."""
    with patch(
        "app.routers.auth.email_service.send_password_reset",
        new_callable=AsyncMock,
        return_value=True,
    ) as mock_send:
        response = await client.post("/api/auth/forgot-password", json={"email": email})
        assert response.status_code == 200
        link = mock_send.call_args.kwargs["reset_link"]
    return link.rsplit("/", 1)[-1]


class TestTokenHashedAtRest:
    async def test_reset_token_not_stored_plaintext(
        self, client: AsyncClient, test_user: User, db_session: AsyncSession
    ):
        raw_token = await request_reset(client, test_user.email)
        assert raw_token

        user = (
            await db_session.execute(select(User).where(User.id == test_user.id))
        ).scalar_one()
        await db_session.refresh(user)
        assert user.password_reset_token != raw_token, "token stored in plaintext"
        assert user.password_reset_token == hash_token(raw_token)

    async def test_valid_token_still_resets_password(
        self, client: AsyncClient, test_user: User
    ):
        raw_token = await request_reset(client, test_user.email)
        response = await client.post(
            "/api/auth/reset-password",
            json={"token": raw_token, "password": "BrandNewPass123"},
        )
        assert response.status_code == 200

        login = await client.post(
            "/api/auth/login",
            json={"email": test_user.email, "password": "BrandNewPass123"},
        )
        assert login.status_code == 200


class TestExpiryFailsClosed:
    async def test_null_expiry_is_rejected(
        self, client: AsyncClient, test_user: User, db_session: AsyncSession
    ):
        """A token with no expiry must be treated as expired, not as eternal."""
        raw_token = "no-expiry-token"
        test_user.password_reset_token = hash_token(raw_token)
        test_user.password_reset_expires = None
        await db_session.commit()

        response = await client.post(
            "/api/auth/reset-password",
            json={"token": raw_token, "password": "AttackerPass123"},
        )
        assert response.status_code == 400

    async def test_expired_token_rejected(
        self, client: AsyncClient, test_user: User, db_session: AsyncSession
    ):
        raw_token = "stale-token"
        test_user.password_reset_token = hash_token(raw_token)
        test_user.password_reset_expires = datetime.utcnow() - timedelta(minutes=1)
        await db_session.commit()

        response = await client.post(
            "/api/auth/reset-password",
            json={"token": raw_token, "password": "AnotherPass123"},
        )
        assert response.status_code == 400

    async def test_token_cannot_be_reused(
        self, client: AsyncClient, test_user: User
    ):
        raw_token = await request_reset(client, test_user.email)
        first = await client.post(
            "/api/auth/reset-password",
            json={"token": raw_token, "password": "FirstReset123"},
        )
        assert first.status_code == 200

        second = await client.post(
            "/api/auth/reset-password",
            json={"token": raw_token, "password": "SecondReset123"},
        )
        assert second.status_code == 400


class TestPasswordStrength:
    async def test_short_password_rejected_on_reset(
        self, client: AsyncClient, test_user: User
    ):
        raw_token = await request_reset(client, test_user.email)
        response = await client.post(
            "/api/auth/reset-password",
            json={"token": raw_token, "password": "short"},
        )
        assert response.status_code == 422

    async def test_short_password_rejected_on_register(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        from tests.test_invites import make_invite

        invite = await make_invite(db_session, email="weakpass@example.com")
        response = await client.post(
            "/api/auth/register",
            json={
                "email": "weakpass@example.com",
                "password": "abc",
                "name": "Weak Pass",
                "invite_token": invite.token,
            },
        )
        assert response.status_code == 422


class TestEnumerationStillPrevented:
    async def test_unknown_email_returns_same_message(self, client: AsyncClient):
        with patch(
            "app.routers.auth.email_service.send_password_reset",
            new_callable=AsyncMock,
        ) as mock_send:
            response = await client.post(
                "/api/auth/forgot-password", json={"email": "nobody@example.com"}
            )
        assert response.status_code == 200
        assert "if an account exists" in response.json()["message"].lower()
        mock_send.assert_not_called()
