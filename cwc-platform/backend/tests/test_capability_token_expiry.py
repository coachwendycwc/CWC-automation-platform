"""Capability tokens must not be valid forever.

An invoice pay-link or a testimonial recording link is a bearer credential
sitting in an email inbox indefinitely. Anyone who later gains access to that
mailbox — a shared laptop, a forwarded thread, a breached account — can still
open it years later. Expiry bounds that window.

Windows are deliberately generous: a client may open an emailed link weeks
after it was sent, and an expired link that should have worked is a support
call. Legacy rows created before this change are backfilled rather than
invalidated.
"""
from datetime import datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.invoice import Invoice
from app.models.testimonial import Testimonial


class TestInvoiceViewTokenExpiry:
    async def test_valid_token_opens_invoice(
        self, client: AsyncClient, test_invoice: Invoice, db_session: AsyncSession
    ):
        test_invoice.view_token_expires_at = datetime.utcnow() + timedelta(days=30)
        await db_session.commit()

        response = await client.get(f"/api/invoice/{test_invoice.view_token}")
        assert response.status_code == 200

    async def test_expired_token_rejected(
        self, client: AsyncClient, test_invoice: Invoice, db_session: AsyncSession
    ):
        test_invoice.view_token_expires_at = datetime.utcnow() - timedelta(days=1)
        await db_session.commit()

        response = await client.get(f"/api/invoice/{test_invoice.view_token}")
        assert response.status_code in (403, 404, 410)

    async def test_legacy_row_without_expiry_still_works(
        self, client: AsyncClient, test_invoice: Invoice, db_session: AsyncSession
    ):
        """Rows created before this change must not break for existing clients."""
        test_invoice.view_token_expires_at = None
        await db_session.commit()

        response = await client.get(f"/api/invoice/{test_invoice.view_token}")
        assert response.status_code == 200


class TestTestimonialRequestTokenExpiry:
    async def test_valid_token_opens_request(
        self,
        client: AsyncClient,
        test_testimonial: Testimonial,
        db_session: AsyncSession,
    ):
        test_testimonial.request_token_expires_at = datetime.utcnow() + timedelta(
            days=30
        )
        await db_session.commit()

        response = await client.get(
            f"/api/testimonial/{test_testimonial.request_token}"
        )
        assert response.status_code == 200

    async def test_expired_token_rejected(
        self,
        client: AsyncClient,
        test_testimonial: Testimonial,
        db_session: AsyncSession,
    ):
        test_testimonial.request_token_expires_at = datetime.utcnow() - timedelta(
            days=1
        )
        await db_session.commit()

        response = await client.get(
            f"/api/testimonial/{test_testimonial.request_token}"
        )
        assert response.status_code in (403, 404, 410)

    async def test_expired_token_blocks_submission(
        self,
        client: AsyncClient,
        test_testimonial: Testimonial,
        db_session: AsyncSession,
    ):
        test_testimonial.request_token_expires_at = datetime.utcnow() - timedelta(
            days=1
        )
        await db_session.commit()

        response = await client.post(
            f"/api/testimonial/{test_testimonial.request_token}",
            json={
                "author_name": "Late Submitter",
                "quote": "Trying to submit after the link expired",
                "permission_granted": True,
            },
        )
        assert response.status_code in (403, 404, 410)

    async def test_legacy_row_without_expiry_still_works(
        self,
        client: AsyncClient,
        test_testimonial: Testimonial,
        db_session: AsyncSession,
    ):
        test_testimonial.request_token_expires_at = None
        await db_session.commit()

        response = await client.get(
            f"/api/testimonial/{test_testimonial.request_token}"
        )
        assert response.status_code == 200


class TestNewRecordsGetExpiry:
    async def test_new_testimonial_request_has_expiry(
        self, client: AsyncClient, auth_headers: dict, test_contact
    ):
        response = await client.post(
            "/api/testimonials",
            json={"contact_id": test_contact.id, "author_name": "New Client"},
            headers=auth_headers,
        )
        assert response.status_code in (200, 201)
        # The model default supplies the window; surfaced so admins can see it
        assert response.json().get("request_token_expires_at") is not None
