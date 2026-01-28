"""
Tests for Client Portal endpoints.
"""
import pytest
from datetime import datetime, timedelta, date
from decimal import Decimal
from unittest.mock import patch, AsyncMock
import uuid

from jose import jwt
from httpx import AsyncClient
from sqlalchemy import select

from app.models.contact import Contact
from app.models.invoice import Invoice
from app.models.contract import Contract
from app.models.booking import Booking
from app.models.booking_type import BookingType
from app.models.project import Project
from app.models.organization import Organization
from app.models.client_session import ClientSession
from app.models.client_note import ClientNote
from app.models.client_action_item import ClientActionItem
from app.models.client_goal import ClientGoal
from app.models.goal_milestone import GoalMilestone
from app.config import get_settings

settings = get_settings()


@pytest.fixture
async def portal_enabled_contact(db_session) -> Contact:
    """Create a contact with portal enabled for client authentication."""
    contact = Contact(
        id=str(uuid.uuid4()),
        first_name="Portal",
        last_name="User",
        email=f"portal_{uuid.uuid4().hex[:8]}@example.com",
        portal_enabled=True,
    )
    db_session.add(contact)
    await db_session.commit()
    await db_session.refresh(contact)
    return contact


@pytest.fixture
async def client_session(db_session, portal_enabled_contact: Contact) -> ClientSession:
    """Create a client session with proper JWT token."""
    session_id = str(uuid.uuid4())
    session_expires = datetime.utcnow() + timedelta(days=7)

    # Create JWT session token
    session_token = jwt.encode(
        {
            "sub": portal_enabled_contact.id,
            "session_id": session_id,
            "exp": session_expires,
            "type": "client",
        },
        settings.secret_key,
        algorithm="HS256",
    )

    session = ClientSession(
        id=session_id,
        contact_id=portal_enabled_contact.id,
        token=str(uuid.uuid4()),  # Magic link token (already used)
        session_token=session_token,  # JWT session token for API calls
        expires_at=session_expires,
        is_active=True,
    )
    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)
    return session


@pytest.fixture
async def client_auth_headers(client_session: ClientSession) -> dict:
    """Get authentication headers for client portal using JWT."""
    return {"Authorization": f"Bearer {client_session.session_token}"}


@pytest.fixture
async def test_invoice_for_client(db_session, portal_enabled_contact: Contact) -> Invoice:
    """Create a test invoice for the client."""
    invoice = Invoice(
        id=str(uuid.uuid4()),
        contact_id=portal_enabled_contact.id,
        invoice_number="INV-TEST-001",
        status="sent",
        subtotal=Decimal("1000.00"),
        total=Decimal("1000.00"),
        balance_due=Decimal("1000.00"),
        due_date=date.today() + timedelta(days=30),
        line_items=[{"description": "Test Service", "quantity": 1, "unit_price": 1000, "amount": 1000}],
        view_token=str(uuid.uuid4()),
    )
    db_session.add(invoice)
    await db_session.commit()
    await db_session.refresh(invoice)
    return invoice


@pytest.fixture
async def test_contract_for_client(db_session, portal_enabled_contact: Contact) -> Contract:
    """Create a test contract for the client."""
    contract = Contract(
        id=str(uuid.uuid4()),
        contact_id=portal_enabled_contact.id,
        contract_number="CON-TEST-001",
        title="Test Contract",
        content="Contract content here",
        status="sent",
        view_token=str(uuid.uuid4()),
    )
    db_session.add(contract)
    await db_session.commit()
    await db_session.refresh(contract)
    return contract


@pytest.fixture
async def test_booking_type_for_client(db_session) -> BookingType:
    """Create a test booking type for client tests."""
    booking_type = BookingType(
        id=str(uuid.uuid4()),
        name="Client Session",
        slug=f"client-session-{uuid.uuid4().hex[:8]}",
        duration_minutes=60,
        is_active=True,
    )
    db_session.add(booking_type)
    await db_session.commit()
    await db_session.refresh(booking_type)
    return booking_type


@pytest.fixture
async def test_booking_for_client(
    db_session, portal_enabled_contact: Contact, test_booking_type_for_client: BookingType
) -> Booking:
    """Create a test booking for the client."""
    booking = Booking(
        id=str(uuid.uuid4()),
        contact_id=portal_enabled_contact.id,
        booking_type_id=test_booking_type_for_client.id,
        start_time=datetime.utcnow() + timedelta(days=7),
        end_time=datetime.utcnow() + timedelta(days=7, hours=1),
        status="confirmed",
    )
    db_session.add(booking)
    await db_session.commit()
    await db_session.refresh(booking)
    return booking


