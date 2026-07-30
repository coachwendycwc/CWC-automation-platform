"""A Stripe checkout must credit an invoice exactly once.

Stripe retries webhooks on any non-2xx or timeout, and checkout.session.completed
and payment_intent.succeeded both fire for the same purchase. Without a guard the
customer's invoice is credited twice and the books are wrong.
"""
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.invoice import Invoice
from app.models.payment import Payment
from app.routers.stripe import handle_checkout_completed, handle_payment_succeeded


def checkout_session(invoice_id: str, session_id="cs_test_1", intent="pi_test_1"):
    return {
        "id": session_id,
        "payment_intent": intent,
        "amount_total": 15000,  # $150.00 in cents
        "metadata": {"invoice_id": invoice_id},
    }


async def payments_for(db: AsyncSession, invoice_id: str) -> list[Payment]:
    result = await db.execute(
        select(Payment).where(Payment.invoice_id == invoice_id)
    )
    return list(result.scalars().all())


class TestCheckoutIdempotency:
    async def test_replayed_checkout_event_credits_once(
        self, db_session: AsyncSession, test_invoice_for_payment: Invoice
    ):
        invoice = test_invoice_for_payment
        starting_paid = invoice.amount_paid
        session = checkout_session(invoice.id)

        await handle_checkout_completed(db_session, session)
        await handle_checkout_completed(db_session, session)  # Stripe retry

        payments = await payments_for(db_session, invoice.id)
        assert len(payments) == 1
        await db_session.refresh(invoice)
        assert invoice.amount_paid == starting_paid + Decimal("150.00")

    async def test_checkout_then_payment_intent_credits_once(
        self, db_session: AsyncSession, test_invoice_for_payment: Invoice
    ):
        invoice = test_invoice_for_payment
        starting_paid = invoice.amount_paid
        session = checkout_session(invoice.id)

        await handle_checkout_completed(db_session, session)
        await handle_payment_succeeded(
            db_session,
            {"id": "pi_test_1", "amount": 15000, "metadata": {"invoice_id": invoice.id}},
        )

        payments = await payments_for(db_session, invoice.id)
        assert len(payments) == 1
        await db_session.refresh(invoice)
        assert invoice.amount_paid == starting_paid + Decimal("150.00")

    async def test_distinct_sessions_each_credit(
        self, db_session: AsyncSession, test_invoice_for_payment: Invoice
    ):
        """Guard must key on the session, not block all later payments."""
        invoice = test_invoice_for_payment
        await handle_checkout_completed(
            db_session, checkout_session(invoice.id, "cs_a", "pi_a")
        )
        await handle_checkout_completed(
            db_session, checkout_session(invoice.id, "cs_b", "pi_b")
        )

        payments = await payments_for(db_session, invoice.id)
        assert len(payments) == 2
