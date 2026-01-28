"""
Tests for ICF Hours Tracker endpoints.
"""
import pytest
from unittest.mock import patch, AsyncMock
from datetime import datetime, date, timedelta
import uuid

from httpx import AsyncClient
from sqlalchemy import select

from app.models.coaching_session import CoachingSession
from app.models.contact import Contact


@pytest.fixture
async def test_coaching_session(db_session, test_contact: Contact) -> CoachingSession:
    """Create a test coaching session."""
    session = CoachingSession(
        id=str(uuid.uuid4()),
        contact_id=test_contact.id,
        client_name=f"{test_contact.first_name} {test_contact.last_name or ''}".strip(),
        client_email=test_contact.email,
        session_date=date.today() - timedelta(days=7),
        session_type="individual",
        duration_hours=1.0,
        payment_type="paid",
        source="manual",
        notes="Initial coaching session - goal setting",
        is_verified=True,
    )
    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)
    return session


class TestICFSummary:
    """Tests for ICF summary statistics."""

    @pytest.mark.asyncio
    async def test_get_summary_unauthenticated(self, client: AsyncClient):
        """Test summary requires authentication."""
        response = await client.get("/api/icf-tracker/summary")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_summary_empty(self, auth_client: AsyncClient):
        """Test summary with no sessions."""
        response = await auth_client.get("/api/icf-tracker/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["total_hours"] == 0
        assert data["total_sessions"] == 0

    @pytest.mark.asyncio
    async def test_get_summary_with_sessions(
        self, auth_client: AsyncClient, test_coaching_session: CoachingSession
    ):
        """Test summary with existing sessions."""
        response = await auth_client.get("/api/icf-tracker/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["total_hours"] >= 1
        assert data["total_sessions"] >= 1

    @pytest.mark.asyncio
    async def test_summary_by_payment_type(
        self, db_session, auth_client: AsyncClient, test_contact: Contact
    ):
        """Test summary shows breakdown by payment type."""
        # Create sessions with different payment types
        for payment_type in ["paid", "pro_bono"]:
            session = CoachingSession(
                id=str(uuid.uuid4()),
                contact_id=test_contact.id,
                client_name=f"{test_contact.first_name} Test",
                session_date=date.today() - timedelta(days=1),
                session_type="individual",
                duration_hours=1.0,
                payment_type=payment_type,
                source="manual",
            )
            db_session.add(session)
        await db_session.commit()

        response = await auth_client.get("/api/icf-tracker/summary")
        assert response.status_code == 200
        data = response.json()
        assert "paid_hours" in data
        assert "pro_bono_hours" in data


class TestListSessions:
    """Tests for listing coaching sessions."""

    @pytest.mark.asyncio
    async def test_list_sessions_empty(self, auth_client: AsyncClient):
        """Test listing sessions when none exist."""
        response = await auth_client.get("/api/icf-tracker")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_list_sessions_with_data(
        self, auth_client: AsyncClient, test_coaching_session: CoachingSession
    ):
        """Test listing sessions with existing data."""
        response = await auth_client.get("/api/icf-tracker")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 1
        assert data["total"] >= 1

    @pytest.mark.asyncio
    async def test_list_sessions_filter_by_type(
        self, db_session, auth_client: AsyncClient, test_contact: Contact
    ):
        """Test filtering sessions by type."""
        # Create sessions of different types
        for stype in ["individual", "group"]:
            session = CoachingSession(
                id=str(uuid.uuid4()),
                contact_id=test_contact.id,
                client_name=f"{test_contact.first_name} Test",
                session_date=date.today(),
                session_type=stype,
                duration_hours=1.0,
                payment_type="paid",
                source="manual",
            )
            db_session.add(session)
        await db_session.commit()

        response = await auth_client.get(
            "/api/icf-tracker",
            params={"session_type": "group"}
        )
        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item["session_type"] == "group"

    @pytest.mark.asyncio
    async def test_list_sessions_filter_by_date_range(
        self, db_session, auth_client: AsyncClient, test_contact: Contact
    ):
        """Test filtering sessions by date range."""
        # Create sessions across different dates
        dates = [
            date.today() - timedelta(days=30),
            date.today() - timedelta(days=15),
            date.today(),
        ]
        for d in dates:
            session = CoachingSession(
                id=str(uuid.uuid4()),
                contact_id=test_contact.id,
                client_name=f"{test_contact.first_name} Test",
                session_date=d,
                session_type="individual",
                duration_hours=1.0,
                payment_type="paid",
                source="manual",
            )
            db_session.add(session)
        await db_session.commit()

        # Filter last 20 days
        start_date = date.today() - timedelta(days=20)
        response = await auth_client.get(
            "/api/icf-tracker",
            params={"start_date": start_date.isoformat()}
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_list_sessions_pagination(
        self, db_session, auth_client: AsyncClient, test_contact: Contact
    ):
        """Test session list pagination."""
        # Create multiple sessions
        for i in range(10):
            session = CoachingSession(
                id=str(uuid.uuid4()),
                contact_id=test_contact.id,
                client_name=f"Client {i}",
                session_date=date.today() - timedelta(days=i),
                session_type="individual",
                duration_hours=1.0,
                payment_type="paid",
                source="manual",
            )
            db_session.add(session)
        await db_session.commit()

        response = await auth_client.get(
            "/api/icf-tracker",
            params={"page": 1, "size": 5}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) <= 5
        assert data["page"] == 1
        assert data["size"] == 5


class TestCreateSession:
    """Tests for creating coaching sessions."""

    @pytest.mark.asyncio
    async def test_create_session_unauthenticated(self, client: AsyncClient):
        """Test session creation requires authentication."""
        response = await client.post(
            "/api/icf-tracker",
            json={
                "client_name": "Test Client",
                "session_date": date.today().isoformat(),
                "session_type": "individual",
                "duration_hours": 1.0,
            }
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_session_success(
        self, auth_client: AsyncClient, test_contact: Contact
    ):
        """Test successful session creation."""
        response = await auth_client.post(
            "/api/icf-tracker",
            json={
                "contact_id": test_contact.id,
                "client_name": f"{test_contact.first_name} {test_contact.last_name or ''}".strip(),
                "client_email": test_contact.email,
                "session_date": date.today().isoformat(),
                "session_type": "individual",
                "duration_hours": 1.5,
                "payment_type": "paid",
                "notes": "Career development session",
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["duration_hours"] == 1.5
        assert data["session_type"] == "individual"

    @pytest.mark.asyncio
    async def test_create_session_without_contact(self, auth_client: AsyncClient):
        """Test session creation without linking to contact."""
        response = await auth_client.post(
            "/api/icf-tracker",
            json={
                "client_name": "New Client",
                "session_date": date.today().isoformat(),
                "session_type": "group",
                "duration_hours": 2.0,
                "group_size": 5,
                "payment_type": "paid",
                "notes": "Group coaching workshop",
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["client_name"] == "New Client"

    @pytest.mark.asyncio
    async def test_create_session_invalid_contact(self, auth_client: AsyncClient):
        """Test session creation with invalid contact."""
        response = await auth_client.post(
            "/api/icf-tracker",
            json={
                "contact_id": str(uuid.uuid4()),
                "client_name": "Test Client",
                "session_date": date.today().isoformat(),
                "session_type": "individual",
                "duration_hours": 1.0,
            }
        )
        assert response.status_code == 400


class TestGetSession:
    """Tests for getting a single session."""

    @pytest.mark.asyncio
    async def test_get_session_not_found(self, auth_client: AsyncClient):
        """Test getting non-existent session."""
        response = await auth_client.get(f"/api/icf-tracker/{uuid.uuid4()}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_session_success(
        self, auth_client: AsyncClient, test_coaching_session: CoachingSession
    ):
        """Test getting existing session."""
        response = await auth_client.get(f"/api/icf-tracker/{test_coaching_session.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_coaching_session.id


class TestUpdateSession:
    """Tests for updating coaching sessions."""

    @pytest.mark.asyncio
    async def test_update_session_not_found(self, auth_client: AsyncClient):
        """Test updating non-existent session."""
        response = await auth_client.put(
            f"/api/icf-tracker/{uuid.uuid4()}",
            json={"duration_hours": 2.0}
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_session_success(
        self, auth_client: AsyncClient, test_coaching_session: CoachingSession
    ):
        """Test successful session update."""
        response = await auth_client.put(
            f"/api/icf-tracker/{test_coaching_session.id}",
            json={
                "duration_hours": 2.0,
                "notes": "Updated notes - extended session",
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["duration_hours"] == 2.0
        assert "Updated notes" in data["notes"]

    @pytest.mark.asyncio
    async def test_update_session_verify(
        self, auth_client: AsyncClient, test_coaching_session: CoachingSession
    ):
        """Test verifying a session."""
        response = await auth_client.put(
            f"/api/icf-tracker/{test_coaching_session.id}",
            json={"is_verified": True}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_verified"] is True


class TestDeleteSession:
    """Tests for deleting coaching sessions."""

    @pytest.mark.asyncio
    async def test_delete_session_not_found(self, auth_client: AsyncClient):
        """Test deleting non-existent session."""
        response = await auth_client.delete(f"/api/icf-tracker/{uuid.uuid4()}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_session_success(
        self, db_session, auth_client: AsyncClient, test_coaching_session: CoachingSession
    ):
        """Test successful session deletion."""
        session_id = test_coaching_session.id
        response = await auth_client.delete(f"/api/icf-tracker/{session_id}")
        assert response.status_code == 204

        # Verify session is deleted
        result = await db_session.execute(
            select(CoachingSession).where(CoachingSession.id == session_id)
        )
        assert result.scalar_one_or_none() is None


class TestByClient:
    """Tests for hours by client."""

    @pytest.mark.asyncio
    async def test_get_by_client_empty(self, auth_client: AsyncClient):
        """Test getting hours by client when empty."""
        response = await auth_client.get("/api/icf-tracker/by-client")
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_get_by_client_with_data(
        self, auth_client: AsyncClient, test_coaching_session: CoachingSession
    ):
        """Test getting hours by client with data."""
        response = await auth_client.get("/api/icf-tracker/by-client")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert "total_hours" in data[0]
        assert "client_name" in data[0]


class TestBulkImport:
    """Tests for bulk session import."""

    @pytest.mark.asyncio
    async def test_bulk_import_empty(self, auth_client: AsyncClient):
        """Test bulk import with empty data."""
        response = await auth_client.post(
            "/api/icf-tracker/bulk-import",
            json={"sessions": []}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["imported"] == 0

    @pytest.mark.asyncio
    async def test_bulk_import_success(
        self, auth_client: AsyncClient, test_contact: Contact
    ):
        """Test successful bulk import."""
        sessions = [
            {
                "contact_id": test_contact.id,
                "client_name": f"Client {i}",
                "session_date": (date.today() - timedelta(days=i)).isoformat(),
                "session_type": "individual",
                "duration_hours": 1.0,
                "payment_type": "paid",
            }
            for i in range(5)
        ]

        response = await auth_client.post(
            "/api/icf-tracker/bulk-import",
            json={"sessions": sessions}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["imported"] == 5

    @pytest.mark.asyncio
    async def test_bulk_import_skip_duplicates(
        self, auth_client: AsyncClient, test_coaching_session: CoachingSession
    ):
        """Test bulk import skips duplicates."""
        sessions = [
            {
                "client_name": test_coaching_session.client_name,
                "session_date": test_coaching_session.session_date.isoformat(),
                "session_type": "individual",
                "duration_hours": test_coaching_session.duration_hours,
                "payment_type": "paid",
            }
        ]

        response = await auth_client.post(
            "/api/icf-tracker/bulk-import",
            json={"sessions": sessions}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["skipped"] >= 1


class TestVerifyAll:
    """Tests for verifying all sessions."""

    @pytest.mark.asyncio
    async def test_verify_all_empty(self, auth_client: AsyncClient):
        """Test verify all with no sessions."""
        response = await auth_client.post("/api/icf-tracker/verify-all")
        assert response.status_code == 200
        data = response.json()
        assert data["verified"] == 0

    @pytest.mark.asyncio
    async def test_verify_all_success(
        self, db_session, auth_client: AsyncClient, test_contact: Contact
    ):
        """Test verify all sessions."""
        # Create unverified sessions
        for i in range(3):
            session = CoachingSession(
                id=str(uuid.uuid4()),
                contact_id=test_contact.id,
                client_name=f"Client {i}",
                session_date=date.today() - timedelta(days=i),
                session_type="individual",
                duration_hours=1.0,
                payment_type="paid",
                source="manual",
                is_verified=False,
            )
            db_session.add(session)
        await db_session.commit()

        response = await auth_client.post("/api/icf-tracker/verify-all")
        assert response.status_code == 200
        data = response.json()
        assert data["verified"] == 3


class TestCertificationDashboard:
    """Tests for ICF certification dashboard."""

    @pytest.mark.asyncio
    async def test_get_certification_dashboard(self, auth_client: AsyncClient):
        """Test getting certification dashboard."""
        response = await auth_client.get("/api/icf-tracker/certification/dashboard")
        assert response.status_code == 200
        data = response.json()
        assert "total_coaching_hours" in data
        assert "requirements" in data
        assert "acc_ready" in data
        assert "pcc_ready" in data

    @pytest.mark.asyncio
    async def test_certification_progress_created_on_first_access(
        self, auth_client: AsyncClient
    ):
        """Test certification progress is auto-created."""
        response = await auth_client.get("/api/icf-tracker/certification/progress")
        assert response.status_code == 200
        data = response.json()
        assert "id" in data


class TestExportCSV:
    """Tests for CSV export."""

    @pytest.mark.asyncio
    async def test_export_csv_empty(self, auth_client: AsyncClient):
        """Test CSV export with no sessions."""
        response = await auth_client.get("/api/icf-tracker/export/csv")
        assert response.status_code == 200
        assert "text/csv" in response.headers.get("content-type", "")

    @pytest.mark.asyncio
    async def test_export_csv_with_data(
        self, auth_client: AsyncClient, test_coaching_session: CoachingSession
    ):
        """Test CSV export with sessions."""
        response = await auth_client.get("/api/icf-tracker/export/csv")
        assert response.status_code == 200
        assert "text/csv" in response.headers.get("content-type", "")
        # CSV should contain data
        content = response.text
        assert "Client Name" in content
