"""Importer v2: ICF coaching-hours log (e.g. Paperbell's ICF export).

Certification hours are the one record a coach genuinely cannot recreate, so
this import matches the existing bulk-import dedupe rule (client + date +
duration) while adding the preview and undo the wizard provides.
"""
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.coaching_session import CoachingSession
from app.services.import_service import run_preview, run_commit, run_undo

ICF_CSV = """Client,Date,Duration,Type,Paid
Amara Johnson,2024-01-15,1.0,individual,paid
Bella Reyes,2024-02-20,1.5,group,pro_bono
"""

MAPPING = {
    "Client": "client_name",
    "Date": "session_date",
    "Duration": "duration_hours",
    "Type": "session_type",
    "Paid": "payment_type",
}


class TestIcfPreview:
    async def test_preview_writes_nothing(self, db_session: AsyncSession):
        result = await run_preview(
            db_session, "icf_sessions", ICF_CSV, mapping=MAPPING
        )
        assert result["counts"]["create"] == 2
        sessions = (await db_session.execute(select(CoachingSession))).scalars().all()
        assert sessions == []

    async def test_row_without_client_or_date_is_error(
        self, db_session: AsyncSession
    ):
        csv_text = "Client,Date,Duration,Type,Paid\n,2024-01-01,1.0,individual,paid\n"
        result = await run_preview(
            db_session, "icf_sessions", csv_text, mapping=MAPPING
        )
        assert result["rows"][0]["outcome"] == "error"


class TestIcfCommit:
    async def test_creates_sessions_with_hours(self, db_session: AsyncSession):
        job = await run_commit(
            db_session, "icf_sessions", ICF_CSV, mapping=MAPPING, user_id="admin-1"
        )
        assert job.created_count == 2

        sessions = (
            await db_session.execute(
                select(CoachingSession).order_by(CoachingSession.session_date)
            )
        ).scalars().all()
        assert [s.client_name for s in sessions] == ["Amara Johnson", "Bella Reyes"]
        assert sessions[0].duration_hours == 1.0
        assert sessions[1].duration_hours == 1.5
        assert sessions[1].session_type == "group"
        assert sessions[1].payment_type == "pro_bono"

    async def test_defaults_applied_when_columns_absent(
        self, db_session: AsyncSession
    ):
        csv_text = "Client,Date\nCarla Diaz,2024-04-04\n"
        await run_commit(
            db_session,
            "icf_sessions",
            csv_text,
            mapping={"Client": "client_name", "Date": "session_date"},
            user_id="a",
        )
        session = (
            await db_session.execute(select(CoachingSession))
        ).scalar_one()
        assert session.duration_hours == 1.0
        assert session.session_type == "individual"

    async def test_recommit_skips_duplicates(self, db_session: AsyncSession):
        await run_commit(
            db_session, "icf_sessions", ICF_CSV, mapping=MAPPING, user_id="a"
        )
        job2 = await run_commit(
            db_session, "icf_sessions", ICF_CSV, mapping=MAPPING, user_id="a"
        )
        assert job2.created_count == 0
        assert job2.skipped_count == 2
        sessions = (await db_session.execute(select(CoachingSession))).scalars().all()
        assert len(sessions) == 2


class TestIcfUndo:
    async def test_undo_removes_sessions(self, db_session: AsyncSession):
        job = await run_commit(
            db_session, "icf_sessions", ICF_CSV, mapping=MAPPING, user_id="a"
        )
        result = await run_undo(db_session, job.id)
        assert result["undone"]["icf_sessions"] == 2
        sessions = (await db_session.execute(select(CoachingSession))).scalars().all()
        assert sessions == []
