"""The assistant role: a coach's assistant runs client work, not the money.

Assistants reach the CRM and delivery surfaces (contacts, projects, tasks,
goals, content) but never revenue, payouts, or contractor tax data. Everything
else keeps failing closed, so a new role can't silently widen access.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services.auth_service import create_access_token, hash_password

STAFF_ROUTES = [
    "/api/contacts",
    "/api/projects",
    "/api/tasks",
    "/api/goals",
    "/api/action-items",
    "/api/content",
    "/api/organizations",
    "/api/contracts",
]

ADMIN_ONLY_ROUTES = [
    "/api/invoices",
    "/api/payments",
    "/api/subscriptions",
    "/api/contractors",
    "/api/imports",
]


@pytest.fixture
async def assistant_user(db_session: AsyncSession) -> User:
    user = User(
        email="assistant@example.com",
        name="Assistant",
        password_hash=hash_password("assistpass123"),
        role="assistant",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def assistant_headers(assistant_user: User) -> dict:
    token = create_access_token(data={"sub": str(assistant_user.id)})
    return {"Authorization": f"Bearer {token}"}


class TestAssistantCanRunClientWork:
    @pytest.mark.parametrize("route", STAFF_ROUTES)
    async def test_assistant_reaches_staff_surfaces(
        self, client: AsyncClient, assistant_headers: dict, route: str
    ):
        response = await client.get(route, headers=assistant_headers)
        assert response.status_code == 200, route

    async def test_assistant_can_create_a_contact(
        self, client: AsyncClient, assistant_headers: dict
    ):
        response = await client.post(
            "/api/contacts",
            json={"first_name": "New", "email": "new-client@example.com"},
            headers=assistant_headers,
        )
        assert response.status_code in (200, 201)


class TestAssistantCannotReachTheMoney:
    @pytest.mark.parametrize("route", ADMIN_ONLY_ROUTES)
    async def test_assistant_blocked_from_financial_surfaces(
        self, client: AsyncClient, assistant_headers: dict, route: str
    ):
        response = await client.get(route, headers=assistant_headers)
        assert response.status_code == 403, route

    async def test_assistant_cannot_invite_users(
        self, client: AsyncClient, assistant_headers: dict
    ):
        response = await client.post(
            "/api/auth/invites",
            json={"email": "someone@example.com", "role": "admin"},
            headers=assistant_headers,
        )
        assert response.status_code == 403


class TestOtherRolesUnchanged:
    async def test_plain_user_still_blocked_from_staff_surfaces(
        self, client: AsyncClient, nonadmin_headers: dict
    ):
        response = await client.get("/api/contacts", headers=nonadmin_headers)
        assert response.status_code == 403

    async def test_admin_still_reaches_everything(
        self, client: AsyncClient, auth_headers: dict
    ):
        for route in STAFF_ROUTES + ["/api/invoices"]:
            response = await client.get(route, headers=auth_headers)
            assert response.status_code == 200, route


class TestAssistantInvites:
    async def test_admin_can_invite_an_assistant(
        self, client: AsyncClient, auth_headers: dict
    ):
        from unittest.mock import AsyncMock, patch

        with patch(
            "app.routers.auth.email_service.send_user_invite",
            new_callable=AsyncMock,
            return_value=True,
        ):
            response = await client.post(
                "/api/auth/invites",
                json={"email": "newassistant@example.com", "role": "assistant"},
                headers=auth_headers,
            )
        assert response.status_code == 201
        assert response.json()["role"] == "assistant"
