"""STEP 2a: contracts, projects, tasks routers are admin-only (router-level gate)."""
import pytest
from httpx import AsyncClient


class TestRouterLevelAdminGate:
    async def test_contracts_rejects_non_admin(
        self, client: AsyncClient, nonadmin_headers: dict
    ):
        response = await client.get("/api/contracts", headers=nonadmin_headers)
        assert response.status_code == 403

    async def test_projects_rejects_non_admin(
        self, client: AsyncClient, nonadmin_headers: dict
    ):
        response = await client.get("/api/projects", headers=nonadmin_headers)
        assert response.status_code == 403

    async def test_tasks_rejects_non_admin(
        self, client: AsyncClient, nonadmin_headers: dict
    ):
        response = await client.get("/api/tasks", headers=nonadmin_headers)
        assert response.status_code == 403

    async def test_contracts_allows_admin(
        self, client: AsyncClient, auth_headers: dict
    ):
        response = await client.get("/api/contracts", headers=auth_headers)
        assert response.status_code == 200

    async def test_projects_allows_admin(
        self, client: AsyncClient, auth_headers: dict
    ):
        response = await client.get("/api/projects", headers=auth_headers)
        assert response.status_code == 200

    async def test_tasks_allows_admin(self, client: AsyncClient, auth_headers: dict):
        response = await client.get("/api/tasks", headers=auth_headers)
        assert response.status_code == 200


class TestPerEndpointAdminGate:
    """STEP 2b: staff-CRM routers gated per-endpoint, reads included."""

    ROUTES = [
        "/api/contacts",
        "/api/goals",
        "/api/action-items",
        "/api/content",
        "/api/extractions",
        "/api/organizations",
    ]

    @pytest.mark.parametrize("route", ROUTES)
    async def test_list_rejects_non_admin(
        self, client: AsyncClient, nonadmin_headers: dict, route: str
    ):
        response = await client.get(route, headers=nonadmin_headers)
        assert response.status_code == 403, route

    @pytest.mark.parametrize("route", ROUTES)
    async def test_list_allows_admin(
        self, client: AsyncClient, auth_headers: dict, route: str
    ):
        response = await client.get(route, headers=auth_headers)
        assert response.status_code == 200, route

    async def test_contact_create_rejects_non_admin(
        self, client: AsyncClient, nonadmin_headers: dict
    ):
        response = await client.post(
            "/api/contacts",
            json={"first_name": "Blocked", "email": "blocked@example.com"},
            headers=nonadmin_headers,
        )
        assert response.status_code == 403
