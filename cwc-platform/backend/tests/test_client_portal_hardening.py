"""Client-portal session hardening (audit item 4).

Three gaps, all in client_auth_service:
1. Magic-link and session tokens were stored in plaintext — anyone with read
   access to the DB (a backup, a dump, a log) could log in as any client.
2. get_current_client never checked session.expires_at, so a JWT that outlived
   its DB session kept working until the JWT itself expired.
3. verify_token never re-checked portal_enabled, so a disabled contact could
   still redeem a magic link issued before they were disabled.
"""
from datetime import datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.models.client_session import ClientSession
from app.models.contact import Contact
from app.services.client_auth_service import ClientAuthService, hash_token


async def request_link(db: AsyncSession, contact: Contact) -> tuple[ClientAuthService, str]:
    """Request a magic link and return (service, raw token from the email)."""
    from unittest.mock import patch, AsyncMock

    service = ClientAuthService(db)
    with patch.object(
        ClientAuthService, "_send_magic_link_email", new_callable=AsyncMock
    ) as mock_send:
        await service.request_magic_link(contact.email, "http://localhost:3001")
        magic_link = mock_send.call_args.args[1]
    return service, magic_link.rsplit("/", 1)[-1]



class TestTokensHashedAtRest:
    async def test_magic_link_token_not_stored_plaintext(
        self, db_session: AsyncSession, test_contact: Contact
    ):
        service, raw_token = await request_link(db_session, test_contact)
        assert raw_token, "expected a magic link token to be emailed"

        session = (
            await db_session.execute(
                select(ClientSession).where(
                    ClientSession.contact_id == test_contact.id
                )
            )
        ).scalars().first()
        assert session is not None
        assert session.token != raw_token, "token stored in plaintext"
        assert session.token == hash_token(raw_token)

    async def test_valid_token_still_verifies(
        self, db_session: AsyncSession, test_contact: Contact
    ):
        service, raw_token = await request_link(db_session, test_contact)

        result = await service.verify_token(raw_token)
        assert result["session_token"]

    async def test_session_jwt_not_stored_plaintext(
        self, db_session: AsyncSession, test_contact: Contact
    ):
        service, raw_token = await request_link(db_session, test_contact)

        result = await service.verify_token(raw_token)
        session_jwt = result["session_token"]

        session = (
            await db_session.execute(
                select(ClientSession).where(
                    ClientSession.contact_id == test_contact.id
                )
            )
        ).scalars().first()
        assert session.session_token != session_jwt
        assert session.session_token == hash_token(session_jwt)


class TestExpiryEnforced:
    async def test_expired_db_session_rejected(
        self, db_session: AsyncSession, test_contact: Contact
    ):
        service, raw_token = await request_link(db_session, test_contact)

        result = await service.verify_token(raw_token)
        session_jwt = result["session_token"]

        # Session is still valid right now
        contact = await service.get_current_client(session_jwt)
        assert contact.id == test_contact.id

        # Expire the DB session; the JWT itself is still cryptographically valid
        session = (
            await db_session.execute(
                select(ClientSession).where(
                    ClientSession.contact_id == test_contact.id
                )
            )
        ).scalars().first()
        session.expires_at = datetime.utcnow() - timedelta(minutes=1)
        await db_session.commit()

        with pytest.raises(HTTPException) as exc:
            await service.get_current_client(session_jwt)
        assert exc.value.status_code == 401


class TestPortalDisabledEnforced:
    async def test_disabled_contact_cannot_redeem_link(
        self, db_session: AsyncSession, test_contact: Contact
    ):
        service, raw_token = await request_link(db_session, test_contact)

        # Access revoked after the link was sent
        test_contact.portal_enabled = False
        await db_session.commit()

        with pytest.raises(HTTPException) as exc:
            await service.verify_token(raw_token)
        assert exc.value.status_code in (400, 403)

    async def test_disabled_contact_loses_active_session(
        self, db_session: AsyncSession, test_contact: Contact
    ):
        service, raw_token = await request_link(db_session, test_contact)

        session_jwt = (await service.verify_token(raw_token))["session_token"]

        test_contact.portal_enabled = False
        await db_session.commit()

        with pytest.raises(HTTPException) as exc:
            await service.get_current_client(session_jwt)
        assert exc.value.status_code in (401, 403)
