"""Importer v2: historical invoices (+ recorded payments) from a CSV export.

Imported invoices exist so revenue history and aging reports are complete after
a migration — they are records of what already happened, not new billing.
"""
import pytest
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contact import Contact
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.services.import_service import run_preview, run_commit, run_undo

INVOICES_CSV = """Client Email,Client Name,Invoice Date,Due Date,Amount,Amount Paid,Description
amara@example.com,Amara Johnson,2024-01-15,2024-02-15,1500.00,1500.00,Coaching package
bella@example.com,Bella Reyes,2024-03-01,2024-04-01,900.00,0,Discovery series
"""

MAPPING = {
    "Client Email": "contact_email",
    "Client Name": "contact_name",
    "Invoice Date": "issue_date",
    "Due Date": "due_date",
    "Amount": "total",
    "Amount Paid": "amount_paid",
    "Description": "description",
}


class TestInvoicePreview:
    async def test_preview_writes_nothing(self, db_session: AsyncSession):
        result = await run_preview(
            db_session, "invoices", INVOICES_CSV, mapping=MAPPING
        )
        assert result["counts"]["create"] == 2
        invoices = (await db_session.execute(select(Invoice))).scalars().all()
        assert invoices == []

    async def test_row_without_amount_is_error(self, db_session: AsyncSession):
        csv_text = (
            "Client Email,Client Name,Invoice Date,Due Date,Amount,Amount Paid,"
            "Description\nx@example.com,X,2024-01-01,2024-02-01,,0,No amount\n"
        )
        result = await run_preview(
            db_session, "invoices", csv_text, mapping=MAPPING
        )
        assert result["rows"][0]["outcome"] == "error"


class TestInvoiceCommit:
    async def test_creates_invoices_contacts_and_payments(
        self, db_session: AsyncSession
    ):
        job = await run_commit(
            db_session, "invoices", INVOICES_CSV, mapping=MAPPING,
            user_id="admin-1",
        )
        assert job.created_count == 2

        invoices = (
            await db_session.execute(select(Invoice).order_by(Invoice.total.desc()))
        ).scalars().all()
        assert len(invoices) == 2

        paid, unpaid = invoices[0], invoices[1]
        assert paid.total == Decimal("1500.00")
        assert paid.amount_paid == Decimal("1500.00")
        assert paid.balance_due == Decimal("0.00")
        assert paid.status == "paid"
        assert unpaid.balance_due == Decimal("900.00")
        assert unpaid.status != "paid"

        # Contacts auto-created from the invoice rows
        contacts = (await db_session.execute(select(Contact))).scalars().all()
        assert {c.email for c in contacts} == {
            "amara@example.com",
            "bella@example.com",
        }

        # A payment record exists only for the paid invoice
        payments = (await db_session.execute(select(Payment))).scalars().all()
        assert len(payments) == 1
        assert payments[0].amount == Decimal("1500.00")
        assert payments[0].invoice_id == paid.id

    async def test_invoice_numbers_are_unique_within_batch(
        self, db_session: AsyncSession
    ):
        await run_commit(
            db_session, "invoices", INVOICES_CSV, mapping=MAPPING, user_id="a"
        )
        invoices = (await db_session.execute(select(Invoice))).scalars().all()
        numbers = [i.invoice_number for i in invoices]
        assert len(set(numbers)) == len(numbers)

    async def test_links_to_existing_contact_instead_of_duplicating(
        self, db_session: AsyncSession
    ):
        db_session.add(Contact(first_name="Amara", email="amara@example.com"))
        await db_session.commit()

        await run_commit(
            db_session, "invoices", INVOICES_CSV, mapping=MAPPING, user_id="a"
        )
        amaras = (
            await db_session.execute(
                select(Contact).where(Contact.email == "amara@example.com")
            )
        ).scalars().all()
        assert len(amaras) == 1

    async def test_recommit_skips_duplicates(self, db_session: AsyncSession):
        await run_commit(
            db_session, "invoices", INVOICES_CSV, mapping=MAPPING, user_id="a"
        )
        job2 = await run_commit(
            db_session, "invoices", INVOICES_CSV, mapping=MAPPING, user_id="a"
        )
        assert job2.created_count == 0
        assert job2.skipped_count == 2
        invoices = (await db_session.execute(select(Invoice))).scalars().all()
        assert len(invoices) == 2


class TestInvoiceUndo:
    async def test_undo_removes_invoices_and_payments(
        self, db_session: AsyncSession
    ):
        job = await run_commit(
            db_session, "invoices", INVOICES_CSV, mapping=MAPPING, user_id="a"
        )
        result = await run_undo(db_session, job.id)
        assert result["undone"]["invoices"] == 2

        invoices = (await db_session.execute(select(Invoice))).scalars().all()
        assert invoices == []
        payments = (await db_session.execute(select(Payment))).scalars().all()
        assert payments == []
        # Contacts created by the same job are removed too
        contacts = (await db_session.execute(select(Contact))).scalars().all()
        assert contacts == []
