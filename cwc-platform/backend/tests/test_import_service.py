"""Migration importer service: parse, preset-detect, map, validate, dedupe, commit, undo."""
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contact import Contact
from app.models.organization import Organization
from app.models.import_job import ImportJob
from app.services.import_service import (
    parse_csv,
    detect_preset,
    run_preview,
    run_commit,
    run_undo,
)

HONEYBOOK_CONTACTS_CSV = """Contact name,Email address,Phone number,Address,Notes,Date created
Amara Johnson,amara@example.com,555-0101,12 Oak St,VIP client,01/15/2024
Bella Reyes,bella@example.com,555-0102,,Referral from Amara,02/20/2024
"""

GENERIC_CONTACTS_CSV = """first,mail,cell,company
Cora,cora@example.com,555-0201,Acme Coaching
Dee,dee@example.com,,Acme Coaching
"""

GENERIC_MAPPING = {
    "first": "first_name",
    "mail": "email",
    "cell": "phone",
    "company": "organization_name",
}


class TestParseAndDetect:
    def test_parse_csv_returns_headers_and_rows(self):
        headers, rows = parse_csv(HONEYBOOK_CONTACTS_CSV)
        assert headers[0] == "Contact name"
        assert len(rows) == 2
        assert rows[0]["Email address"] == "amara@example.com"

    def test_parse_csv_rejects_empty(self):
        with pytest.raises(ValueError):
            parse_csv("")

    def test_detect_preset_honeybook_contacts(self):
        headers, _ = parse_csv(HONEYBOOK_CONTACTS_CSV)
        assert detect_preset(headers, "contacts") == "honeybook"

    def test_detect_preset_unknown_headers_returns_none(self):
        assert detect_preset(["foo", "bar"], "contacts") is None


class TestPreviewContacts:
    async def test_preview_honeybook_creates_nothing_and_maps_rows(
        self, db_session: AsyncSession
    ):
        result = await run_preview(db_session, "contacts", HONEYBOOK_CONTACTS_CSV)
        assert result["preset"] == "honeybook"
        assert result["counts"]["create"] == 2
        first = result["rows"][0]
        assert first["outcome"] == "create"
        # HoneyBook "Contact name" is split into first/last
        assert first["data"]["first_name"] == "Amara"
        assert first["data"]["last_name"] == "Johnson"
        # nothing written
        db_contacts = (await db_session.execute(select(Contact))).scalars().all()
        assert db_contacts == []

    async def test_preview_flags_duplicate_email_as_skip(
        self, db_session: AsyncSession
    ):
        db_session.add(Contact(first_name="Amara", email="amara@example.com"))
        await db_session.commit()
        result = await run_preview(db_session, "contacts", HONEYBOOK_CONTACTS_CSV)
        outcomes = [r["outcome"] for r in result["rows"]]
        assert outcomes == ["skip_duplicate", "create"]

    async def test_preview_row_without_email_or_phone_is_error(
        self, db_session: AsyncSession
    ):
        csv_text = "first,mail,cell,company\nNoContact,,,\n"
        result = await run_preview(
            db_session, "contacts", csv_text, mapping=GENERIC_MAPPING
        )
        assert result["rows"][0]["outcome"] == "error"
        assert result["counts"]["error"] == 1


class TestCommitContacts:
    async def test_commit_creates_contacts_orgs_and_job(
        self, db_session: AsyncSession
    ):
        job = await run_commit(
            db_session,
            "contacts",
            GENERIC_CONTACTS_CSV,
            mapping=GENERIC_MAPPING,
            dedupe_strategy="skip",
            user_id="admin-1",
        )
        assert job.created_count == 2
        assert job.error_count == 0
        assert job.status == "committed"

        contacts = (await db_session.execute(select(Contact))).scalars().all()
        assert {c.first_name for c in contacts} == {"Cora", "Dee"}
        assert all(c.source == "import:custom" for c in contacts)

        # Both rows share one auto-created organization
        orgs = (await db_session.execute(select(Organization))).scalars().all()
        assert len(orgs) == 1
        assert orgs[0].name == "Acme Coaching"
        assert all(c.organization_id == orgs[0].id for c in contacts)

    async def test_recommit_is_idempotent(self, db_session: AsyncSession):
        await run_commit(
            db_session, "contacts", GENERIC_CONTACTS_CSV,
            mapping=GENERIC_MAPPING, dedupe_strategy="skip", user_id="admin-1",
        )
        job2 = await run_commit(
            db_session, "contacts", GENERIC_CONTACTS_CSV,
            mapping=GENERIC_MAPPING, dedupe_strategy="skip", user_id="admin-1",
        )
        assert job2.created_count == 0
        assert job2.skipped_count == 2
        contacts = (await db_session.execute(select(Contact))).scalars().all()
        assert len(contacts) == 2

    async def test_update_strategy_fills_blanks_only(self, db_session: AsyncSession):
        db_session.add(Contact(first_name="Cora", email="cora@example.com"))
        await db_session.commit()
        await run_commit(
            db_session, "contacts", GENERIC_CONTACTS_CSV,
            mapping=GENERIC_MAPPING, dedupe_strategy="update", user_id="admin-1",
        )
        existing = (
            await db_session.execute(
                select(Contact).where(Contact.email == "cora@example.com")
            )
        ).scalar_one()
        assert existing.phone == "555-0201"  # blank got filled
        assert existing.first_name == "Cora"  # non-empty untouched


class TestUndo:
    async def test_undo_removes_created_records(self, db_session: AsyncSession):
        job = await run_commit(
            db_session, "contacts", GENERIC_CONTACTS_CSV,
            mapping=GENERIC_MAPPING, dedupe_strategy="skip", user_id="admin-1",
        )
        result = await run_undo(db_session, job.id)
        assert result["undone"]["contacts"] == 2
        contacts = (await db_session.execute(select(Contact))).scalars().all()
        assert contacts == []
        orgs = (await db_session.execute(select(Organization))).scalars().all()
        assert orgs == []  # org created by this job and now empty -> removed
        refreshed = (
            await db_session.execute(select(ImportJob).where(ImportJob.id == job.id))
        ).scalar_one()
        assert refreshed.status == "undone"

    async def test_undo_twice_rejected(self, db_session: AsyncSession):
        job = await run_commit(
            db_session, "contacts", GENERIC_CONTACTS_CSV,
            mapping=GENERIC_MAPPING, dedupe_strategy="skip", user_id="admin-1",
        )
        await run_undo(db_session, job.id)
        with pytest.raises(ValueError):
            await run_undo(db_session, job.id)
