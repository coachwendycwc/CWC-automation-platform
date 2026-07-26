"""Google OAuth verification must bind the token to OUR client and require a
verified email before it can be used to find or link an account.

Without the audience check any Google access token minted for ANY OAuth client
authenticates here (confused deputy); without email_verified an attacker can
claim an unverified address that matches an existing password account, and
get_or_create_user links the two = account takeover.
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services.auth_service import verify_google_token, get_or_create_user

OUR_CLIENT_ID = "cwc-client-id.apps.googleusercontent.com"
ATTACKER_CLIENT_ID = "attacker-app.apps.googleusercontent.com"


def _response(status_code: int, payload: dict) -> MagicMock:
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = payload
    return response


def _mock_google(tokeninfo: dict, userinfo: dict, tokeninfo_status: int = 200):
    """Patch httpx so tokeninfo and userinfo return canned payloads."""

    async def fake_get(url, *args, **kwargs):
        if "tokeninfo" in url:
            return _response(tokeninfo_status, tokeninfo)
        return _response(200, userinfo)

    client = AsyncMock()
    client.get = AsyncMock(side_effect=fake_get)
    context = MagicMock()
    context.__aenter__ = AsyncMock(return_value=client)
    context.__aexit__ = AsyncMock(return_value=False)
    return patch("app.services.auth_service.httpx.AsyncClient", return_value=context)


@pytest.fixture(autouse=True)
def our_client_id():
    with patch("app.services.auth_service.settings") as mock_settings:
        mock_settings.google_client_id = OUR_CLIENT_ID
        yield mock_settings


class TestAudienceBinding:
    async def test_token_for_another_client_is_rejected(self):
        with _mock_google(
            tokeninfo={
                "aud": ATTACKER_CLIENT_ID,
                "email": "victim@example.com",
                "email_verified": "true",
            },
            userinfo={"id": "g-1", "email": "victim@example.com"},
        ):
            with pytest.raises(HTTPException) as exc:
                await verify_google_token("attacker-token")
        assert exc.value.status_code == 401

    async def test_token_for_our_client_is_accepted(self):
        with _mock_google(
            tokeninfo={
                "aud": OUR_CLIENT_ID,
                "email": "real@example.com",
                "email_verified": "true",
            },
            userinfo={
                "id": "g-2",
                "email": "real@example.com",
                "name": "Real User",
                "verified_email": True,
            },
        ):
            result = await verify_google_token("good-token")
        assert result["email"] == "real@example.com"

    async def test_azp_matching_our_client_is_accepted(self):
        """Google puts the client id in azp for some flows."""
        with _mock_google(
            tokeninfo={
                "azp": OUR_CLIENT_ID,
                "aud": "some-other-audience",
                "email": "real@example.com",
                "email_verified": "true",
            },
            userinfo={"id": "g-3", "email": "real@example.com"},
        ):
            result = await verify_google_token("good-token")
        assert result["email"] == "real@example.com"

    async def test_rejected_when_tokeninfo_call_fails(self):
        with _mock_google(
            tokeninfo={"error": "invalid_token"},
            userinfo={"id": "g-4", "email": "x@example.com"},
            tokeninfo_status=400,
        ):
            with pytest.raises(HTTPException) as exc:
                await verify_google_token("expired-token")
        assert exc.value.status_code == 401


class TestEmailVerifiedRequired:
    async def test_unverified_email_is_rejected(self):
        with _mock_google(
            tokeninfo={
                "aud": OUR_CLIENT_ID,
                "email": "victim@example.com",
                "email_verified": "false",
            },
            userinfo={"id": "g-5", "email": "victim@example.com"},
        ):
            with pytest.raises(HTTPException) as exc:
                await verify_google_token("unverified-token")
        assert exc.value.status_code == 401


class TestAccountLinking:
    async def test_verified_google_identity_links_existing_account(
        self, db_session: AsyncSession
    ):
        db_session.add(
            User(email="existing@example.com", name="Existing", password_hash="x")
        )
        await db_session.commit()

        user = await get_or_create_user(
            db_session,
            {
                "id": "g-100",
                "email": "existing@example.com",
                "email_verified": True,
                "name": "Existing",
            },
        )
        assert user.google_id == "g-100"

    async def test_unverified_identity_never_links_existing_account(
        self, db_session: AsyncSession
    ):
        db_session.add(
            User(email="target@example.com", name="Target", password_hash="x")
        )
        await db_session.commit()

        with pytest.raises(HTTPException) as exc:
            await get_or_create_user(
                db_session,
                {
                    "id": "g-evil",
                    "email": "target@example.com",
                    "email_verified": False,
                    "name": "Attacker",
                },
            )
        assert exc.value.status_code == 401

        existing = (
            await db_session.execute(
                select(User).where(User.email == "target@example.com")
            )
        ).scalar_one()
        assert existing.google_id is None
