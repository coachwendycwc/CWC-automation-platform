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