class TestClientDashboard:
    """Tests for client dashboard."""

    @pytest.mark.asyncio
    async def test_get_dashboard_unauthenticated(self, client: AsyncClient):
        """Test dashboard requires authentication."""
        response = await client.get("/api/client/dashboard")
        assert response.status_code in [401, 422]

    @pytest.mark.asyncio
    async def test_get_dashboard_success(
        self, client: AsyncClient, client_auth_headers: dict
    ):
        """Test getting dashboard."""
        response = await client.get(
            "/api/client/dashboard",
            headers=client_auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "stats" in data


class TestClientInvoices:
    """Tests for client invoice endpoints."""

    @pytest.mark.asyncio
    async def test_list_invoices(
        self, client: AsyncClient, client_auth_headers: dict, test_invoice_for_client: Invoice
    ):
        """Test listing client invoices."""
        response = await client.get(
            "/api/client/invoices",
            headers=client_auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_invoice_detail(
        self, client: AsyncClient, client_auth_headers: dict, test_invoice_for_client: Invoice
    ):
        """Test getting invoice detail."""
        response = await client.get(
            f"/api/client/invoices/{test_invoice_for_client.id}",
            headers=client_auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_invoice_for_client.id


class TestClientContracts:
    """Tests for client contract endpoints."""

    @pytest.mark.asyncio
    async def test_list_contracts(
        self, client: AsyncClient, client_auth_headers: dict, test_contract_for_client: Contract
    ):
        """Test listing client contracts."""
        response = await client.get(
            "/api/client/contracts",
            headers=client_auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestClientBookings:
    """Tests for client booking endpoints."""

    @pytest.mark.asyncio
    async def test_list_bookings(
        self, client: AsyncClient, client_auth_headers: dict, test_booking_for_client: Booking
    ):
        """Test listing client bookings."""
        response = await client.get(
            "/api/client/bookings",
            headers=client_auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestClientProfile:
    """Tests for client profile endpoints."""

    @pytest.mark.asyncio
    async def test_get_profile(
        self, client: AsyncClient, client_auth_headers: dict
    ):
        """Test getting client profile."""
        response = await client.get(
            "/api/client/profile",
            headers=client_auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "first_name" in data


class TestClientNotes:
    """Tests for client notes/messaging."""

    @pytest.mark.asyncio
    async def test_list_notes(
        self, client: AsyncClient, client_auth_headers: dict
    ):
        """Test listing notes."""
        response = await client.get(
            "/api/client/notes",
            headers=client_auth_headers,
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_get_unread_count(
        self, client: AsyncClient, client_auth_headers: dict
    ):
        """Test getting unread note count."""
        response = await client.get(
            "/api/client/notes/unread-count",
            headers=client_auth_headers,
        )
        assert response.status_code == 200
        assert "count" in response.json()


class TestClientActionItems:
    """Tests for client action items."""

    @pytest.mark.asyncio
    async def test_list_action_items(
        self, client: AsyncClient, client_auth_headers: dict
    ):
        """Test listing action items."""
        response = await client.get(
            "/api/client/action-items",
            headers=client_auth_headers,
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_get_pending_count(
        self, client: AsyncClient, client_auth_headers: dict
    ):
        """Test getting pending action items count."""
        response = await client.get(
            "/api/client/action-items/pending-count",
            headers=client_auth_headers,
        )
        assert response.status_code == 200
        assert "count" in response.json()


class TestClientGoals:
    """Tests for client goals."""

    @pytest.mark.asyncio
    async def test_list_goals(
        self, client: AsyncClient, client_auth_headers: dict
    ):
        """Test listing goals."""
        response = await client.get(
            "/api/client/goals",
            headers=client_auth_headers,
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_get_goals_stats(
        self, client: AsyncClient, client_auth_headers: dict
    ):
        """Test getting goals statistics."""
        response = await client.get(
            "/api/client/goals/stats/summary",
            headers=client_auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "active_goals" in data or "total_goals" in data


class TestClientTimeline:
    """Tests for client timeline."""

    @pytest.mark.asyncio
    async def test_get_timeline(
        self, client: AsyncClient, client_auth_headers: dict
    ):
        """Test getting timeline."""
        response = await client.get(
            "/api/client/timeline",
            headers=client_auth_headers,
        )
        assert response.status_code == 200


class TestClientResources:
    """Tests for client resources/content."""

    @pytest.mark.asyncio
    async def test_list_resources(
        self, client: AsyncClient, client_auth_headers: dict
    ):
        """Test listing resources."""
        response = await client.get(
            "/api/client/resources",
            headers=client_auth_headers,
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)
