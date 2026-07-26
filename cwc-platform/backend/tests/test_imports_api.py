"""Migration importer API: admin-gated preview/commit/undo/history/presets."""
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contact import Contact

CSV = """Contact name,Email address,Phone number,Address,Notes,Date created
Amara Johnson,amara@example.com,555-0101,12 Oak St,VIP client,01/15/2024
"""


class TestImportsAuth:
    async def test_preview_requires_auth(self, client: AsyncClient):
        response = await client.post(
            "/api/imports/preview", json={"entity_type": "contacts", "csv_text": CSV}
        )
        assert response.status_code in (401, 403)

    async def test_preview_rejects_non_admin(
        self, client: AsyncClient, nonadmin_headers: dict
    ):
        response = await client.post(
            "/api/imports/preview",
            json={"entity_type": "contacts", "csv_text": CSV},
            headers=nonadmin_headers,
        )
        assert response.status_code == 403

    async def test_commit_rejects_non_admin(
        self, client: AsyncClient, nonadmin_headers: dict
    ):
        response = await client.post(
            "/api/imports/commit",
            json={"entity_type": "contacts", "csv_text": CSV},
            headers=nonadmin_headers,
        )
        assert response.status_code == 403


class TestImportsFlow:
    async def test_presets_listed(self, client: AsyncClient, auth_headers: dict):
        response = await client.get("/api/imports/presets", headers=auth_headers)
        assert response.status_code == 200
        names = [p["name"] for p in response.json()]
        assert "honeybook" in names

    async def test_preview_returns_outcomes_writes_nothing(
        self, client: AsyncClient, auth_headers: dict, db_session: AsyncSession
    ):
        response = await client.post(
            "/api/imports/preview",
            json={"entity_type": "contacts", "csv_text": CSV},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["preset"] == "honeybook"
        assert data["counts"]["create"] == 1
        contacts = (await db_session.execute(select(Contact))).scalars().all()
        assert contacts == []

    async def test_preview_bad_csv_is_400(
        self, client: AsyncClient, auth_headers: dict
    ):
        response = await client.post(
            "/api/imports/preview",
            json={"entity_type": "contacts", "csv_text": "   "},
            headers=auth_headers,
        )
        assert response.status_code == 400

    async def test_commit_then_history_then_undo(
        self, client: AsyncClient, auth_headers: dict, db_session: AsyncSession
    ):
        commit = await client.post(
            "/api/imports/commit",
            json={"entity_type": "contacts", "csv_text": CSV},
            headers=auth_headers,
        )
        assert commit.status_code == 201
        job = commit.json()
        assert job["created_count"] == 1
        assert job["source"] == "honeybook"

        history = await client.get("/api/imports", headers=auth_headers)
        assert history.status_code == 200
        assert any(j["id"] == job["id"] for j in history.json())

        undo = await client.post(
            f"/api/imports/{job['id']}/undo", headers=auth_headers
        )
        assert undo.status_code == 200
        contacts = (await db_session.execute(select(Contact))).scalars().all()
        assert contacts == []

        undo_again = await client.post(
            f"/api/imports/{job['id']}/undo", headers=auth_headers
        )
        assert undo_again.status_code == 400
