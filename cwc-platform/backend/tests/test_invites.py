"""Invite-only registration: /register requires a valid invite; admins manage invites."""
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.user_invite import UserInvite


async def make_invite(
    db_session: AsyncSession,
    email: str = "invited@example.com",
    role: str = "user",
    token: str = "test-invite-token",
    expires_delta: timedelta = timedelta(days=7),
    used_at: datetime | None = None,
) -> UserInvite:
    invite = UserInvite(
        email=email,
        role=role,
        token=token,
        invited_by="admin-id",
        expires_at=datetime.utcnow() + expires_delta,
        used_at=used_at,
    )
    db_session.add(invite)
    await db_session.commit()
    await db_session.refresh(invite)
    return invite


class TestRegisterRequiresInvite:
    async def test_register_without_invite_token_rejected(self, client: AsyncClient):
        response = await client.post(
            "/api/auth/register",
            json={"email": "new@example.com", "password": "Pass1234", "name": "New"},
        )
        assert response.status_code == 422

    async def test_register_with_bogus_token_rejected(self, client: AsyncClient):
        response = await client.post(
            "/api/auth/register",
            json={
                "email": "new@example.com",
                "password": "Pass1234",
                "name": "New",
                "invite_token": "no-such-token",
            },
        )
        assert response.status_code == 403
        # No user must be created on a rejected registration
        login = await client.post(
            "/api/auth/login",
            json={"email": "new@example.com", "password": "Pass1234"},
        )
        assert login.status_code == 401

    async def test_register_with_valid_invite_succeeds(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        invite = await make_invite(db_session, email="invited@example.com")
        response = await client.post(
            "/api/auth/register",
            json={
                "email": "invited@example.com",
                "password": "Pass1234",
                "name": "Invited User",
                "invite_token": invite.token,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["user"]["email"] == "invited@example.com"
        assert data["user"]["role"] == "user"

        # Invite is consumed
        await db_session.refresh(invite)
        assert invite.used_at is not None

    async def test_register_with_admin_invite_grants_admin_role(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        invite = await make_invite(
            db_session, email="newadmin@example.com", role="admin", token="admin-tok"
        )
        response = await client.post(
            "/api/auth/register",
            json={
                "email": "newadmin@example.com",
                "password": "Pass1234",
                "name": "New Admin",
                "invite_token": invite.token,
            },
        )
        assert response.status_code == 201
        assert response.json()["user"]["role"] == "admin"

    async def test_register_with_used_invite_rejected(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        invite = await make_invite(
            db_session,
            email="reuse@example.com",
            token="used-tok",
            used_at=datetime.utcnow(),
        )
        response = await client.post(
            "/api/auth/register",
            json={
                "email": "reuse@example.com",
                "password": "Pass1234",
                "name": "Reuse",
                "invite_token": invite.token,
            },
        )
        assert response.status_code == 403

    async def test_register_with_expired_invite_rejected(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        invite = await make_invite(
            db_session,
            email="late@example.com",
            token="expired-tok",
            expires_delta=timedelta(days=-1),
        )
        response = await client.post(
            "/api/auth/register",
            json={
                "email": "late@example.com",
                "password": "Pass1234",
                "name": "Late",
                "invite_token": invite.token,
            },
        )
        assert response.status_code == 403

    async def test_register_with_email_mismatch_rejected(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        invite = await make_invite(
            db_session, email="intended@example.com", token="mismatch-tok"
        )
        response = await client.post(
            "/api/auth/register",
            json={
                "email": "someoneelse@example.com",
                "password": "Pass1234",
                "name": "Wrong Person",
                "invite_token": invite.token,
            },
        )
        assert response.status_code == 403


class TestInviteAdminEndpoints:
    async def test_create_invite_requires_admin(
        self, client: AsyncClient, nonadmin_headers: dict
    ):
        response = await client.post(
            "/api/auth/invites",
            json={"email": "x@example.com", "role": "user"},
            headers=nonadmin_headers,
        )
        assert response.status_code == 403

    async def test_create_invite_requires_auth(self, client: AsyncClient):
        response = await client.post(
            "/api/auth/invites",
            json={"email": "x@example.com", "role": "user"},
        )
        assert response.status_code in (401, 403)

    async def test_admin_creates_invite_and_email_sent(
        self, client: AsyncClient, auth_headers: dict, db_session: AsyncSession
    ):
        with patch(
            "app.routers.auth.email_service.send_user_invite",
            new_callable=AsyncMock,
            return_value=True,
        ) as mock_send:
            response = await client.post(
                "/api/auth/invites",
                json={"email": "fresh@example.com", "role": "user"},
                headers=auth_headers,
            )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "fresh@example.com"
        assert data["role"] == "user"
        assert data["token"]

        mock_send.assert_awaited_once()
        _, kwargs = mock_send.call_args
        sent_args = kwargs if kwargs else dict(
            zip(["to_email", "invite_link", "role"], mock_send.call_args[0])
        )
        assert sent_args["to_email"] == "fresh@example.com"
        assert data["token"] in sent_args["invite_link"]

        result = await db_session.execute(
            select(UserInvite).where(UserInvite.email == "fresh@example.com")
        )
        invite = result.scalar_one()
        assert invite.used_at is None
        assert invite.expires_at > datetime.utcnow()

    async def test_create_invite_rejects_bad_role(
        self, client: AsyncClient, auth_headers: dict
    ):
        response = await client.post(
            "/api/auth/invites",
            json={"email": "x@example.com", "role": "superuser"},
            headers=auth_headers,
        )
        assert response.status_code == 422

    async def test_create_invite_rejects_existing_user_email(
        self, client: AsyncClient, auth_headers: dict, test_user: User
    ):
        response = await client.post(
            "/api/auth/invites",
            json={"email": test_user.email, "role": "user"},
            headers=auth_headers,
        )
        assert response.status_code == 400

    async def test_admin_lists_invites(
        self, client: AsyncClient, auth_headers: dict, db_session: AsyncSession
    ):
        await make_invite(db_session, email="listed@example.com", token="list-tok")
        response = await client.get("/api/auth/invites", headers=auth_headers)
        assert response.status_code == 200
        emails = [i["email"] for i in response.json()]
        assert "listed@example.com" in emails

    async def test_list_invites_requires_admin(
        self, client: AsyncClient, nonadmin_headers: dict
    ):
        response = await client.get("/api/auth/invites", headers=nonadmin_headers)
        assert response.status_code == 403

    async def test_admin_revokes_invite(
        self, client: AsyncClient, auth_headers: dict, db_session: AsyncSession
    ):
        invite = await make_invite(
            db_session, email="revoke@example.com", token="revoke-tok"
        )
        response = await client.delete(
            f"/api/auth/invites/{invite.id}", headers=auth_headers
        )
        assert response.status_code == 204

        # Revoked invite can no longer be used to register
        register = await client.post(
            "/api/auth/register",
            json={
                "email": "revoke@example.com",
                "password": "Pass1234",
                "name": "Revoked",
                "invite_token": "revoke-tok",
            },
        )
        assert register.status_code == 403

    async def test_revoke_invite_requires_admin(
        self, client: AsyncClient, nonadmin_headers: dict, db_session: AsyncSession
    ):
        invite = await make_invite(
            db_session, email="keep@example.com", token="keep-tok"
        )
        response = await client.delete(
            f"/api/auth/invites/{invite.id}", headers=nonadmin_headers
        )
        assert response.status_code == 403
